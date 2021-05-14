import os
import json
import logging
import tempfile
import sys
from urllib.request import urlopen
import azure.functions as func
from azure.storage.blob import BlobServiceClient

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname('buildmsgs_and_export.py'))))

def main(event: func.EventGridEvent):
    logger = logging.getLogger("logger_name")
    logger.disabled = True

    from . import buildmsgs_and_export # Must be here to re-initialize variables every time
    result = json.dumps({
        'id': event.id,
        'data': event.get_json(),
        'topic': event.topic,
        'subject': event.subject,
        'event_type': event.event_type,
    })
    logging.info('Python EventGrid trigger processed an event: %s', result)

    fileName = event.subject.split('/')[-1]
    updateImage = False
    if '--update-image' in fileName:
        updateImage = True

    wzID = fileName.replace('path-data', '').replace('.csv', '').replace('--update-image', '')

    csv_path = tempfile.gettempdir() + '/path-data.csv'
    config_path = tempfile.gettempdir() + '/config.json'
    # parameter_path = tempfile.gettempdir() + '/parameters.json'
    
    blob_service_client = BlobServiceClient.from_connection_string(os.environ['neaeraiotstorage_storage'], logger=logger)
    container_name = 'workzoneuploads'
    blob_name = event.subject.split('/')[-1]
    logging.info('CSV: container: ' + container_name + ', blob: ' + blob_name)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    logging.info('39')
    with open(csv_path, 'wb') as download_file:
        download_file.write(blob_client.download_blob().readall())
    logging.info('42')

    blob_name = 'config' + wzID + '.json'
    container_name = 'publishedconfigfiles'
    logging.info('Config: container: ' + container_name + ', blob: ' + blob_name)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    with open(config_path, 'wb') as download_file:
        download_file.write(blob_client.download_blob().readall())

    logging.info('Wrote local files')

    # with open(parameter_path, 'w') as f:
    #     parameters = {}
    #     parameters['id'] = wzID
    #     f.write(json.dumps(parameters))

    buildmsgs_and_export.build_messages_and_export(wzID, csv_path, config_path, updateImage)
    # sys.exit(0)