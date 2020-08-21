from helpers import yesNoInput
from helpers import filePathInput
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD
from interactive import InteractiveClient
import re
import yaml

def getConfigInput():
    print "No configuration file specified."
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
    userInput = yesNoInput("Enter the configuration information interactively using a series of prompts? (Y/N):\n")
    if userInput == "n" or userInput == "no":
        return filePathInput("Enter the full directory path to the config YAML file, including the file name.\n"), None
    elif userInput == "y" or userInput == "yes":
        auditIds = []
        existingBucketName = ""
        existingResourceGroupName = ""
        allAuditSubscriptions = False
        while True:
            setupPrefix = raw_input("Enter a lowercase 1-3 character setup string that will be prefixed to each resource name created by this script. (Do not specify a space or special characters except '-'):\n")
            setupPrefix = setupPrefix.lower()
            if ' ' in setupPrefix:
                print "No space characters are allowed in setup prefix!"
            elif regex.search(setupPrefix):
                print "Special characters are not allowed in setup prefix!"
            elif setupPrefix == "":
                print "Enter a valid setup prefix."
            elif len(setupPrefix) > 3:
                print "Length of setup prefix cannot exceed 3!"
            else:
                break

        while True:
            authType = raw_input("Enter the authentication method based on where the script is run (CLI/PORTAL/USER_PASS):\n")
            authType = authType.upper()
            if authType == "CLI" or authType == "PORTAL" or authType == "USER_PASS":
                interactive = InteractiveClient(authType, AZURE_PUBLIC_CLOUD)
                interactive.getUserNamePasswordCredentials()
                break
            else:
                print "Enter a valid authentication type."

        tenantId = interactive.selectTenants()

        while True:
            complianceAndAudit = raw_input("What types of integrations do you want to create? \n1. Compliance Only\n2. Compliance and Activity Log\nPlease enter 1 or 2:\n")
            if complianceAndAudit == '1' or complianceAndAudit =='2':
                break
            else:
                print "Enter 1 or 2."

        complianceId = interactive.selectSubscriptions()
        if complianceAndAudit == "2":
            if len(complianceId) == 0:
                print ("Need to select at least one subscription for Activity Log!")
                raise Exception("Need to select at least one subscription for Activity Log!")

            auditIds = complianceId

        configInput = {
            "setupPrefix": setupPrefix,
            "activityLogSetupEnabled": complianceAndAudit=="2",
            "authType": authType,
            "tenantId": tenantId,
            "complianceSetup": {
                "subscriptionId": complianceId
            }
        }
        if complianceAndAudit == "2":
            configInput["activityLogSetup"] = {
                "subscriptionId": auditIds
            }
            if existingBucketName is not "":
                configInput["activityLogSetup"]["existingBucketName"] = existingBucketName
                configInput["activityLogSetup"]["existingResourceGroupName"] = existingResourceGroupName

        with open("configCustom.yml", "w") as outputFile:
            yaml.dump(configInput, outputFile)

        file = open("configCustom.yml", "r")
        print file.read()

        print "Review the configuration settings. "
        configAccept = yesNoInput("Accept Settings? (Y/N)\n")
        if configAccept == "n" or configAccept == "no":
            raise Exception("Configuration settings were rejected. No configuration YAML file is created.")
        elif configAccept == "y" or configAccept == "yes":
            return "configCustom.yml", interactive

    else:
        print "Enter valid input."
