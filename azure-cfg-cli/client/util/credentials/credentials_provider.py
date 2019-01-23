from abc import abstractmethod
from msrestazure.azure_active_directory import UserPassCredentials, AADTokenCredentials
from azure.graphrbac import GraphRbacManagementClient
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD, AZURE_CHINA_CLOUD, AZURE_US_GOV_CLOUD, AZURE_GERMAN_CLOUD
import adal
from msrestazure.azure_active_directory import AdalAuthentication
KEY_VAULT_RESOURCE = "https://vault.azure.net"

class ResourceCredentialsProvider(object):
    def __init__(self, config):
        self.__config = config

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

    def getConfig(self):
        return self.__config


class UserPasswordCredentialsProvider(ResourceCredentialsProvider):
    def __init__(self, userName, password, config):
        super(UserPasswordCredentialsProvider, self).__init__(config)
        cloud = config.getCloudType()
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
        graphClient = GraphRbacManagementClient(self.__graphCredentials, config.getTenantId())
        currentUser = graphClient.objects.get_current_user()
        self.__objectId = currentUser.object_id

    def getGraphResourceCredentials(self):
        return self.__graphCredentials

    def getManagementCredentials(self):
        return self.__managementCredentials

    def getGrantResourceCredentials(self):
        return self.__grantCredentials

    def getKeyVaultCredentials(self):
        return self.__keyVaultCredentials

    def getObjectId(self):
        if self.__objectId == None:
            graphClient = GraphRbacManagementClient(self.__graphCredentials, config.getTenantId())
            currentUser = graphClient.objects.get_current_user()
            self.__objectId = currentUser.object_id
        return self.__objectId
        # graphRbacClient = GraphRbacManagementClient(self.__graphCredentials, self.getConfig().getTenantId())
        # for user in graphRbacClient.users.list():
        #     if user.mail == self.__userName:
        #         return user.object_id


class AppCredentialsProvider(ResourceCredentialsProvider):
    def __init__(self, appId, secret, config):
        super(AppCredentialsProvider, self).__init__(config)
        cloud = config.getCloudType()
        self.__appId = appId
        graphResource = cloud.endpoints.active_directory_graph_resource_id
        managementResource = cloud.endpoints.management

        self.__getAADTokenCredentials(cloud, graphResource, appId, config.getTenantId(), secret)

        self.__graphCredentials = self.__getAADTokenCredentials(cloud, graphResource, appId, config.getTenantId(),
                                                                secret)

        self.__grantCredentials = self.__getAADTokenCredentials(cloud, "74658136-14ec-4630-ad9b-26e160ff0fc6", appId,
                                                                config.getTenantId(), secret)

        self.__managementCredentials = self.__getAADTokenCredentials(cloud, managementResource, appId,
                                                                     config.getTenantId(), secret)
        self.__keyVaultCredentials = self.__getAADTokenCredentials(cloud, KEY_VAULT_RESOURCE, appId,
                                                                     config.getTenantId(), secret)
        self.__objectId = None

    def __getAADTokenCredentials(self, cloudType, resource, appId, tenantId, secret):
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
        if self.__objectId ==None:
            graphClient = GraphRbacManagementClient(self.__graphCredentials, config.getTenantId())
            currentUser = graphClient.objects.get_current_user()
            self.__objectId = currentUser.object_id
        return self.__objectId


class CredentialsProviderFactory():
    @staticmethod
    def getUserCredentialsProvider(userName, password, config):
        return UserPasswordCredentialsProvider(userName, password, config);

    @staticmethod
    def getAppCredentialsProvider(appId, secret, config):
        return AppCredentialsProvider(appId, secret, config);
