from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD, AZURE_CHINA_CLOUD, AZURE_US_GOV_CLOUD, AZURE_GERMAN_CLOUD

class Config(object):

    def __init__(self, credentials, userClientSecret, subscriptionList, allSubscriptions, tenantId, identifierUrl, cloudType, providerRegistrationList, updateApp):

        if not isinstance(allSubscriptions, bool):
            raise Exception("Invalid value for All Subscriptions:" + str(allSubscriptions))
        if not isinstance(subscriptionList, list):
            raise Exception("Invalid value for SubscriptionsList:" + subscriptionList)
        if not isinstance(providerRegistrationList, list):
            raise Exception("Invalid value for ProviderRegistrationList:" + providerRegistrationList)
        if tenantId is not None and not isinstance(tenantId, str):
            raise Exception("Invalid value for Tenant Id:" + tenantId)
        if identifierUrl is not None and not isinstance(identifierUrl, str):
            raise Exception("Invalid value for Identifier Url:" + identifierUrl)
        if not isinstance(cloudType, str):
            raise Exception("Invalid value for Cloud Type:" + cloudType)
        if not isinstance(updateApp, bool):
            raise Exception("Invalid value for Update App:" + str(updateApp))

        self.__credentials = credentials
        self.__providerRegistrationList = providerRegistrationList
        self.__subscriptionList = subscriptionList
        self.__allSubscriptions = allSubscriptions
        self.__tenantId = tenantId
        self.__identifierUrl = identifierUrl
        self.__cloudType = self.__getCloudType(cloudType)
        self.__updateApp = updateApp
        self.__userClientSecret = userClientSecret

    def __getCloudType(self, cloudType):
        if cloudType == AZURE_PUBLIC_CLOUD.name:
            return AZURE_PUBLIC_CLOUD
        elif cloudType == AZURE_CHINA_CLOUD.name:
            return AZURE_CHINA_CLOUD
        elif cloudType == AZURE_US_GOV_CLOUD.name:
            return AZURE_US_GOV_CLOUD
        elif cloudType == AZURE_GERMAN_CLOUD.name:
            return AZURE_GERMAN_CLOUD
        else: raise Exception("Could not find cloud Endpoints for cloud type: " + cloudType)


    def getSubscriptionList(self):
        return self.__subscriptionList

    def setSubscriptionList(self, subscriptionList):
        self.__subscriptionList = subscriptionList

    def getAllSubscriptions(self):
        return self.__allSubscriptions

    def setAllSubscriptions(self, allSubscriptions):
        self.__allSubscriptions = allSubscriptions

    def getTenantId(self):
        return self.__tenantId

    def setTenantId(self, tenantId):
        self.__tenantId = tenantId

    def getIdentifierUrl(self):
        return self.__identifierUrl

    def setIdentifierUrl(self, identifierUrl):
        self.__identifierUrl = identifierUrl

    def getCloudType(self):
        return self.__cloudType

    def setCloudType(self, cloudType):
        self.__cloudType = cloudType

    def getProviderRegistrationList(self):
        return self.__providerRegistrationList

    def setProviderRegistrationList(self, providerRegistrationList):
        self.__providerRegistrationList = providerRegistrationList

    def getCredentials(self):
        return self.__credentials

    def setCredentials(self, credentials):
        self.__credentials = credentials

    def getUserClientSecret(self):
        return self.__userClientSecret

    def setUserClientSecret(self, userClientSecret):
        self.__userClientSecret = userClientSecret

    def isUpdateApp(self):
        return self.__updateApp

    def setIsUpdateApp(self, updateApp):
        self.__updateApp = updateApp
