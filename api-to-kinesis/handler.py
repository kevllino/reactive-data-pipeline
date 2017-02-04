from __future__ import print_function
from lib.common import exportJsonToString
import boto3
import base64
import json
import uuid
import time

kinesis = boto3.client('kinesis')

def enrich(event):
    # add event_id + timestamp in millis
    event['event_id'] = str(uuid.uuid4())
    event['timestamp'] = str(long(time.time()))  # utc timestamp in seconds

def lambda_handler(event, context):
    for record in event['Records']:
        try:
            # read, convert and enrich api data
            payload = json.loads(base64.b64decode(record['kinesis']['data']))
            enrich(payload)
            # post enriched record to kinesis stream
            enrichedata = exportJsonToString(payload)
            response = kinesis.put_record(
                StreamName='raw_events-stream',
                Data=enrichedata,
                PartitionKey='1')
        except:
            pass

    return 'Successfully processed {} records.'.format(len(event['Records']))
