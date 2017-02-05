from __future__ import print_function

import boto3
import base64
import json
import uuid
import time
import re

kinesis = boto3.client('kinesis')
firehose = boto3.client('firehose')

def exportJsonToString(jsonObject):
    return json.dumps(jsonObject, separators=(',', ':')) + "\n"

def enrich(event):
    # add event_id + timestamp in millis
    event['event_id'] = str(uuid.uuid4())
    event['timestamp'] = str(long(time.time()))  # utc timestamp in seconds

def isValid(event):
    build_pattern = re.compile("^(f[1-9]|10)\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    inst_id_pattern = re.compile("^[0-9a-fA-F]{2,}$")
    pro_pattern = re.compile("^pro(.*)")
    reader_pattern = re.compile("^reader(.*)")

    try:
        if (event['timestamp'] is not None and event['action'] is not None and event['inst_id'] is not None):
            if (build_pattern.match(str(event['build_id'])) and inst_id_pattern.match(str(event['inst_id'])) and (
                reader_pattern.match(str(event['action'])) or (
                pro_pattern.match(str(event['action'])) and event['trialstate'] in ["Expired", "Activated", "Trial"]))):
                return True
            else:
                return False
    except KeyError, e:
        return False

# takes data simulated from event.json
def api_to_kinesis(event, context):
    for record in event['Records']:
        try:
            if (isValid(payload)):
                # read, convert and enrich api data
                payload = json.loads(base64.b64decode(record['kinesis']['data']))
                enrich(payload)
                # post enriched record to kinesis stream
                enrichedata = exportJsonToString(payload)
                response = kinesis.put_record(
                    StreamName='raw_events-stream',
                    Data=enrichedata,
                    PartitionKey='1')
            else:
                firehose.put_record(
                    DeliveryStreamName='dump-events-delivery',
                    Record={'Data': exportJsonToString(payload)}
                )
        except:
            pass

    return 'Successfully processed {} records.'.format(len(event['Records']))
