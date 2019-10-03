from helpers import filePathInput
from config.config import BUCKET_ROLES
from config.config import BUCKET_SINK_ROLES
import yaml
import json
import requests
import base64
import logging
import time
import getpass

SLEEP_SECS=15

LACEWORK_SCHEMA_CHECK = "https://%laceworkAccount.lacework.net/api/v1/external/integrations/schema/GCP_CFG"
LACEWORK_GET_INTEGRATIONS = "https://%laceworkAccount.lacework.net/api/v1/external/integrations/type/GCP_CFG"
LACEWORK_INTEGRATION = "https://%laceworkAccount.lacework.net/api/v1/external/integrations"
LACEWORK_TOKEN = "https://%laceworkAccount.lacework.net/api/v1/access/tokens"
LACEWORK_RUN_REPORT = "https://%laceworkAccount.lacework.net/api/v1/external/runReport/integration/%integrationGuid"

def createLaceworkIntegration(deploymentOutput, config, util):
    deploymentOutput = yaml.safe_load(deploymentOutput)['outputs']
    deploymentOutputJson = {}
    deploymentOutputJson["idTypeCompliance"] = config.getComplianceSetupType()
    deploymentOutputJson["idCompliance"] = config.getComplianceSetupId()
    if config.isAuditLogSetup():
        deploymentOutputJson["idTypeAudit"] = config.getAuditSetupType()
        deploymentOutputJson["idAudit"] = config.getAuditSetupId()
    deploymentOutputJson["privateKey"] = None
    deploymentOutputJson["privateKeyId"] = None
    deploymentOutputJson["clientId"] = None
    deploymentOutputJson["clientEmail"] = None
    sinkEmail = ""
    privateKeyData = ""
    if config.isAuditLogSetup():
        deploymentOutputJson["subscription"] = None
    for output in deploymentOutput:
        if output['name'] == "privateKey":
            privateKeyData = output['finalValue']

        if config.isAuditLogSetup():
            if output['name'] == "subscription":
                deploymentOutputJson["subscription"] = str(output['finalValue'])

        if config.doesBucketExist():
            if output['name'] == "sinkEmail":
                sinkEmail = str(output['finalValue']).replace("serviceAccount:", "")

    if privateKeyData == "":
        raise Exception("Deployment output not found!")

    outputDataJson = json.loads(base64.b64decode(privateKeyData))
    privateKey = outputDataJson['private_key'].replace("\n", "")
    privateKey = privateKey.replace("-----BEGIN PRIVATE KEY-----", "-----BEGIN PRIVATE KEY-----\n")
    privateKey = privateKey.replace("-----END PRIVATE KEY-----", "\n-----END PRIVATE KEY-----")
    deploymentOutputJson["privateKey"] = str(privateKey)
    deploymentOutputJson["privateKeyId"] = str(outputDataJson['private_key_id'])
    deploymentOutputJson["clientId"] = str(outputDataJson['client_id'])
    deploymentOutputJson["clientEmail"] = str(outputDataJson['client_email'])

    if config.doesBucketExist():
        util.setBucketIAMPolicy(config.getExistingBucketName(), deploymentOutputJson["clientEmail"], BUCKET_ROLES)
        util.setBucketIAMPolicy(config.getExistingBucketName(), sinkEmail, BUCKET_SINK_ROLES)

    print "Compliance Integration Level\n" + deploymentOutputJson["idTypeCompliance"]
    print "Compliance ID\n" + deploymentOutputJson["idCompliance"]
    print "Client Email \n" + deploymentOutputJson["clientEmail"]
    print "Client Id \n" + deploymentOutputJson["clientId"]
    print "Private Key Id \n" + deploymentOutputJson["privateKeyId"]
    print "Private Key \n" + deploymentOutputJson["privateKey"]

    if config.isAuditLogSetup():
        print "Audit Logging Integration Level\n" + deploymentOutputJson["idTypeAudit"]
        print "Audit Logging ID\n" + deploymentOutputJson["idAudit"]
        if config.doesBucketExist():
            print "Subscription Name: \nSame as when script was run for existing bucket \n"
        else:
            print "Subscription Name \n" + deploymentOutputJson["subscription"]

    if (config.getToIntegrate()):
        createIntegration(deploymentOutputJson, config)

    with open("deploymentOutput.txt", "w") as outputFile:
        json.dump(deploymentOutputJson, outputFile)

def createIntegration(deploymentJson, config):
    body = {
        "NAME": config.getIntegrationName(),
        "TYPE": "GCP_CFG",
        "ENABLED": 1,
        "DATA": {
            "CREDENTIALS": {
                "CLIENT_ID": deploymentJson["clientId"],
                "PRIVATE_KEY_ID": deploymentJson["privateKeyId"],
                "CLIENT_EMAIL": deploymentJson["clientEmail"],
                "PRIVATE_KEY": deploymentJson["privateKey"]
            },
            "ID_TYPE": deploymentJson["idTypeCompliance"],
            "ID": deploymentJson["idCompliance"]
        }
    }
    url = LACEWORK_INTEGRATION.replace("%laceworkAccount", config.getLaceworkAccount())
    headers = {"Authorization": config.getLaceworkToken(), "Content-Type":"application/json"}
    response = requests.post(url, data=json.dumps(body), headers=headers)
    responseJson = response.json()
    if response.status_code >= 200 and response.status_code <= 299:
        if responseJson['ok']:
            logging.info("The integration for compliance has been created in Lacework!")
            print "The integration for compliance has been created in Lacework!"
            # TODO: Uncomment when lacework api is tested
            logging.info("Running report for integration in " + str(SLEEP_SECS) + " seconds!")
            print "Running report for integration in " + str(SLEEP_SECS) + " seconds!"
            time.sleep(SLEEP_SECS)
            intgGuid = str(responseJson["data"][0]["INTG_GUID"])
            url = LACEWORK_RUN_REPORT.replace("%laceworkAccount", config.getLaceworkAccount())
            url = url.replace("%integrationGuid", intgGuid)
            response = requests.post(url, headers=headers)
            responseJson = response.json()
            if response.status_code >= 200 and response.status_code <= 299:
                logging.info("Compliance report is running!")
                print "Compliance report is running!"
            else:
                print ("Report for created integration could not be run, please run it manually: \n" + str(responseJson))
        else:
            raise Exception("The Lacework integration for compliance could not be created: \n" + str(responseJson))
    else:
        raise Exception("The Lacework integration for compliance could not be created: \n" + str(responseJson))

    if (config.isAuditLogSetup and not config.doesBucketExist()):
        body = {
            "NAME": config.getIntegrationName(),
            "TYPE": "GCP_AT_SES",
            "ENABLED": 1,
            "DATA": {
                "CREDENTIALS": {
                    "CLIENT_ID": deploymentJson["clientId"],
                    "PRIVATE_KEY_ID": deploymentJson["privateKeyId"],
                    "CLIENT_EMAIL": deploymentJson["clientEmail"],
                    "PRIVATE_KEY": deploymentJson["privateKey"]
                },
                "ID_TYPE": deploymentJson["idTypeAudit"],
                "ID": deploymentJson["idAudit"],
                "SUBSCRIPTION_NAME": deploymentJson["subscription"]
            }
        }
        url = LACEWORK_INTEGRATION.replace("%laceworkAccount", config.getLaceworkAccount())
        headers = {"Authorization": config.getLaceworkToken(), "Content-Type":"application/json"}
        response = requests.post(url, data=json.dumps(body), headers=headers)
        responseJson = response.json()
        if response.status_code >= 200 and response.status_code <= 299:
            if responseJson['ok']:
                logging.info("The integration for audit logging has been created in Lacework!")
                print "The integration for audit logging has been created in Lacework!"
            else:
                raise Exception("The Lacework integration for audit could not be created: \n" + str(responseJson))
        else:
            raise Exception("The Lacework integration for audit could not be created: \n" + str(responseJson))


def getToken():
    filePath = filePathInput("Enter the full directory path (including file name) of the Lacework access key file: \n")
    accessKeyData = open(filePath, "r").read()
    accessKey = json.loads(accessKeyData)['keyId']
    while True:
        secretKey = getpass.getpass("Enter the secret key for your Lacework application: \n")
        if " " in secretKey or secretKey is "":
            print "Enter a valid secret key."
        else:
            break

    while True:
        laceworkAccount = raw_input("Enter your Lacework application where you want to create the integration(s). Just specify the myLacework part of the Lacework application URL: myLacework.lacework.net.\n")
        if " " in laceworkAccount or laceworkAccount is "":
            print "Enter a Lacework application:"
        else:
            break

    url = LACEWORK_TOKEN.replace("%laceworkAccount", laceworkAccount)
    body = {"keyId": accessKey, "expiryTime":3600}
    headers = {"X-LW-UAKS": secretKey, "Content-Type":"application/json"}
    response = requests.post(url, data=json.dumps(body), headers=headers)
    status = str(response.status_code)
    if response.status_code >= 200 and response.status_code <= 299:
        responseJson = response.json()
        if responseJson['ok']:
            return responseJson, laceworkAccount, "valid"
        else:
            raise Exception("Error occured while getting Lacework access token: \n" + str(responseJson))
    elif status == "401" or status == "403" or status == "400":
        return None, laceworkAccount, "authIssue"
    elif status == "404":
        return None, laceworkAccount, "serverIssue"
    else:
        raise Exception("Error occured while getting Lacework access token!")


def getSchema(token, laceworkAccount):
    if laceworkAccount is None:
        while True:
            laceworkAccount = raw_input("Enter your Lacework application where you want to create the integration(s). Just specify the myLacework part of the Lacework application URL: myLacework.lacework.net. \n")
            if " " in laceworkAccount or laceworkAccount is "":
                print "Enter a valid Lacework application."
            else:
                break

    url = LACEWORK_SCHEMA_CHECK.replace("%laceworkAccount", laceworkAccount)
    headers = {"Authorization": token}
    response = requests.get(url, headers=headers)
    status = str(response.status_code)
    if response.status_code >= 200 and response.status_code <= 299:
        responseJson = response.json()
        if responseJson['ok']:
            return laceworkAccount, "valid"
        else:
            raise Exception("Error occured while verifying Lacework access token, maybe the token is expired. Generate a new token!")
    elif status == "401" or status == "403" or status == "400":
        return laceworkAccount, "tokenIssue"
    elif status == "404":
        return laceworkAccount, "serverIssue"
    else:
        raise Exception("Error occured while verifying the Lacework access token!")

def getIntegrations(token, laceworkAccount):
    url = LACEWORK_GET_INTEGRATIONS.replace("%laceworkAccount", laceworkAccount)
    headers = {"Authorization": token}
    response = requests.get(url, headers=headers)
    if response.status_code >= 200 and response.status_code <= 299:
        responseJson = response.json()
        if responseJson['ok']:
            return responseJson
        else:
            raise Exception("Error occured while checking for existing integrations!")
    else:
        raise Exception("Error occured while checking for existing integrations!")
