import logging
ORG_VIEWER_ROLE =  "roles/resourcemanager.organizationViewer"
VIEWER_ROLE = "roles/viewer"
# {u'bindings': [{u'role': u'roles/axt.admin', u'members': [u'user:dudhaneviraj@gmail.com']}, {u'role': u'roles/container.admin', u'members': [u'serviceAccount:serviceaccountvirajlaceworkorg@virajlaceworktestproject.iam.gserviceaccount.com']}, {u'role': u'roles/owner', u'members': [u'serviceAccount:serviceaccountvirajlaceworkorg@virajlaceworktestproject.iam.gserviceaccount.com', u'user:divyang@virajlacework.com', u'user:dudhaneviraj@virajlacework.com']}, {u'role': u'roles/resourcemanager.organizationAdmin', u'members': [u'serviceAccount:serviceaccountvirajlaceworkorg@virajlaceworktestproject.iam.gserviceaccount.com', u'user:divyang@virajlacework.com', u'user:dudhaneviraj@virajlacework.com']}, {u'role': u'roles/resourcemanager.organizationViewer', u'members': [u'serviceAccount:serviceaccountvirajlaceworkorg@virajlaceworktestproject.iam.gserviceaccount.com']}, {u'role': u'roles/viewer', u'members': [u'serviceAccount:serviceaccountvirajlaceworkorg@virajlaceworktestproject.iam.gserviceaccount.com']}], u'etag': u'BwV9ZFLHMJo='}
GET_ORG_IAM_POLICY="https://cloudresourcemanager.googleapis.com/v1/organizations/%orgId:getIamPolicy"
GET_PROJECT_IAM_POLICY="https://cloudresourcemanager.googleapis.com/v1/projects/%projectId:getIamPolicy"
SET_ORG_IAM_POLICY="https://cloudresourcemanager.googleapis.com/v1/organizations/%orgId:setIamPolicy"
SET_PROJECT_IAM_POLICY="https://cloudresourcemanager.googleapis.com/v1/projects/%projectId:setIamPolicy"
org_roles = ["roles/owner","roles/resourcemanager.organizationAdmin"]
project_roles = ["roles/owner"]

HTTP_GET_METHOD = "GET"
HTTP_POST_METHOD = "POST"
SERVICE_ACCOUNT_ID = "lacework-cfg-sa"
from util_base import UtilBase

class UtilIAM(UtilBase):

    def __init__(self, config):
        UtilBase.__init__(self, config)

    def getOrgIAMPolicy(self):
        if self.config.getIdType() != "ORGANIZATION":
            raise Exception("Config is not of type organization")
        projectId = self.config.getServiceAccountProjectId()
        url = GET_ORG_IAM_POLICY.replace("%orgId", self.config.getId())
        response = self.config.getHttpClient().make_request(HTTP_POST_METHOD, url, projectId, None)
        if response['isError']:
            raise Exception("Error fetching org Iam Policy \n" + str(response['defaultErrorObject']))
        return response['data']

    def getProjectIAMPolicy(self):
        if self.config.getIdType() != "PROJECT":
            raise Exception("Config is not of type PROJECT")
        projectId = self.config.getServiceAccountProjectId()
        response = self.config.getHttpClient().make_request(HTTP_POST_METHOD, GET_PROJECT_IAM_POLICY, projectId, None)
        if response['isError']:
            raise Exception("Error fetching project Iam Policy \n" + str(response['defaultErrorObject']))
        return response['data']

    def getIAMPolicy(self):
        return self.getOrgIAMPolicy() if (self.config.getIdType() == "ORGANIZATION") else self.getProjectIAMPolicy()

    def setOrgIAMPolicy(self, body):
        if self.config.getIdType() != "ORGANIZATION":
            raise Exception("Config is not of type organization")
        projectId = self.config.getServiceAccountProjectId()
        url = SET_ORG_IAM_POLICY.replace("%orgId", self.config.getId())
        response = self.config.getHttpClient().make_request(HTTP_POST_METHOD, url, projectId, body)
        if response['isError']:
            raise Exception("Error setting org Iam Policy \n" + str(response['defaultErrorObject']))
        return response['data']

    def setProjectIAMPolicy(self, body):
        if self.config.getIdType() != "PROJECT":
            raise Exception("Config is not of type PROJECT")
        projectId = self.config.getServiceAccountProjectId()
        response = self.config.getHttpClient().make_request(HTTP_POST_METHOD, SET_PROJECT_IAM_POLICY, projectId, body)
        if response['isError']:
            raise Exception("Error setting project Iam Policy \n" + str(response['defaultErrorObject']))
        return response['data']

    def setIAMPolicy(self, serviceAccountEmail):
        if not self.config.getSetIAMPolicy():
            return
        policy = self.getIAMPolicy()
        bindings = policy.get('bindings')
        if bindings == None:
            bindings = []
            policy['bindings'] = bindings

        for role in self.config.getServiceAccountRoleList():
            self.__addMemberToRole(bindings, role, serviceAccountEmail)

        data = {
            "policy": policy,
        }
        return self.setOrgIAMPolicy(data) if (self.config.getIdType() == "ORGANIZATION") else self.setProjectIAMPolicy(data)

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