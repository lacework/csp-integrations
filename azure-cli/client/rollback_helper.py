import logging

import yaml
from msrestazure.azure_exceptions import CloudError

from client.util.app_util import AppUtil
from client.util.credentials.credentials_provider import ResourceCredentialsProvider
from client.util.event_subscription_util import EventSubscriptionUtil
from client.util.monitor_util import MonitorUtil
from client.util.resource_util import ResourceUtil
from client.util.role_util import RoleUtil
from client.util.storage_util import StorageUtil


class RollbackHelper(object):

    def __init__(self, credentialsProvider):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        self.__credentialProvider = credentialsProvider

    def saveRollbackToFile(self, saveState):
        with open("rollback.yml", 'w') as f:
            yaml.dump(saveState, f)

    def getSaveState(self):
        return self.__getRollbackFromFile()

    def performRollback(self, saveState=None):
        if saveState is None:
            saveState = self.__getRollbackFromFile()

        appUtil = AppUtil(self.__credentialProvider)
        roleUtil = RoleUtil(saveState.appId, self.__credentialProvider, False)
        resourceUtil = ResourceUtil(self.__credentialProvider)
        storageUtil = StorageUtil(self.__credentialProvider)
        monitorUtil = MonitorUtil(self.__credentialProvider)
        eventSubUtil = EventSubscriptionUtil(self.__credentialProvider)

        self.__surroundWithTry(roleUtil.removeRoleAssignment, "Custom Role Assignment", saveState.assignedCustomRole,
            saveState.roleDefinitionName, saveState.subscriptionId)

        if storageUtil.checkStorageAccountExists(saveState.storageAccountName, saveState.subscriptionId):
            storageAccount = storageUtil.getStorageAccount(saveState.resourceGroupName, saveState.storageAccountName, saveState.subscriptionId)
            self.__surroundWithTry(eventSubUtil.deleteEventGridSubscription, "Event Grid Subscription", saveState.createdEventGridSub,
                saveState.eventSubName, storageAccount.id, saveState.subscriptionId)

        self.__surroundWithTry(monitorUtil.deleteLogProfile, "Log Profile", saveState.createdLogProfile,
            saveState.logProfileName, saveState.subscriptionId)

        storageExists = storageUtil.checkStorageAccountExists(saveState.storageAccountName, saveState.subscriptionId)
        if storageExists:
            try:
                storageKeys = storageUtil.getStorageAccountKeys(saveState.resourceGroupName, saveState.storageAccountName, saveState.subscriptionId)
                self.__surroundWithTry(storageUtil.deleteQueue, "Storage Queue", saveState.createdQueue,
                    saveState.queueName, saveState.storageAccountName, storageKeys['key1'])
            except CloudError:
                logging.exception("Error finding Storage Account.")

        self.__surroundWithTry(storageUtil.deleteStorageAccount, "Storage Account", saveState.createdStorageAccount,
            saveState.resourceGroupName, saveState.storageAccountName, saveState.subscriptionId)

        self.__surroundWithTry(resourceUtil.deleteResourceGroup, "Resource Group", saveState.createdResourceGroup,
            saveState.resourceGroupName, saveState.subscriptionId)

        self.__surroundWithTry(roleUtil.removeRoleAssignment, "Reader Role Assignment", "Reader", saveState.assignedReaderRole,
            saveState.subscriptionId)

        self.__surroundWithTry(roleUtil.deleteServicePrincipal, "Service Principal", saveState.createdServicePrincipal and not saveState.createdApp)

        self.__surroundWithTry(appUtil.deleteAppIfExist, "Application", saveState.createdApp)

        # Waiting till the end to delete Custom Role
        self.__surroundWithTry(roleUtil.deleteRoleDefinition, "Custom Role Definition", saveState.createdCustomRole,
            saveState.roleDefinitionName, saveState.subscriptionId)

    def __surroundWithTry(self, func, resource, created, *kargs):
        if not created:
            return
        try:
            func(*kargs)
        except:
            logging.exception("Error in rolling back " + resource)

    def __getRollbackFromFile(self):
        with open("rollback.yml", 'r') as f:
            return yaml.load(f, Loader=yaml.FullLoader)
