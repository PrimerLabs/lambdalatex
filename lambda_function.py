import os
import io
import shutil
import subprocess
import base64
import zipfile
import boto3
from urllib.parse import unquote_plus

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    lambda_client = boto3.client('lambda')

    # Get the Bucket where the event occured
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']['object']['key'])
    filename, file_extension = os.path.splitext(key)
    target_key = filename + '.pdf'
    print("Waiting for the file persist in the source_bucket")
    waiter = s3.get_waiter('object_exists')
    waiter.wait(Bucket=source_bucket, Key=key)

    # Get the zip File
    responseObject = s3.get_object(Bucket=source_bucket, Key=key)
    encodedZipFile = responseObject["Body"].read()

    z = zipfile.ZipFile(io.BytesIO(encodedZipFile))

    # Extract input     ZIP file to /tmp/latex...
    shutil.rmtree("/tmp/latex", ignore_errors=True)
    os.mkdir("/tmp/latex")
    z.extractall(path="/tmp/latex")

    os.environ['PATH'] += ":/var/task/texlive/2017/bin/x86_64-linux/"
    os.environ['HOME'] = "/tmp/latex/"
    os.environ['PERL5LIB'] = "/var/task/texlive/2017/tlpkg/TeXLive/"

    os.chdir("/tmp/latex/")

    # Run pdflatex...
    r = subprocess.run(["latexmk",
                        "-verbose",
                        "-interaction=batchmode",
                        "-pdf",
                        "-output-directory=/tmp/latex",
                        "document.tex"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    print(r.stdout.decode('utf_8'))

    # Read "document.pdf"...
    with open("document.pdf", "rb") as f:
        s3.upload_fileobj(f, source_bucket, target_key )

    with open("document.pdf", "rb") as f:
        pdf = f.read()

    # Save the pdf in the Source bucket


    # Return base64 encoded pdf and stdout log from pdflaxex...
    return {
        "output": base64.b64encode(pdf).decode('ascii'),
        "stdout": r.stdout.decode('utf_8')
    }
