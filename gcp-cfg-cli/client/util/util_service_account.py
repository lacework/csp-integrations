import logging
import time
SERVICE_ACCOUNTS = "https://iam.googleapis.com/v1/projects/%projectId/serviceAccounts"
SERVICE_ACCOUNTS_KEYS = "https://iam.googleapis.com/v1/projects/%projectId/serviceAccounts/%serviceAccountId/keys"
org_roles = ["roles/owner","roles/resourcemanager.organizationAdmin"]
project_roles = ["roles/owner"]

HTTP_GET_METHOD = "GET"
HTTP_POST_METHOD = "POST"
SERVICE_ACCOUNT_ID = "lacework-cfg-sa"


from util_base import UtilBase


class UtilServiceAccount(UtilBase):

    def __init__(self, config):
        UtilBase.__init__(self, config)

    def validateUserServiceAccountRole(self):
        return self.__validateServiceAccountRole(self.config.getServiceAccountEmail())

    def __validateServiceAccountRole(self, serviceAccountEmail):
        policy = self.getIAMPolicy()
        memberName = "serviceAccount:" + serviceAccountEmail
        if 'bindings' not in policy:
            return False
        roleList = []
        for binding in policy['bindings']:
            if memberName in binding['members']:
                roleList.append(binding['role'])

        requiredRoles = org_roles if self.config.getIdType() == "ORGANIZATION" else project_roles

        for role in requiredRoles:
            if role not in roleList:
                logging.error("Required role :" + role + " not assigned to Service Account. Service Account Does not have sufficient privileges")
                return False
        return True

    def getServiceAccountIfExists(self):
        service_account_list = self.getServiceAccountList()
        for service_account in service_account_list:
            service_account_id = str(service_account['email']).split("@",1)[0]
            if service_account_id == SERVICE_ACCOUNT_ID:
                return service_account
        return False

    def getServiceAccountInProjectIfExists(self, projectId):
        service_account_list = self.getServiceAccountsInProject(projectId)
        for service_account in service_account_list:
            service_account_id = str(service_account['email']).split("@",1)[0]
            if service_account_id == SERVICE_ACCOUNT_ID:
                return service_account
        return False


    def getServiceAccountInProjectRecursive(self, projectId, i=1):
        service_account = self.getServiceAccountInProjectIfExists(projectId)
        if not service_account:
            if i>10:
                raise Exception("Could not find service account after creation")
            time.sleep(3)
            return self.getServiceAccountInProjectRecursive(projectId, i+1)
        return service_account


    def getServiceAccountList(self):
        projectList = self.getProjectList()
        service_account_list = []
        for project in projectList:
            projectId = str(project['projectId'])
            service_account_list = service_account_list + self.getServiceAccountsInProject(projectId)
        return service_account_list

    def getServiceAccountsInProject(self, projectId):
        service_account_list = []
        service_account_data = self.config.getHttpClient().make_request(HTTP_GET_METHOD, SERVICE_ACCOUNTS, projectId, None)
        if service_account_data['isError']:
            raise Exception("Error fetching Service Accounts \n" + str(service_account_data['defaultErrorObject']))
        if 'accounts' in service_account_data['data']:
            service_account_list = service_account_data['data']['accounts']
        return service_account_list


    def createServiceAccountIfNotExists(self):
        projectId = self.config.getServiceAccountProjectId()
        service_account = self.getServiceAccountInProjectIfExists(projectId)
        if service_account:
            logging.info("Service account exists Skipping Service account Key Creation")
            return service_account, None
        body = {
            "accountId": SERVICE_ACCOUNT_ID,
            "serviceAccount":{
                "displayName": "Lacework SA Audit"
            }
        }

        response = self.config.getHttpClient().make_request(HTTP_POST_METHOD, SERVICE_ACCOUNTS, projectId, body)
        if response['isError']:
            raise Exception("Error creating a Service Account \n" + str(response['defaultErrorObject']))
        logging.info("Created Service account.")
        logging.info("Creating Service account Key.")
        return self.createServiceAccountKey()
        # return response['data']

    def getServiceAccountKeys(self, projectId, serviceAccountId):
        service_account_keys_url = SERVICE_ACCOUNTS_KEYS.replace("%serviceAccountId", serviceAccountId)
        service_account_keys = self.config.getHttpClient().make_request(HTTP_GET_METHOD, service_account_keys_url, projectId, None)
        if service_account_keys['isError']:
            raise Exception("Error Fetching Service Account Key " + str(service_account_keys['defaultErrorObject']))
        service_account_key_list = []
        if 'keys' in  service_account_keys['data']:
            service_account_key_list = service_account_keys['data']['keys']
        return service_account_key_list

    def createServiceAccountKey(self):
        projectId = self.config.getServiceAccountProjectId()
        service_account = self.getServiceAccountInProjectRecursive(projectId)
        serviceAccountId = service_account['email']
        body=  {
            "keyAlgorithm": "KEY_ALG_RSA_2048"
        };
        service_account_keys_url = SERVICE_ACCOUNTS_KEYS.replace("%serviceAccountId", serviceAccountId)
        service_account_key = self.config.getHttpClient().make_request(HTTP_POST_METHOD, service_account_keys_url,
                                                                        projectId, body)
        if service_account_key['isError']:
            raise Exception("Error Creating Service Account Key " + str(service_account_key['defaultErrorObject']))
        logging.info("Successfully created service account Key")
        return service_account, service_account_key['data']