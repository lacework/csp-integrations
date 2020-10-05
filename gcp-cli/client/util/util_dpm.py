from __future__ import print_function
from __future__ import absolute_import
from builtins import input
from builtins import str
import logging
from .util_base import UtilBase
from . import util_template

HTTP_GET_METHOD = "GET"
HTTP_POST_METHOD = "POST"
HTTP_DELETE_METHOD = "DELETE"
SERVICE_ACCOUNT_ID = "lacework-cfg-sa"

GET_DEPLOYMENT_URL= "https://www.googleapis.com/deploymentmanager/v2/projects/%projectId/global/deployments/%deployment"
GET_DEPLOYMENTS_URL= "https://www.googleapis.com/deploymentmanager/v2/projects/%projectId/global/deployments"
from client.config.client_helper import ClientHelper
import time
SLEEP_SECS = 20

class UtilDpm(UtilBase):
    def __init__(self):
        UtilBase.__init__(self)

    def checkIfDeploymentExists(self, projectId, deployment):
        isinstance(self.getHttpClient(), ClientHelper)
        url = GET_DEPLOYMENT_URL.replace("%deployment", deployment)
        deployment = self.getHttpClient().make_request(HTTP_GET_METHOD, url, projectId, None)
        if deployment['isError']:
            if deployment['defaultErrorObject'].get("status") == 404:
                return False
            else:
                raise Exception("Error fetching deployment: \n" + str(deployment['defaultErrorObject']))
        return True

    def getDeploymentDetails(self, projectId, deployment):
        isinstance(self.getHttpClient(), ClientHelper)
        url = GET_DEPLOYMENT_URL.replace("%deployment", deployment)
        deployment = self.getHttpClient().make_request(HTTP_GET_METHOD, url, projectId, None)
        if deployment['isError']:
            raise Exception("Error fetching deployment: \n" + str(deployment['defaultErrorObject']))
        return deployment["data"]

    def deploymentWait(self, setupProjectId, deploymentName):
        while (True):
            deployment = self.getDeploymentDetails(setupProjectId, deploymentName)
            if (deployment["operation"]["status"] == "DONE" and "error" in deployment["operation"]):
                logging.warning("Deployment has failed, please run again and check configuration")
                logging.warning("Rolling back and deleting failed deployment")
                self.deleteDeployment(setupProjectId, deploymentName)
                logging.error(str(deployment["operation"]["error"]))
                return None
            elif (deployment["operation"]["status"] == "RUNNING"):
                if (deployment["operation"]["operationType"] == "insert"):
                    logging.info("Deployment is running! Sleeping for " + str(SLEEP_SECS) + " seconds before checking again")
                    print("Deployment is running! Sleeping for " + str(SLEEP_SECS) + " seconds before checking again")
                    time.sleep(SLEEP_SECS)
                else:
                    raise Exception("The deployment with name " + deploymentName + " is being used or being deleted, please wait until all operations are done!")
            else:
                logging.info("Deployment has been created and successfully deployed!")
                return self.getDeploymentOutput(deployment["manifest"])

    def getDeploymentOutput(self, url):
        isinstance(self.getHttpClient(), ClientHelper)
        manifest = self.getHttpClient().make_request(HTTP_GET_METHOD, url, None, None)
        if manifest['isError']:
            raise Exception("Error fetching deployment: \n" + str(manifest["defaultErrorObject"]))
        return manifest["data"]["layout"]

    def deleteDeployment(self, projectId, deploymentName):
        isinstance(self.getHttpClient(), ClientHelper)
        logging.info("Deleting deployment with name: " + deploymentName)
        url = GET_DEPLOYMENT_URL.replace("%deployment", deploymentName)
        deployment = self.getHttpClient().make_request(HTTP_DELETE_METHOD, url, projectId, None)
        if deployment['isError']:
            raise Exception("Error deleting deployment: \n" + str(deployment['defaultErrorObject']))
        logging.info("Deployment with name " + deploymentName + " has been deleted")
        return deployment['data']

    def createDeployment(self, config, deploymentName):
        logging.info("Creating the request body to be sent to the deployment manager")
        body = self.buildDeploymentBody(config, deploymentName)
        projectId = config.getSetupProjectId()
        isinstance(self.getHttpClient(), ClientHelper)
        logging.info("Creating new deployment named " + deploymentName + " in project " + projectId)
        deployment = self.getHttpClient().make_request(HTTP_POST_METHOD, GET_DEPLOYMENTS_URL, projectId, body)
        if deployment['isError']:
            raise Exception("Error creating deployment: \n" + str(deployment['defaultErrorObject']))
        return deployment['data']

    def buildDeploymentBody(self, config, deploymentName):
        setupPrefix = config.getSetupPrefix()
        projectId = config.getSetupProjectId()

        resources = util_template.SERVICE_ACCOUNT
        if (config.isAuditLogSetup()):
            if (not config.doesBucketExist()):
                resources = resources + util_template.BUCKET_CREATION
                resources = resources + util_template.TOPIC_CREATION
                resources = resources + util_template.SUBSCRIPTION_CREATION
                resources = resources + util_template.NOTIFICATION_CREATION
            idType = config.getAuditSetupType()
            id = config.getAuditSetupId()
            sinkAndBucketBinding = util_template.SINK_CREATION
            if not config.doesBucketExist():
                sinkAndBucketBinding += util_template.BUCKET_DEPENDENCY
                sinkAndBucketBinding += util_template.BUCKET_BINDING
            if (idType == "ORGANIZATION"):
                sinkAndBucketBinding = sinkAndBucketBinding.replace("%resourceTypeAudit", "organizations")
                sinkAndBucketBinding = sinkAndBucketBinding.replace("%resourceTypeSingle", "organization")
            elif (idType == "PROJECT"):
                sinkAndBucketBinding = sinkAndBucketBinding.replace("%resourceTypeAudit", "projects")
                sinkAndBucketBinding = sinkAndBucketBinding.replace("%resourceTypeSingle", "project")
            else:
                sinkAndBucketBinding = sinkAndBucketBinding.replace("%resourceTypeAudit", "folders")
                sinkAndBucketBinding = sinkAndBucketBinding.replace("%resourceTypeSingle", "folder")
            sinkAndBucketBinding = sinkAndBucketBinding.replace("%resourceIdAudit", id)
            sinkAndBucketBinding = sinkAndBucketBinding.replace("%sinkProp", setupPrefix + "-" + id + "-lacework-sink")
            sinkAndBucketBinding = sinkAndBucketBinding.replace("%bucketBindingName", setupPrefix+ "-" + id + "-bucket-binding")
            resources = resources + sinkAndBucketBinding

        if config.customRole():
            resources = resources + util_template.CUSTOM_ROLE
            resources = resources + util_template.ASSIGN_ROLE
        resources = resources + util_template.VIEWER_BINDING
        resources = resources + util_template.SECURITY_REVIEWER_BINDING
        if (config.getComplianceSetupType() == "ORGANIZATION"):
            resources = resources + util_template.ORG_VIEWER_BINDING
        resources = resources + util_template.ACCOUNT_KEY

        resources = resources + util_template.OUTPUT
        resources = resources + util_template.OUTPUT_KEY
        if (config.isAuditLogSetup()):
            if config.doesBucketExist():
                resources = resources + util_template.OUTPUT_SINK
            else:
                resources = resources + util_template.OUTPUT_SUBSCRIPTION
            id = config.getAuditSetupId()
            resources = resources.replace("%sinkName", setupPrefix + "-" + projectId + "-" + id + "-lacework-sink")

        if config.customRole():
            if (config.getComplianceSetupType() == "ORGANIZATION"):
                resources = resources.replace("%customRole", setupPrefix + "-lacework-custom-role-org")
                resources = resources.replace("%roleType", "organizations")
                resources = resources.replace("%roleId", setupPrefix.replace("-","") + config.getComplianceSetupId() + "laceworkCustomRoleOrg")
                resources = resources.replace("%roleParent", "organizations/" + config.getComplianceSetupId())
            elif (config.getComplianceSetupType() == "PROJECT"):
                resources = resources.replace("%customRole", setupPrefix + "-lacework-custom-role-project")
                resources = resources.replace("%roleId", setupPrefix.replace("-","") + projectId.replace("-", "") + "laceworkCustomRoleProject")
                resources = resources.replace("%roleType", "projects")
                resources = resources.replace("%roleParent", "projects/" + projectId)

        resources = resources.replace("%setRoleName", setupPrefix + "-lacework-role-assignment")
        resources = resources.replace("%serviceAccountName", setupPrefix + "-" + projectId + "-" + "lacework-serviceaccnt")
        resources = resources.replace("%serviceAccountId", setupPrefix + "-" + SERVICE_ACCOUNT_ID)
        if config.doesBucketExist():
            resources = resources.replace("$(ref.%bucketName.name)", config.getExistingBucketName())
            resources = resources.replace("%projectNumber", config.getBucketParent())
        else:
            resources = resources.replace("%bucketName", setupPrefix + "-" + projectId + "-" + "lacework-bucket")
            resources = resources.replace("%projectNumber", config.getSetupProjectNumber())
        resources = resources.replace("%projectId", projectId)
        resources = resources.replace("%topicName", setupPrefix + "-" + projectId + "-" + "lacework-topic")
        resources = resources.replace("%topicProp", setupPrefix + "-" + projectId + "-" + "lacework-topic-prop")
        resources = resources.replace("%subscriptionName", setupPrefix + "-" + projectId + "-" + "lacework-subscription")
        resources = resources.replace("%subscriptionProp", setupPrefix + "-" + projectId + "-" + "lacework-subscription-prop")
        resources = resources.replace("%notificationName", setupPrefix + "-" + projectId + "-" + "lacework-notification")
        resources = resources.replace("%setupPrefix", setupPrefix)
        if (config.getComplianceSetupType() == "ORGANIZATION"):
            resources = resources.replace("%resourceType", "organizations")
            resources = resources.replace("%resourceId", "organizations/" + config.getComplianceSetupId())
        else:
            resources = resources.replace("%resourceType", "projects")
            resources = resources.replace("%resourceId", projectId)


        print(resources)
        print("Please review the above configuration to be deployed")
        if config.getToIntegrate():
            print("This deployment will be integrated with following lacework account: " + config.getLaceworkAccount())
        while (True):
            userInput = input("Accept? (Y/N): ")
            userInput = userInput.lower()

            if (userInput == "n" or userInput == "no"):
                raise Exception("Created configuration rejected by user, please check the config.yml")
            elif (userInput == "y" or userInput == "yes"):
                body = {
                    "name" : deploymentName,
                    "target" : {
                        "config" : {
                            "content" : resources
                        }
                    }
                }
                return body
            else:
                print ("Please enter valid input")
