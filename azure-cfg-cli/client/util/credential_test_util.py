from azure.graphrbac import GraphRbacManagementClient
from azure.keyvault.v2016_10_01 import KeyVaultClient
import logging
from common_util import CommonUtil
import adal, uuid, time

class CredentialsTestUtil(CommonUtil):


    def __init__(self, credentialsProvider):
        super(CredentialsTestUtil, self).__init__(credentialsProvider)
        self.__credentialsProvider  = credentialsProvider

    def listApplications(self):
        isinstance(self.getGraphRbacClient(), GraphRbacManagementClient)
        for app in self.getGraphRbacClient().applications.list():
            logging.info("App details: " +  str(app));

    def listKeys(self):
        for subscription in self.getSubscriptions():
            keyVault = KeyVaultClient(self.__credentialsProvider.getKeyVaultCredentials())
            keyVaultClient = self.getKeyVaultManagementClient(subscription.subscription_id)
            for vault in keyVaultClient.vaults.list():
                vaultName = vault.name
                for key in keyVault.get_keys("https://"+vaultName+".vault.azure.net/"):
                    logging.info("Able to list key: " + key.kid + " in Vault:" + vaultName)
                logging.info("Able to list Keys In KeyVault: " + vaultName)