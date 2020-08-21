import logging
import logging as log
import time
import uuid

from azure.mgmt.authorization.v2018_01_01_preview import AuthorizationManagementClient
from azure.mgmt.authorization.v2018_01_01_preview.models import RoleAssignmentCreateParameters, RoleDefinition, Permission
from msrestazure.azure_exceptions import CloudError

from common_util import CommonUtil
from credentials.credentials_provider import ResourceCredentialsProvider


class RoleUtil(CommonUtil):
    def __init__(self, appId, credentialsProvider, createServicePrincipal=True):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        super(RoleUtil, self).__init__(credentialsProvider)
        self.__credentialsProvider = credentialsProvider
        self.__appId = appId

        if createServicePrincipal:
            self.__createServicePrincipalWithRetry(3)

    def __createServicePrincipalWithRetry(self, retry):
        if retry <= 0:
            raise Exception("Service Principal Creation Failed")
        servicePrincipalId = self.__getServicePrincipalId()
        if servicePrincipalId is not None:
            log.info("Service principal exists : " + servicePrincipalId)
            return servicePrincipalId

        appId = "" if self.__appId is None else self.__appId
        log.info("Attempting to create ServicePrincipal for appId: " + appId + ". Retries Remaining: " + str((retry - 1)))
        self.__createServicePrincipal()
        servicePrincipalId = self.__getServicePrincipalId()
        if servicePrincipalId is None:
            time.sleep(5)
            return self.__createServicePrincipalWithRetry(retry - 1)
        return servicePrincipalId

    def __createServicePrincipal(self):
        if self.__appId is None:
            return None

        if self.getServicePrincipalId() is None:
            log.info("Creating service principal for appId " + self.__appId)
            return self.getGraphRbacClient().service_principals.create({
                'app_id': self.__appId,
                'account_enabled': True
            })

    def deleteRoleDefinition(self, roleName, subscriptionId):
        authorizationClient = AuthorizationManagementClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)
        roleDefinitionId = self.getRoleDefinitionId(subscriptionId, authorizationClient, roleName)

        if roleDefinitionId is None:
            log.info("Role Definition already not present for Subscription Id: " + subscriptionId)
            return

        scope = "/subscriptions/{}".format(subscriptionId)

        try:
            authorizationClient.role_definitions.delete(scope, roleDefinitionId)
        except CloudError:
            roleDefinitionId = roleDefinitionId.split('/')[-1]
            authorizationClient.role_definitions.delete(scope, roleDefinitionId)

    def makeRoleAssignments(self):
        subscriptionList = self.getSubscriptions()
        for subscription in subscriptionList:
            self.__assignReaderRoleToSubscription(subscription.subscription_id)

    def makeRoleAssignment(self, roleName, subscriptionId):
        authClient = self.getAuthorizationManagementClient(subscriptionId)
        roleDefinitionId = self.__getRoleIdWithRetry(roleName, subscriptionId, authClient, 3)
        self.__assignRoleToSubscription(roleDefinitionId, subscriptionId)

    def __getRoleIdWithRetry(self, roleName, subscriptionId, authClient, retry):
        if retry <= 0:
            logging.debug("Custom Role Definition not found.")
            return None

        roleDefinitionId = self.getRoleDefinitionId(subscriptionId, authClient, roleName)

        if roleDefinitionId is not None:
            return roleDefinitionId

        time.sleep(5)
        return self.__getRoleIdWithRetry(roleName, subscriptionId, authClient, retry - 1)

    def removeRoleAssignment(self, roleName, subscriptionId):
        self.__unassignRoleFromSubscription(roleName, subscriptionId)

    def deleteServicePrincipal(self):
        servicePrincipalId = self.getServicePrincipalId()

        if servicePrincipalId is None:
            logging.debug("Service Principal not found")
            return

        self.getGraphRbacClient().service_principals.delete(servicePrincipalId)

    def createCustomRoleDefinition(self, roleName, subscriptionId):
        authorizationClient = AuthorizationManagementClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)

        roleDefinitionId = self.getRoleDefinitionId(subscriptionId, authorizationClient, roleName)
        if roleDefinitionId is not None:
            return roleDefinitionId

        servicePrincipalId = self.getServicePrincipalId()
        if servicePrincipalId is None:
            raise Exception("Could not find servicePrincipal")

        scope = "/subscriptions/{}".format(subscriptionId)

        roleDefId = str(uuid.uuid4())

        permisison = Permission(
            actions=[
                "Microsoft.Resources/subscriptions/resourceGroups/read",
                "Microsoft.Storage/storageAccounts/read",
                "Microsoft.Storage/storageAccounts/blobServices/containers/read",
                "Microsoft.Storage/storageAccounts/queueServices/queues/read",
                "Microsoft.EventGrid/eventSubscriptions/read",
                "Microsoft.Storage/storageAccounts/listkeys/action"
            ],
            data_actions=[
                "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
                "Microsoft.Storage/storageAccounts/queueServices/queues/messages/read",
                "Microsoft.Storage/storageAccounts/queueServices/queues/messages/delete"
            ]
        )

        roleDefinition = RoleDefinition(
            role_name=roleName,
            description="Monitors Activity Log",
            type="CustomRole",
            permissions=[permisison],
            assignable_scopes=[scope]
        )

        roleDefinition.name = roleDefId

        authorizationClient.role_definitions.create_or_update(scope, roleDefId, roleDefinition)
        return roleDefId

    def __assignRoleToSubscription(self, roleDefinitionId, subscriptionId):
        servicePrincipalId = self.getServicePrincipalId()
        if servicePrincipalId is None:
            raise Exception("Could not find Service Principal")

        authorizationClient = AuthorizationManagementClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)

        roleAssignment = self.__getRoleAssignments(subscriptionId, servicePrincipalId, roleDefinitionId, authorizationClient)
        if roleAssignment is not None:
            log.info("Role Assignment already present for Subscription Id: " + subscriptionId)
            return roleAssignment

        roleAssignmentProperties = RoleAssignmentCreateParameters(
            role_definition_id=roleDefinitionId,
            principal_id=self.getServicePrincipalId()
        )

        return self.__createRoleAssignmentWithRetry(subscriptionId, roleAssignmentProperties, authorizationClient)

    def __unassignRoleFromSubscription(self, roleName, subscriptionId):
        servicePrincipalId = self.getServicePrincipalId()
        if servicePrincipalId is None:
            logging.debug("Could not find Service Principal")
            return

        authorizationClient = AuthorizationManagementClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)
        roleDefinitionId = self.getRoleDefinitionId(subscriptionId, authorizationClient, roleName)

        roleAssignment = self.__getRoleAssignments(subscriptionId, servicePrincipalId, roleDefinitionId, authorizationClient)
        if roleAssignment is None:
            log.info("Role Assignment already not present for Subscription Id: " + subscriptionId)
            return

        scope = "/subscriptions/{}".format(subscriptionId)
        authorizationClient.role_assignments.delete(scope, roleAssignment.name)

    def __assignReaderRoleToSubscription(self, subscriptionId):

        authorizationClient = AuthorizationManagementClient(self.__credentialsProvider.getManagementCredentials(), subscriptionId)
        roleDefinitionId = self.__getReaderRoleDefinitionId(subscriptionId, authorizationClient)

        self.__assignRoleToSubscription(roleDefinitionId, subscriptionId)

    def __createRoleAssignmentWithRetry(self, subscriptionId, roleAssignmentProperties, authorizationClient):
        exception = None
        scope = "/subscriptions/{}".format(subscriptionId)
        for i in range(1, 7):
            try:
                log.info("Creating role assignment in Subscription: " + subscriptionId + ". Attempt " + str(i))
                assignment = authorizationClient.role_assignments.create(scope, str(uuid.uuid4()), roleAssignmentProperties)
                log.info("Successfully Created role assignment in Subscription: " + subscriptionId + " in Attempt " + str(i))
                return assignment
            except Exception as e:
                exception = e
                log.warn("Could not create role assignment for subscription" + subscriptionId + ", " + e.message)
                time.sleep(10)
        raise exception

    def __getReaderRoleDefinitionId(self, subscriptionId, authorizationClient):
        roleId = self.getRoleDefinitionId(subscriptionId, authorizationClient, "Reader")
        if roleId is None:
            raise Exception("Could not find roleId for role: Reader")
        return roleId

    def __getRoleAssignments(self, subscriptionId, servicePrincipalId, roleDefinitionId, authorizationClient):
        isinstance(authorizationClient, AuthorizationManagementClient)
        return self.getRoleAssignment(subscriptionId, servicePrincipalId, roleDefinitionId, authorizationClient)

    def __getServicePrincipalId(self):
        if self.__appId is None:
            return None

        for servicePrincipal in self.getGraphRbacClient().service_principals.list():
            if servicePrincipal.app_id == self.__appId:
                return servicePrincipal.object_id
        log.info("Could not Find Service Principal for App Id")
        return None
