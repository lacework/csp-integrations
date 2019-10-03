from helpers import yesNoInput
from helpers import filePathInput
from id_reader import readId
from id_reader import getProjectsFromGcp
from util.util import Util
import re
import yaml

def getProjectId(util):
    projectSource = yesNoInput("Do you want to choose from a list of found projects (Y/N): \n")
    if projectSource == "y" or projectSource == "yes":
        projectList = getProjectsFromGcp(util, "Do you want to select one of the following projects?:\n")
        while True:
            projectNumber = raw_input("Enter the project number to select the project:\n")
            if projectNumber != "" and projectNumber != " " and int(projectNumber) <= len(projectList) and int(projectNumber) >= 1:
                projectId = projectList[int(projectNumber) - 1]
                return projectId
    elif projectSource == "n" or projectSource == "no":
        while True:
            projectId = raw_input("Enter the project ID for the setup project for the new integration(s):\n")
            if " " in projectId or projectId == "":
                print "Enter a valid project ID."
            else:
                return projectId

def getConfigInput():
    util = Util()
    print "No configuration file specified."
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
    userInput = yesNoInput("Enter the configuration information interactively using a series of prompts? (Y/N):\n")
    if userInput == "n" or userInput == "no":
        return filePathInput("Enter the full directory path to the config YAML file, including the file name.\n")
    elif userInput == "y" or userInput == "yes":
        complianceId = ""
        exports = {}
        existingBucketName = ""
        enableApi = yesNoInput("Do you want this script to enable the requried APIs in GCP? (Y/N): \n")
        setIamPolicy = yesNoInput("Do you want this script to modify the IAM policy and create roles in GCP? (Y/N):\n")
        while True:
            setupPrefix = raw_input("Enter a setup string that will be prefixed to each resource name created by this script. (Do not specify a space or special characters except '-'):\n")
            if ' ' in setupPrefix:
                print "No space characters are allowed in setup prefix!"
            elif regex.search(setupPrefix):
                print "Special characters are not allowed in setup prefix!"
            elif setupPrefix == "":
                print "Enter a valid setup prefix."
            else:
                break

        setupProjectId = getProjectId(util)

        while True:
            complianceAndAudit = raw_input("What types of integrations do you want to create? \n1. Compliance Only\n2. Compliance and Audit Trail\nPlease enter 1 or 2:\n")
            if complianceAndAudit == '1' or complianceAndAudit =='2':
                break
            else:
                print "Enter 1 or 2."
        while True:
            complianceType = raw_input("For compliance, do you want to integrate at the project or organization level?\nProject/Organization?\n")
            complianceType = complianceType.upper()
            if complianceType == "PROJECT":
                complianceId = setupProjectId
                print "The specified setup project will also be used for integrating for compliance. To select a different project, Control-C out of this script and specify a different project for both."
                break
            elif complianceType == "ORGANIZATION":
                while True:
                    complianceId = raw_input("Enter the ID for the organization that you want to integrate with for compliance: \n")
                    if " " in complianceId or complianceId == "":
                        print "Enter a valid organization ID."
                    else:
                        break
                break
            else:
                print "Enter valid input."
        if complianceAndAudit == "2":
            existingBucket = yesNoInput("Did you run this script before and already have a bucket from that integration which you want to use for a new Audit Trail integration? (Y/N): \n")
            if existingBucket == "y" or existingBucket == "yes":
                while True:
                    existingBucketName = raw_input("Enter the existing bucket's name: \n")
                    if " " in existingBucketName or existingBucketName == "":
                        print "Enter a valid bucket name."
                    else:
                        break
            elif existingBucket == "n" or existingBucket == "no":
                print "A new bucket will be created during integration!"

            while True:
                auditType = raw_input("For Audit logging, do you want to integrate at the project or organization level?\nProject/Organization\n")
                auditType = auditType.upper()
                if auditType == "PROJECT":
                    if complianceType == "PROJECT":
                        auditIds = complianceId
                    else:
                        auditIds = getProjectId(util)
                        # TODO: UNCOMMENT WHEN MULTIPLE PROJECTS CAN BE DONE IN SAME DEPLOYMENT (IAMMEMBERBINDING NEEDED FOR BUCKET)
                        # while True:
                        #     listOrFile = raw_input("Enter project IDs or read project IDs from somewhere else? (enter/read)\n")
                        #     listOrFile = listOrFile.lower()
                        #     if listOrFile == "enter":
                        #         while True:
                        #             auditIds = raw_input("Enter project id (project1,project2,...): \n")
                        #             if " " in auditIds:
                        #                 "Make sure there are no space characters!"
                        #             elif auditIds == "":
                        #                 "Enter valid project IDs."
                        #             else:
                        #                 break
                        #         auditIds = auditIds.split(',')
                        #         break
                        #     elif listOrFile == "read":
                        #         auditIds = readId(auditType)
                        #         break
                        #     else:
                        #         print "Enter valid input."
                elif auditType == "ORGANIZATION":
                    if complianceType == "ORGANIZATION":
                        auditIds = complianceId
                    else:
                        while True:
                            orgId = raw_input("Enter the organization ID you want to integrate with for audit logging: \n")
                            if " " in orgId or orgId == "":
                                print "Enter a valid organization ID. "
                            else:
                                auditIds = orgId
                                break
                # TODO: UNCOMMENT WHEN FOLDER SUPPORT IS ADDED IN PRODUCT
                # elif auditType == "FOLDER":
                #     while True:
                #         listOrFile = raw_input("List folder ids or read folder ids from somewhere else? (list/read)\n")
                #         listOrFile = listOrFile.lower()
                #         if listOrFile == "list":
                #             while True:
                #                 auditIds = raw_input("Please enter comma seperated folder ids WITHOUT SPACE IN BETWEEN (folder1,folder2,...): \n")
                #                 if " " in auditIds:
                #                     "Please make sure there is no space!"
                #                 elif auditIds == "":
                #                     "Please enter valid input"
                #                 else:
                #                     break
                #             auditIds = auditIds.split(',')
                #             break
                #         elif listOrFile == "read":
                #             auditIds = readId(auditType)
                #             break
                else:
                    print "Enter valid input."
                    continue

                exports = {"idType": auditType, "id": auditIds}
                break

        configInput = {
            "setupPrefix": setupPrefix,
            "auditLogSetupEnabled": complianceAndAudit=="2",
            "setupProjectId": setupProjectId,
            "complianceSetup": {
                "idType": complianceType,
                "id": complianceId,
                "enableApi" : enableApi == "y" or enableApi == "yes",
                "setIamPolicy" : setIamPolicy == "y" or setIamPolicy == "yes"
            }
        }
        if complianceAndAudit == "2":
            configInput["auditLogSetup"] = {
                "exports": exports
            }
            if existingBucketName is not "":
                configInput["auditLogSetup"]["existingBucketName"] = existingBucketName

        with open("configCustom.yml", "w") as outputFile:
            yaml.dump(configInput, outputFile)

        file = open("configCustom.yml", "r")
        print file.read()

        print "Review the configation settings. "
        configAccept = yesNoInput("Accept Settings? (Y/N)\n")
        if configAccept == "n" or configAccept == "no":
            raise Exception("Configuration settings were rejected. No configuration YAML file is created.")
        elif configAccept == "y" or configAccept == "yes":
            return "configCustom.yml"

    else:
        print "Enter valid input."
