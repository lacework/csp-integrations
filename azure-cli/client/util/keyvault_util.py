from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.keyvault import KeyVaultClient
from common_util import CommonUtil
from credentials.credentials_provider import ResourceCredentialsProvider
import logging as log
from azure.mgmt.keyvault.v2016_10_01.models import AccessPolicyUpdateKind, VaultAccessPolicyProperties, \
    AccessPolicyEntry, Permissions, KeyPermissions, SecretPermissions


class KeyVaultUtil(CommonUtil):
    def __init__(self, credentialsProvider):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        super(KeyVaultUtil, self).__init__(credentialsProvider)
        self.__credentialsProvider = credentialsProvider

    def setKeyVaultPolicy(self):
        subscriptionList = self.getSubscriptions()
        for subscription in subscriptionList:
            subscriptionId = subscription.subscription_id
            keyVaultList = self.__listKeyVaults(subscriptionId)
            log.info("Found " + str(len(keyVaultList)) + " KeyVaults")
            for keyVault in keyVaultList:
                keyVaultClient = self.getKeyVaultManagementClient(subscriptionId)
                keyPermissionList = [KeyPermissions.list]
                secretPermissionList = [SecretPermissions.list]
                permissions = Permissions(keys=keyPermissionList, secrets=secretPermissionList)

                tenantId = self.__credentialsProvider.getConfig().getTenantId()
                servicePrincipalId = self.getServicePrincipalId()
                if servicePrincipalId == None:
                    raise Exception("Error Fetching service Principal Id")
                appId = self.getAppId()
                if appId == None:
                    raise Exception("Error Fetching service App Id")

                accessPolicyEntry = AccessPolicyEntry(tenant_id=tenantId, object_id=servicePrincipalId,
                                                      application_id=None, permissions=permissions)
                vaultAccessProperties = VaultAccessPolicyProperties(access_policies=[accessPolicyEntry])
                accessPolicyKind = AccessPolicyUpdateKind(AccessPolicyUpdateKind.add)
                accessPolicy = keyVaultClient.vaults.update_access_policy(keyVault.getResourceGroupName(),
                                                                          keyVault.getKeyVaultName(), accessPolicyKind,
                                                                          vaultAccessProperties)
                log.info("Assigned access policy permissions to KeyVault: " + keyVault.getKeyVaultName()
                         + " Resource Group: " + keyVault.getResourceGroupName())

    def __listKeyVaults(self, subscriptionId):
        keyVaultClient = KeyVaultManagementClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)
        keyVaultList = []
        for keyVault in keyVaultClient.vaults.list(raw=True):
            keyVaultList.append(KeyVaultParsed(keyVault.id))
        return keyVaultList


class KeyVaultParsed(object):
    def __init__(self, id):
        self.__resourceGroup = id.split("/")[4];
        self.__keyVaultName = id.split("/")[8];

    def getResourceGroupName(self):
        return self.__resourceGroup

    def getKeyVaultName(self):
        return self.__keyVaultName
