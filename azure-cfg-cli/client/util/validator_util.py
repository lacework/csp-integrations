from common_util import CommonUtil
import logging as log
OWNER_ROLE = "Owner"

class ValidatorUtil(CommonUtil):

    def __init__(self, credentialsProvider):
        super(ValidatorUtil, self).__init__(credentialsProvider)
        self.__credentialsProvider = credentialsProvider


    def getUserGroupObjectIds(self, user_objectId):
        userGroupObjectIdList = []
        group_list= self.getGraphRbacClient().groups.list()
        for group in group_list:
            group_members = self.getGraphRbacClient().groups.get_group_members(group.object_id)
            for member in group_members:
                if member.object_id == user_objectId:
                    userGroupObjectIdList.append(group.object_id)
                    break
        return userGroupObjectIdList

    def validateUserPermissions(self):
        objectId = self.__credentialsProvider.getObjectId()
        userGroupObjectIdList=  self.getUserGroupObjectIds(objectId)
        for subscription in self.getSubscriptions():
            try:
                authorizationManagementClient = self.getAuthorizationManagementClient(subscription.subscription_id);
                roleDefinitionId = self.getRoleDefinitionId(subscription.subscription_id, authorizationManagementClient,
                                                            OWNER_ROLE)
                objectId = self.__credentialsProvider.getObjectId()
                roleAssignment = self.getRoleAssignmentForUserAndGroup(subscription.subscription_id, objectId, userGroupObjectIdList, roleDefinitionId,
                                                        authorizationManagementClient)
                if roleAssignment == None:
                    raise Exception(
                        "User does not have owner role on subscription Id: " + subscription.subscription_id + " Name: " + subscription.display_name)
            except Exception as e:
                log.error("User does not have owner role on subscription Id: " + subscription.subscription_id + " Name: " + subscription.display_name)
                raise e


