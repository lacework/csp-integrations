from config.config import API_LIST
from config.config import ROLES
from config.config import ORG_ROLES
from config.config import AUDIT_ROLES
from config.config_parser import ConfigParser
from config.config import Config
from config.config import PROJECT_PERMISSIONS
from config.config import ORG_PERMISSIONS
from config.config import AUDIT_PERMISSIONS
from config.config import BUCKET_PERMISSIONS
from lacework_api import getSchema
from lacework_api import getToken
from lacework_api import getIntegrations
from lacework_api import createLaceworkIntegration
from helpers import yesNoInput
import logging
import sys
import getpass

def runIndependentChecks(configFile, util):
    logging.info("Running all preliminary checks for the script!")
    print "Running all preliminary checks for the script!"
    config = checkConfigFile(configFile)
    setupProjectId = config.getSetupProjectId()
    deploymentName = config.getSetupPrefix() + "-" + setupProjectId + "-lacework-deployment"
    config.setDeploymentName(deploymentName)
    toEnable = checkApiEnablement(setupProjectId, util)
    if config.doesBucketExist():
        config.setBucketParent(checkExistingBucket(config.getExistingBucketName(), util))
    return config, toEnable

def runDependentChecks(config, util, rollback=False):
    toIntegrate = checkAssumptions(config, rollback, util)
    config.setToIntegrate(toIntegrate)
    setupProjectId = config.getSetupProjectId()
    deploymentName = config.getDeploymentName()
    if (toIntegrate):
        token, laceworkAccount = checkLaceworkToken()
        config.setLaceworkToken(token)
        config.setLaceworkAccount(laceworkAccount)
        integration = config.getSetupPrefix() + "-" + setupProjectId + "-" + config.getComplianceSetupType().lower() + "-gcp-integration"
        config.setIntegrationName(integration)
        checkExistingIntegration(token, laceworkAccount, integration)
    deploymentExists = checkDeployment(deploymentName, setupProjectId, config, util)
    if (deploymentExists):
        return deploymentExists, None, None, None, None
    projectDetails = checkProjectdetails(setupProjectId, util)
    if (config.doesBucketExist()):
        checkServiceAccount(config.getBucketParent(), util)
    else:
        checkServiceAccount(setupProjectId, util)
    config.setSetupProjectNumber(projectDetails["projectNumber"])
    rolesProject, rolesOrg, rolesAudit = checkAllIamPolicies(config, util)

    return deploymentExists, projectDetails, rolesProject, rolesOrg, rolesAudit

def checkExistingIntegration(token, laceworkAccount, integration):
    logging.info("Checking if an integration called " + integration + " already exists in Lacework.")
    print "Checking if an integration called " + integration + " already exists in Lacework."
    responseJson = getIntegrations(token, laceworkAccount)
    for entry in responseJson['data']:
        if entry['NAME'] == integration:
            logging.info("Check: An integration already exists with following settings: \n" + str(entry))
            print "Check: An integration already exists with following settings: \n" + str(entry)
            sys.exit()

    logging.info("Check: An integration called " + integration + " does not exist in Lacework. " )
    print "Check: An integration called " + integration + " does not exist in Lacework. "


def checkLaceworkToken():
    laceworkAccount = None
    while True:
        yesOrNo = yesNoInput("Do you have a valid Lacework API token? (Y/N): \n")
        if yesOrNo == "yes" or yesOrNo == "y":
            while True:
                token = getpass.getpass("Enter the Lacework API token: \n")
                if " " in token or token == "":
                    print "Enter a valid API token."
                else:
                    break
        else:
            logging.info("Getting the Lacework API token for this Lacework application.")
            print "Getting the Lacework API token for this Lacework application."
            responseJson, laceworkAccount, result = getToken()
            if result == "valid":
                token = responseJson['data'][0]['token']
            elif result == "authIssue":
                logging.info("Authorization failed. Verify that the specified access key, secret key, and Lacework application (" + laceworkAccount + ") are correct. ")
                print "Authorization failed. Verify that the specified access key, secret key, and Lacework application (" + laceworkAccount + ") are correct. "
                continue
            elif result == "serverIssue":
                logging.info("Unable to connect to the Lacework application or incorrect Lacework application specified (" + laceworkAccount + "). Just specify the myLacework part of the Lacework application URL: myLacework.lacework.net.")
                print "Unable to connect to the Lacework application or incorrect Lacework application specified (" + laceworkAccount + "). Just specify the myLacework part of the Lacework application URL: myLacework.lacework.net."
                continue

        logging.info("Checking the connection to the Lacework application and if the API token is valid.")
        print "Checking the connection to the Lacework application and if the API token is valid."
        laceworkAccount, result = getSchema(token, laceworkAccount)
        if result == "valid":
            logging.info("Check: Passed! Can connect to Lacework and the API Token is valid.")
            print "Check: Passed! Can connect to Lacework and the API Token is valid."
            return token, laceworkAccount
        elif result == "tokenIssue":
            logging.info("Check: Failed! Specified API Token is invalid. Follow the prompts to get new API token or verify that the specifed Lacework application name " + laceworkAccount + " is correct.")
            print "Check: Failed! Specified API token is invalid. Follow the prompts to get new API token or verify that the specifed Lacework application name " + laceworkAccount + " is correct."
        elif result == "serverIssue":
            logging.info("Check: Failed! Cannot connect to Lacework or specified Lacework application name (" + laceworkAccount + ") is incorrect. ")
            print "Check: Failed! Cannot connect to Lacework or specified Lacework application name (" + laceworkAccount + ") is incorrect. "

def checkAssumptions(config, rollback, util):
    logging.info("Checking if the current user has required permissions needed to run the script.")
    print "Checking if the current user has required permissions needed to run the script."
    neededPermissions = util.testProjectPermissions(config.getSetupProjectId(), PROJECT_PERMISSIONS)
    if len(neededPermissions) is not 0:
        logging.info("The GCP user needs following permissions in the project " + config.getSetupProjectId() + " to run the script: \n" + str(neededPermissions))
        print "The GCP user needs following permissions in the project " + config.getSetupProjectId() + " to run the script: \n" + str(neededPermissions)
        yesOrNo = yesNoInput("Try anyway? (Y/N): ")
        if yesOrNo == "no" or yesOrNo == "n":
            raise Exception("The GCP user needs the required permissions for project before running script!")
        logging.warn("This script run may have permission issues!")
        print "This script run may have permission issues!"
    else:
        logging.info("Check: Passed, all required permissions were granted!")
        print "Check: Passed, all required permissions were granted!"
    if config.getComplianceSetupType() == "ORGANIZATION":
        logging.info("Organization-level integration detected! Checking if the GCP user has required permissions in the organization, where the id is " + config.getComplianceSetupId() + ".")
        print "Organization-level integration detected! Checking if the GCP user has required permissions in the organization, where the id is " + config.getComplianceSetupId() + "."
        neededPermissions = util.testOrgPermissions(config.getComplianceSetupId(), ORG_PERMISSIONS)
        if len(neededPermissions) is not 0:
            logging.info("The GCP user needs following permissions in the " + config.getComplianceSetupId() + " organization to run the script: \n" + str(neededPermissions))
            print "The GCP user needs following permissions in the " + config.getComplianceSetupId() + " organization to run the script: \n" + str(neededPermissions)
            yesOrNo = yesNoInput("Try anyway? (Y/N): ")
            if yesOrNo == "no" or yesOrNo == "n":
                raise Exception("The GCP user needs the required permissions in the organization before running script!")
            logging.warn("This script run may have permission issues!")
            print "This script run may have permission issues!"
        else:
            logging.info("Check: Passed, all permissions found!")
            print "Check: Passed, all permissions found!"
    if config.isAuditLogSetup():
        logging.info("Settings to create an Audit Trail integration are also specified.")
        print "Settings to create an Audit Trail integration are also specified."
        idType = config.getAuditSetupType()
        id = config.getAuditSetupId()
        logging.info("Checking if the GCP user has the required permissions in " + idType.lower() + " with id " + id + "!")
        print "Checking if the GCP user has the required permissions in " + idType.lower() + " with id " + id + "!"
        if idType == "ORGANIZATION":
            neededPermissions = util.testOrgPermissions(id, ORG_PERMISSIONS)
        elif idType == "PROJECT":
            neededPermissions = util.testProjectPermissions(id, AUDIT_PERMISSIONS)
        if len(neededPermissions) is not 0:
            logging.info("The GCP user needs following permissions in " + idType.lower() + " " + config.getComplianceSetupId() + " to run the script: \n" + str(neededPermissions))
            print "The GCP user needs the following permissions in " + idType.lower() + " " + config.getComplianceSetupId() + " to run the script: \n" + str(neededPermissions)
            yesOrNo = yesNoInput("Try anyway? (Y/N): ")
            if yesOrNo == "no" or yesOrNo == "n":
                raise Exception("The GCP user needs some required permissions in the project before running script!")
            logging.warn("This script run may have permission issues!")
            print "This script run may have permission issues!"
        else:
            logging.info("Check: Passed, all permissions found!")
            print "Check: Passed, all permissions found!"
    if config.doesBucketExist():
        logging.info("Checking if the GCP user has the required permissions for bucket " + config.getExistingBucketName())
        print "Checking if the GCP user has the required permissions for bucket " + config.getExistingBucketName()
        neededPermissions = util.testProjectPermissions(config.getBucketParent(), BUCKET_PERMISSIONS)
        if len(neededPermissions) is not 0:
            logging.info("The GCP user needs the following permissions in the project " + config.getSetupProjectId() + " to run the script: \n" + str(neededPermissions))
            print "The GCP user needs the following permissions in the project " + config.getSetupProjectId() + " to run the script: \n" + str(neededPermissions)
            yesOrNo = yesNoInput("Try anyway? (Y/N): ")
            if yesOrNo == "no" or yesOrNo == "n":
                raise Exception("The GCP user needs some required permissions in the project before running script!")
            logging.warn("The script run may have permission issues!")
            print "The script run may have permission issues!"
        else:
            logging.info("Check: Passed, all permissions found!")
            print "Check: Passed, all permissions found!"

    if not rollback:
        yesOrNo = yesNoInput("Do you want the script to automatically create a new integration in your Lacework application? (Y/N): \n")
        if yesOrNo == "y" or yesOrNo == "yes":
            return True
        elif yesOrNo == "n" or yesOrNo == "no":
            return False
        else:
            return None
    else:
        return False

def checkApiEnablement(setupProjectId, util, toCheck=API_LIST):
    logging.info("Checking if all the required APIs are enabled...")
    print "Checking if all the required APIs are enabled..."
    toEnable = []
    for api in toCheck:
        apiEnabled = util.checkApiEnabled(setupProjectId, api)
        if not apiEnabled:
            toEnable.append(api)

    if len(toEnable) == 0:
        logging.info("Check: All the required APIs are already enabled!")
        print "Check: All the required APIs are already enabled!"
    else:
        logging.info("Check: Need to enable following APIs: \n" + str(toEnable))
        print "Check: Need to enable following APIs: \n" + str(toEnable)
        yesOrNo = yesNoInput("Confirm Enablement (Y/N): \n")
        if yesOrNo == "no" or yesOrNo == "n":
            sys.exit("The necessary API enablement was rejected! Exting the script.")
    return toEnable

def checkDeployment(deploymentName, setupProjectId, config, util):
    logging.info("Checking if the deployment called " + deploymentName + " already exists." )
    print "Checking if the deployment called " + deploymentName + " already exists."
    # If a deployment already exists we do not need a new deployment as we can use the resources already
    # created and just print the output
    if (util.checkIfDeploymentExists(setupProjectId, deploymentName)):
        logging.info("Deployment called " + deploymentName + " has been found, checking status")
        deploymentOutput = util.deploymentWait(setupProjectId, deploymentName)
        if deploymentOutput is None:
            raise Exception("Deployment found has a failed status with above error!\n")

        createLaceworkIntegration(deploymentOutput, config, util)
        return True
    else:
        logging.info("Check: Passed! No deployments with this name already exists.")
        print "Check: Passed! No deployments with this name already exists."
        return False

def checkExistingBucket(bucketName, util):
    logging.info("Checking if existing Bucket is valid!")
    print "Checking if existing Bucket is valid!"
    bucketDetails = util.getBucket(bucketName)
    if "projectNumber" in bucketDetails:
        bucketParent = bucketDetails["projectNumber"]
        print "Check: Passed! Existing bucket name is correct!"
        logging.info("Check: Passed! Existing bucket name is correct!")
        return bucketParent
    else:
        print "Check: Failed! Existing bucket name is not correct!"
        raise Exception("Check: Failed! Existing bucket name is not correct!")


def checkProjectdetails(setupProjectId, util):
    logging.info("Checking if setup Project is valid!")
    print "Checking if setup Project is valid!"
    # We need to fetch project number to create a google service account needed for deployment manager
    projectDetails = util.getProjectDetails(setupProjectId)
    logging.info("Check: Passed! Project details were acquired.")
    print "Check: Passed! Project details were acquired."
    return projectDetails

def checkServiceAccount(projectId, util):
    logging.info("Checking if setup Project has valid storage service account!")
    print "Checking if setup Project has valid storage service account!"
    # We need to fetch project number to create a google service account needed for deployment manager
    serviceAccount = util.getProjectServiceAccount(projectId)
    if "email_address" in serviceAccount:
        logging.info("Check: Passed! Project has valid storage service account!")
        print "Check: Passed! Project has valid storage service account!"
    else:
        print "Check: Failed!"
        raise Exception("Check: Failed!")

def checkConfigFile(configFile):
    logging.info("Checking and loading the configuration YAML file...")
    print("Checking and loading the configuration YAML file...")
    config = Config(ConfigParser.parseConfig(configFile))
    logging.info("Check: Passed! Configuration was successfully loaded.")
    print "Check: Passed! Configuration was successfully loaded."
    return config

def checkAllIamPolicies(config, util, toCheckProj=ROLES, toCheckOrg=ORG_ROLES):
    googleServiceAccount = config.getSetupProjectNumber() + "@cloudservices.gserviceaccount.com"
    rolesAudit = []
    rolesOrg = []
    logging.info("Checking if the Google-managed service account has the required roles for project!")
    print "Checking if the Google-managed service account has the required roles for project!"
    rolesProject = checkIamPolicies(googleServiceAccount, config.getSetupProjectId(), "PROJECT", util, toCheckProj)
    if len(rolesProject) == 0:
        logging.info("Check: No roles need to be added to project!")
        print "Check: No roles need to be added to project!"
    else:
        logging.info("Check: For the Google-managed service account called " + googleServiceAccount + " the following roles must be granted to the project: " + config.getSetupProjectId() + "\n" + str(rolesProject))
        print "Check: For the Google-managed service account called " + googleServiceAccount + " the following roles must be granted to the project: " + config.getSetupProjectId() + "\n" + str(rolesProject)
        yesOrNo = yesNoInput("Confirm Grant (Y/N): \n")
        if yesOrNo == "no" or yesOrNo == "n":
            sys.exit("The necessary role granting was rejected. Exiting the script.!")
    if config.getComplianceSetupType() == "ORGANIZATION":
        logging.info("Checking if the Google-managed service account has the required roles for the organization!")
        print "Checking if the Google-managed service account has the required roles for the organization!"
        rolesOrg = checkIamPolicies(googleServiceAccount, config.getComplianceSetupId(), config.getComplianceSetupType(), util, toCheckOrg)
        if len(rolesOrg) == 0:
            logging.info("Check: No roles need to be granted to the organization!")
            print "Check: No roles need to be granted to the organization!"
        else:
            logging.info("Check: For the Google-managed service account called " + googleServiceAccount + ", the following roles must be granted to the organization: " + config.getComplianceSetupId() + ".\n" + str(rolesOrg))
            print "Check: For the Google-managed service account called " + googleServiceAccount + ", the following roles must be granted to the organization: " + config.getComplianceSetupId() + ".\n" + str(rolesOrg)
            yesOrNo = yesNoInput("Confirm Grant (Y/N): \n")
            if yesOrNo == "no" or yesOrNo == "n":
                sys.exit("The necessary role granting to the organization was rejected. Exiting the script.")

    if config.isAuditLogSetup():
        logging.info("Checking if the Google-managed service account has the required roles for audit log exporting!")
        print "Checking if the Google-managed service account has the required roles for audit log exporting!"
        idType = config.getAuditSetupType()
        id = config.getAuditSetupId()
        rolesToGive = checkIamPolicies(googleServiceAccount, id, idType, util, AUDIT_ROLES)
        if len(rolesToGive) is not 0:
            rolesAudit.append({"id": id, "idType": idType, "roles": rolesToGive})

        if len(rolesAudit) == 0:
            logging.info("Check: No additional roles need to be granted for audit log exporting!")
            print "Check: No additional roles need to be granted for audit log exporting!"
        else:
            logging.info("Check: The following roles for the Google-managed service account called " + googleServiceAccount + " must be granted for audit log exporting. \n" + str(rolesAudit))
            print "Check: The following roles for the Google-managed service account called " + googleServiceAccount + " must must be granted for audit log exporting. \n" + str(rolesAudit)
            yesOrNo = yesNoInput("Confirm Grant? (Y/N): \n")
            if yesOrNo == "no" or yesOrNo == "n":
                sys.exit("The necessary role granting was rejected for audit log exporting! Exiting the script. ")

    return rolesProject, rolesOrg, rolesAudit

def checkIamPolicies(googleServiceAccount, id, idType, util, rolesToCheck):
    policy = util.getIAMPolicy(id, idType)
    bindings = policy.get('bindings')
    if bindings == None:
        rolesToGrant = rolesToCheck
    else:
        rolesToGrant = checkRoles(bindings, rolesToCheck, googleServiceAccount)

    return rolesToGrant

def checkRoles(bindings, roles, member):
    memberName = "serviceAccount:" + member
    rolesToGrant = []
    for role in roles:
        roleFound = False
        for roleobj in bindings:
            if roleobj['role'] == role:
                roleFound = True
                if memberName not in roleobj['members']:
                    rolesToGrant.append(role)
        if not roleFound:
            rolesToGrant.append(role)

    return rolesToGrant
