

import xml.etree.ElementTree as ET 
from jsonschema import validate
import json
from datetime import datetime
import uuid
import random
import string
import logging
import copy

# info = {}
# info['feed_info_id'] = feed_info_id
# info['road_name'] = roadName
# info['road_number'] = roadNumber
# info['description'] = wzDesc
# info['direction'] = direction
# info['beginning_cross_street'] = beginningCrossStreet
# info['ending_cross_street'] = endingCrossStreet
# info['beginning_milepost'] = beginningMilepost
# info['ending_milepost'] = endingMilepost
# info['issuing_organization'] = issuingOrganization
# info['creation_date'] = creationDate
# info['update_date'] = updateDate
# info['event_status'] = eventStatus
# info['beginning_accuracy'] = beginingAccuracy
# info['ending_accuracy'] = endingAccuracy
# info['start_date_accuracy'] = startDateAccuracy
# info['end_date_accuracy'] = endDateAccuracy

# info['metadata'] = {}
# info['metadata']['wz_location_method'] = wzLocationMethod
# info['metadata']['lrs_type'] = lrsType
# info['metadata']['location_verify_method'] = locationVerifyMethod
# if dataFeedFrequencyUpdate:
#     info['metadata']['datafeed_frequency_update'] = dataFeedFrequencyUpdate
# info['metadata']['timestamp_metadata_update'] = timestampMetadataUpdate
# info['metadata']['contact_name'] = contactName
# info['metadata']['contact_email'] = contactEmail
# info['metadata']['issuing_organization'] = issuingOrganization

# info['types_of_work'] = typeOfWork
# info['lanes_obj'] = lanes_obj

# Translator 
def wzdx_creator(messages, dataLane, info):
    wzd = {}
    wzd['road_event_feed_info'] = {}
    wzd['road_event_feed_info']['feed_info_id'] = info['feed_info_id']
    wzd['road_event_feed_info']['update_date'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    wzd['road_event_feed_info']['publisher'] = 'POC Work Zone Integrated Mapping'
    wzd['road_event_feed_info']['contact_name'] = 'Tony English'
    wzd['road_event_feed_info']['contact_email'] = 'tony@neaeraconsulting.com'
    if info['metadata'].get('datafeed_frequency_update', False):
        wzd['road_event_feed_info']['update_frequency'] = info['metadata']['datafeed_frequency_update'] # Verify data type
    wzd['road_event_feed_info']['version'] = '3.0'

    data_source = {}
    data_source['data_source_id'] = str(uuid.uuid4())
    data_source['feed_info_id'] = info['feed_info_id']
    data_source['organization_name'] = info['metadata']['issuing_organization']
    data_source['contact_name'] = info['metadata']['contact_name']
    data_source['contact_email'] = info['metadata']['contact_email']
    if info['metadata'].get('datafeed_frequency_update', False):
        data_source['update_frequency'] = info['metadata']['datafeed_frequency_update']
    data_source['update_date'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    data_source['location_verify_method'] = info['metadata']['location_verify_method']
    data_source['location_method'] = info['metadata']['wz_location_method']
    data_source['lrs_type'] = info['metadata']['lrs_type']
    # data_source['lrs_url'] = "basic url"

    wzd['road_event_feed_info']['data_sources'] = [data_source]

    wzd['type'] = 'FeatureCollection'
    nodes = []
    sub_identifier = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6)) #Create random 6 character digit/letter string
    road_event_id = str(uuid.uuid4())
    ids = {}
    ids['sub_identifier'] = sub_identifier
    ids['road_event_id'] = road_event_id
    wzdxMessages = []

    containers = {
      'commonContainers': []
      'rszContainers': []
      'laneClosureContainers': []
    }

    for message in messages:
        rsm = message['RoadsideSafetyMessage']

        containers['commonContainers'].append(rsm['commonContainer'])

        if rsm.get('rszContainer'):
            containers['rszContainers'].append('rszContainer': rsm['rszContainer'], 'workersPresent': rsm.get('situationalContainer') != None)

        if rsm.get('laneCLosureContainer'):
            containers['laneClosureContainers'].append(rsm['laneClosureContainer'])

        numLanes = len(containers['commonContainer']['regionInfo'].get('approachRegion', {}).get('paths', {}).get('path', []))

        initialLaneStatus = []
        restrictions = []
        for i in range(numLanes):
            lane_num = i + 1
            lane = {
                'order': lane_num,
                'type': get_lane_type(lane_num, numLanes),
                'status': 'open',
                'lane_number': lane_num,
                'restrictions': [],
            }
            # Overwrite lane_type and restrictions if in info
            lane, restrictions = get_lane_restrictions(info, lane, restrictions)
            initialLaneStatus.append(lane)

        nodes, indices = getNodesAndIndices(containers, numLanes, dataLane, initialLaneStatus)
        
        wzdxMessages = createWzdxMessages(nodes, indices, numLanes, initialLaneStatus, restrictions, containers['commonContainers'][0]['commonContainer'], workersPresent, info)

    wzd['features'] = wzdxMessages
    wzd = add_ids(wzd, True)
    validate(schema=WZDx_schema, instance=wzd) # This will throw an exception if the message is invalid
    return wzd

# Add ids to message
def add_ids(message, add_ids):
    if add_ids:
        feed_info_id = message['road_event_feed_info']['feed_info_id']
        data_source_id = message['road_event_feed_info']['data_sources'][0]['data_source_id']

        road_event_length = len(message['features'])
        road_event_ids = []
        for i in range(road_event_length):
            road_event_ids.append(str(uuid.uuid4()))

        for i in range(road_event_length):
            feature = message['features'][i]
            road_event_id = road_event_ids[i]
            feature['properties']['road_event_id'] = road_event_id
            # feature['properties']['feed_info_id'] = feed_info_id
            feature['properties']['data_source_id'] = data_source_id
            # feature['properties']['relationship'] = {}
            feature['properties']['relationship']['relationship_id'] = str(uuid.uuid4())
            feature['properties']['relationship']['road_event_id'] = road_event_id
            if i == 0: feature['properties']['relationship']['first'] = road_event_ids
            else: feature['properties']['relationship']['next'] = road_event_ids
            # for lane in feature['properties']['lanes']:
            #     lane_id = str(uuid.uuid4())
            #     lane['lane_id'] = lane_id
            #     lane['road_event_id'] = road_event_id
            #     for lane_restriction in lane.get('restrictions', []):
            #         lane_restriction_id = str(uuid.uuid4())
            #         lane_restriction['lane_restriction_id'] = lane_restriction_id
            #         lane_restriction['lane_id'] = lane_id
            # for types_of_work in feature['properties']['types_of_work']:
            #     types_of_work_id = str(uuid.uuid4())
            #     types_of_work['types_of_work_id'] = types_of_work_id
            #     types_of_work['road_event_id'] = road_event_id
    return message

# 0 pad times to 2 digits (2 -> 02)
def form_len(string):
    num = int(string)
    return format(num, '02d')

def convertLatLong(num):
    return float(num)/10000000

def reformatNodePoint(node):
    return [convertLatLong(node['long']), convertLatLong(node['lat']), node['elevation']]

def reformatGeometry(pathPoints):
    nodes = []
    for nodePoint in pathPoints:
        node = nodePoint['nodePoint']['node-3Dabsolute']
        nodes.append(reformatNodePoint(node))
    
    return nodes

def transformLaneStatus(numLanes, initialLaneStatus, laneStatus):
    currLaneStatus = copy.deepcopy(initialLaneStatus)
    for index, status in enumerate(laneStatus):
        if status['laneClosed'].get('True', {}) == None:
            currLaneStatus[index]['status'] = 'closed'

    return currLaneStatus

def getNodesAndIndices(containers, numLanes, dataLane, initialLaneStatus):
    datalaneIndex = dataLane - 1

    nodes = []

    indices = {
        'speedLimits': [],
        'workersPresent': [],
        'laneClosures': []
    }

    rszContainers = containers['rszContainers']['rszContainer']
    for rsz in rszContainers:
        speedLimit = rsz['speedLimit']['speed']
        
        currIndex = len(nodes)
        indices['speedLimits'].append({'speedLimit': speedLimit, 'startIndex': currIndex})
        
        path = rsz['rszRegion']['paths']['path'][datalaneIndex]
        geometry = reformatGeometry(path['pathPoints']['pathPoint'])

        for i in geometry:
          nodes.append(i)

    laneClosureContainers = containers['laneClosureContainers']['laneClosureContainer']
    for lc in laneClosureContainers:
        laneStatus = transformLaneStatus(numLanes, initialLaneStatus, lc['laneStatus']['laneStatus'])

        firstLane = lc['closureRegion']['paths']['path'][datalaneIndex]['pathPoints']['pathPoint']

        firstNode = reformatNodePoint(firstLane[0]['nodePoint']['node-3Dabsolute'])
        lastNode = reformatNodePoint(firstLane[-1]['nodePoint']['node-3Dabsolute'])

        firstIndex = nodes.index(firstNode)
        lastIndex = nodes.index(lastNode)
        indices['laneClosures'].append({'laneStatus': laneStatus, 'startIndex': firstIndex, 'endIndex': lastIndex})

    # situationalContainers = containers['situationalContainers']['situationalContainer']
    # for sit in situationalContainers:

    return nodes, indices


# def createIndividualWzdxMessage(numLanes, dataLane, restrictions, info, commonContainer, rszContainer = None, laneClosureContainer = None, situationalContainer = None):
#     prevSpeedlimit = 0
#     prevLaneStatus = initialLaneStatus
#     restrictions = []

#     features = []

#     createFeature(node, numLanes, currLaneStatus, currSpeedLimit, restrictions, commonContainer, workersPresent, info)

#     for index, node in enumerate(nodes):
#         currSpeedLimit = prevSpeedlimit
#         for speedLimit in indices['speedLimits']:
#             if speedLimit['startIndex'] == index:
#                 currSpeedLimit = speedLimit['speedLimit']
        
#         currLaneStatus = prevLaneStatus
#         for laneStatus in indices['laneClosures']:
#             if index >= laneStatus['startIndex'] and index <= laneStatus['endIndex']:
#                 currLaneStatus = laneStatus['laneStatus']
#             else:
#                 currLaneStatus = initialLaneStatus

#         if currSpeedLimit != prevSpeedlimit or currLaneStatus != prevLaneStatus or index == 0:

#             if (index != 0):
#                 features[-1]['geometry']['coordinates'].append(node)

#             features.append()
            
#             prevSpeedlimit = currSpeedLimit
#             prevLaneStatus = currLaneStatus
        
#         else:
#             features[-1]['geometry']['coordinates'].append(node)
#     return features

def createConnectedWzdxMessages(nodes, indices, numLanes, initialLaneStatus, restrictions, commonContainer, workersPresent, info):
    prevSpeedlimit = 0
    prevLaneStatus = initialLaneStatus
    restrictions = []

    features = []

    for index, node in enumerate(nodes):
        currSpeedLimit = prevSpeedlimit
        for speedLimit in indices['speedLimits']:
            if speedLimit['startIndex'] == index:
                currSpeedLimit = speedLimit['speedLimit']
        
        currLaneStatus = prevLaneStatus
        for laneStatus in indices['laneClosures']:
            if index >= laneStatus['startIndex'] and index <= laneStatus['endIndex']:
                currLaneStatus = laneStatus['laneStatus']
            else:
                currLaneStatus = initialLaneStatus

        if currSpeedLimit != prevSpeedlimit or currLaneStatus != prevLaneStatus or index == 0:

            if (index != 0):
                features[-1]['geometry']['coordinates'].append(node)

            features.append(createFeature(node, numLanes, currLaneStatus, currSpeedLimit, restrictions, commonContainer, workersPresent, info))
            
            prevSpeedlimit = currSpeedLimit
            prevLaneStatus = currLaneStatus
        
        else:
            features[-1]['geometry']['coordinates'].append(node)
    return features

def createFeature(node, numLanes, lanes, speedLimit, restrictions, commonContainer, workersPresent, info):
    properties = setFeatureProperties(commonContainer, info)

    num_closed_lanes = 0
    for lane in lanes:
        if lane['status'] == 'closed' or lane['status'] == 'merge-left' or lane['status'] == 'merge-right':
            num_closed_lanes = num_closed_lanes + 1
    if num_closed_lanes == 0:
        properties['vehicle_impact'] = 'all-lanes-open'
    elif num_closed_lanes == numLanes:
        properties['vehicle_impact'] = 'all-lanes-closed'
    else:
        properties['vehicle_impact'] = 'some-lanes-closed'

    # workser_present
    properties['workers_present'] = True # people_present

    # reduced_speed_limit
    properties['reduced_speed_limit'] = speedLimit

    # description
    properties['description'] = info['description']

    # restrictions
    if restrictions:
        properties['restrictions'] = restrictions

    # Lanes object
    properties['lanes'] = lanes

    # properties
    feature = {}
    feature['type'] = 'Feature'
    feature['properties'] = properties
    feature['geometry'] = {'type': 'LineString', 'coordinates': [node]}

    return feature

def get_lane_restrictions(info, lane, restrictions):
    lane_type = ''
    lane['restrictions'] = [] #no-trucks, travel-peak-hours-only, hov-3, hov-2, no-parking
        #reduced-width, reduced-height, reduced-length, reduced-weight, axle-load-limit, gross-weight-limit, towing-prohibited, permitted-oversize-loads-prohibited

    # Overwrite lane_type if present in configuration file
    for lane_obj in info['lanes_obj']:
        if lane_obj['LaneNumber'] == lane['lane_number']:
            lane['type'] = lane_obj['LaneType']
            for lane_restriction_info in lane_obj['LaneRestrictions']:
                lane_restriction = {}
                lane_restriction['lane_restriction_id'] = ''
                lane_restriction['lane_id'] = ''
                lane_restriction['restriction_type'] = lane_restriction_info['RestrictionType']
                if not lane_restriction_info['RestrictionType'] in restrictions: 
                    restrictions.append(lane_restriction_info['RestrictionType'])
                if lane_restriction['restriction_type'] in ['reduced-width', 'reduced-height', 'reduced-length', 'reduced-weight', 'axle-load-limit', 'gross-weight-limit']:
                    lane_restriction['restriction_value'] = lane_restriction_info['RestrictionValue']
                    lane_restriction['restriction_units'] = lane_restriction_info['RestrictionUnits']
                lane['restrictions'].append(lane_restriction)

    return lane, restrictions


def get_lane_type(lane_number, num_lanes):
    # Lane Type
    lane_type = 'middle-lane' #left-lane, right-lane, middle-lane, right-exit-lane, left-exit-lane, ... (exit lanes, merging lanes, turning lanes)
    if lane_number == 1:
        lane_type = 'left-lane'
    elif lane_number == num_lanes:
        lane_type = 'right-lane'

    return lane_type

def setFeatureProperties(commonContainer, info):
    feature = {}
    feature['road_event_id'] = ''
    feature['data_source_id'] = ''

    # Event Type ['work-zone', 'detour']
    feature['event_type'] = 'work-zone'

    # Relationship
    feature['relationship'] = {}

    # Subidentifier
    # feature['sub_identifier'] = ids['sub_identifier']

    # road_name
    feature['road_name'] = info['road_name']

    # road_name
    feature['road_number'] = info['road_number']

    # direction
    feature['direction'] = info['direction']

    # beginning_cross_street
    if info['beginning_cross_street']:
        feature['beginning_cross_street'] = info['beginning_cross_street']

    # beginning_cross_street
    if info['ending_cross_street']:
        feature['ending_cross_street'] = info['ending_cross_street']

    # beginning_milepost
    if info['beginning_milepost']:
        feature['beginning_milepost'] = info['beginning_milepost']

    # ending_milepost
    if info['ending_milepost']:
        feature['ending_milepost'] = info['ending_milepost']

    # beginning_accuracy
    feature['beginning_accuracy'] = info['beginning_accuracy']

    # ending_accuracy
    feature['ending_accuracy'] = info['ending_accuracy']

    # start_date
    start_date = commonContainer['eventInfo']['startDateTime'] #Offset is in minutes from UTC (-5 hours, ET), unused
    feature['start_date'] = str(start_date['year']+'-'+form_len(start_date['month'])+'-'+form_len(start_date['day'])+'T'+form_len(start_date['hour'])+':'+form_len(start_date['minute'])+':00Z')
    
    # end_date
    end_date = commonContainer['eventInfo']['endDateTime']
    feature['end_date'] = str(end_date['year']+'-'+form_len(end_date['month'])+'-'+form_len(end_date['day'])+'T'+form_len(end_date['hour'])+':'+form_len(end_date['minute'])+':00Z')
    
    # start_date_accuracy
    feature['start_date_accuracy'] = info['start_date_accuracy']

    # end_date_accuracy
    feature['end_date_accuracy'] = info['end_date_accuracy']

    # event status
    if info['event_status']:
        feature['event_status'] = info['event_status']
        if info['event_status'] == 'planned':
            feature['start_date_accuracy'] = 'estimated'
            feature['end_date_accuracy'] = 'estimated'

    # other stuffs was here

    # issuing_organization
    if info['issuing_organization']:
        feature['issuing_organization'] = info['issuing_organization']
    
    # creation_date
    if info['creation_date']:
        feature['creation_date'] = info['creation_date']
    
    # update_date
    feature['update_date'] = info['update_date']

    # creation_date
    feature['creation_date'] = info['update_date']

    #type_of_work
    #maintenance, minor-road-defect-repair, roadside-work, overhead-work, below-road-work, barrier-work, surface-work, painting, roadway-relocation, roadway-creation
    feature['types_of_work'] = []
    for types_of_work in info['types_of_work']:
        type_of_work = {}
        type_of_work['types_of_work_id'] = ''
        type_of_work['road_event_id'] = ''
        type_of_work['type_name'] = types_of_work['WorkType']
        if types_of_work.get('Is_Architectural_Change', '') != '': type_of_work['is_architectural_change'] = types_of_work['Is_Architectural_Change']
        feature['types_of_work'].append(type_of_work)

    return feature

WZDx_schema = {
  "$id": "https://github.com/usdot-jpo-ode/jpo-wzdx/tree/v3/create-feed/schemas/wzdx_v3.0_feed.json",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "WZDx v3.0 Feed",
  "description": "The GeoJSON output of a WZDx v3.0 data feed",
  "type": "object",
  "properties": {
    "road_event_feed_info": {
      "$ref": "#/definitions/road_event_feed_info"
    },
    "type": {
      "description": "The GeoJSON type",
      "enum": ["FeatureCollection"]
    },
    "features": {
      "description": "The list of road events (GeoJSON Features)",
      "type": "array",
      "items": {
        "title": "Road Event (GeoJSON Feature)",
        "type": "object",
        "properties": {
          "type": {
            "description": "The GeoJSON Feature type",
            "enum": ["Feature"]
          },
          "properties": {
            "$ref": "#/definitions/road_event"
          },
          "geometry": {
            "oneOf": [
              {
                "$ref": "https://geojson.org/schema/LineString.json"
              },
              {
                "$ref": "https://geojson.org/schema/MultiPoint.json"
              }
            ]
          }
        },
        "required": ["type","properties","geometry"]
      }
    }
  },
  "required": ["road_event_feed_info", "type", "features"],
  "definitions": {
    "road_event_feed_info": {
      "title": "Road Event Feed Information",
      "type": "object",
      "properties": {
        "publisher": {
          "description": "The organization responsible for publishing the feed",
          "type": "string"
        },
        "contact_name": {
          "description": "The name of the individual or group responsible for the data feed",
          "type": "string"
        },
        "contact_email": {
          "description": "The email address of the individual or group responsible for the data feed",
          "type": "string",
          "format": "email"
        },
        "update_frequency": {
          "description": "The frequency in seconds at which the data feed is updated",
          "type": "integer",
          "minimum": 1
        },
        "update_date": {
          "description": "The UTC date and time when the data feed was last updated",
          "type": "string",
          "format": "date-time"
        },
        "version": {
          "description": "The WZDx specification version used to create the data feed, in 'major.minor' format",
          "type": "string",
          "pattern": "^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$"
        },
        "data_sources": {
          "description": "A list of specific data sources for the road event data in the feed",
          "type": "array",
          "items": {
            "$ref": "#/definitions/road_event_data_source"
          },
          "minItems": 1
        }
      },
      "required": ["update_date", "version", "publisher", "data_sources"]
    },
    "road_event_data_source": {
      "title": "Road Event Data Source",
      "type": "object",
      "properties": {
        "data_source_id": {
          "description": "Unique identifier for the organization providing work zone data",
          "type": "string"
        },
        "organization_name": {
          "description": "The name of the organization for the authoritative source of the work zone data",
          "type": "string"
        },
        "contact_name": {
          "description": "The name of the individual or group responsible for the data source",
          "type": "string"
        },
        "contact_email": {
          "description": "The email address of the individual or group responsible for the data source",
          "type": "string",
          "format": "email"
        },
        "update_frequency": {
          "description": "The frequency in seconds at which the data source is updated",
          "type": "integer",
          "minimum": 1
        },
        "update_date": {
          "description": "The UTC date and time when the data source was last updated",
          "type": "string",
          "format": "date-time"
        },
        "location_method": {
          "$ref": "#/definitions/location_method"
        },
        "location_verify_method": {
          "description": "The method used to verify the accuracy of the location information",
          "type": "string"
        },
        "lrs_type": {
          "description": "Describes the type of linear referencing system used for the milepost measurements",
          "type": "string"
        },
        "lrs_url": {
          "description": "A URL where additional information on the LRS information and transformation information is stored",
          "type": "string",
          "format": "uri"
        }
      },
      "required": ["data_source_id", "organization_name", "location_method"]
    },
    "location_method": {
      "title": "Location Method Enumerated Type",
      "description": "The typical method used to locate the beginning and end of a work zone impact area",
      "enum": [
        "channel-device-method",
        "sign-method",
        "junction-method",
        "other",
        "unknown"
      ]
    },
    "road_event": {
      "title": "Road Event",
      "type": "object",
      "properties": {
        "road_event_id": {
          "description": "A unique identifier issued by the data feed provider to identify the work zone project or activity",
          "type": "string"
        },
        "data_source_id": {
          "description": "Identifies the data source from which the road event data is sourced from",
          "type": "string"
        },
        "event_type": {
          "$ref": "#/definitions/event_type"
        },
        "relationship": {
          "$ref": "#/definitions/relationship"
        },
        "road_name": {
          "description": "Publicly known name of the road on which the event occurs",
          "type": "string"
        },
        "road_number": {
          "description": "The road number designated by a jurisdiction such as a county, state or interstate (e.g. I-5, VT 133)",
          "type": "string"
        },
        "direction": {
          "$ref": "#/definitions/direction"
        },
        "beginning_cross_street": {
          "description": "Name or number of the nearest cross street along the roadway where the event begins",
          "type": "string"
        },
        "ending_cross_street": {
          "description": "Name or number of the nearest cross street along the roadway where the event ends",
          "type": "string"
        },
        "beginning_milepost": {
          "description": "The linear distance measured against a milepost marker along a roadway where the event begins",
          "type": "number",
          "minimum": 0
        },
        "ending_milepost": {
          "description": "The linear distance measured against a milepost marker along a roadway where the event ends",
          "type": "number",
          "minimum": 0
        },
        "beginning_accuracy": {
          "$ref": "#/definitions/spatial_verification"
        },
        "ending_accuracy": {
          "$ref": "#/definitions/spatial_verification"
        },
        "start_date": {
          "description": "The UTC date and time (formatted according to RFC 3339, Section 5.6) when the road event begins (e.g. 2020-11-03T19:37:00Z)",
          "type": "string",
          "format": "date-time"
        },
        "end_date": {
          "description": "The UTC date and time (formatted according to RFC 3339, Section 5.6) when the road event ends (e.g. 2020-11-03T19:37:00Z)",
          "type": "string",
          "format": "date-time"
        },
        "start_date_accuracy": {
          "$ref": "#/definitions/time_verification"
        },
        "end_date_accuracy": {
          "$ref": "#/definitions/time_verification"
        },
        "event_status": {
          "$ref": "#/definitions/event_status"
        },
        "total_num_lanes": {
          "description": "The total number of lanes associated with the road event",
          "type": "integer",
          "exclusiveMinimum": 0
        },
        "vehicle_impact": {
          "$ref": "#/definitions/vehicle_impact"
        },
        "workers_present": {
          "description": "A flag indicating that there are workers present in the road event",
          "type": "boolean"
        },
        "reduced_speed_limit": {
          "description": "The reduced speed limit posted within the road event",
          "type": "integer",
          "minimum": 0
        },
        "restrictions": {
          "description": "Zero or more road restrictions applying to the road event",
          "type": "array",
          "items": {
            "$ref": "#/definitions/road_restriction"
          },
          "uniqueItems": True
        },
        "description": {
          "description": "Short free text description of the road event",
          "type": "string"
        },
        "creation_date": {
          "description": "The UTC date and time (formatted according to RFC 3339, Section 5.6) when the road event was created (e.g. 2020-11-03T19:37:00Z)",
          "type": "string",
          "format": "date-time"
        },
        "update_date": {
          "description": "The UTC date and time (formatted according to RFC 3339, Section 5.6) when the road event was last updated (e.g. 2020-11-03T19:37:00Z)",
          "type": "string",
          "format": "date-time"
        },
        "types_of_work": {
          "description": "A list of the types of work being done in a road event",
          "type": "array",
          "items": {
            "$ref": "#/definitions/type_of_work"
          }
        },
        "lanes": {
          "description": "A list of individual lanes within a road event (roadway segment)",
          "type": "array",
          "items": {
            "$ref": "#/definitions/lane"
          }
        }
      },
      "required": [
        "road_event_id",
        "data_source_id",
        "road_name",
        "direction",
        "beginning_accuracy",
        "ending_accuracy",
        "start_date",
        "end_date",
        "start_date_accuracy",
        "end_date_accuracy",
        "vehicle_impact"
      ]
    },
    "relationship": {
      "title": "Relationship",
      "description": "Identifies both sequential and hierarchical relationships between road events and other entities. For example, a relationship can be used to link multiple road events to a common 'parent', such as a project or phase, or identify a sequence of road events",
      "type": "object",
      "properties": {
        "first": {
          "description": "Indicates the first (can be multiple) road event in a sequence of road events by 'road_event_id'",
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string"
          }
        },
        "next": {
          "description": "Indicates the next (can be multiple) road event in a sequence of road events by 'road_event_id'",
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string"
          }
        },
        "parents": {
          "description": "Indicates entities that the road event with this relationship is a part of, such as a work zone project or phase. Values can but do not have to correspond to a WZDx entity",
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string"
          }
        },
        "children": {
          "description": "Indicates entities that are part of the road event with this relationship, such as a detour or piece of equipment. Values can but do not have to correspond to a WZDx entity",
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string"
          }
        }
      }
    },
    "type_of_work": {
      "title": "Type of Work",
      "description": "A description of the type of work being done in a road event and an indication of if that work will result in an architectural change to the roadway",
      "type": "object",
      "properties": {
        "type_name": {
          "$ref": "#/definitions/work_type_name"
        },
        "is_architectural_change": {
          "description": "A flag indicating whether the type of work will result in an architectural change to the roadway",
          "type": "boolean"
        }
      },
      "required": ["type_name"]
    },
    "lane": {
      "title": "Lane",
      "description": "An individual lane within a road event",
      "type": "object",
      "properties": {
        "order": {
          "description": "The position (index) of the lane in sequence on the roadway, where '1' represents the left-most lane",
          "type": "integer",
          "minimum": 1
        },
        "status": {
          "$ref": "#/definitions/lane_status"
        },
        "type": {
          "$ref": "#/definitions/lane_type"
        },
        "lane_number": {
          "description": "The number assigned to the lane to help identify its position. Flexible, but usually used for regular, driveable lanes",
          "type": "integer",
          "minimum": 1
        },
        "restrictions": {
          "description": "A list of restrictions specific to the lane",
          "type": "array",
          "items": {
            "$ref": "#/definitions/lane_restriction"
          }
        }
      },
      "required": ["status", "type", "order"]
    },
    "lane_restriction": {
      "title": "Lane Restriction",
      "description": "A lane-level restriction, including type and value",
      "type": "object",
      "properties": {
        "restriction_type": {
          "$ref": "#/definitions/road_restriction"
        },
        "restriction_value": {
          "type": "number"
        },
        "restriction_units": {
          "$ref": "#/definitions/lane_restriction_unit"
        }
      },
      "required": ["restriction_type"],
      "dependencies": {
        "restriction_value": ["restriction_units"]
      }
    },
    "event_type": {
      "title": "Road Event Type Enumerated Type",
      "description": "The type of WZDx road event",
      "enum": ["work-zone", "detour"]
    },
    "direction": {
      "title": "Direction Enumerated Type",
      "description": "The direction for a road event based on standard naming for US roads; indicates the direction the traffic flow regardless of the real heading angle",
      "enum": ["northbound", "eastbound", "southbound", "westbound"]
    },
    "spatial_verification": {
      "title": "Spatial Verification Enumerated Type",
      "description": "An indication of how a geographical coordinate was defined",
      "enum": ["estimated", "verified"]
    },
    "time_verification": {
      "title": "Time Verification Enumerated Type",
      "description": "A measure of how accurate the a datetime is",
      "enum": ["estimated", "verified"]
    },
    "event_status": {
      "title": "Event Status Enumerated Type",
      "description": "The status of the road event",
      "enum": ["planned", "pending", "active", "completed", "cancelled"]
    },
    "vehicle_impact": {
      "title": "Vehicle Impact Enumerated Type",
      "description": "The impact to vehicular lanes along a single road in a single direction",
      "enum": ["all-lanes-closed", "some-lanes-closed", "all-lanes-open", "alternating-one-way", "unknown"]
    },
    "road_restriction": {
      "title": "Road Restriction Enumerated Type",
      "description": "The type of vehicle restriction on a roadway",
      "enum": [
        "no-trucks",
        "travel-peak-hours-only",
        "hov-3",
        "hov-2",
        "no-parking",
        "reduced-width",
        "reduced-height",
        "reduced-length",
        "reduced-weight",
        "axle-load-limit",
        "gross-weight-limit",
        "towing-prohibited",
        "permitted-oversize-loads-prohibited"
      ]
    },
    "work_type_name": {
      "title": "Work Type Name Enumerated Type",
      "description": "A high-level text description of the type of work being done in a road event",
      "enum": [
        "maintenance",
        "minor-road-defect-repair",
        "roadside-work",
        "overhead-work",
        "below-road-work",
        "barrier-work",
        "surface-work",
        "painting",
        "roadway-relocation",
        "roadway-creation"
      ]
    },
    "lane_status": {
      "title": "Lane Status Enumerated Type",
      "description": "The status of the lane for the traveling public",
      "enum": ["open", "closed", "shift-left", "shift-right", "merge-left", "merge-right", "alternating-one-way"]
    },
    "lane_type": {
      "title": "Lane Type Enumerated Type",
      "description": "An indication of the type of lane or shoulder",
      "enum": [
        "left-lane",
        "right-lane",
        "middle-lane",
        "center-lane",
        "lane",
        "right-turning-lane",
        "left-turning-lane",
        "right-exit-lane",
        "left-exit-lane",
        "right-merging-lane",
        "left-merging-lane",
        "right-exit-ramp",
        "right-second-exit-ramp",
        "left-exit-ramp",
        "left-second-exit-ramp",
        "right-entrance-ramp",
        "right-second-entrance-ramp",
        "left-entrance-ramp",
        "left-second-entrance-ramp",
        "sidewalk",
        "bike-lane",
        "alternating-flow-lane",
        "right-shoulder",
        "left-shoulder",
        "shoulder",
        "hov-lane",
        "reversible-lane",
        "center-left-turn-lane"
      ]
    },
    "lane_restriction_unit": {
      "title": "Lane Restriction Unit Enumerated Type",
      "description": "Units of measure used for the lane restriction value",
      "enum": ["feet", "inches", "centimeters", "pounds", "tons", "kilograms"]
    }
  }
}