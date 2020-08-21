import getpass
import json
import logging
import time

import requests

from helpers import filePathInput

SLEEP_SECS = 15

AZURE_CFG = "AZURE_CFG"
AZURE_AL = "AZURE_AL_SEQ"
LACEWORK_SCHEMA_CHECK = "https://%laceworkAccount.lacework.net/api/v1/external/integrations/schema/"
LACEWORK_GET_INTEGRATIONS = "https://%laceworkAccount.lacework.net/api/v1/external/integrations/type/"
LACEWORK_INTEGRATION = "https://%laceworkAccount.lacework.net/api/v1/external/integrations"
LACEWORK_TOKEN = "https://%laceworkAccount.lacework.net/api/v1/access/tokens"
LACEWORK_RUN_REPORT = "https://%laceworkAccount.lacework.net/api/v1/external/runReport/integration/%integrationGuid"


def createLaceworkIntegration(appId, queueUrl, config):

    intgGuid = checkExistingIntegration(config.getLaceworkToken(), config.getLaceworkAccount(), config.getIntegrationName(), AZURE_CFG)
    if intgGuid is None:
        createLaceworkIntegrationCFG(appId, config)
    else:
        print "Skipping " + AZURE_CFG + " because integration already exists."
        logging.info("Running report for integration!")
        print "Running report for integration"
        runComplianceReport(config, intgGuid)

    if config.isActivityLogSetup:
        intgGuid = checkExistingIntegration(config.getLaceworkToken(), config.getLaceworkAccount(), config.getIntegrationName(), AZURE_AL)
        if intgGuid is None:
            createLaceworkIntegrationAL(appId, queueUrl, config)
        else:
            print "Skipping " + AZURE_AL + " because integration already exists."

def createLaceworkIntegrationCFG(appId, config):
    body = {
        "NAME": config.getIntegrationName(),
        "TYPE": AZURE_CFG,
        "ENABLED": 1,
        "DATA": {
            "CREDENTIALS": {
                "CLIENT_ID": appId,
                "CLIENT_SECRET": config.getUserClientSecret()
            },
            "TENANT_ID": config.getTenantId()
        }
    }
    url = LACEWORK_INTEGRATION.replace("%laceworkAccount", config.getLaceworkAccount())
    headers = {"Authorization": "Bearer " + config.getLaceworkToken(), "Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(body), headers=headers)
    responseJson = response.json()
    if 200 <= response.status_code <= 299:
        if responseJson['ok']:
            logging.info("The integration for compliance has been created in Lacework!")

            logging.info("Running report for integration in " + str(SLEEP_SECS) + " seconds!")
            print "Running report for integration"
            time.sleep(SLEEP_SECS)

            intgGuid = str(responseJson["data"][0]["INTG_GUID"])
            runComplianceReport(config, intgGuid)

        else:
            raise Exception("The Lacework integration for compliance could not be created: \n" + str(responseJson))
    else:
        raise Exception("The Lacework integration for compliance could not be created: \n" + str(responseJson))

def runComplianceReport(config, intgGuid):

    headers = {"Authorization": "Bearer " + config.getLaceworkToken(), "Content-Type": "application/json"}

    url = LACEWORK_RUN_REPORT.replace("%laceworkAccount", config.getLaceworkAccount())
    url = url.replace("%integrationGuid", intgGuid)
    response = requests.post(url, headers=headers)
    responseJson = response.json()
    if 200 <= response.status_code <= 299:
        logging.info("Compliance report is running!")
    else:
        print ("Report for created integration could not be run, please run it manually: \n" + str(responseJson))

def createLaceworkIntegrationAL(appId, queueUrl, config):
    body = {
        "NAME": config.getIntegrationName(),
        "TYPE": AZURE_AL,
        "ENABLED": 1,
        "DATA": {
            "CREDENTIALS": {
                "CLIENT_ID": appId,
                "CLIENT_SECRET": config.getUserClientSecret()
            },
            "TENANT_ID": config.getTenantId(),
            "QUEUE_URL": queueUrl
        }
    }

    url = LACEWORK_INTEGRATION.replace("%laceworkAccount", config.getLaceworkAccount())
    headers = {"Authorization": "Bearer " + config.getLaceworkToken(), "Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(body), headers=headers)
    responseJson = response.json()
    if 200 <= response.status_code <= 299:
        if responseJson['ok']:
            logging.info("The integration for Azure Activity Logs has been created in Lacework!")
        else:
            raise Exception("The Lacework integration for Azure Activity Logs could not be created: \n" + str(responseJson))
    else:
        raise Exception("The Lacework integration for Azure Activity Logs could not be created: \n" + str(responseJson))


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
    body = {"keyId": accessKey, "expiryTime": 3600}
    headers = {"X-LW-UAKS": secretKey, "Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(body), headers=headers)
    status = str(response.status_code)
    if 200 <= response.status_code <= 299:
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


def getSchema(token, laceworkAccount, integrationType):
    if laceworkAccount is None:
        while True:
            laceworkAccount = raw_input("Enter your Lacework application where you want to create the integration(s). Just specify the myLacework part of the Lacework application URL: myLacework.lacework.net. \n")
            if " " in laceworkAccount or laceworkAccount is "":
                print "Enter a valid Lacework application."
            else:
                break

    url = LACEWORK_SCHEMA_CHECK.replace("%laceworkAccount", laceworkAccount) + integrationType
    headers = {"Authorization": token}
    response = requests.get(url, headers=headers)
    status = str(response.status_code)

    if 200 <= response.status_code <= 299:
        responseJson = response.json()
        if responseJson['ok']:
            return laceworkAccount, "valid"
        else:
            raise Exception("Error occurred while verifying Lacework access token, maybe the token is expired. Generate a new token!")
    elif status == "401" or status == "403" or status == "400":
        return laceworkAccount, "tokenIssue"
    elif status == "404":
        return laceworkAccount, "serverIssue"
    else:
        raise Exception("Error occurred while verifying the Lacework access token!")


def getIntegrations(token, laceworkAccount, integrationType):
    url = LACEWORK_GET_INTEGRATIONS.replace("%laceworkAccount", laceworkAccount) + integrationType
    headers = {"Authorization": token}
    response = requests.get(url, headers=headers)
    if 200 <= response.status_code <= 299:
        responseJson = response.json()
        if responseJson['ok']:
            return responseJson
        else:
            raise Exception("Error occurred while checking for existing integrations!")
    else:
        raise Exception("Error occurred while checking for existing integrations!")


def checkExistingIntegration(token, laceworkAccount, integrationName, integrationType):
    logging.info("Checking if an integration called " + integrationName + " already exists in Lacework of type " + integrationType)

    responseJson = getIntegrations(token, laceworkAccount, integrationType)
    for entry in responseJson["data"]:
        if entry["NAME"] == integrationName:
            logging.info("Integration called " + integrationName + " already exist in Lacework of type " + integrationType)
            return entry["INTG_GUID"]

    logging.info("Integration called " + integrationName + " does not exist in Lacework of type " + integrationType)
    return None
