from __future__ import print_function

import base64
import json
import uuid
import boto3
import re

firehose = boto3.client('firehose')
sessionsDict = dict()
fields = ["session_id", "session_status", "inst_id", "start_tsp", "end_tsp", "start_event", "end_event", "duration",
          "nb_of_events"]
opening_pattern = re.compile("(.*)start(.*)|(.*)firstrun(.*)")


# dicionnary operations
def init_session(payload, ses_id):
    key = payload['inst_id']
    sessionDict = sessionsDict[key] = {}
    sessionDict['session_id'] = ses_id
    sessionDict['session_status'] = "running"
    sessionDict['inst_id'] = payload['inst_id']
    sessionDict['start_tsp'] = payload['timestamp']
    sessionDict['end_tsp'] = payload['timestamp']
    sessionDict['last_updated'] = payload['timestamp']
    sessionDict['start_event'] = payload['action']
    sessionDict['end_event'] = payload['action']
    sessionDict['nb_of_events'] = 1
    sessionDict['new'] = True


def update_session(payload, session_status):
    key = payload['inst_id']
    sessionDict = sessionsDict[key] = {}
    sessionDict['session_status'] = session_status
    sessionDict['end_tsp'] = payload['timestamp']
    sessionDict['last_updated'] = payload['timestamp']
    sessionDict['end_event'] = payload['action']
    sessionDict['nb_of_events'] += 1
    sessionDict['new'] = False


def close_session(payload, reason):
    key = payload['inst_id']
    sessionDict = sessionsDict[key] = {}
    sessionDict['session_status'] = reason
    sessionDict['new'] = False


def exportJsonToString(payload):
    return json.dumps(payload, separators=(',', ':')) + "\n"


def sessionize(event, context):
    for record in event['Records']:
        print("new event")
        payload = json.loads(base64.b64decode(record['kinesis']['data']))

        if payload['inst_id'] in sessionsDict.keys():
            print("updating session")

            # close on opening event
            if opening_pattern.match(payload['action']):
                close_session(payload, "closedOnOpenEvent")
                print("closing on open")
                sessionData = sessionsDict[payload['inst_id']]
                del sessionData['new']
                firehose.put_record(DeliveryStreamName='sessions-delivery',
                                    Record={'Data': exportJsonToString(sessionData)})

                # include current event in new session
                session_id = str(uuid.uuid4())
                init_session(payload, session_id)
                payload['session_id'] = session_id
                firehose.put_record(DeliveryStreamName='sessionized-events-delivery',
                                    Record={'Data': exportJsonToString(payload)})


            elif (int(payload['timestamp']) - int(sessionsDict[payload['inst_id']]['end_tsp'])) > 1800:
                close_session(payload, "timeout")
                print("closing on timeout")
                sessionData = sessionsDict[payload['inst_id']]
                del sessionData['new']
                firehose.put_record(DeliveryStreamName='sessions-delivery',
                                    Record={'Data': exportJsonToString(sessionData)})

                # include current event in new session
                session_id = str(uuid.uuid4())
                init_session(payload, session_id)
                payload['session_id'] = session_id
                firehose.put_record(DeliveryStreamName='sessionized-events-delivery',
                                    Record={'Data': exportJsonToString(payload)})

            else:
                # update
                payload['session_id'] = sessionsDict[payload['inst_id']]['session_id']
                firehose.put_record(DeliveryStreamName='sessionized-events-delivery',
                                    Record={'Data': exportJsonToString(payload)})
                update_session(payload, "running")

        # create new session
        else:
            session_id = str(uuid.uuid4())
            payload['session_id'] = session_id
            firehose.put_record(DeliveryStreamName='sessionized-events-delivery',
                                Record={'Data': exportJsonToString(payload)})
            init_session(payload, session_id)
            print("creating session")


    return 'Successfully transferred {} events to raw-events bucket'.format(len(event['Records']))
