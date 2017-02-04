from __future__ import print_function

import boto3
import base64
import json
import datetime
import time
import re

kinesis = boto3.client('kinesis')
firehose = boto3.client('firehose')


def exportJsonToString(jsonObject):
    return json.dumps(jsonObject, separators=(',', ':')) + "\n"


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


fixed_schema = ["_l", "timestamp", "apptoken", "action", "inst_id", "installsource", "language", "nid",
                "ip_address", "event_id", "trialstate", "build_id", "_p2", "extended"]


def remove_dict_element(initial_dict, key):
    dict_copy = dict(initial_dict)
    del dict_copy[key]
    return dict_copy


def createExtendedField(event):
    extended_field = {}
    for key in event.keys():
        if key not in fixed_schema:
            extended_field[key] = event[key]
            event = remove_dict_element(event, key)
    event[u'extended'] = extended_field
    return event


def deriveBuild(event):
    build_id = event['build_id']
    major_version = (re.search("^([1-9]|10)\\.", build_id)).group(1)
    minor_version = (re.search("(([1-9]|10)\\.\\d{1,3})", build_id)).group(1)
    maintenance_id = (re.search("(([1-9]|10)\.\d{1,3}\.\d{1,3})", build_id)).group(1)
    event[u'major_version'] = major_version
    event[u'minor_version'] = minor_version
    event[u'maint_id'] = maintenance_id


def deriveProduct(event):
    pro_pattern = re.compile("^pro(.*)")
    reader_pattern = re.compile("^reader(.*)")
    action = str(event['action'])
    if (pro_pattern.match(action)):
        event[u'product'] = "pro"
    elif (reader_pattern.match(action)):
        event[u'product'] = "reader"
    else:
        event[u'product'] = "inconsistency"


def deriveInstId(event):
    try:
        split_index = event['_l']
        inst_id = str(event['inst_id'])
        event[u'machine_id_hash'] = inst_id[:split_index]
        event[u'user_id_hash'] = inst_id[split_index:]
    except IndexError:
        pass
    except KeyError, e:
        pass


def deriveDate(event):
    tsp = event['timestamp']
    date = datetime.datetime.fromtimestamp(float(tsp))
    date_id = str(date.year) + str(date.month) + str(date.day)
    hour_id = date_id + str(date.hour)
    minute_id = hour_id + str(date.minute)
    event[u'date'] = date.strftime('%Y-%m-%d %H:%M:%S')
    event[u'date_id'] = int(date_id)
    event[u'hour_id'] = int(hour_id)
    event[u'minute_id'] = int(minute_id)


def lambda_handler(event, context):
    for record in event['Records']:
        try:
            # Kinesis data is base64 encoded so decode here
            payload = json.loads(base64.b64decode(record['kinesis']['data']))

            # technical filtering
            if (isValid(payload)):
                # technical fixing + probably proceed to a renaming
                fixed_payload = createExtendedField(payload)

                # business mapping
                deriveBuild(fixed_payload)
                deriveProduct(fixed_payload)
                deriveInstId(fixed_payload)
                deriveDate(fixed_payload)

                # deliver to Stream
                kinesis.put_record(StreamName='clean_events-stream', Data=exportJsonToString(fixed_payload),
                                   PartitionKey='1')

            else:
                firehose.put_record(DeliveryStreamName='dump-events-delivery',
                                    Record={'Data': exportJsonToString(payload)})
        except:
            pass

    return 'Successfully processed {} records.'.format(len(event['Records']))

