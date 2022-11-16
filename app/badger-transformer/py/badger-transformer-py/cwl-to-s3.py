
# Set Lambda Timeout to 3 min
# Memory 128MB

import base64
import json
import gzip


def transformLogEvent(log_event):
    return log_event['message']


def lambda_handler(event, context):
    output = []
    for record in event.get('records', []):
        compressed_payload = base64.b64decode(record['data'])
        uncompressed_payload = gzip.decompress(compressed_payload)
        payload = json.loads(uncompressed_payload)
        joineddata = '\n'.join([transformLogEvent(e) for e in payload['logEvents']])
        joineddata = joineddata + '\n'
        compressed_payload = gzip.compress(bytes(joineddata, 'utf-8'))
        encodeddata = base64.b64encode(compressed_payload)
        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': encodeddata
        }
        output.append(output_record)
    return {"records": output}
