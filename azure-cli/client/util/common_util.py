import logging as log

from azure.graphrbac import GraphRbacManagementClient
from azure.keyvault import KeyVaultClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.eventgrid import EventGridManagementClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.monitor.monitor_management_client import MonitorManagementClient
from azure.mgmt.resource import SubscriptionClient, ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient

from credentials.credentials_provider import ResourceCredentialsProvider


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
        self.__subscriptionList = None
        self.__subscriptionClient = SubscriptionClient(credentialsProvider.getManagementCredentials())

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

    def getStorageManagementClient(self, subscriptionId):
        return StorageManagementClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)

    def getEventGridManagementClient(self, subscriptionId):
        return EventGridManagementClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)

    def getMonitorManagementClient(self, subscriptionId):
        return MonitorManagementClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)

    def getSubscriptionClient(self):
        return self.__subscriptionClient

    def getSubscriptions(self):
        if self.__subscriptionList:
            return self.__subscriptionList

        knownSubscriptionList = self.__getKnownSubscriptionsAsList()
        subscriptionList = []
        configSubscriptionList = self.__config.getSubscriptionList()
        for configSubscription in configSubscriptionList:
            subscription = self.__getSubscriptionFromList(configSubscription, knownSubscriptionList)
            if subscription is None:
                raise Exception(
                    "Subscription with name/id: " + configSubscription + " not found. Please ensure that the subscription exists and the user has Owner role access to it.")
            subscriptionList.append(subscription)
        log.info("Found " + str(len(subscriptionList)) + " Subscriptions: ")
        for subscription in subscriptionList:
            log.info(
                "Subscription Id: " + subscription.subscription_id + " Subscription Name: " + subscription.display_name)
            if str(subscription.state) != 'SubscriptionState.enabled':
                raise Exception("Subscription Id: " + subscription.subscription_id + " Subscription Name: " + subscription.display_name + " is not enabled")
        self.__subscriptionList = subscriptionList
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

    def getAppObjId(self):
        isinstance(self.__graphRbacClient, GraphRbacManagementClient)
        for app in self.__graphRbacClient.applications.list():
            if self.__identifierUrl in app.identifier_uris:
                return app.object_id
        return None

    def getAppId(self):
        appId = self.__checkAppExists(self.__identifierUrl)
        return appId

    def getServicePrincipalId(self):
        appId = self.getAppId()
        if appId is None:
            return None
        for servicePrincipal in self.__graphRbacClient.service_principals.list(filter="appId eq '{}'".format(appId)):
            return servicePrincipal.object_id
        log.info("Could not Find Service Principal for App Id")
        return None

    def getRoleDefinitionId(self, subscriptionId, authorizationClient, roleName):
        isinstance(authorizationClient, AuthorizationManagementClient)
        roleId = None
        for role in authorizationClient.role_definitions.list(scope="/subscriptions/" + subscriptionId,
                                                              filter="roleName eq '{}'".format(roleName)):
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