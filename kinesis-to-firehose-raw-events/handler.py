from __future__ import print_function

import boto3
import base64

firehose = boto3.client('firehose')


def lambda_handler(event, context):
    for record in event['Records']:

        try:
            payload = base64.b64decode(record['kinesis']['data'])

            # post to S3 via the Firehose delivery system
            response = firehose.put_record(
                DeliveryStreamName='raw-events-delivery',
                Record={'Data': payload}
            )
        except:
            pass

    return 'Successfully transferred {} events to raw-events bucket'.format(len(event['Records']))
