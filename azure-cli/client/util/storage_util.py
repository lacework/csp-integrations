import logging
import time

from azure.mgmt.storage.models import StorageAccountCreateParameters, Sku, SkuName, Kind
from azure.storage.common import CloudStorageAccount

from common_util import CommonUtil
from credentials.credentials_provider import ResourceCredentialsProvider


class StorageUtil(CommonUtil):
    def __init__(self, credentialsProvider):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        super(StorageUtil, self).__init__(credentialsProvider)

    def createStorageAccount(self, resourceGroupName, storageAccountName, resourceGroupLocation, subscriptionId):
        logging.info("Creating new Storage Account with Name: " + storageAccountName + " and Location: " + resourceGroupLocation)
        storageClient = self.getStorageManagementClient(subscriptionId)

        check = self.__checkStorageAccountExists(storageAccountName, storageClient)
        if check:
            logging.info("Storage Account with Name: " + storageAccountName + " and Location: " + resourceGroupLocation + " already exists.")
            return self.getStorageAccount(resourceGroupName, storageAccountName, subscriptionId)

        storage_async_operation = storageClient.storage_accounts.create(
            resourceGroupName,
            storageAccountName,
            StorageAccountCreateParameters(
                sku=Sku(name=SkuName.standard_lrs),
                kind=Kind.storage_v2,
                location=resourceGroupLocation,
                supportsHttpsTrafficOnly=True
            )
        )
        storageAccount = storage_async_operation.result()
        logging.info("Storage account created successfully with Name: " + storageAccountName + " and Location: " + resourceGroupLocation)
        return storageAccount

    def getStorageAccount(self, resourceGroupName, storageAccountName, subscriptionId):
        storageClient = self.getStorageManagementClient(subscriptionId)
        storageAccount = storageClient.storage_accounts.get_properties(resourceGroupName, storageAccountName)
        return storageAccount

    def getStorageAccountKeys(self, resourceGroupName, storageAccountName, subscriptionId):
        storageClient = self.getStorageManagementClient(subscriptionId)
        storage_keys = storageClient.storage_accounts.list_keys(resourceGroupName, storageAccountName)
        storage_keys = {v.key_name: v.value for v in storage_keys.keys}
        return storage_keys

    def checkStorageAccountExists(self, storageAccountName, subscriptionId):
        storageClient = self.getStorageManagementClient(subscriptionId)
        return self.__checkStorageAccountExists(storageAccountName, storageClient)

    def __checkStorageAccountExists(self, storageAccountName, storageClient):
        availability = storageClient.storage_accounts.check_name_availability(storageAccountName)
        return not availability.name_available

    def deleteStorageAccount(self, resourceGroupName, storageAccountName, subscriptionId):
        logging.info("Deleting Storage account with Name: " + storageAccountName)

        storageClient = self.getStorageManagementClient(subscriptionId)
        found = self.__checkStorageAccountExists(storageAccountName, storageClient)

        if not found:
            logging.debug("Storage account not found.")
            return

        storageClient.storage_accounts.delete(resourceGroupName, storageAccountName)
        logging.info("Successfully Deleted Storage account with Name: " + storageAccountName)

    def createQueue(self, queueName, resourceGroupName, storageAccountName, storageKey, subscriptionId):
        logging.info("Creating new Queue with Name: " + storageAccountName + " inside Storage Account: " + storageAccountName)
        self.__waitForStorageWithRetry(resourceGroupName, storageAccountName, subscriptionId, 5)
        account = CloudStorageAccount(storageAccountName, storageKey)
        queue_service = account.create_queue_service()
        queue_service.create_queue(queueName)
        logging.info("Queue created successfully with Name: " + storageAccountName + " inside Storage Account: " + storageAccountName)

    def __waitForStorageWithRetry(self, resourceGroupName, storageAccountName, subscriptionId, retry):
        if retry <= 0:
            raise Exception("Storage Account not found.")
        check = self.getStorageAccount(resourceGroupName, storageAccountName, subscriptionId)

        if check:
            return

        time.sleep(5)
        self.__waitForStorageWithRetry(resourceGroupName, storageAccountName, subscriptionId, retry - 1)

    def deleteQueue(self, queueName, storageAccountName, storageKey):
        logging.info('Attempting deletion of queue: %s', queueName)
        account = CloudStorageAccount(storageAccountName, storageKey)
        queue_service = account.create_queue_service()
        if queue_service.exists(queueName):
            queue_service.delete_queue(queueName)
            logging.info('Successfully deleted queue: %s', queueName)

    def checkQueueExists(self, queueName, storageAccountName, storageKey):
        account = CloudStorageAccount(storageAccountName, storageKey)
        queue_service = account.create_queue_service()
        return queue_service.exists(queueName)
