from credentials.credentials_provider import ResourceCredentialsProvider
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.authorization.v2018_01_01_preview.models import RoleAssignmentCreateParameters
from azure.graphrbac.models import ServicePrincipalCreateParameters
from common_util import CommonUtil
import uuid
import time
import logging as log


class RoleUtil(CommonUtil):
    def __init__(self, appId, credentialsProvider):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        super(RoleUtil, self).__init__(credentialsProvider)
        self.__credentialsProvider = credentialsProvider;
        self.__appId = appId
        self.__createServicePrincipalWithRetry(3)

    def __createServicePrincipalWithRetry(self, retry):
        if retry <= 0:
            raise Exception("Service Principal Creation Failed")
        servicePrincipalId = self.__getServicePrincipalId()
        if servicePrincipalId != None:
            log.info("Service principal exists : " + servicePrincipalId)
            return servicePrincipalId
        log.info("Attempting to create ServicePrincipal for appId: " + self.__appId + ". Retries Remaining: " + str(
            (retry - 1)))
        self.__createServicePrincipal()
        time.sleep(5)
        servicePrincipalId = self.__getServicePrincipalId()
        if servicePrincipalId == None:
            time.sleep(5)
            return self.__createServicePrincipalWithRetry(retry - 1)
        return servicePrincipalId

    def __createServicePrincipal(self):
        if self.getServicePrincipalId() == None:
            log.info("Creating service principal for appId " + self.__appId)
            servicePrincipalCreateParameters = ServicePrincipalCreateParameters(self.__appId, True, None);
            return self.getGraphRbacClient().service_principals.create(servicePrincipalCreateParameters)

    def makeRoleAssignments(self):
        subscriptionList = self.getSubscriptions()
        for subscription in subscriptionList:
            self.__assignReaderRoleToSubscription(subscription.subscription_id)

    def __assignReaderRoleToSubscription(self, subscriptionId):

        authorizationClient = AuthorizationManagementClient(self.__credentialsProvider.getManagementCredentials(),
                                                            subscriptionId)
        servicePrincipalId = self.getServicePrincipalId()
        if servicePrincipalId == None:
            raise Exception("Could not find servicePrincipal")

        roleDefinitionId = self.__getRoleDefinitionId(subscriptionId, authorizationClient)

        roleAssignment = self.__getRoleAssignments(subscriptionId, servicePrincipalId, roleDefinitionId,
                                                   authorizationClient)
        if roleAssignment != None:
            log.info("Role Assignment already Present for Subscription Id: " + subscriptionId);
            return roleAssignment

        roleAssignmentProperties = RoleAssignmentCreateParameters(role_definition_id=roleDefinitionId,
                                                                  principal_id=self.getServicePrincipalId())
        return self.__createRoleAssignmentWithRetry(subscriptionId, roleAssignmentProperties, authorizationClient)

    def __createRoleAssignmentWithRetry(self, subscriptionId, roleAssignmentProperties, authorizationClient):
        exception = None
        for i in range(1, 7):
            try:
                log.info("Creating role assignment in Subscription: " + subscriptionId + ". Attempt " + str(i))
                assignment = authorizationClient.role_assignments.create("/subscriptions/" + subscriptionId,
                                                                   str(uuid.uuid4()), roleAssignmentProperties)
                log.info("Successfully Created role assignment in Subscription: " + subscriptionId + " in Attempt " + str(i))
                return assignment
            except Exception as e:
                exception = e
                log.warn("Could not create role assignment for subscription" + subscriptionId + ", " + e.message)
                time.sleep(10)
        raise exception

    def __getRoleDefinitionId(self, subscriptionId, authorizationClient):
        roleId = self.getRoleDefinitionId(subscriptionId, authorizationClient, "Reader")
        if roleId == None:
            raise Exception("Could not find roleId for role: Reader")
        return roleId

    def __getRoleAssignments(self, subscriptionId, servicePrincipalId, roleDefinitionId, authorizationClient):
        isinstance(authorizationClient, AuthorizationManagementClient)
        return self.getRoleAssignment(subscriptionId, servicePrincipalId, roleDefinitionId, authorizationClient)

    def __getServicePrincipalId(self):
        for servicePrincipal in self.getGraphRbacClient().service_principals.list():
            if servicePrincipal.app_id == self.__appId:
                return servicePrincipal.object_id
        log.info("Could not Find Service Principal for App Id")
        return None
