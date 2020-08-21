import logging

from azure.mgmt.monitor.models import LogProfileResource, RetentionPolicy

from common_util import CommonUtil
from credentials.credentials_provider import ResourceCredentialsProvider


class MonitorUtil(CommonUtil):

    def __init__(self, credentialsProvider):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        super(MonitorUtil, self).__init__(credentialsProvider)

    def createLogProfile(self, name, storageAccountId, subscriptionId):
        monitorMgmtClient = self.getMonitorManagementClient(subscriptionId)

        locations = [l.name for l in self.getSubscriptionClient().subscriptions.list_locations(subscriptionId)]
        locations.append("global")

        parameters = LogProfileResource()
        parameters.storage_account_id = storageAccountId
        parameters.locations = locations
        parameters.categories = ["Write", "Delete", "Action"]
        parameters.location = "westus2"
        parameters.retention_policy = RetentionPolicy(enabled=True, days=7)

        monitorMgmtClient.log_profiles.create_or_update(name, parameters)

    def checkLogProfileExists(self, name, subscriptionId):
        monitorMgmtClient = self.getMonitorManagementClient(subscriptionId)

        return self.__checkLogProfileExists(name, monitorMgmtClient)

    def __checkLogProfileExists(self, name, monitorMgmtClient):
        for p in monitorMgmtClient.log_profiles.list():
            if p.name.lower() == name.lower():
                return True
        return False

    def deleteLogProfile(self, name, subscriptionId):
        monitorMgmtClient = self.getMonitorManagementClient(subscriptionId)

        found = self.__checkLogProfileExists(name, monitorMgmtClient)

        if not found:
            logging.debug("Log Profile not found.")
            return

        monitorMgmtClient.log_profiles.delete(name)
