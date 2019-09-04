from azure.graphrbac import GraphRbacManagementClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.keyvault import KeyVaultClient
from azure.mgmt.resource import SubscriptionClient, ResourceManagementClient
from credentials.credentials_provider import ResourceCredentialsProvider
import logging as log
from azure.mgmt.authorization import AuthorizationManagementClient


class CommonUtil(object):
    def __init__(self, credentialsProvider):
        if not isinstance(credentialsProvider, ResourceCredentialsProvider):
            raise Exception("Invalid Credentials Provider")
        self.__credentialsProvider = credentialsProvider
        self.__subscriptionClient = SubscriptionClient(credentialsProvider.getManagementCredentials())
        self.__graphRbacClient = GraphRbacManagementClient(credentialsProvider.getGraphResourceCredentials(),
                                                           credentialsProvider.getConfig().getTenantId())
        self.__subscriptionClient = SubscriptionClient(credentialsProvider.getManagementCredentials())
        self.__identifierUrl = credentialsProvider.getConfig().getIdentifierUrl()
        self.__config = credentialsProvider.getConfig()
        self.__subScriptionList = None

    def getGraphRbacClient(self):
        return self.__graphRbacClient

    def getSubscriptionClient(self):
        return self.__subscriptionClient

    def getKeyVaultManagementClient(self, subscriptionId):
        return KeyVaultManagementClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)

    def getKeyVaultClient(self, subscriptionId):
        return KeyVaultClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)

    def getAuthorizationManagementClient(self, subscriptionId):
        return AuthorizationManagementClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)

    def getResourceManagementClient(self, subscriptionId):
        return ResourceManagementClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)

    def getSubscriptions(self):
        if self.__subScriptionList:
            return self.__subScriptionList

        knownSubscriptionList = self.__getKnownSubscriptionsAsList()
        subscriptionList = []
        if self.__config.getAllSubscriptions():
            subscriptionList = knownSubscriptionList
        else:
            configSubscriptionList = self.__config.getSubscriptionList()
            for configSubscription in configSubscriptionList:
                subscription = self.__getSubscriptionFromList(configSubscription, knownSubscriptionList)
                if subscription == None:
                    raise Exception(
                        "Subscription with name/id: " + configSubscription + " not found. Please ensure that the subscription exists and the user has Owner role access to it.")
                subscriptionList.append(subscription)
        log.info("Found " + str(len(subscriptionList)) + " Subscriptions: ")
        for subscription in subscriptionList:
            log.info(
                "Subscription Id: " + subscription.subscription_id + " Subscription Name: " + subscription.display_name)
            if str(subscription.state) != 'SubscriptionState.enabled':
                raise Exception("Subscription Id: " + subscription.subscription_id + " Subscription Name: " + subscription.display_name + " is not enabled")
        self.__subScriptionList = subscriptionList
        return subscriptionList

    def __getSubscriptionFromList(self, subscriptionNameOrId, subscriptionList):
        for subscription in subscriptionList:
            if subscription.display_name == subscriptionNameOrId or subscription.subscription_id == subscriptionNameOrId:
                return subscription
        return None

    def __getKnownSubscriptionsAsList(self):
        subscriptionList = []
        subscriptionIter = self.__subscriptionClient.subscriptions.list()

        for subscription in subscriptionIter:
            if str(subscription.state) == 'SubscriptionState.enabled':
                subscriptionList.append(subscription)
        return subscriptionList

    def __checkAppExists(self, identifierUrl):
        isinstance(self.__graphRbacClient, GraphRbacManagementClient)
        for app in self.__graphRbacClient.applications.list():
            if identifierUrl in app.identifier_uris:
                return app.app_id
        return None

    def getAppId(self):
        appId = self.__checkAppExists(self.__identifierUrl)
        return appId

    def getServicePrincipalId(self):
        appId = self.getAppId()
        if appId == None:
            raise Exception("Error Fetching App id")
        for servicePrincipal in self.__graphRbacClient.service_principals.list():
            if servicePrincipal.app_id == appId:
                return servicePrincipal.object_id
        log.info("Could not Find Service Principal for App Id")
        return None

    def getRoleDefinitionId(self, subscriptionId, authorizationClient, role):
        isinstance(authorizationClient, AuthorizationManagementClient)
        roleId = None
        for role in authorizationClient.role_definitions.list(scope="/subscriptions/" + subscriptionId,
                                                              filter="roleName eq '{}'".format(role)):
            roleId = role.id
        return roleId


    def getRoleAssignment(self, subscriptionId, principalId,  roleDefinitionId, authorizationClient):
        isinstance(authorizationClient, AuthorizationManagementClient)

        for roleAssignment in authorizationClient.role_assignments.list(scope="/subscriptions/" + subscriptionId):
            if roleAssignment.principal_id == principalId and roleAssignment.role_definition_id == roleDefinitionId:
                return roleAssignment
        return None

    def getRoleAssignmentForUserAndGroup(self, subscriptionId, principalId, userGroupObjectId, roleDefinitionId, authorizationClient):
        isinstance(authorizationClient, AuthorizationManagementClient)
        scope = "/subscriptions/" + subscriptionId
        for roleAssignment in authorizationClient.role_assignments.list(scope="/subscriptions/" + subscriptionId):
            if (roleAssignment.principal_id == principalId or roleAssignment.principal_id in userGroupObjectId) and roleAssignment.role_definition_id == roleDefinitionId:
                if roleAssignment.scope == scope:
                    return roleAssignment
                else:
                    log.info("Role assignment is present with invalid scope: "  + roleAssignment.scope)
        return None
