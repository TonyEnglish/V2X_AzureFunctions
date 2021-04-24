#!/usr/bin/env python3
###
#   Software module builds .exer (xml format) file for RSZW/LC message for UPER encoding
#   This is based on the proposed NEW CAMP Version of ASN.1 definition proposed to SAE standard for RSM - J2945/4...
#
#   Developed By J. Parikh (CAMP) / Nov. 2017
#   Modified by J. Parikh for RSM V 0.5 - December, 2017
#   Modified by J. Parikh for RSM V 1.0 - January, 2018
#   Modified by J. Parikh for RSM V 4.4 - February, 2018
#   Modified by J. Parikh for RSM V 4.8 - March, 2018
#   Modified by J. Parikh for RSM V 5.1 - May, 2018
#
#   Revised to Software Ver 2.51    --    Jun, 2018
#       Set new referencePoint for each segment
#       Repeat referencepPoint for each segment
#
#       Repeat Event Info...
#           eventID
#           msgSegmentInfo
#           startDateTime, endDateTime
#           eventRecurrence
###
#
#
#   Revised to Software Ver 1.51   --     May, 2018
#       Added following:
#           <eventInfo>...</eventInfo>          --To address other RSM applications from SwRI...
#
#           Under following conditions, the generated WZ map nodes are split into multiple segments:
#           1.  When number of nodes generated per lane exceeds 64 (2..63)
#           2.  When expected UPER encoded message size exceeds 1200 octets (PDU Upper limit is 1500) +
#               space for header and security for about 300 octets
#
#           The point of segmentation generated in the "wz_msg_segmentation" is based on:
#           1.  1 node is equivalent to approx. 10 octets when nodes are presented as xyz_offset,
#                 therefore total 110 nodes per message segment makes map data approx. 1100 octets
#           2.  1 node is equivalent to approx. 15 octets when nodes are represented as 3d_absolute of lat, lot, alt,
#                 therefore total 75 nodes per message segment
#
#           <regionInfo>...</regionInfo>        --To address other RSM applications from SwRI...
#
#   Revised to Software Ver 1.48       Mar, 2018
#   Revised to Software Ver 1.44       Feb, 2018
#
###

###
#   Following function constructs the "Common Container" based on RSM.4.4 ASN.1 Definition
###

# import xmltodict

def build_xml_CC(idList, eDateTime, endDateTime, timeOffset, wzDaysOfWeek, c_sc_codes, refPoint, appHeading, hTolerance,
                 speedLimit, laneWidth, rW, eL, lS, arrayMapPt, msgSegList, currSeg, descName):

    ###
    #       Following data are passed from the caller for constructing Common Container...
    ###
    #       idLIst      = message ID, Station ID and Event ID [142,aabbccdd,255]
    #       eDateTime   = event start date & time [yyyy,mm,dd,hh,mm,ss]
    #       durDateTime = event duration date & time [yyyy,mm,dd,hh,mm,ss]
    #       timeOffset  = offset in minutes from UTC -300 minutes
    #       c_sc_codes  = cause and subcause codes [c,sc]
    #       refPoint    = reference point [lat,lon,alt]
    #       appHeading  = applicable heading in degrees (0..360) at the ref point
    #       hTolerance  = heading tolerance in degrees (0..360)
    #       slType      = speedLimit [0,1,2,3,4,5]
    #       speedList   = allowed max speed in mph [0,0,45,60,0,70] --- MUST match with slType
    #       rW          = roadWidth (m)
    #       eL          = eventLength (m)
    #       lS          = laneStat lane status array
    #       appMapPt    = array containing approach map points constructed earlier before calling this function
    #       msgSegList  = generated list based on message segmentation containing following:
    #                       [[# of segments, nodes per segment],
    #                        [seg #(1), start node, end node for approach lane]
    #                        [seg #(1), start node, end node (max nodes per lane - approach lane nodes) for wz lane]
    #                        [seg #2, start node, end node (max nodes per lane)for wz lane]
    #                        [seg #n, until all wz nodes are done]]
    #       currSeg     = current message segment for processing
    #
    #
    ###

    ###
    #   Write initial xml lines in the output xml file...
    #   Following introductory lines are written in the calling routine (WZ_MapBuilder.py)...
    ###

    tab = "\t"  # define tab char equal editor's tab value...
    tab = "  "  # define tab char equal to 2 spaces...
    laneWidth = round(laneWidth*100)  # define laneWidth in cm

###
#   RSM: MessageFrame...  Following are REPEATED for all Message Segments...
###

###
#   RSM: Common Container for RSZW/LC...
###
    commonContainer = {}

###
#   Event Info...   Repeat for all message segments
#       eventID
#       msgSegmentInfo
#       startDateTime, endDateTime
#       eventRecurrence
###
    commonContainer['eventInfo'] = {}
    commonContainer['eventInfo']['eventID'] = idList[1]

###
#   Message segmentation section...   Repeated for all segments
#   Added - June, 2018
###
    commonContainer['eventInfo']['msgSegmentInfo'] = {}
    commonContainer['eventInfo']['msgSegmentInfo']['totalMsgSegments'] = msgSegList[0][0]

    commonContainer['eventInfo']['eventCancellation'] = False

###
#   Event start/end date & time... REPEAT for all message segments ...
###

    # commonContainer['eventInfo']['#comment'] = '\n...Event start Date and Time...\n'
    # xmlFile.write ("<!--\n\t\t ...Event start Date & Time...\n-->\n")                       ###comment in XML file

###
#   WZ start date and time are required. If not specified, use current date and 00h:00m
#   WZ end date and time are optional, if not present, skip it
###

    commonContainer['eventInfo']['startDateTime'] = {}
    commonContainer['eventInfo']['startDateTime']['year'] = eDateTime[2]
    commonContainer['eventInfo']['startDateTime']['month'] = eDateTime[0]
    commonContainer['eventInfo']['startDateTime']['day'] = eDateTime[1]
    commonContainer['eventInfo']['startDateTime']['hour'] = eDateTime[3]
    commonContainer['eventInfo']['startDateTime']['minute'] = eDateTime[4]
    commonContainer['eventInfo']['startDateTime']['offset'] = timeOffset

###
#       Event duration - End date & time can be optional...
###

    if str(endDateTime[0]) != "":
        commonContainer['eventInfo']['endDateTime'] = {}
        commonContainer['eventInfo']['endDateTime']['year'] = endDateTime[2]
        commonContainer['eventInfo']['endDateTime']['month'] = endDateTime[0]
        commonContainer['eventInfo']['endDateTime']['day'] = endDateTime[1]
        commonContainer['eventInfo']['endDateTime']['hour'] = endDateTime[3]
        commonContainer['eventInfo']['endDateTime']['minute'] = endDateTime[4]

###
#       Event Recurrence...
###

    commonContainer['eventInfo']['eventRecurrence'] = {}
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence'] = {}
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startTime'] = {}
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startTime']['hour'] = eDateTime[3]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startTime']['minute'] = eDateTime[4]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startTime']['second'] = 0
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endTime'] = {}
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endTime']['hour'] = endDateTime[3]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endTime']['minute'] = endDateTime[4]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endTime']['second'] = 0
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startDate'] = {}
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startDate']['year'] = eDateTime[2]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startDate']['month'] = eDateTime[0]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startDate']['day'] = eDateTime[1]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endDate'] = {}
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endDate']['year'] = endDateTime[2]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endDate']['month'] = endDateTime[0]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endDate']['day'] = endDateTime[1]
    days_of_week = ['monday', 'tuesday', 'wednesday',
                    'thursday', 'friday', 'saturday', 'sunday']
    days_of_week_convert = {'monday': 'Mon', 'tuesday': 'Tue', 'wednesday': 'Wen',
                            'thursday': 'Thu', 'friday': 'Fri', 'saturday': 'Sat', 'sunday': 'Sun'}
    for day in days_of_week:
        commonContainer['eventInfo']['eventRecurrence']['EventRecurrence'][day] = {
            str(days_of_week_convert[day] in wzDaysOfWeek).lower(): None}

###
#       Cause and optional subcause codes...
###
    commonContainer['eventInfo']['causeCode'] = c_sc_codes[0]
    commonContainer['eventInfo']['subCauseCode'] = c_sc_codes[1]

    # TODO: commonContainer['eventInfo']['affectedVehicles'] (optional)

###
#   Start of regionInfo
#       applicableHeading    ... Repeat for all message segments...
#       referencePoint, type ... Repeat for all message segments...
#       speedLimit
#       eventLength
#       approachRegion
#
###
    commonContainer['regionInfo'] = {}

###
#   Applicable Heading and Tolerance... REPEAT for message segments ...
#
#   Convert heading to int before converting to str
####

    appHeading = round(float(appHeading))

    commonContainer['regionInfo']['applicableHeading'] = {}
    commonContainer['regionInfo']['applicableHeading']['heading'] = appHeading
    commonContainer['regionInfo']['applicableHeading']['tolerance'] = hTolerance

###
#   Reference Point...    REPEAT for all message segments   ...
#
#   However following is done in the calling routine since wzMapPt is not available here...
#       Update refPoint to a new value for different message segment > 1.
#       Since the distance between the original reference point and the first node for message segment 2 to the last segment is
#       too far apart (xyz_offset) to be represented in just one offset node. To alleviate the issue, for every segment, a new reference
#       point is set as same as the first node point of of the lane for which the vehicle path data was collected.
###
#
#   1. Convert ref point lat/lon degrees to 1/10th of micro degrees (multiply by 10^7)
###

    lat = int(float(refPoint[0]) * 10000000)
    lon = int(float(refPoint[1]) * 10000000)
    elev = round(float(refPoint[2]))  # in meters no fraction

    commonContainer['regionInfo']['referencePoint'] = {}
    commonContainer['regionInfo']['referencePoint']['lat'] = lat
    commonContainer['regionInfo']['referencePoint']['long'] = lon
    commonContainer['regionInfo']['referencePoint']['elevation'] = elev

###
#
###
    # TODO: commonContainer['regionInfo']['locationUncertainty'] (optional)

###
#   Reference Point Type...
###
    commonContainer['regionInfo']['referencePointType'] = {
        "startOfEvent": None}
    commonContainer['regionInfo']['descriptiveName'] = descName


###
#   Following - ONLY for the message segment #1...
###
#   Speed limits...  type, speed and unit...
###
#       As of Nov. 2017...
#       speedLimit list is defined as follows: The values are input by the user...
#           0. type  = "vehicleMaxSpeed"
#           1. speed =  normal (what is on approach lanes...)
#           2.          in WZ at the reference point + applicable speed for WZ lane as node attribute
#           3.          when workers present (applicable only for WZ lane as node attribute)
#           4. unit  = "mph" or "kph" or "mpsXpt02"
#
#       The speed limit set here is at the start of the event (at the reference point)...
#       In case of CSW, it would be the advisory speed...
###

    # TODO: No longer exists
    # if currSeg == 1:
    #     commonContainer['regionInfo']['speedLimit'] = {}
    #     commonContainer['regionInfo']['speedLimit']['type'] = {}
    #     commonContainer['regionInfo']['speedLimit']['type'][speedLimit[0]] = None
    #     commonContainer['regionInfo']['speedLimit']['speed'] = speedLimit[2]
    #     commonContainer['regionInfo']['speedLimit']['speedUnits'] = {}
    #     commonContainer['regionInfo']['speedLimit']['speedUnits'][speedLimit[4]] = None


###
#   Event length in meters...
###

    # TODO: No longer exists
    # if currSeg == 1:
    #     commonContainer['regionInfo']['eventLength'] = eL

###
#   Start of approachRegion...
#
#   Scale factor for Approach Lanes Node Points is set to 1 (Default)...
###

    # AreaType -> Choice:
    #   broadRegion -> BroadRegion:
    #
    #   paths -> PathList (Sequence 1..10 of Path):
    #     pathWidth -> Int 0..1000 (10cm increments)
    #     pathPoints -> PathPoints (Sequence 2..50 of NodePointLLE):
    #       node-3Dabsolute -> DSRC.Position3D
    #       node-3Doffset -> Offset3D

    alScale = 1  # default approach lane scale factor
    if currSeg == 1:

        commonContainer['regionInfo']['approachRegion'] = {}
        commonContainer['regionInfo']['approachRegion']['paths'] = {}
        # paths = []
        # path = {}
        # path['pathWidth'] = 1 #int 0-1000, by 10cm increments
        # pathPoints = [] # NodePointLLE 2-50
        # pathPoint = {}
        # pathPoint['node-3Dabsolute'] = {}

        # path['pathPoints'] = pathPoints
        # commonContainer['regionInfo']['approachRegion']['paths'] = paths # 0-10
        # commonContainer['regionInfo']['approachRegion']['paths']['scale'] = alScale
        # commonContainer['regionInfo']['approachRegion']['paths']['rsmLanes'] = {}

###
#   For a lane closure starting at the ref. point, approach lane "connectsTO" a lane
#   for travel.
#
#   The following value is setup for testing only...
#
###

        commonContainer['regionInfo']['approachRegion']['paths']['path'] = []

        tL = lS[0][0]  # number of lanes
        ln = 0
        while ln < tL:
            preName = "Lane "
            if ln == 0:
                preName = "Left Lane: Lane "
            if ln == tL-1:
                preName = "Right Lane: Lane "
#

###
#       Following is needed for all cases... Either connectsTo or NOT...
###
            Path = {}
            Path['pathWidth'] = laneWidth
            Path['pathPoints'] = {}
            Path['pathPoints']['pathPoint'] = []
            # Path['laneID'] = ln+1
            # Path['lanePosition'] = ln+1
            # Path['laneName'] = "Lane #" + str(ln+1)
            # Path['laneGeometry'] = {}
            # Path['laneGeometry']['nodeSet'] = {}
            # Path['laneGeometry']['nodeSet']['NodeLLE'] = []
###
#       Repeat the following for all nodes in approach for lane ln+1
###

            kt = 0
            while kt < len(arrayMapPt):  # lat/lon/alt for each data point
                NodePoint = {}

###
#           Convert lat/lon degrees to 1/10th of micro degrees (multiply by 10^7)
#           Multiply converted lat/lon by the scaling factor...
#
#       NOTE:
#          ASN.1 value range defined in J2735 (-900000000) .. (900000001)
#
###
                lat = int((arrayMapPt[kt][ln*5+0]) * 10000000)
                lon = int((arrayMapPt[kt][ln*5+1]) * 10000000)
                elev = round(arrayMapPt[kt][ln*5+2])  # in full meters only

                NodePoint = {}
                NodePoint['nodePoint'] = {}
                NodePoint['nodePoint']['node-3Dabsolute'] = {}
                NodePoint['nodePoint']['node-3Dabsolute']['lat'] = lat
                NodePoint['nodePoint']['node-3Dabsolute']['long'] = lon
                NodePoint['nodePoint']['node-3Dabsolute']['elevation'] = elev

###
#           Before closing the "NodePoint, see if there are any node attributes that should be
#           added for the node. The attributes can be for example, vehicleMaxSpeed, taperLeft,
#           taper right, laneClosed, etc.
#
#           These attributes are generally not applicable to the approach lanes but certainly
#           would apply to the WZ lanes...
###
                Path['pathPoints']['pathPoint'].append(NodePoint)
                kt = kt + 1  # incr row (next node point for same lane
                # end of while

###
#       End of Path
###

            commonContainer['regionInfo']['approachRegion']['paths']['path'].append(
                Path)
            ln = ln + 1  # next lane

    # TODO: commonContainer['crossLinking'] (optional)

###
##
#       *****************  ... End of Common Container...  *****************
##
###
    return commonContainer


###
#       *****************  ... RSM: Start of Workzone Container...  *****************
#
#       NOTE: Added <scale> nn </scale> to change resolution from 1/10th microdegrees (default) to ...
#       In the following, it's scaled up to microdegrees...
#
# ----------------------------------------------------------------------------------------------------------

###
#   Following function generates "Work Zone" container .exer file using xml tags
#   defined in rsm4.4.asn for WZ lanes.
#
#   updated in June, 2018 for ASN. version 5.1...
#
#####

def build_xml_RSZC(speedLimit, laneWidth, arrayMapPt, RN, msgSegList, currSeg):

    ##print ("in build_xml_WZC, current segment", currSeg)

    ###
    #   Following data elements are passed by the calling routine
    #
    #   xmlFile     -   output .exer file in xml format
    #   speedLimit  -   List of speed limits for all lanes in WZ for:
    #                       normal speed limit (not in work zone)
    #                       speed limit in work zone
    #                       speed limit in work zone when workers are present
    #   laneWidth   -   lane width from the user input config file, converted to cms here... (Added on 3-11-2019)
    #   laneStat    -   list containing information about lane status - Lane#, Data point#, LC or LO, Offset in meters from ref. pt.
    #   wpStat      -   list of WP status
    #   arrayMapPt  -   array of node lists generated in getLanePt function
    #   RN          -   Boolean - True:  Generate reduced nodes for closed lanes
    #                           - False: Generate all nodes for closed lanes
    ###

    ###
    #   Set scale factor for WZ Lanes Node Points to 10 set as default...
    ###

    totLane = laneStat[0][0]  # total number of lanes
    wzLaneScale = 10  # WZ Lane scale factor(default)
    laneWidth = int(laneWidth*100)  # in cms

###
#   Start WZ lane map waypoints...
###

    rszContainer = {}

###
#   Added on Jan. 25, 2018
#   Add <laneStatus>..<LaneInfo> for each lane... in WZ
#
#   NOTE: Modify the following ONLY if the lane is closed for the entire WZ
#       Otherwise, specified in <nodeAttributes>
#       If both are present, <nodeAttributes> will be ignored...
#
###
#
###
#   Add <laneStatus> for each lane...
#
#   Revised on March 19, 2019...
#
#   As per DENSO logic in the OBU, this upper level "laneClosed" is used ONLY when, once the lane is closed, remains closed for
#   the entire work zone. If in the work zone, a lane has multiple lane closures, it is indicated at a node level.
#   In such case, the upper level lane status (closed/open) for the entire lane shall not be included. Otherwise, the application logic
#   will ignore the node level attributes.
#
#   The correct way should be to use the upper level lane status unless specified at the node attribute level which should take precedence...
#
#   Following logic is commented out since in this implementation, lane status is captured at node level and specified in node attribute.
#
#   Date Modified: March 12, 2019
#
###

###
#   Add speedLimit for the entire WZ under rszContainer. speedLimit can be updated at node level
#   when appropriate - e.g. workers present, otherwise the limit is applied for the entire WZ.
###
    rszContainer['speedLimit'] = {}
    rszContainer['speedLimit']['type'] = {}
    rszContainer['speedLimit']['type'][speedLimit[0]] = None
    rszContainer['speedLimit']['speed'] = speedLimit[1]

###
#   ... Start of WZ Lane Geometry ...
###
    rszContainer['rszRegion'] = {}
    rszContainer['rszRegion']['paths'] = {}
    rszContainer['rszRegion']['paths']['path'] = []
    ln = 0
    while ln < totLane:

        preName = "Lane #"
        if ln == 0:
            preName = "Left Lane: Lane #"
        if ln == totLane-1:
            preName = "Right Lane: Lane #"

        Path = {}
        Path['pathWidth'] = laneWidth
        Path['pathPoints'] = {}
        Path['pathPoints']['pathPoint'] = []

        # RSMLane = {}
        # RSMLane['laneID'] = ln+1
        # RSMLane['lanePosition'] = ln+1
        # RSMLane['laneName'] = preName+str(ln+1)
        # RSMLane['laneWidth'] = laneWidth
        # RSMLane['laneGeometry'] = {}
        # RSMLane['laneGeometry']['nodeSet'] = {}
        # RSMLane['laneGeometry']['nodeSet']['NodeLLE'] = []

###
#       Repeat the following for all nodes in WZ for lane ln+1
#
#       Following revised to support multiple message segments (message segmentation)
#
#       For each lane, the nodes will be from startNode to endNode as constructed in msgSegList
#       The msgSegList is organized as follows:
#
#       msgSegList[0]  = (totMsgSeg, maxNPL)
#       msgSegList[1]  = (1,startNode for appLane,endNode of appLane)    --- NOTE --- approach lane nodes ARE NOT SPLIT in multiple msg Seg.
#       msgSegList[2]  = (segNum,startNode for wzLane,endNode of wzLane)
#               ...
#               ...
#       msgSegList[n]  = (segNum,startNode for wzLane,endNode of wzLane)

#       Revised June 6, 2018
###

        #kt = 0
        kt = msgSegList[currSeg+1][1] - 1  # wz start and end nodes/seg starts
        prevLaneStat = 0  # previous lane state (open)
        prevLaneTaperStat = 0  # previous lane state (open)
        prevWPStat = 0  # previous WP state (no WP)
        connToFlag = 0  # set flag for connectsTo 0

        while kt < msgSegList[currSeg+1][2]:  # end node #
            ###
            #           First Get lane and WP status at the current node for the lane...
            ###
            # get lc/lo status for the node
            currLaneStat = arrayMapPt[kt][ln*5+3]
            # get lc/lo status for the node
            currLaneTaperStat = arrayMapPt[kt][ln*5+4]
            # get WP flag for the node
            currWPStat = arrayMapPt[kt][len(arrayMapPt[kt])-2]

###
#           Added on Jan. 26, 2018
#
#           Following determines if the lane is closed at the previous node for the lane,
#               If so AND RS is TRUE, NO NEED to write node and node attributes. This will reduce the DSRC message size
#
#           If the lane is opened again before the end of the WZ, node geometry is specified from lane opening
#           till it's closed again OR end of WZ.
#
# NOTE: For a lane that is closed from ref. pt. till the end of the WZ, TWO nodes are required.
#               1. first node at the ref. point and
#               2. last node at the end of the WZ
#
###
            ###
            #               Convert lat/lon degrees to 1/10th of micro degrees (multiply by 10^7) and add the node
            #               Multiply the converted lat/lon with the scaling factor
            #           NOTE:
            #               ASN.1 value range defined in J2735 (-900000000) .. (900000001)
            #
            ###
            lat = int((arrayMapPt[kt][ln*5+0]) * 10000000)
            lon = int((arrayMapPt[kt][ln*5+1]) * 10000000)
            elev = round(arrayMapPt[kt][ln*5+2])  # in full meters

            NodePoint = {}
            NodePoint['nodePoint'] = {}
            NodePoint['nodePoint']['node-3Dabsolute'] = {}
            NodePoint['nodePoint']['node-3Dabsolute']['lat'] = lat
            NodePoint['nodePoint']['node-3Dabsolute']['long'] = lon
            NodePoint['nodePoint']['node-3Dabsolute']['elevation'] = elev

###
#               Add Attributes here, IF....
#
#               1. Workers are present (TRUE), add new speed limit attribute
#               2. Lane closure/open, add lane taper attributes
#
#               Check for workers presence (0/1)
#               Check for lo/lc (0/1) for the current lane/node
#
#               Check following logic for adding node attributes...
###

            Path['pathPoints']['pathPoint'].append(NodePoint)

            kt = kt + 1  # incr for next node point for same lane
            # end of while - all nodes for the lane

###
#       For Closed Lane only, add "connectsTo" attribute for lane...
#       Must have at least two lanes for "connectsTo"...
###

        rszContainer['rszRegion']['paths']['path'].append(
            Path)

        ln = ln + 1  # next lane
        # end of while

    return rszContainer



def buildCommonContainer(eventId, startDateTime, endDateTime, timeOffset, wzDaysOfWeek, causeCodes, refPoint, heading, 
    laneWidth, rW, numlanes, arrayMapPt, descName):

    ###
    #       Following data are passed from the caller for constructing Common Container...
    ###
    #       eventId     = message ID
    #       eDateTime   = event start date & time [yyyy,mm,dd,hh,mm,ss]
    #       durDateTime = event duration date & time [yyyy,mm,dd,hh,mm,ss]
    #       timeOffset  = offset in minutes from UTC -300 minutes
    #       causeCodes  = cause and subcause codes [c,sc]
    #       refPoint    = reference point [lat,lon,alt]
    #       rW          = roadWidth (m)
    #       appMapPt    = array containing approach map points constructed earlier before calling this function
    #
    ###
    laneWidth = round(laneWidth * 100)  # define laneWidth in cm

    commonContainer = {}

    commonContainer['eventInfo'] = {}
    commonContainer['eventInfo']['eventID'] = eventId

    commonContainer['eventInfo']['eventCancellation'] = False

    ###
    #   WZ start date and time are required. If not specified, use current date and 00h:00m
    #   WZ end date and time are optional, if not present, skip it
    ###

    commonContainer['eventInfo']['startDateTime'] = {}
    commonContainer['eventInfo']['startDateTime']['year'] = startDateTime[2]
    commonContainer['eventInfo']['startDateTime']['month'] = startDateTime[0]
    commonContainer['eventInfo']['startDateTime']['day'] = startDateTime[1]
    commonContainer['eventInfo']['startDateTime']['hour'] = startDateTime[3]
    commonContainer['eventInfo']['startDateTime']['minute'] = startDateTime[4]
    commonContainer['eventInfo']['startDateTime']['offset'] = timeOffset

    ###
    #       Event duration - End date & time can be optional...
    ###

    if str(endDateTime[0]) != "":
        commonContainer['eventInfo']['endDateTime'] = {}
        commonContainer['eventInfo']['endDateTime']['year'] = endDateTime[2]
        commonContainer['eventInfo']['endDateTime']['month'] = endDateTime[0]
        commonContainer['eventInfo']['endDateTime']['day'] = endDateTime[1]
        commonContainer['eventInfo']['endDateTime']['hour'] = endDateTime[3]
        commonContainer['eventInfo']['endDateTime']['minute'] = endDateTime[4]

    ###
    #       Event Recurrence...
    ###

    commonContainer['eventInfo']['eventRecurrence'] = {}
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence'] = {}
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startTime'] = {}
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startTime']['hour'] = startDateTime[3]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startTime']['minute'] = startDateTime[4]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startTime']['second'] = 0
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endTime'] = {}
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endTime']['hour'] = endDateTime[3]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endTime']['minute'] = endDateTime[4]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endTime']['second'] = 0
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startDate'] = {}
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startDate']['year'] = startDateTime[2]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startDate']['month'] = startDateTime[0]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['startDate']['day'] = startDateTime[1]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endDate'] = {}
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endDate']['year'] = endDateTime[2]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endDate']['month'] = endDateTime[0]
    commonContainer['eventInfo']['eventRecurrence']['EventRecurrence']['endDate']['day'] = endDateTime[1]
    days_of_week = ['monday', 'tuesday', 'wednesday',
                    'thursday', 'friday', 'saturday', 'sunday']
    days_of_week_convert = {'monday': 'Mon', 'tuesday': 'Tue', 'wednesday': 'Wen',
                            'thursday': 'Thu', 'friday': 'Fri', 'saturday': 'Sat', 'sunday': 'Sun'}
    for day in days_of_week:
        commonContainer['eventInfo']['eventRecurrence']['EventRecurrence'][day] = {
            str(days_of_week_convert[day] in wzDaysOfWeek).lower(): None}

    ###
    #       Cause and optional subcause codes...
    ###
    commonContainer['eventInfo']['causeCode'] = causeCodes[0]
    commonContainer['eventInfo']['subCauseCode'] = causeCodes[1]

    # TODO: commonContainer['eventInfo']['affectedVehicles'] (optional)

    commonContainer['regionInfo'] = {}

    commonContainer['regionInfo']['applicableHeading'] = {}
    commonContainer['regionInfo']['applicableHeading']['heading'] = round(float(heading['heading']))
    commonContainer['regionInfo']['applicableHeading']['tolerance'] = heading['tolerance']

    lat = int(float(refPoint[0]) * 10000000)
    lon = int(float(refPoint[1]) * 10000000)
    elev = round(float(refPoint[2]))  # in meters no fraction

    commonContainer['regionInfo']['referencePoint'] = {}
    commonContainer['regionInfo']['referencePoint']['lat'] = lat
    commonContainer['regionInfo']['referencePoint']['long'] = lon
    commonContainer['regionInfo']['referencePoint']['elevation'] = elev

    # TODO: commonContainer['regionInfo']['locationUncertainty'] (optional)

    commonContainer['regionInfo']['referencePointType'] = {
        "startOfEvent": None}
    commonContainer['regionInfo']['descriptiveName'] = descName

    alScale = 1  # default approach lane scale factor

    commonContainer['regionInfo']['approachRegion'] = {}
    commonContainer['regionInfo']['approachRegion']['paths'] = {}

    commonContainer['regionInfo']['approachRegion']['paths']['path'] = []

    ln = 0
    while ln < numlanes:

        Path = {}
        Path['pathWidth'] = laneWidth
        Path['pathPoints'] = {}
        Path['pathPoints']['pathPoint'] = []

        kt = 0
        while kt < len(arrayMapPt):  # lat/lon/alt for each data point
            NodePoint = {}

            lat = int((arrayMapPt[kt][ln*5+0]) * 10000000)
            lon = int((arrayMapPt[kt][ln*5+1]) * 10000000)
            elev = round(arrayMapPt[kt][ln*5+2])  # in full meters only

            NodePoint = {}
            NodePoint['nodePoint'] = {}
            NodePoint['nodePoint']['node-3Dabsolute'] = {}
            NodePoint['nodePoint']['node-3Dabsolute']['lat'] = lat
            NodePoint['nodePoint']['node-3Dabsolute']['long'] = lon
            NodePoint['nodePoint']['node-3Dabsolute']['elevation'] = elev

            Path['pathPoints']['pathPoint'].append(NodePoint)
            kt = kt + 1  # incr row (next node point for same lane
            # end of while

        commonContainer['regionInfo']['approachRegion']['paths']['path'].append(
            Path)
        ln = ln + 1  # next lane

    # TODO: commonContainer['crossLinking'] (optional)

    return commonContainer


def buildLaneClosureContainer(laneStat, laneStatusVaries, geometry, laneWidth):
    laneClosureContainer = {}

    laneClosureContainer['laneStatus'] = {}
    laneClosureContainer['laneStatus']['laneStatus'] = []
    for index, status in enumerate(laneStat):
        laneStatus = {}
        laneStatus['lanePosition'] = index + 1
        laneStatus['laneClosed'] = {str(status): None}
        # laneStatus['laneCloseOffset'] = obstacleDistance # NOT IMPLEMENTED
        laneClosureContainer['laneStatus']['laneStatus'].append(laneStatus)
        
    if laneStatusVaries is not None:
        laneClosureContainer['laneStatusVaries'] = {str(laneStatusVaries): None}

    
    
    laneClosureContainer['closureRegion'] = {}
    laneClosureContainer['closureRegion']['paths'] = {}
    laneClosureContainer['closureRegion']['paths']['path'] = []

    laneWidth = round(laneWidth * 100)  # in cms
    
    for lane in geometry:
        Path = {}
        Path['pathWidth'] = laneWidth
        Path['pathPoints'] = {}
        Path['pathPoints']['pathPoint'] = []

        for node in lane:
            lat = int(node[0] * 10000000)
            lon = int(node[1] * 10000000)
            elev = round(node[2])  # in full meters

            NodePoint = {}
            NodePoint['nodePoint'] = {}
            NodePoint['nodePoint']['node-3Dabsolute'] = {}
            NodePoint['nodePoint']['node-3Dabsolute']['lat'] = lat
            NodePoint['nodePoint']['node-3Dabsolute']['long'] = lon
            NodePoint['nodePoint']['node-3Dabsolute']['elevation'] = elev
            
            Path['pathPoints']['pathPoint'].append(NodePoint)

        laneClosureContainer['closureRegion']['paths']['path'].append(Path)

    return laneClosureContainer


def buildRszContainer(speedLimit, geometry, laneWidth):
    rszContainer = {}

    rszContainer['speedLimit'] = {}
    rszContainer['speedLimit']['type'] = {speedLimit['type']: None}
    rszContainer['speedLimit']['speed'] = speedLimit['value']
    
    rszContainer['rszRegion'] = {}
    rszContainer['rszRegion']['paths'] = {}
    rszContainer['rszRegion']['paths']['path'] = []

    laneWidth = round(laneWidth * 100)  # in cms
    
    
    for lane in geometry:
        Path = {}
        Path['pathWidth'] = laneWidth
        Path['pathPoints'] = {}
        Path['pathPoints']['pathPoint'] = []

        for node in lane:
            lat = int(node[0] * 10000000)
            lon = int(node[1] * 10000000)
            elev = round(node[2])  # in full meters

            NodePoint = {}
            NodePoint['nodePoint'] = {}
            NodePoint['nodePoint']['node-3Dabsolute'] = {}
            NodePoint['nodePoint']['node-3Dabsolute']['lat'] = lat
            NodePoint['nodePoint']['node-3Dabsolute']['long'] = lon
            NodePoint['nodePoint']['node-3Dabsolute']['elevation'] = elev
            
            Path['pathPoints']['pathPoint'].append(NodePoint)

        rszContainer['rszRegion']['paths']['path'].append(Path)
    # End iterating over lanes

    return rszContainer


def buildSituationalContainer(obstructions, visibility, peoplePresent, anomalousTraffic):
    situationalContainer = {}

    if obstructions is not None:
        situationalContainer['obstructions'] = obstructions

    if visibility is not None:
        situationalContainer['visibility'] = visibility

    if peoplePresent is not None:
        situationalContainer['peoplePresent'] = {str(peoplePresent): None}

    if anomalousTraffic is not None:
        situationalContainer['anomalousTraffic'] = {str(anomalousTraffic): None}

    return situationalContainer