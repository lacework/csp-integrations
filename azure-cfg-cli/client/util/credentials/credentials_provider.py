from abc import abstractmethod
from msrestazure.azure_active_directory import UserPassCredentials, AADTokenCredentials
from azure.graphrbac import GraphRbacManagementClient

from azure_cli_credentials_provider import  AzureEnvironmentSessionCredentials
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD, AZURE_CHINA_CLOUD, AZURE_US_GOV_CLOUD, AZURE_GERMAN_CLOUD
import adal
from msrestazure.azure_active_directory import AdalAuthentication
KEY_VAULT_RESOURCE = "https://vault.azure.net"

CREDENTIALS_TYPE_USER_PASS = "USER_PASS"
CREDENTIALS_TYPE_CLI = "CLI"
CREDENTIALS_TYPE_PORTAL = "PORTAL"
CREDENTIALS_TYPE_APP = "APP"
KEY_USERNAME="userName"
KEY_PASSWORD = "password"
KEY_APP_ID = "appId"
KEY_CLIENT_SECRET = "secret"

class ResourceCredentialsProvider(object):
    def __init__(self, config):
        self.__config = config
        self.__objectId = None

    @abstractmethod
    def getGraphResourceCredentials(self):
        pass

    @abstractmethod
    def getGrantResourceCredentials(self):
        pass

    @abstractmethod
    def getManagementCredentials(self):
        pass

    @abstractmethod
    def getKeyVaultCredentials(self):
        pass

    @abstractmethod
    def getObjectId(self):
        pass

    def getObjectIdData(self, graphClient):
        if self.__objectId == None:
            currentUser = graphClient.objects.get_current_user()
            self.__objectId = currentUser.object_id
        return self.__objectId

    def getConfig(self):
        return self.__config

class AzureEnvironmentSessionCredentialsProvider(ResourceCredentialsProvider):
    def __init__(self, config):
        super(AzureEnvironmentSessionCredentialsProvider, self).__init__(config)
        cloud = config.getCloudType()
        credentials = config.getCredentials()
        userName = credentials[KEY_USERNAME]
        self.__userName = userName
        graphResource = cloud.endpoints.active_directory_graph_resource_id
        managementResource = cloud.endpoints.management
        self.__graphCredentials = AzureEnvironmentSessionCredentials(resource=graphResource, tenant=config.getTenantId())
        self.__grantCredentials = AzureEnvironmentSessionCredentials( resource="74658136-14ec-4630-ad9b-26e160ff0fc6", tenant=config.getTenantId())
        self.__managementCredentials = AzureEnvironmentSessionCredentials(resource=managementResource, tenant=config.getTenantId())
        self.__keyVaultCredentials = AzureEnvironmentSessionCredentials(resource="https://vault.azure.net", tenant=config.getTenantId())
        # self.__objectId = None
        self.getObjectId()

    def getGraphResourceCredentials(self):
        return self.__graphCredentials

    def getManagementCredentials(self):
        return self.__managementCredentials

    def getGrantResourceCredentials(self):
        return self.__grantCredentials

    def getKeyVaultCredentials(self):
        return self.__keyVaultCredentials

    def getObjectId(self):
        # if self.__objectId == None:
        graphRbacClient = GraphRbacManagementClient(self.__graphCredentials, self.getConfig().getTenantId())
        return self.getObjectIdData(graphRbacClient)
    #         for user in graphRbacClient.users.list():
    #             if user.mail == self.__userName or user.given_name == self.__userName or ('additionalProperties' in user and self.__userName in user.get('additionalProperties').get('otherMails')):
    #                 self.__objectId = user.object_id
    #     return self.__objectId



class UserPasswordCredentialsProvider(ResourceCredentialsProvider):
    def __init__(self, config):
        super(UserPasswordCredentialsProvider, self).__init__(config)
        cloud = config.getCloudType()
        credentials = config.getCredentials()
        userName = credentials[KEY_USERNAME]
        password =credentials[KEY_PASSWORD]

        self.__userName = userName
        graphResource = cloud.endpoints.active_directory_graph_resource_id
        managementResource = cloud.endpoints.management
        self.__graphCredentials = UserPassCredentials(userName, password,
                                                      resource=graphResource, tenant=config.getTenantId())
        self.__grantCredentials = UserPassCredentials(userName, password,
                                                      resource="74658136-14ec-4630-ad9b-26e160ff0fc6",
                                                      tenant=config.getTenantId())
        self.__managementCredentials = UserPassCredentials(userName, password,
                                                           resource=managementResource, tenant=config.getTenantId())
        self.__keyVaultCredentials = UserPassCredentials(userName, password,resource = "https://vault.azure.net"
                                                         ,tenant=config.getTenantId())
        # graphClient = GraphRbacManagementClient(self.__graphCredentials, config.getTenantId())
        # currentUser = graphClient.objects.get_current_user()
        # self.__objectId = currentUser.object_id

    def getGraphResourceCredentials(self):
        return self.__graphCredentials

    def getManagementCredentials(self):
        return self.__managementCredentials

    def getGrantResourceCredentials(self):
        return self.__grantCredentials

    def getKeyVaultCredentials(self):
        return self.__keyVaultCredentials

    def getObjectId(self):
        graphRbacClient = GraphRbacManagementClient(self.__graphCredentials, self.getConfig().getTenantId())
        return self.getObjectIdData(graphRbacClient)

class AppCredentialsProvider(ResourceCredentialsProvider):
    def __init__(self, config):
        super(AppCredentialsProvider, self).__init__(config)
        cloud = config.getCloudType()
        credentials = config.getCredentials()
        appId = credentials[KEY_APP_ID]
        secret = credentials[KEY_CLIENT_SECRET]
        self.__appId = appId
        graphResource = cloud.endpoints.active_directory_graph_resource_id
        managementResource = cloud.endpoints.management

        self.__graphCredentials = AppCredentialsProvider.getAADTokenCredentials(cloud, graphResource, appId, config.getTenantId(),
                                                                secret)

        self.__grantCredentials = AppCredentialsProvider.getAADTokenCredentials(cloud, "74658136-14ec-4630-ad9b-26e160ff0fc6", appId,
                                                                config.getTenantId(), secret)

        self.__managementCredentials = AppCredentialsProvider.getAADTokenCredentials(cloud, managementResource, appId,
                                                                     config.getTenantId(), secret)
        self.__keyVaultCredentials = AppCredentialsProvider.getAADTokenCredentials(cloud, KEY_VAULT_RESOURCE, appId,
                                                                     config.getTenantId(), secret)
        self.__objectId = None

    @staticmethod
    def getAADTokenCredentials( cloudType, resource, appId, tenantId, secret):
        LOGIN_ENDPOINT = cloudType.endpoints.active_directory
        context = adal.AuthenticationContext(LOGIN_ENDPOINT + '/' + tenantId)
        credentials = AdalAuthentication(
            context.acquire_token_with_client_credentials,
            resource,
            appId,
            secret
        )
        return credentials

    def getGraphResourceCredentials(self):
        return self.__graphCredentials

    def getManagementCredentials(self):
        return self.__managementCredentials

    def getGrantResourceCredentials(self):
        return self.__grantCredentials

    def getKeyVaultCredentials(self):
        return self.__keyVaultCredentials

    def getObjectId(self):
        graphRbacClient = GraphRbacManagementClient(self.__graphCredentials, self.getConfig().getTenantId())
        return self.getObjectIdData(graphRbacClient)

class CredentialsProviderFactory():

    @staticmethod
    def getCredentialsProvider(config):

        credentials = config.getCredentials()
        authType = credentials['type']

        if authType == CREDENTIALS_TYPE_USER_PASS:
            return UserPasswordCredentialsProvider(config);
        if authType in [CREDENTIALS_TYPE_CLI,  CREDENTIALS_TYPE_PORTAL]:
            return AzureEnvironmentSessionCredentialsProvider(config);
        if authType == CREDENTIALS_TYPE_APP:
            return AppCredentialsProvider(config);
        raise Exception("Invalid Auth Type: " + authType)

    @staticmethod
    def getCredentialsForResource(config, resource):

        credentials = config.getCredentials()
        authType = credentials['type']
        tenantId = config.getTenantId()
        if authType == CREDENTIALS_TYPE_USER_PASS:
            userName = credentials[KEY_USERNAME]
            password = credentials[KEY_PASSWORD]
            if tenantId:
                return UserPassCredentials(userName, password, resource=resource, tenant=config.getTenantId())
            else:
                return UserPassCredentials(userName, password, resource=resource)
        if authType in [CREDENTIALS_TYPE_CLI,  CREDENTIALS_TYPE_PORTAL]:
            if tenantId:
                return AzureEnvironmentSessionCredentials(resource=resource, tenant=config.getTenantId());
            else:
                return AzureEnvironmentSessionCredentials(resource=resource);
        if authType == CREDENTIALS_TYPE_APP:
            appId = credentials[KEY_APP_ID]
            secret = credentials[KEY_CLIENT_SECRET]
            return AppCredentialsProvider.getAADTokenCredentials(AZURE_PUBLIC_CLOUD, resource, appId, config.getTenantId(),
                                                          secret)
        raise Exception("Invalid Auth Type: " + authType)


