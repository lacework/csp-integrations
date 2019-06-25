from common_util import CommonUtil
import logging as log
OWNER_ROLE = "Owner"

class ValidatorUtil(CommonUtil):

    def __init__(self, credentialsProvider):
        super(ValidatorUtil, self).__init__(credentialsProvider)
        self.__credentialsProvider = credentialsProvider

    def validateUserPermissions(self):
        for subscription in self.getSubscriptions():
            try:
                authorizationManagementClient = self.getAuthorizationManagementClient(subscription.subscription_id);
                roleDefinitionId = self.getRoleDefinitionId(subscription.subscription_id, authorizationManagementClient,
                                                            OWNER_ROLE)
                objectId = self.__credentialsProvider.getObjectId()
                roleAssignment = self.getRoleAssignment(subscription.subscription_id, objectId, roleDefinitionId,
                                                        authorizationManagementClient)
                if roleAssignment == None:
                    raise Exception(
                        "User does not have owner role on subscription Id: " + subscription.subscription_id + " Name: " + subscription.display_name)
            except Exception as e:
                log.error("User does not have owner role on subscription Id: " + subscription.subscription_id + " Name: " + subscription.display_name)
                raise e


