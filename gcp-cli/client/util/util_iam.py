import logging
GET_ORG_IAM_POLICY="https://cloudresourcemanager.googleapis.com/v1/organizations/%orgId:getIamPolicy"
GET_PROJECT_IAM_POLICY="https://cloudresourcemanager.googleapis.com/v1/projects/%projectId:getIamPolicy"
GET_FOLDER_IAM_POLICY="https://cloudresourcemanager.googleapis.com/v2/folders/%folderName:getIamPolicy"
SET_ORG_IAM_POLICY="https://cloudresourcemanager.googleapis.com/v1/organizations/%orgId:setIamPolicy"
SET_PROJECT_IAM_POLICY="https://cloudresourcemanager.googleapis.com/v1/projects/%projectId:setIamPolicy"
SET_FOLDER_IAM_POLICY="https://cloudresourcemanager.googleapis.com/v2/folders/%folderName:setIamPolicy"
BUCKET_IAM_POLICY="https://www.googleapis.com/storage/v1/b/%bucketName/iam"

TEST_PROJECT_PERMISSIONS="https://cloudresourcemanager.googleapis.com/v1/projects/%projectId:testIamPermissions"
TEST_ORG_PERMISSIONS="https://cloudresourcemanager.googleapis.com/v1/organizations/%orgId:testIamPermissions"

HTTP_GET_METHOD = "GET"
HTTP_POST_METHOD = "POST"
HTTP_PUT_METHOD = "PUT"
SERVICE_ACCOUNT_ID = "lacework-cfg-sa"
from util_base import UtilBase
import time
SLEEP_SECS = 15

class UtilIAM(UtilBase):
    def __init__(self):
        UtilBase.__init__(self)

    def getFolderIAMPolicy(self, folderName):
        url = GET_FOLDER_IAM_POLICY.replace("%folderName", folderName)
        response = self.getHttpClient().make_request(HTTP_POST_METHOD, url, None, None)
        if response['isError']:
            raise Exception("Error fetching folder Iam Policy \n" + str(response['defaultErrorObject']))
        return response['data']

    def getOrgIAMPolicy(self, orgId):
        url = GET_ORG_IAM_POLICY.replace("%orgId", orgId)
        response = self.getHttpClient().make_request(HTTP_POST_METHOD, url, None, None)
        if response['isError']:
            raise Exception("Error fetching org Iam Policy \n" + str(response['defaultErrorObject']))
        return response['data']

    def getProjectIAMPolicy(self, projectId):
        response = self.getHttpClient().make_request(HTTP_POST_METHOD, GET_PROJECT_IAM_POLICY, projectId, None)
        if response['isError']:
            raise Exception("Error fetching project Iam Policy \n" + str(response['defaultErrorObject']))
        return response['data']

    def getIAMPolicy(self, id, idType):
        if (idType == "FOLDER"):
            return self.getFolderIAMPolicy(id)
        return self.getOrgIAMPolicy(id) if (idType == "ORGANIZATION") else self.getProjectIAMPolicy(id)

    def setFolderIAMPolicy(self, folderName, body):
        url = SET_FOLDER_IAM_POLICY.replace("%folderName", folderName)
        return self.getHttpClient().make_request(HTTP_POST_METHOD, url, None, body)

    def setOrgIAMPolicy(self, orgId, body):
        url = SET_ORG_IAM_POLICY.replace("%orgId", orgId)
        return self.getHttpClient().make_request(HTTP_POST_METHOD, url, None, body)

    def setProjectIAMPolicy(self, projectId, body):
        return self.getHttpClient().make_request(HTTP_POST_METHOD, SET_PROJECT_IAM_POLICY, projectId, body)

    def setIAMPolicy(self, id, serviceAccountEmail, idType, customRoles):
        for i in range(3):
            logging.info("Getting existing IAM policies for " + id)
            policy = self.getIAMPolicy(id, idType)
            bindings = policy.get('bindings')
            if bindings == None:
                bindings = []
                policy['bindings'] = bindings

            for role in customRoles:
                logging.info("Adding role " + role + " for " + serviceAccountEmail + " in " + id)
                self.__addMemberToRole(bindings, role, serviceAccountEmail)

            data = {
                "policy": policy,
            }

            logging.info("Setting the newly created IAM policies for " + id)
            if (idType == "FOLDER"):
                response = self.setFolderIAMPolicy(id, data)
            else:
                response = self.setOrgIAMPolicy(id, data) if (idType == "ORGANIZATION") else self.setProjectIAMPolicy(id, data)

            if response['isError']:
                if "There were concurrent policy changes. " in response['defaultErrorObject']['error']:
                    logging.info("There were concurrent Policy changes, retrying in " + str(SLEEP_SECS) + " seconds.")
                    time.sleep(SLEEP_SECS)
                    continue
                else:
                    raise Exception("Error setting " + idType + " Iam Policy \n" + str(response['defaultErrorObject']))
            else:
                return response['data']


    def removeIamPolicy(self, id, serviceAccountEmail, idType, customRoles):
        for i in range(3):
            logging.info("Getting existing IAM policies for " + id)
            policy = self.getIAMPolicy(id, idType)
            bindings = policy.get('bindings')
            if bindings == None:
                return None

            for role in customRoles:
                logging.info("Removing role " + role + " for " + serviceAccountEmail + " in " + id)
                self.__removeMemberToRole(bindings, role, serviceAccountEmail)

            data = {
                "policy": policy,
            }

            logging.info("Setting the newly created IAM policies for " + id)
            if (idType == "FOLDER"):
                response = self.setFolderIAMPolicy(id, data)
            else:
                response = self.setOrgIAMPolicy(id, data) if (idType == "ORGANIZATION") else self.setProjectIAMPolicy(id, data)

            if response['isError']:
                if "There were concurrent policy changes. " in response['defaultErrorObject']['error']:
                    logging.info("There were concurrent Policy changes, retrying in " + str(SLEEP_SECS) + " seconds.")
                    time.sleep(SLEEP_SECS)
                    continue
                else:
                    raise Exception("Error setting " + idType + " Iam Policy \n" + str(response['defaultErrorObject']))
            else:
                return response['data']

    def __removeMemberToRole(self, bindings, role, member):
        memberName = "serviceAccount:"+member
        for roleobj in bindings:
            if roleobj['role'] == role:
                if memberName in roleobj['members']:
                    roleobj['members'].remove(memberName)

    def __addMemberToRole(self, bindings, role, member):
        roleFound = False
        memberName = "serviceAccount:"+member
        for roleobj in bindings:
            if roleobj['role'] == role:
                roleFound = True
                if memberName not in roleobj['members']:
                    roleobj['members'].append(memberName)
        if not roleFound:
            bindings.append({
                "role": role,
                "members": [memberName]
            })

    def getBucketIAMPolicy(self, bucketName):
        url = BUCKET_IAM_POLICY.replace("%bucketName", bucketName)
        response = self.getHttpClient().make_request(HTTP_GET_METHOD, url, None, None)
        if response['isError']:
            raise Exception("Error fetching bucket Iam Policy \n" + str(response['defaultErrorObject']))
        return response['data']

    def setBucketIAMPolicy(self, bucketName, serviceAccountEmail, customRoles):
        for i in range(3):
            logging.info("Getting existing IAM policies for " + bucketName)
            policy = self.getBucketIAMPolicy(bucketName)
            bindings = policy.get('bindings')
            if bindings == None:
                bindings = []
                policy['bindings'] = bindings

            for role in customRoles:
                logging.info("Adding role " + role + " for " + serviceAccountEmail + " in " + bucketName)
                self.__addMemberToRole(bindings, role, serviceAccountEmail)

            data = policy

            logging.info("Setting the newly created IAM policies for " + bucketName)
            url = BUCKET_IAM_POLICY.replace("%bucketName", bucketName)
            response = self.getHttpClient().make_request(HTTP_PUT_METHOD, url, None, data, {"Content-Type":"application/json"})

            if response['isError']:
                if "There were concurrent policy changes. " in response['defaultErrorObject']['error']:
                    logging.info("There were concurrent Policy changes, retrying in " + str(SLEEP_SECS) + " seconds.")
                    time.sleep(SLEEP_SECS)
                    continue
                else:
                    raise Exception("Error setting bucket Iam Policy \n" + str(response['defaultErrorObject']))
            else:
                return response['data']


    def testProjectPermissions(self, projectId, permissions):
        body = {
            "permissions": permissions
        }
        response = self.getHttpClient().make_request(HTTP_POST_METHOD, TEST_PROJECT_PERMISSIONS, projectId, body)
        if response['isError']:
            raise Exception("Error testing project Iam Policy \n" + str(response['defaultErrorObject']))
        if "permissions" not in response['data']:
            return permissions
        return list(set(permissions) - set(response['data']['permissions']))

    def testOrgPermissions(self, orgId, permissions):
        body = {
            "permissions": permissions
        }
        url = TEST_ORG_PERMISSIONS.replace("%orgId", orgId)
        response = self.getHttpClient().make_request(HTTP_POST_METHOD, url, None, body)
        if response['isError']:
            raise Exception("Error testing project Iam Policy \n" + str(response['defaultErrorObject']))
        if "permissions" not in response['data']:
            return permissions
        return list(set(permissions) - set(response['data']['permissions']))
