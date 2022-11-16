import json
import boto3
import os
import re
import subprocess
import shutil


def unzip_pglog(lfile):
    p = subprocess.Popen(['/usr/bin/gunzip', lfile], universal_newlines=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = p.communicate()
    if p.returncode != 0:
        raise Exception(errors)


def decode_escape_s3key(path):
    escape_map = {"+": " ",
                  "%21": "!",
                  "%24": "$",
                  "%26": "&",
                  "%27": "'",
                  "%28": "(",
                  "%29": ")",
                  "%2B": "+",
                  "%40": "@",
                  "%3A": ":",
                  "%3B": ";",
                  "%2C": ",",
                  "%3D": "=",
                  "%3F": "?"
                  }
    escape_map = dict((re.escape(k), v) for k, v in escape_map.items())
    pattern = re.compile("|".join(escape_map.keys()))
    return pattern.sub(lambda m: escape_map[re.escape(m.group(0))], path)


def downloadfroms3(s3bucket, key, workdir):
    s3 = boto3.client('s3')
    dfile = '{}/logs/{}'.format(workdir, key.split('/')[-1])
    inputfile = '{}/logs/{}'.format(workdir, key.split('/')[-1]).replace('.gz', '')
    for fl in [dfile, inputfile]:
        if os.path.exists(fl) and os.path.isfile(fl):
            os.remove(fl)
    s3.download_file(s3bucket, key, dfile)
    unzip_pglog(dfile)
    ufile = re.sub(r".gz$", "", dfile)
    os.rename(ufile, dfile)
    try:
        unzip_pglog(dfile)
    except Exception as e:
        print ("Ignoring exception during gunzip {}".format(e))
    return {'statusCode': 200, 'body': 'stdout=Successfully downloaded and uncompressed s3 object'}


def delete_s3_processed_objects(event):
    s3 = boto3.client('s3')
    for data in event.get('Records', []):
        data = data.get('body')
        if isinstance(data, str):
            data = json.loads(data)
        x = data['Records'][0] or {}
        s3bucket = x.get('s3', {}).get('bucket', {}).get('name')
        if s3bucket:
            key = x.get('s3', {}).get('object', {}).get('key')
            if key:
                s3.delete_object(Bucket=s3bucket, Key=key)


def runpgbadger(pgbadgerscript, outputfile, outputdir, workdir, event):
    cmd = "{0} -v -f rds --no-process-info --pid-dir {1}/tmp --anonymize " \
            "--last-parsed {2}/last-parsed-custom " \
            "-X -I -H {2}/html -O {2}/binary {1}/logs/*".format(pgbadgerscript, workdir, outputdir)
    print(cmd)
    pgbp = subprocess.Popen(cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, errors = pgbp.communicate()
    print(output)
    print(errors)
    if os.path.exists(workdir):
        shutil.rmtree(workdir, ignore_errors=True)
    if pgbp.returncode != 0:
        raise Exception(errors)
    else:
        # Remove processed files from s3
        delete_s3_processed_objects(event)
        # Remove last-parsed file
        if os.path.exists("{0}/last-parsed-custom".format(outputdir)):
            os.remove("{0}/last-parsed-custom".format(outputdir))
        return {'statusCode': 200, 'body': 'stdout={}, stderr={}'.format(output, errors)}


def lambdaHandler(event, context):
    inputfile = os.environ.get('BADGER_INPUT_FILE')  # debug parameter
    outputfile = os.environ.get('BADGER_OUTPUT_FILE')
    outputdir = os.environ.get('BADGER_OUTPUT_DIR')
    pgbadgerscript = "/opt/badger/pgbadger"  # location of executable in the container
    workdir = "/tmp/pgbadger-work"  # working files dir on lambda
    if os.path.exists(workdir):
        shutil.rmtree(workdir, ignore_errors=True)
    os.mkdir(workdir)
    for x in ["tmp", "logs"]:
        os.mkdir("{}/{}".format(workdir, x))
    for x in ["html", "binary", "report", "log"]:
        if not os.path.exists("{}/{}".format(outputdir, x)):
            os.mkdir("{}/{}".format(outputdir, x))
    if not inputfile:
        for data in event.get('Records', []):
            data = data.get('body')
            if isinstance(data, str):
                data = json.loads(data)
            x = data.get('Records', []) and data['Records'][0] or {}
            if not x:
                print('Invalid record, Records attribute not found in event data - {}'.format(data))
                return
            s3bucket = x.get('s3', {}).get('bucket', {}).get('name')
            if not s3bucket:
                raise Exception('Failed to get Bucket Name from event {}'.format(event))
            key = x.get('s3', {}).get('object', {}).get('key')
            if not key:
                raise Exception('Failed to get Key from event {}'.format(event))
            key = decode_escape_s3key(key)
            r = downloadfroms3(s3bucket, key, workdir)
            if r.get('statusCode', 0) != 200:
                raise Exception('Unable to download file from s3 {}'.format(r))
    return runpgbadger(pgbadgerscript, outputfile, outputdir, workdir, event)
