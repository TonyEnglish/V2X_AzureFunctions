#!/usr/bin/env python3
###
#   This software module to:
#   A. Parse the vehicle path data collected through traversing WZ lanes
#       A.1 construct node points for representing lane geometry for both approach and WZ lanes 
#           a. WZ map - Read collected vehicle path data file - lat,lon,elev,heading,speed,time, and few other elements
#           a. reference point - start of WZ   
#           b. approach lane geometry
#           b. WZ lane geometry 
#       A.2 Lane attributes
#           a. Lane closures (both offset from RP and nodeAttributeXYlist of taperToLeft and taperToRight
#           b. Support of opening of the closed lane up to 4 times
#           c.Presence of workers at designated area (zone) support of up to 4 zones 
#       A.3 WZ length
#       A.4 eventID, Duration, speed limits. etc.
#
#   B. Construct .exer (XML Format) file for WZ as prescribed in ASN.1 for RSM (SAE J2945/4 WIP) including:
#   C. Construct .js (javaScript) file containing several arrays for visualization overlay on Google Satellite map

#
#   By J. Parikh / Nov, 2017
#   Revised June 2018
#   Revised Aug  2018
#
#   Ver 2.0 -   Proposed new RSM/XML(EXER) for ASN.1 and map visualization
#
###

import os.path
import sys
import subprocess
import urllib
import requests
import base64

import tempfile

###
#     Open and read csv file...    
###

import  logging
import  re
import  csv                                             #csv file processor
import  datetime                                        #Date and Time methods...
import  time                                            #do I need time???
import  math                                            #math library for math functions
import  random                                          #random number generator
import  xmltodict                                       #dict to xml converter
import  json                                            #json manipulation
import  zipfile
import  requests

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

from . import wz_vehpath_lanestat_builder

from . import wz_map_constructor

from . import wz_xml_builder

from . import rsm_2_wzdx_translator

from . import wz_msg_segmentation


###
#   Following to get user input for WZ config file name and display output for user...
### ---------------------------------------------------------------------------------------------------------------------

###
#   User input/output for work zone map builder is created using 'Tkinter' (TK Interface) module. The  Tkinter
#   is the standard Python interface to the Tk GUI toolkit from Scriptics (formerly developed by Sun Labs).
#
#   The public interface is provided through a number of Python modules. The most important interface module is the
#   Tkinter module itself.
#
#   Just import the Tkinter module to use
#
###

###


###
#   Following added to read and parse WZ config file
###


connect_str_env_var = 'neaeraiotstorage_storage'
connect_str = os.getenv(connect_str_env_var)
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

### ------------------------------------------------------------------------------------------------------------------
#
#   Local methods/functions...
###

###
#   ACTIONS... input file dialog...
###

def inputFileDialog(filename):

    if len(filename): 
        configRead(filename)
    pass

##
#   -------------- End of input_file_dialog ------------------
##

def buildWZMap(filename):
    
    startMainProcess()

    if msgSegList[0][0] == -1:                          #Segmentation failed...
        error = True
        # logMsg('Error in building message segmentation')
    # else:
        # logMsg('WZ Map Completed Successfully\nReview map_builder.log file in WP_MapMsg Folder...')

##
#   -------------- End of build_WZ_map ------------------------
##

# def viewMapLogFile():
  
#     WZ_mapLogFile = './WZ_MapMsg/map_builder_log.txt'
#     if os.path.exists(WZ_mapLogFile):
#         os.system('notepad ' + WZ_mapLogFile)        
    
#     else:
#         messagebox.showinfo('WZ Map Log File','Work Zone Map Log File ' + WZ_mapLogFile + ' NOT Found ...')

##
#   -------------- End of viewLogFile ------------------------
##
   
def configRead(file):
    global wzConfig
    if os.path.exists(file):
        try:
            cfg = open(file)
            wzConfig = json.loads(cfg.read())
            cfg.close()
            getConfigVars()
		
        except Exception as e:
            logMsg('ERROR: Configuration file read failed: ' + file + '\n' + str(e))
            uploadLogFile()
            raise e
    else:
        logMsg('Configuration file NOT FOUND')

###
# ----------------- End of config_read --------------------
###
#
#   Following user specified values are read from the WZ config file specified by user in WZ_Config_UI.pyw...
#
#   WZ Configuration file is parsed here to get the user input values for used by different modules/functions...
#
#   Added: Aug. 2018
#
### -------------------------------------------------------------------------------------------------------
    
# Read configuration file
def getConfigVars():

###
#   Following are global variables are later used by other functions/methods...
###

    # WZDx Feed Info ID
    global  feed_info_id
    
    # General Information
    global  wzDesc                                          #WZ Description
    global  roadName
    global  roadNumber
    global  direction
    global  beginningCrossStreet
    global  endingCrossStreet
    global  beginningMilepost
    global  endingMilepost
    global  eventStatus
    global  creationDate
    global  updateDate

    # Types of Work
    global  typeOfWork

    # Lane Information
    global  totalLanes                                      #total number of lanes in wz
    global  laneWidth                                       #average lane width in meters
    global  lanePadApp                                      #approach lane padding in meters
    global  lanePadWZ                                       #WZ lane padding in meters
    global  dataLane                                        #lane used for collecting veh path data
    global  lanes_obj

    # Speed Limits
    global  speedList                                       #speed limits

    # Cause Codes
    global  c_sc_codes                                      #cause/subcause code

    # Schedule
    global  startDateTime
    global  wzStartDate                                     #wz start date
    global  wzStartTime                                     #wz start time
    global  startDateAccuracy
    global  endDateTime
    global  wzEndDate                                       #wz end date
    global  wzEndTime                                       #wz end time
    global  endDateAccuracy
    global  wzDaysOfWeek                                    #wz active days of week

    # Location
    global  wzStartLat                                     #wz start date
    global  wzStartLon                                     #wz start time
    global  beginningAccuracy
    global  wzEndLat                                       #wz end date
    global  wzEndLon                                       #wz end time
    global  endingAccuracy
    
    # WZDx Metadata
    global  wzLocationMethod
    global  lrsType
    global  locationVerifyMethod
    global  dataFeedFrequencyUpdate
    global  timestampMetadataUpdate
    global  contactName
    global  contactEmail
    global  issuingOrganization

    # Image Info
    global  mapImageZoom
    global  mapImageCenterLat
    global  mapImageCenterLon
    global  mapImageMarkers
    global  marker_list
    global  mapImageMapType
    global  mapImageHeight
    global  mapImageWidth
    global  mapImageFormat
    global  mapImageString

    global  mapFailed
    
    feed_info_id            = wzConfig['FeedInfoID']

    wzDesc                  = wzConfig['GeneralInfo']['Description']
    roadName                = wzConfig['GeneralInfo']['RoadName']
    roadNumber              = wzConfig['GeneralInfo']['RoadNumber']
    direction               = wzConfig['GeneralInfo']['Direction']
    beginningCrossStreet    = wzConfig['GeneralInfo']['BeginningCrossStreet']
    endingCrossStreet       = wzConfig['GeneralInfo']['EndingCrossStreet']
    beginningMilepost       = wzConfig['GeneralInfo']['BeginningMilePost']
    endingMilepost          = wzConfig['GeneralInfo']['EndingMilePost']
    eventStatus             = wzConfig['GeneralInfo']['EventStatus']
    creationDate            = wzConfig['GeneralInfo'].get('CreationDate', '')
    updateDate              = wzConfig['GeneralInfo'].get('UpdateDate', datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))

    typeOfWork = wzConfig['TypesOfWork']
    if not typeOfWork: typeOfWork = []

    totalLanes              = int(wzConfig['LaneInfo']['NumberOfLanes'])           #total number of lanes in wz
    laneWidth               = float(wzConfig['LaneInfo']['AverageLaneWidth'])      #average lane width in meters
    lanePadApp              = float(wzConfig['LaneInfo']['ApproachLanePadding'])   #approach lane padding in meters
    lanePadWZ               = float(wzConfig['LaneInfo']['WorkzoneLanePadding'])   #WZ lane padding in meters
    dataLane                = int(wzConfig['LaneInfo']['VehiclePathDataLane'])     #lane used for collecting veh path data
    lanes_obj               = list(wzConfig['LaneInfo']['Lanes'])

    speedList               = wzConfig['SpeedLimits']['NormalSpeed'], wzConfig['SpeedLimits']['ReferencePointSpeed'], \
                              wzConfig['SpeedLimits']['WorkersPresentSpeed']

    c_sc_codes              = [int(wzConfig['CauseCodes']['CauseCode']), int(wzConfig['CauseCodes']['SubCauseCode'])]

    startDateTime           = wzConfig['Schedule']['StartDate']
    wzStartDate             = datetime.datetime.strptime(startDateTime, "%Y-%m-%dT%H:%M:%SZ").strftime("%m/%d/%Y")
    wzStartTime             = datetime.datetime.strptime(startDateTime, "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M")
    startDateAccuracy       = wzConfig['Schedule'].get('StartDateAccuracy', 'estimated')
    endDateTime             = wzConfig['Schedule']['EndDate']
    wzEndDate               = datetime.datetime.strptime(endDateTime, "%Y-%m-%dT%H:%M:%SZ").strftime("%m/%d/%Y")
    wzEndTime               = datetime.datetime.strptime(endDateTime, "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M")
    endDateAccuracy         = wzConfig['Schedule'].get('EndDateAccuracy', 'estimated')
    wzDaysOfWeek            = wzConfig['Schedule']['DaysOfWeek']

    wzStartLat              = wzConfig['Location']['BeginningLocation']['Lat']
    wzStartLon              = wzConfig['Location']['BeginningLocation']['Lon']
    beginningAccuracy        = wzConfig['Location']['BeginningAccuracy']
    wzEndLat                = wzConfig['Location']['EndingLocation']['Lat']
    wzEndLon                = wzConfig['Location']['EndingLocation']['Lon']
    endingAccuracy          = wzConfig['Location']['EndingAccuracy']

    wzLocationMethod        = wzConfig['metadata']['wz_location_method']
    lrsType                 = wzConfig['metadata']['lrs_type']
    locationVerifyMethod    = wzConfig['metadata']['location_verify_method']
    dataFeedFrequencyUpdate = wzConfig['metadata']['datafeed_frequency_update']
    timestampMetadataUpdate = wzConfig['metadata']['timestamp_metadata_update']
    contactName             = wzConfig['metadata']['contact_name']
    contactEmail            = wzConfig['metadata']['contact_email']
    issuingOrganization     = wzConfig['metadata']['issuing_organization']

    try:
        mapImageZoom            = wzConfig['ImageInfo']['Zoom']
        mapImageCenterLat       = wzConfig['ImageInfo']['Center']['Lat']
        mapImageCenterLon       = wzConfig['ImageInfo']['Center']['Lon']
        mapImageMarkers         = wzConfig['ImageInfo']['Markers'] # Markers:List of {Name, Color, Location {Lat, Lon, ?Elev}}
        marker_list = []
        for marker in mapImageMarkers:
            marker_list.append("markers=color:" + marker['Color'].lower() + "|label:" + marker['Name'] + "|" + str(marker['Location']['Lat']) + "," + str(marker['Location']['Lon']) + "|")
        mapImageMapType         = wzConfig['ImageInfo']['MapType']
        mapImageHeight          = wzConfig['ImageInfo']['Height']
        mapImageWidth           = wzConfig['ImageInfo']['Width']
        mapImageFormat          = wzConfig['ImageInfo']['Format']
        mapImageString          = wzConfig['ImageInfo']['ImageString']
    except KeyError:
        pass

###
#   ------------------------- End of getConfigVars -----------------------
#
#
### --------------------------- Build .js File -----------------------------------
#
#   Open js file for writing js arrays for map data points, approach lanes points, wz lanes points and ref. point
#
#   js_outFile  - data and array for JavaScript for visualization.
#                 fixed file name in the visualization directory 
###

def build_messages():
    global files_list
    
###
#   Data elements for 'common' container...
###

    msgID       = 33                                #RSM message ID is assigned as 33

###
#   Generate rendom eventID between 0 and 32767
###

    eventID     = '0000000'+str(hex(random.randint(0, 32767))).replace('0x','')     #randomly generated between 0 and 32767 in hex
    eventID     = eventID[len(eventID)-8:len(eventID)]                              #hex string of 4 octetes padded with 0 in the front

###
#   idList - message ID and Event Id
###

    idList      = [msgID,eventID]                           #msgID and eventID only. No stationId        


###
#   Set
#       WZ start date and time and end date and time in yyyy,mm,dd,hh,mm
#       UTC time offset
#       headway tolerance
#       road width - NOT used any more...
#       event length same as workzone length
###

    wzStart     = wzStartDate.split('/') + wzStartTime.split(':')
    wzEnd       = wzEndDate.split('/')   + wzEndTime.split(':')

    timeOffset  = 0                                     #UTC time offset in minutes for Eastern Time Zone
    hTolerance  = 20                                        #applicable heading tolerance set to 20 degrees (+/- 20deg?)

    roadWidth   = totalLanes*laneWidth*100                  #roadWidth in cm
    eventLength = wzLen                                     #WZ length in meters, computed earlier


###
#   Set speed limits in WZ as vehicle max speed..from user input saved in config file...
###

    speedLimit  = ['vehicleMaxSpeed',speedList[0],speedList[1],speedList[2],'mph'] #NEW Version of XER... Nov. 2017

### -------------------------------------------------
#
#   BUILD XML (exer) file for 'Common Container'...
#
### -------------------------------------------------

###
#
#   Build multiple .exer (XML) files for segmented message.
#   Build one file for each message segment
#
#   Created June, 2018
#
####

    currSeg = 1                                             #current message segment
    totSeg  = msgSegList[0][0]                              #total message segments
    rsmSegments = []
        
    wzdx_outFile = tempfile.gettempdir() + '/WZDx_File-' + ctrDT + '.geojson'
    logMsg('WZDx output file path: ' + wzdx_outFile)
    wzdxFile = open(wzdx_outFile, 'w')
    files_list.append(wzdx_outFile)
    
    devnull = open(os.devnull, 'w')

    while currSeg <= totSeg:                                #repeat for all segments
        logMsg("Segment Number: " + str(currSeg))
        logMsg("Segment Range: " + str(msgSegList[currSeg+1][1] - 1) + " - " + str(msgSegList[currSeg+1][2]))
        logMsg("AppMapPt Length: " + str(len(appMapPt)))
        

###
### Create and open output xml file...
###
        if noRSM:
            logMsg('Accuracy too low, not adding RSM files to files_list ')
        else:
            xml_outFile = tempfile.gettempdir() + '/RSZW_MAP_xml_File-' + ctrDT + '-' + str(currSeg)+'_of_'+str(totSeg)+'.xml'
            logMsg('RSM XML output file path: ' + xml_outFile)

            uper_outFile = tempfile.gettempdir() + '/RSZW_MAP_xml_File-' + ctrDT + '-' + str(currSeg)+'_of_'+str(totSeg)+'.uper'
            logMsg('RSM UPER output file path: ' + uper_outFile)

            xmlFile = open(xml_outFile, 'w')

            files_list.append(xml_outFile)
            files_list.append(uper_outFile)

###
#   Build common container...
#
#   Update refPoint to a new value for different message segment > 1.
#   Since the distance between the original reference point and the first node for message segment 2 to the last segment could be 
#   too far apart (xyz_offset) to be represented in just one offset node. To alleviate the issue, for every segment, a new reference
#   point is set as follows:
#
#   1st segment   - Original marked reference point
#   2..n segments - Use first set of node points and select for the open lane for which vehicle path data is collected.
#                   The first set of node points are the same as the last set of node points of of the previous segment.
#                   They are repeated for map matching purpose
###

        startNode = 1
        if currSeg == startNode:    
            newRefPt = refPoint
        else:
            dL = (dataLane - 1) * 4                                 #location pinter in wzMapPt list
            startNode = msgSegList[currSeg+1][1]                    #wz start node, index in wzMapPt is startNode-1 
            newRefPt  = (wzMapPt[startNode-1][dL+0],wzMapPt[startNode-1][dL+1],wzMapPt[startNode-1][dL+2])
        pass


###
#   Build xml for common container...
###
        commonContainer = wz_xml_builder.build_xml_CC (idList,wzStart,wzEnd,timeOffset,wzDaysOfWeek,c_sc_codes,newRefPt,appHeading,hTolerance, \
                      speedLimit,laneWidth,roadWidth,eventLength,laneStat,appMapPt,msgSegList,currSeg,wzDesc)

###
#       WZ length, LC characteristic, workers present, etc. 
###
    
        wpFlag  = 0                         #Workers present flag, 0=no, 1=yes   NOT Used in RSM (was for BIM)
        RN      = False                     #Boolean - True: Generate reduced nodes for closed lanes
                                            #        - False: Generate all nodes for closed lanes
###
#   Build WZ container
###
        rszContainer = wz_xml_builder.build_xml_WZC (speedLimit,laneWidth,laneStat,wpStat,wzMapPt,RN,msgSegList,currSeg)

        rsm = {}
        rsm['MessageFrame'] = {}
        rsm['MessageFrame']['messageId'] = idList[0]
        rsm['MessageFrame']['value'] = {}
        rsm['MessageFrame']['value']['RoadsideSafetyMessage'] = {}
        rsm['MessageFrame']['value']['RoadsideSafetyMessage']['version'] = 1
        rsm['MessageFrame']['value']['RoadsideSafetyMessage']['commonContainer'] = commonContainer
        rsm['MessageFrame']['value']['RoadsideSafetyMessage']['rszContainer'] = rszContainer

        rsmSegments.append(rsm)
        if not noRSM:
            rsm_xml = xmltodict.unparse(rsm, short_empty_elements=True, pretty=True, indent='  ')
            xmlFile.write(rsm_xml)

            xmlFile.close()
            # logging.warning('ABOUT TO CREATE UPER FILE')

            linux = subprocess.check_output(['uname', '-a'], stderr=subprocess.STDOUT).decode('utf-8')
            logMsg("Linux Installation Information: " + str(linux))
            # try:
                # p = subprocess.Popen(['./EventGridTrigger1/jvm/bin/java', '-jar', './EventGridTrigger1/CVMsgBuilder_xmltouper_v8.jar', str(xml_outFile), str(uper_outFile)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # output, err = p.communicate(b"input data that is passed to subprocess' stdin")
                # # rc = p.returncode
                # logMsg('ERROR: RSM UPER conversion FAILED. Output: ' + str(output))
                # logMsg('ERROR: RSM UPER conversion FAILED. Error: ' + str(err))
            subprocess.call(['./EventGridTrigger1/jvm/bin/java', '-jar', './EventGridTrigger1/CVMsgBuilder_xmltouper_v8.jar', str(xml_outFile), str(uper_outFile)]) #jre1.8.0_261-i586/bin/ jvm/java-11-openjdk-amd64/bin/  ,stdout=devnull
            # except Exception as e:
                # logMsg('ERROR: RSM UPER conversion FAILED. Message: ' + str(e))
            
            if not os.path.exists(uper_outFile) or os.stat(uper_outFile).st_size == 0:
                logMsg('ERROR: UPER FILE DOES NOT EXIST OR HAS SIZE 0')
                logMsg('ERROR: RSM UPER conversion FAILED, ')
            #     print('RSM Binary conversion FAILED', 'RSM Binary (UPER) conversion failed\nEnsure that you have java installed (version>=1.8 or jdk>=8) and added to your system path\nThen run WZ_BuildMsgs_and_Export.pyw')
            #     # logMsg('Exiting Application')
            #     logFile.close()
            #     sys.exit(0)

        currSeg = currSeg+1
    pass
    info = {}
    info['feed_info_id'] = feed_info_id
    info['road_name'] = roadName
    info['road_number'] = roadNumber
    info['description'] = wzDesc
    info['direction'] = direction
    info['beginning_cross_street'] = beginningCrossStreet
    info['ending_cross_street'] = endingCrossStreet
    info['beginning_milepost'] = beginningMilepost
    info['ending_milepost'] = endingMilepost
    info['issuing_organization'] = issuingOrganization
    info['creation_date'] = creationDate
    info['update_date'] = updateDate
    info['event_status'] = eventStatus
    info['beginning_accuracy'] = beginningAccuracy
    info['ending_accuracy'] = endingAccuracy
    info['start_date_accuracy'] = startDateAccuracy
    info['end_date_accuracy'] = endDateAccuracy

    info['metadata'] = {}
    info['metadata']['wz_location_method'] = wzLocationMethod
    info['metadata']['lrs_type'] = lrsType
    info['metadata']['location_verify_method'] = locationVerifyMethod
    if dataFeedFrequencyUpdate: info['metadata']['datafeed_frequency_update'] = dataFeedFrequencyUpdate
    info['metadata']['timestamp_metadata_update'] = timestampMetadataUpdate
    info['metadata']['contact_name'] = contactName
    info['metadata']['contact_email'] = contactEmail
    info['metadata']['issuing_organization'] = issuingOrganization

    info['types_of_work'] = typeOfWork
    info['lanes_obj'] = lanes_obj
    # logMsg('Converting RSM XMl to WZDx message')
    wzdx = {}
    try:
        wzdx = rsm_2_wzdx_translator.wzdx_creator(rsmSegments, dataLane, info)
        logMsg("WZDx message generated and validated successfully")
    except Exception as e:
        logMsg("ERROR: WZDx Message Generation Failed: "+ str(e))
        uploadLogFile()
        raise e
    wzdxFile.write(json.dumps(wzdx, indent=2))
    wzdxFile.close()

###
#   May want to print WZ length per segment and total WZ length...
###

    # logMsg('--- Done Building WZ MAP ---')
    #logFile.close()    

###
#   > > > > > > > > > > > START MAIN PROCESS < < < < < < < < < < < < < < <
###

def startMainProcess(vehPathDataFile):

    # global  vehPathDataFile                                         #collected vehicle path data file name
    global  refPtIdx                                                #data point number where reference point is set
    global  wzLen                                                   #work zone length in meters
    global  wzMapLen                                                #Mapped approach and wz lane length in meters
    global  appHeading                                              #approach heading
    global  sampleFreq
    global  noRSM                                                   #If accuracy is too low, do not generate RSM message
    global  msgSegList                                              #WZ message segmentation list
##  global  wzMapBuiltSuccess                                       #WZ map built successful or not flag
##  wzMapBuiltSuccess = False                                       #Default set to False                                  
    
    csvList = []
    csvList = list(csv.reader(open(vehPathDataFile)))

    timeRegex = '[0-9]{2}(:[0-9]{2}){3}'
    lastIndex = len(csvList) - 1
    logMsg('Length of CSV data: ' + str(lastIndex))
    time1 = re.search(timeRegex, str(csvList[1])).group(0).split(':')
    time2 = re.search(timeRegex, str(csvList[lastIndex])).group(0).split(':')

    deltaTime = (int(time2[0])-int(time1[0]))*3600 + (int(time2[1])-int(time1[1]))*60 + (int(time2[2])-int(time1[2])) + (int(time2[3])-int(time1[3]))/100
    # diffmSec = (int(time2[9:11]) - int(time1[9:11])) / 100
    # diffSec = int(time2[6:8]) - int(time1[6:8])
    if (deltaTime) != 0:
        sampleFreq = lastIndex/deltaTime
    else:
        sampleFreq = 10
    if sampleFreq < 1 or sampleFreq > 10:
        sampleFreq = 10

    logMsg('Sample Frequency: ' + str(sampleFreq))

    totRows = len(csvList) - 1      ###total records or lines in file

    # logMsg('*** - '+wzDesc+' - ***')    
    # logMsg('--- Processing Input File: '+vehPathDataFile+', Total input lines: '+str(totRows))

###
#
#   Call function to read and parse the vehicle path data file created by the 'vehPathDataAcq.pyw'
#   to build vehicle path data array, lane status and workers presence status arrays.
#
#   refPtIdx, wzLen and appHeading values are returned in atRefPoint list...
#
#   Updated on Aug. 23, 2018
#   
###
    logMsg('Length of Path Point Before: ' + str(len(pathPt)))

    atRefPoint  = [0,0,0,0]                                             #temporary list to hold return values from function below 
    wz_vehpath_lanestat_builder.buildVehPathData_LaneStat(vehPathDataFile,totalLanes,pathPt,laneStat,wpStat,refPoint,atRefPoint,sampleFreq)
    logMsg('Length of Path Points After: ' + str(len(pathPt)))
    refPtIdx    = atRefPoint[0]
    wzLen       = atRefPoint[1]
    appHeading  = atRefPoint[2]
    maxHDOP     = atRefPoint[3]
    maxAllowableHDOP = 2        # meters
    if maxHDOP > maxAllowableHDOP:
        logMsg('GPS Accuracy too low, max value of HDOP: ' + str(maxHDOP) + ' is greater than the limit of ' + str(maxAllowableHDOP) + '. Cannot upload RSM messages')
        noRSM = True
    else:
        noRSM = False
        logMsg('GPS Accuracy high enough, max value of HDOP: ' + str(maxHDOP) + ' is greater than the limit of ' + str(maxAllowableHDOP) + '. RSM messages will be uploaded')

    # logMsg(' --- Start of Work Zone at Data Point: '+str(refPtIdx))
    # logMsg('Reference Point @ '+refPoint[0]+', '+refPoint[1]+', '+refPoint[2])

    

###
#   ====================================================================================================
###
#    -----  Read and processed vehPathDataFile
#           Compiled pathPt, reference point and lane closures  -----
###
###
#   Function to populate Approach Lane Map points...
#
#   refPtIdx determined in the above function...
###

###
#   'laneType'              1 = Approach lanes, 2 = wz Lanes for mapping
#   'pathPt'                contains list of data points collected by driving the vehicle on one open WZ lane
#   'appMapPt/wzMapPt'      constructed node list for lane map for BIM (RSM)
#                           contains lat,lon,alt,lcloStat for each node, each lane + heading + WP flag + distVec (dist from prev. node)
#   'lanePadApp/lanePadWz'  lane padding in addition to laneWidth
#   'refPtIdx'              Data location of the reference point in pathPt array
#   'laneStat'              A two-dimensional list to hold lane status, 0=open, 1=closed.
#                               Generated from lane closed/opened marker from collected data
#                               List location [0,0,0] provides total number of lanes
#                               It holds for each lane closed/opened instance, data point index, lane number and lane status (1/0)
#   'wpStat'                list containing location where 'workers present' is set/unset
#   'dataLane'              Lane on which the vehicle path data for wz mapping was collected.
#                               'dataLane' is used to derive map data for the adjacent lanes. One lane to the left of the 'dataLane' and one to right in
#                               case of total 3 lanes. For more than 5 lanes, data from multiple lanes to be collected to create map for adjascent lanes
#   'laneWidth'             lane width in meters
#
#   For approach lanes, map for all lanes are created
#
#   For wz lanes, node points for map for all lanes including closed lanes are created.
#
###

    wzMapLen = [0,0]                                    #both approach and wz mapped length
    laneType = 1                                        #approach lanes
    logMsg(str(laneType) + ', ' + str(len(pathPt)) + ', ' + str(len(appMapPt)) + ', ' + str(laneWidth) + ', ' + str(lanePadApp) + ', ' + str(refPtIdx) + ', ' + str(appMapPtDist))
    logMsg(str(laneStat) + ',' + str(wpStat) + ', ' + str(dataLane) + ', ' + str(wzMapLen) + ', ' + str(speedList) + ', ' + str(sampleFreq))
    wz_map_constructor.getLanePt(laneType,pathPt,appMapPt,laneWidth,lanePadApp,refPtIdx,appMapPtDist,laneStat,wpStat,dataLane,wzMapLen,speedList,sampleFreq)
    logMsg('Length of Approach Points: ' + str(len(appMapPt)))
    logMsg('Length of Path Point: ' + str(len(pathPt)))

    # logMsg(' --- Mapped Approach Lanes: '+str(int(wzMapLen[0]))+' meters')

    
###
#
#   Now repeat the above for WZ map data point array starting from the ref point until end of the WZ
#   First WZ map point closest to the reference point is the next point after the ref. point.
#
###
    
    laneType    = 2                                     #wz lanes

    logMsg('Length of Work Zone Points Before: ' + str(len(wzMapPt)))
    wz_map_constructor.getLanePt(laneType,pathPt,wzMapPt,laneWidth,lanePadWZ,refPtIdx,wzMapPtDist,laneStat,wpStat,dataLane,wzMapLen,speedList,sampleFreq)
    logMsg('Length of Work Zone Points After: ' + str(len(wzMapPt)))
    logMsg('Length of Path Point: ' + str(len(pathPt)))

    # logMsg(' --- Mapped Work zone Lanes: '+str(int(wzMapLen[1]))+' meters')


###
#   print/log lane status and workers present/not present status...
###

    laneStatIdx = len(laneStat)
    if laneStatIdx > 1:                               #have lane closures...NOTE: Index 0 location is dummy value...
        # logMsg(' --- Start/End of lane closure Offset from the reference point ---')
        for L in range(1, laneStatIdx):
            stat = 'Start'
            if laneStat[L][2] == 0: stat = 'End'
            # logMsg('\t '+stat+' of lane '+str(laneStat[L][1])+' closure, at data point: '+str(laneStat[L][0])+', Offset: '+ \
            #                str(int(laneStat[L][3]))+' meters')
        pass
    pass                                            

###
#       Do for workers present/not present zone?          
###
    wpStatIdx = len(wpStat)    
    if wpStatIdx > 0:                                       #have workers present/not present
        # logMsg(' --- Start/End of workers present offset from the reference point ---')
        for w in range(0, wpStatIdx):
            stat = 'End'
            if wpStat[w][1] == 1:  stat = 'Start'
            # logMsg('\t '+stat+' of workers present @ data point: '+str(wpStat[w][0])+  \
            #                ', Offset: '+str(wpStat[w][2])+' meters')
        pass
    pass                                            

###
#   Get nodes list for each segmented message in message segmentation...
#
#   Following revised to address error in generating message segmentation
#       Revised - Jan. 22, 2019
#
#       If computed nodes per approach lane is > computed nodes per lane (Approach nodes/lane + min. 2 nodes for WZ lane in 1st segment)
#       msgSegList[0][0] is set to -1 indicating error in generating segmentation.
#
###

    msgSegList = wz_msg_segmentation.buildMsgSegNodeList(len(appMapPt),len(wzMapPt),totalLanes)     #build message segment list

    if msgSegList[0][0] == -1:                                                  #Error
        ANPL = msgSegList[1][2]
        MNPL = msgSegList[0][1]
        logMsg('ERROR: MESSAGE SEGMENTATION FAILED')
        # logMsg('\tThe 1st message segment must be able to include all nodes for approach lane plus at atleast first 2 nodes of WZ lane')
        # logMsg('\tNodes per approach lane: '+str(ANPL)+' > allowed max nodes per lane: ' +str(MNPL)+' to stay within message payload size\n\t')
        # logMsg('\tThe 1st message segment must be able to include all nodes for approach lane')
        # logMsg('\tReduce length of vehicle path data for approach lane to no more than 1km and try again')
        print('MESSAGE SEGMENTATION ERROR', 'Reduce length of vehicle path data for approach lane to no more than 1km and try again')
        # TODO: Fix this error/make this never happen. throw away some data from start of approach region?
        # logFile.close()
        sys.exit(0)
        #logFile.close()                                                         #stopping the program, close file so eror message is saved...
        return                                                                  #return to caller                  

    else:    

        ANPL    = msgSegList[1][2]                                              #Approach lane Nodes Per Lane
        WZNPL   = msgSegList[len(msgSegList)-1][2]                              #Work zone lane Nodes Per Lane
        TNPL    = ANPL + WZNPL
        MS      = msgSegList[0][0]                                              #Constructed message segments
        NPL     = msgSegList[0][1]                                              #no of Nodes Per Lane
        # logMsg('Total Nodes per Lane: ' +str(TNPL))
        # logMsg('Total Nodes per Approach Lane: '+str(ANPL))
        # logMsg('Total Nodes per WZ Lane: '  +str(WZNPL))
        # logMsg('Total message segment(s): '  +str(MS))
        # logMsg('Nodes per Message Segment: '+str(NPL))
        # logMsg('Message segment list: '  +str(msgSegList))
    pass

###
#   Build XML File...
###
    # logMsg('Building messages')
    build_messages()


##############################################################################################
#
# ----------------------------- END of startMainProcess --------------------------------------
#
###############################################################################################

def openLog():
    global logFile
    if os.path.exists(logFileName):
        append_write = 'a' # append if already exists
    else:
        append_write = 'w' # make a new file if not
    logFile = open(logFileName, append_write)

def logMsg(msg):
    formattedTime = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S') + '+00:00'
    logFile.write('[' + formattedTime + '] ' + msg + '\n')

def uploadArchive(zip_name, container_name):
    # logMsg('Creating blob in azure: ' + zip_name + ', in container: ' + container_name)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=zip_name.split('/')[-1])
    # logMsg('Uploading zip archive to blob')
    with open(zip_name, 'rb') as data:
        blob_client.upload_blob(data, overwrite=True)

    uploadLogFile()

    # logMsg('Closing log file in Message Builder and Export')
    # logFile.close()
    print('Upload Successful', 'Data upload successful! Please navigate to\nhttp://www.neaeraconsulting.com/V2x_Verification\nto view and verify the mapped workzone.\nYou will find your data under\n' + name_id)

def uploadLogFile():
    logFile.close()
    blob_client_log = blob_service_client.get_blob_client(container="logs", blob=logFileName.replace(".txt",ctrDT+".txt"))
    with open(logFileName, 'rb') as data:
        blob_client_log.upload_blob(data, overwrite=True)
##
#   ---------------------------- END of Functions... -----------------------------------------
##

logFileName = tempfile.gettempdir() + '/data_collection_log.txt'
local_updated_config_path = tempfile.gettempdir() + '/updatedConfig.json'
# logFile = ''
mapFileName = tempfile.gettempdir() + '/mapImage.png'

def updateConfigImage(vehPathDataFile):
    global needsImage
    global wzConfig
    global center
    global wzStartLat
    global wzStartLon
    global wzEndLat
    global wzEndLon

    got_rp = False
    with open(vehPathDataFile, 'r') as f:
        headers = f.readline()
        data = f.readline().rstrip('\n')
        while data:
            fields = data.split(',')
            nextData = f.readline().rstrip('\n')
            if not got_rp and (fields[8] == 'RP' or fields[8] == 'WP+RP' or fields[8] == 'LC+RP'):
                # Starting location found
                wzConfig['Location']['BeginningLocation']['Lat'] = float(fields[3])
                wzStartLat = float(fields[3])
                wzConfig['Location']['BeginningLocation']['Lon'] = float(fields[4])
                wzStartLon = float(fields[4])
            elif (fields[8] == 'Data Log' and fields[9] == 'False') or not nextData:
                # Ending location found
                wzConfig['Location']['EndingLocation']['Lat'] = float(fields[3])
                wzEndLat = float(fields[3])
                wzConfig['Location']['EndingLocation']['Lon'] = float(fields[4])
                wzEndLon = float(fields[4])

            data = nextData

    centerLat = (float(wzStartLat) + float(wzEndLat))/2
    centerLon = (float(wzStartLon) + float(wzEndLon))/2
    center = str(centerLat) + ',' + str(centerLon)
    
    north = max(float(wzStartLat), float(wzEndLat))
    south = min(float(wzStartLat), float(wzEndLat))
    east = max(float(wzStartLon), float(wzEndLon))
    west = min(float(wzStartLon), float(wzEndLon))
    calcZoomLevel(north, south, east, west, mapImageWidth, mapImageHeight)

    marker_list = []
    marker_list.append("markers=color:green|label:Start|" + str(wzStartLat) + "," + str(wzStartLon) + "|")
    marker_list.append("markers=color:red|label:End|" + str(wzEndLat) + "," + str(wzEndLon) + "|")

    encoded_string = ''
    get_static_google_map(mapFileName, center=center, zoom=zoom, imgsize=(mapImageWidth, mapImageHeight), imgformat="png", markers=marker_list)
    with open(mapFileName, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    needsImage = False

    wzConfig['ImageInfo']['Zoom'] = zoom
    wzConfig['ImageInfo']['Center']['Lat'] = centerLat
    wzConfig['ImageInfo']['Center']['Lon'] = centerLon



    markers = []
    markers.append({'Name': 'Start', 'Color': 'Green', 'Location': {'Lat': wzStartLat, 'Lon': wzStartLon, 'Elev': None}})
    markers.append({'Name': 'End', 'Color': 'Red', 'Location': {'Lat': wzEndLat, 'Lon': wzEndLon, 'Elev': None}})
    wzConfig['ImageInfo']['Markers'] = markers

    wzConfig['ImageInfo']['MapType'] = mapImageMapType
    wzConfig['ImageInfo']['Height'] = mapImageHeight
    wzConfig['ImageInfo']['Width'] = mapImageWidth
    wzConfig['ImageInfo']['Format'] = mapImageFormat

    wzConfig['ImageInfo']['ImageString'] = encoded_string

    cfg = open(local_updated_config_path, 'w')
    cfg.write(json.dumps(wzConfig, indent='  '))
    cfg.close()

def get_static_google_map(filename_wo_extension, center=None, zoom=None, imgsize="640x640", imgformat="png",
                          maptype="roadmap", markers=None ):  
    """retrieve a map (image) from the static google maps server 
    
     See: http://code.google.com/apis/maps/documentation/staticmaps/
        
        Creates a request string with a URL like this:
        http://maps.google.com/maps/api/staticmap?center=Brooklyn+Bridge,New+York,NY&zoom=14&size=512x512&maptype=roadmap
&markers=color:blue|label:S|40.702147,-74.015794&sensor=false"""
    
    # assemble the URL
    request =  "http://maps.google.com/maps/api/staticmap?" # base URL, append query params, separated by &
    apiKey = os.getenv('GOOGLE_MAPS_API_KEY')
    # if center and zoom  are not given, the map will show all marker locations
    request += "key=%s&" % apiKey
    if center != None:
        request += "center=%s&" % center
    if zoom != None:
        request += "zoom=%i&" % zoom  # zoom 0 (all of the world scale ) to 22 (single buildings scale)

    request += "size=%ix%i&" % (imgsize)  # tuple of ints, up to 640 by 640
    request += "format=%s&" % imgformat
    request += "bearing=90&"
    # request += "maptype=%s&" % maptype  # roadmap, satellite, hybrid, terrain

    # add markers (location and style)
    if markers != None:
        for marker in markers:
                request += "%s&" % marker

    request = request.rstrip('&')
    # #request += "mobile=false&"  # optional: mobile=true will assume the image is shown on a small screen (mobile device)
    # request += "sensor=false"   # must be given, deals with getting loction from mobile device
    # try:
    urllib.request.urlretrieve(request, filename_wo_extension)
    # except Exception as e:
    # logMsg('Error retrieving map image: ' + str(e))

# Calculate google maps zoom level to fit a rectangle
def calcZoomLevel(north, south, east, west, pixelWidth, pixelHeight):
    global zoom
    global centerLat

    GLOBE_WIDTH = 256
    ZOOM_MAX = 21
    angle = east - west
    if angle < 0:
        angle += 360
    zoomHoriz = round(math.log(pixelWidth * 360 / angle / GLOBE_WIDTH) / math.log(2)) - 1

    angle = north - south
    centerLat = (north + south) / 2
    if angle < 0:
        angle += 360
    zoomVert = round(math.log(pixelHeight * 360 / angle / GLOBE_WIDTH * math.cos(centerLat*math.pi/180)) / math.log(2)) - 1

    zoom = max(min(zoomHoriz, zoomVert, ZOOM_MAX), 0)

##############################################################################################
#
# ---------------------------- Automatically Export Files ------------------------------------
#
###############################################################################################

def initVars():
    global wzConfig
    global cDT
    global pathPt
    global appMapPt
    global wzMapPt
    global refPoint
    global appHeading
    global refPtIdx
    global gotRefPt
    global appMapPtDist
    global wzMapPtDist
    global laneStat
    global laneStatIdx
    global wpStat
    global wpStatIdx
    global wzLen
    global msgSegList
    global files_list
    global ctrDT

    wzConfig        = {}

    ###
    #   --------------------------------------------------------------------------------------------------
    ###
    #   Get current date and time...
    ###

    cDT = datetime.datetime.now().strftime('%m/%d/%Y - ') + time.strftime('%H:%M:%S')

    ###
    #   Map builder output log file...
    ###


    ### --------------------------------------------------------------------------------------------------
    #       Following are local variables with set default values...
    #
    #	Setup array for collected data for mapping, construcyed node points for approach and WZ lanes, and
    #       reference point
    ### --------------------------------------------------------------------------------------------------

    pathPt          = []			#test vehicle path data points generated by WZ_VehPathDataAcq.py module
    appMapPt        = [] 		        #array to hold approach lanes map node points
    wzMapPt         = []                    #array to hold wz lanes map node points
    refPoint        = [0,0,0]               #Ref. point (lat, lon, alt), initial value... ONLY ONE reference point...
    appHeading      = 0                     #applicable Heading to the WZ event at the ref. point. Needed for XML for RSM Message

    ###
    #	Variables for book keeping...
    ###

    refPtIdx        = 0                     #index into pathPt array where the reference point is...
    gotRefPt        = False                 #default 

    ###
    #	For fixed equidistant node selection for approach and WZ lanes
    #
    #       As of Feb. 2018 --  Node point selection based on equidistant is NO LONGER in use...
    #                           Replace by dynamic node point selection based on right triangle using change in heading angle method... 
    ###

    appMapPtDist    = 50                    #set distance in meters between map data points for approach lanes - not used in the algo.
    wzMapPtDist     = 200	                #set distance in meters between map data point for WZ map - not used in the algo.

    ###
    #	Keep track of lane status such as point where lane closed or open is marked within WZ for each lane
    #       including offset from ref. pt.
    #
    #       Contains 4 elements - [data point#, lane#, lane status (0-open/1-closed), offset from ref. point)  
    ###

    laneStat        = []                    #contains lane status, data point#, lane #, 0/1 0=open, 1=closed and offset from ref point.
                                            #Generated from lane closed/opened marker from colleted data
    laneStatIdx     = 0                     #laneStat + lcOffset array index

    ###
    #	Keep track of workers present status such as point where they are present and then not present at **road level**
    #       including offset from the reference point
    ###

    wpStat          = []                    #array to hold WP location, WP status and offset from ref. point default - no workers present
    wpStatIdx       = 0                     #wpStat array index    

    ###
    #       Work zone length
    ###

    wzLen           = 0                     #init WZ length

    msgSegList      = []                    #WZ message node segmentation list

    files_list      = []

    ctrDT   = datetime.datetime.now().strftime('%Y%m%d-') + time.strftime('%H%M%S')

def build_messages_and_export(wzID, vehPathDataFile, local_config_path, updateImage):
    global blob_service_client
    global name_id
    global files_list

    initVars()
    # wzID = 'sample-work-zone--white-rock-cir'
    # vehPathDataFile = './WZ_VehPathData/path-data--' + wzID + '.csv'
    # local_config_path = './Config Files/config--' + wzID + '.json'

    openLog()
    logMsg('*** Running Message Builder and Export ***')
    logMsg(str(datetime.datetime.now()))
    inputFileDialog(local_config_path)

    description = wzDesc.lower().strip().replace(' ', '-')
    road_name = roadName.lower().strip().replace(' ', '-')
    name_id = description + '--' + road_name
    logMsg('WZID: ' + str(name_id))

    if not mapImageString:
        updateImage = True

    if updateImage:
        updateConfigImage(vehPathDataFile)
        files_list.append(local_updated_config_path)
        logMsg('Update image true')
    else:
        files_list.append(local_config_path)
        logMsg('Update image false')
    startMainProcess(vehPathDataFile)
    files_list.append(vehPathDataFile)
    files_list.append(local_config_path)

    description = wzDesc.lower().strip().replace(' ', '-')
    road_name = roadName.lower().strip().replace(' ', '-')
    name_id = description + '--' + road_name
    # logMsg('Work zone name id: ' + name_id)
    zip_name = tempfile.gettempdir() + '/wzdc-exports--' + name_id + '.zip'
    logMsg('Creating zip archive: ' + zip_name)

    zipObj = zipfile.ZipFile(zip_name, 'w')
    names = []
    for filename in files_list:
        if not os.path.exists(filename):
            logMsg("File does not exist: " + filename)
            continue
        name = filename.split('/')[-1]
        name_orig = name
        name_wo_ext = name[:name.rfind('.')]
        if '.csv' in filename.lower():
            name = 'path-data--' + name_id + '.csv'
        elif '.json' in filename.lower():
            if updateImage:
                name = 'config--' + name_id + '-updated.json'
            else:
                name = 'config--' + name_id + '.json'
        elif '.xml' in filename.lower():
            number = name[name.rfind('-')+1:name.rfind('.')]
            name = 'rsm-xml--' + name_id + '--' + number + '.xml'
        elif '.uper' in filename.lower():
            number = name[name.rfind('-')+1:name.rfind('.')]
            name = 'rsm-uper--' + name_id + '--' + number + '.uper'
        elif '.geojson' in filename.lower():
            name = 'wzdx--' + name_id + '.geojson'
        else:
            continue
        logMsg('Adding file to archive: ' + filename + ', as: ' + name)
        if name not in names:
            names.append(name)
            zipObj.write(filename, name)

    # close the Zip File
    zipObj.close()

    # logMsg('Removing local configuration file: ' + local_config_path)
    # os.remove(local_config_path)

    # connect_str_env_var = 'neaeraiotstorage_storage'
    # connect_str = os.getenv(connect_str_env_var)
    # print('\nDownloading blob to \n\t' + download_file_path)
    # logMsg('Loaded connection string from environment variable: ' + connect_str_env_var)
    # blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    # container_client = blob_service_client.get_container_client('unzippedworkzonedatauploads')
    container_name = 'workzonedatauploads'

    uploadArchive(zip_name, container_name)