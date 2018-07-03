import boto3
import json
import base64
import shutil
import os
from os import path
from zipfile import ZipFile
import ast

role_policy_document = {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}

iam_client = boto3.client('iam')
env_variables = dict() # Environment Variables

roles_list = []
RoleList = iam_client.list_roles()
for i in RoleList["Roles"]:
    roles_list.append(i["RoleName"])

if "TufteLambdaExecution" not in roles_list:
    iam_client.create_role(
        RoleName='TufteLambdaExecution',
        AssumeRolePolicyDocument=json.dumps(role_policy_document),
    )

role = iam_client.get_role(RoleName='TufteLambdaExecution')
client = boto3.client('lambda')

functionsList = []
lambdaFunctions = client.list_functions()
for i in lambdaFunctions["Functions"]:
    functionsList.append(i["FunctionName"].encode("ascii", "ignore"))

# Check if the function already exists in the lambda list
# Create or Update the function accordingly

if "tuftelatex" in functionsList:
    print "Updating function tuftelatex "
    updateResponse = client.update_function_code(
        FunctionName = "tuftelatexlambda",
        S3Bucket = "tuftelatex",
        S3Key= "latexlambda.zip"
    )
    if updateResponse["ResponseMetadata"]["HTTPStatusCode"] == 200:
        print "Successfully updated the function"

else:
    print "Creating a New function as the tuftelatex function doesn't exist "
    createResponse = client.create_function(
        FunctionName="tuftelatexlambda",
        Runtime="python3.6",
        Role=role['Role']['Arn'],
        Handler="lambda_function.lambda_handler",
        Code={
            "S3Bucket" : "tuftelatex",
            "S3Key" : "latexlambda.zip"
        },
        Timeout=300,
        Environment=dict(Variables=env_variables),
        MemorySize=1792
    )
    if createResponse["ResponseMetadata"]["HTTPStatusCode"] == 200:
        print "Successfully updated the function"
#
# Create Duplicate
if path.exists("sample.tex"):
# get the path to the file in the current directory
    src = path.realpath("sample.tex");# rename the original file
    os.rename("sample.tex", "document.tex")

# Convert the Tex Input to Zip
with ZipFile('texZip.zip', 'w') as myzip:
	myzip.write('document.tex')


# Encode the Zip File
with open('texZip.zip', 'rb') as f:
    bytes = f.read()
    encoded = base64.b64encode(bytes)


# Generate the payload
data = { "input" : encoded }
json_data = json.dumps(data)

# Invoke the Lambda Function
client = boto3.client('lambda')
print "Connected to client"
response = client.invoke(FunctionName='latex', Payload=json_data)
output = ast.literal_eval(response["Payload"].read())["output"]
with open("test_output_lambda.pdf", "w") as res:
	res.write(base64.b64decode(output))
