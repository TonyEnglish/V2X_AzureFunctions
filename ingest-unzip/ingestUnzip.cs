// Default URL for triggering event grid function in the local environment.
// http://localhost:7071/runtime/webhooks/EventGrid?functionName={functionname}
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.EventGrid;
using Microsoft.Extensions.Logging;
using Azure.Storage.Blobs;
using Microsoft.WindowsAzure.Storage;
using Microsoft.WindowsAzure.Storage.Blob;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace Company.Function
{
    public static class ingestUnzip
    {
        [FunctionName("ingest-unzip")]
        public static async Task Run([EventGridTrigger] JObject eventGridEvent, ILogger log)
        {
            log.LogInformation(eventGridEvent.ToString(Formatting.Indented));
            string fileName = Path.GetFileName(eventGridEvent["subject"].ToString());
            string connectionString = Environment.GetEnvironmentVariable("destinationStorage");
            string containerName1 = "unapprovedworkzones";
            string containerName2 = "publishedconfigfiles";
            try
            {
                if (!(((IEnumerable<string>)fileName.Split('.')).Last<string>().ToLower() == "zip"))
                    return;
                CloudStorageAccount cloudStorageAccount = CloudStorageAccount.Parse(connectionString);

                BlobServiceClient blobServiceClient = new BlobServiceClient(connectionString);
                BlobContainerClient containerClient = blobServiceClient.GetBlobContainerClient(containerName1);
                BlobContainerClient configContainerClient = blobServiceClient.GetBlobContainerClient(containerName2);

                CloudBlockBlob cloudBlockBlob = new CloudBlockBlob(new Uri(eventGridEvent["data"]["url"].ToString()), cloudStorageAccount.Credentials);
                bool configUpdated = false;
                bool needsImage = false;
                bool isConfig = false;
                IDictionary<string, string> metadata = new Dictionary<string, string>();
                using (MemoryStream blobMemStream = new MemoryStream())
                {
                    await cloudBlockBlob.DownloadToStreamAsync(blobMemStream);
                    using (ZipArchive archive = new ZipArchive(blobMemStream))
                    {
                        List<Tuple<BlobClient, ZipArchiveEntry>> blobsToUpload = new List<Tuple<BlobClient, ZipArchiveEntry>>();
                        foreach (ZipArchiveEntry entry in archive.Entries)
                        {
                            configUpdated = false;
                            needsImage = false;
                            isConfig = false;
                            log.LogInformation("Now processing " + entry.FullName);
                            string blobName = Regex.Replace(entry.Name, "[^a-zA-Z0-9.\\-]", "-").ToLower();
                            string str = "unidentified";
                            if (blobName.Contains(".csv"))
                                str = "pathdatafiles";
                            else if (blobName.Contains(".json"))
                            {
                                str = "configurationfiles";
                                isConfig = true;
                                if (blobName.Contains("-updated"))
                                {
                                    log.LogInformation("Updated config file found");
                                    blobName = blobName.Replace("-updated", "");
                                    configUpdated = true;
                                    if (blobName.Contains("-needsimage"))
                                    {
                                        log.LogInformation("Config file needs updated image");
                                        blobName = blobName.Replace("-needsimage", "");
                                        needsImage = true;
                                    }
                                }
                            }
                            else if (blobName.Contains(".geojson"))
                                str = "wzdxfiles";
                            else if (blobName.Contains(".xml"))
                                str = "rsm-xmlfiles";
                            else if (blobName.Contains(".uper"))
                                str = "rsm-uperfiles";
                            log.LogInformation("Upload path: " + str + "/" + blobName);
                            log.LogInformation("blob list: " + blobsToUpload.Count);
                            BlobClient blockBlobReference = containerClient.GetBlobClient(str + "/" + blobName);
                            blobsToUpload.Add(new Tuple<BlobClient, ZipArchiveEntry>(blockBlobReference, entry));
                            log.LogInformation("blob list: " + blobsToUpload.Count);

                            if (isConfig)
                            {
                                using (Stream fileStream = entry.Open())
                                {
                                    if (str == "unidentified")
                                        log.LogInformation("Unable to identify file: " + str + "/" + blobName);
                                    if (isConfig)
                                    {
                                        BlobClient blockBlobConfig = configContainerClient.GetBlobClient(blobName);
                                        string filePath = Path.GetTempPath() + "\\configFile";
                                        string end = new StreamReader(fileStream).ReadToEnd();

                                        JObject configObj = JObject.Parse(end);

                                        metadata = new Dictionary<string, string>
                                        {
                                            { "center_lat", (string)configObj["ImageInfo"]["Center"]["Lat"] },
                                            { "center_lon", (string)configObj["ImageInfo"]["Center"]["Lon"] }
                                        };
                                        log.LogInformation("metadata: " + metadata);

                                        if (configUpdated)
                                        {
                                            if (needsImage)
                                            {
                                                configObj["ImageInfo"]["ImageString"] = getMapString(configObj, log);
                                                end = configObj.ToString();
                                            }
                                            using (StreamWriter streamWriter = new StreamWriter(filePath))
                                                streamWriter.Write(end);

                                            using (FileStream uploadFileStream = File.OpenRead(filePath))
                                            {
                                                await blockBlobConfig.UploadAsync(uploadFileStream, overwrite: true);
                                            }

                                            File.Delete(filePath);
                                        }
                                        blockBlobConfig = null;
                                        filePath = null;
                                    }
                                }
                            }
                        }

                        log.LogInformation("blob list: " + blobsToUpload.Count);
                        foreach (Tuple<BlobClient, ZipArchiveEntry> blob in blobsToUpload)
                        {
                            log.LogInformation("Uploading file");
                            using (Stream fileStream = blob.Item2.Open())
                            {
                                await blob.Item1.UploadAsync(fileStream, overwrite: true);
                                await blob.Item1.SetMetadataAsync(metadata);
                                log.LogInformation("Upload path: " + blob.Item1.GetProperties());
                            }
                        }
                    }
                }
                containerClient = null;
                configContainerClient = null;
            }
            catch (Exception ex)
            {
                log.LogInformation("Error! Something went wrong: " + ex.Message);
            }
        }

        public static string getMapString(JObject configObj, ILogger log)
        {
            int zoom = int.Parse((string)configObj["ImageInfo"]["Zoom"]);
            string center = (string)configObj["ImageInfo"]["Center"]["Lat"] + "," + (string)configObj["ImageInfo"]["Center"]["Lon"];
            IList<JObject> jobjectList = configObj["ImageInfo"]["Markers"].ToObject<IList<JObject>>();
            List<string> markers = new List<string>();
            foreach (JObject jobject in jobjectList)
            {
                string str = "markers=color:" + jobject["Color"].ToString().ToLower() + "|label:" + jobject["Name"].ToString() + "|" + jobject["Location"]["Lat"].ToString() + "," + jobject["Location"]["Lon"].ToString() + "|";
                markers.Add(str);
            }
            string maptype = (string)configObj["ImageInfo"]["MapType"];
            int num1 = int.Parse((string)configObj["ImageInfo"]["Height"]);
            int num2 = int.Parse((string)configObj["ImageInfo"]["Width"]);
            string imgsize = num1.ToString() + "x" + num2.ToString();
            string imgformat = (string)configObj["ImageInfo"]["Format"];
            string staticMap = getStaticMap("mapImage", center, zoom, log, imgsize, imgformat, maptype, markers);
            byte[] inArray = File.ReadAllBytes(staticMap);
            File.Delete(staticMap);

            return Convert.ToBase64String(inArray);
        }

        public static string getStaticMap(
        string filename_wo_extension,
        string center,
        int zoom,
        ILogger log,
        string imgsize = "640x640",
        string imgformat = "jpeg",
        string maptype = "roadmap",
        List<string> markers = null)
        {
            string str1 = "http://maps.google.com/maps/api/staticmap?";
            string environmentVariable = Environment.GetEnvironmentVariable("GoogleMapsAPIKey");
            string str2 = str1 + string.Format("key={0}&", environmentVariable) + string.Format("center={0}&", center) + string.Format("zoom={0}&", zoom) + string.Format("size={0}&", imgsize) + string.Format("format={0}&", imgformat) + "bearing=90&";
            if (markers != null)
            {
                foreach (string marker in markers)
                    str2 += string.Format("{0}&", marker);
            }
            string address = str2.TrimEnd('&');
            log.LogInformation("Map image request (without API key): " + address.Replace(environmentVariable, ""));
            string fileName = Path.GetTempPath() + "\\" + filename_wo_extension + "." + imgformat;
            using (WebClient webClient = new WebClient())
                webClient.DownloadFile(address, fileName);
            return fileName;
        }
    }
}