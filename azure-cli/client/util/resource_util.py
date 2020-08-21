import logging
import time

from common_util import CommonUtil
from credentials.credentials_provider import ResourceCredentialsProvider


class ResourceUtil(CommonUtil):
    def __init__(self, credentialsProvider):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        super(ResourceUtil, self).__init__(credentialsProvider)

    def createResourceGroup(self, resourceGroupName, resourceGroupLocation, subscriptionId):
        logging.info("Creating new Resource Group with Name: " + resourceGroupName + " and Location: " + resourceGroupLocation)
        resourceManagementClient = self.getResourceManagementClient(subscriptionId)
        resourceGroupParams = {'location': resourceGroupLocation}
        resourceManagementClient.resource_groups.create_or_update(resourceGroupName, resourceGroupParams)
        logging.info("Resource Group created successfully with Name: " + resourceGroupName + " and Location: " + resourceGroupLocation)

    def checkResourceGroupExists(self, resourceGroupName, subscriptionId):
        resourceManagementClient = self.getResourceManagementClient(subscriptionId)
        return self.__checkResourceGroupExists(resourceGroupName, resourceManagementClient)

    def __checkResourceGroupExists(self, resourceGroupName, resourceManagementClient):
        return resourceManagementClient.resource_groups.check_existence(resourceGroupName)

    def deleteResourceGroup(self, resourceGroupName, subscriptionId):
        logging.info("Deleting Resource Group with Name: " + resourceGroupName)
        resourceManagementClient = self.getResourceManagementClient(subscriptionId)

        found = self.__checkResourceGroupExists(resourceGroupName, resourceManagementClient)
        if not found:
            logging.debug("Resource Group not found.")
            return

        resourceManagementClient.resource_groups.delete(resourceGroupName)
        logging.info("Successfully Deleted Resource Group with Name: " + resourceGroupName)
