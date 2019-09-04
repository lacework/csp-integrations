
from client_helper import ClientHelper

API_LIST = [
    "serviceusage.googleapis.com",
    "iam.googleapis.com",
    "cloudkms.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "dns.googleapis.com",
    "sqladmin.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "storage-component.googleapis.com"
]
class Config(object):

    def __init__(self, credentials, project_id,isCloudShell, id_type, id, enable_api, service_account_project_id, set_iam_policy):
        self.__credentials = credentials
        self.__project_id = project_id
        self.__isCloudShell = isCloudShell
        self.__httpClient =  ClientHelper(credentials)
        self.__id_type = id_type
        self.__id = id
        self.__enable_api = enable_api
        self.__service_account_project_id = service_account_project_id
        self.__set_iam_policy = set_iam_policy
        self.__api_list = API_LIST
        self.__ORG_VIEWER_ROLE =  "roles/resourcemanager.organizationViewer"
        self.__VIEWER_ROLE = "roles/viewer"
        self.__SECURITY_REVIEWER = "roles/iam.securityReviewer"


    # Input Service Account Email
    def getServiceAccountEmail(self):
        return self.__credentials.service_account_email

    # Input Service Account Email
    def getUserServiceAccountProjectId(self):
        if self.__project_id == None:
            raise Exception("Project Id not in service account credentials File")
        return self.__project_id

    def getHttpClient(self):
        return self.__httpClient

    def getIdType(self):
        return self.__id_type

    def setIdType(self, id_type):
        self.__id_type = id_type

    def getId(self):
        return self.__id

    def setId(self, id):
        self.__id = id

    def getEnableApi(self):
        return self.__enable_api

    def setEnableApi(self, enable_api):
        self.__enable_api = enable_api

    def getServiceAccountProjectId(self):
        return self.__service_account_project_id

    def setServiceAccountProjectId(self, service_account_project_id):
        self.__service_account_project_id = service_account_project_id

    def getSetIAMPolicy(self):
        return self.__set_iam_policy

    def setSetIAMPolicy(self, set_iam_policy):
        self.__set_iam_policy = set_iam_policy

    def getApiList(self):
        return self.__api_list

    def isCloudShell(self):
        return self.__isCloudShell

    def getServiceAccountRoleList(self):
        if self.__id_type == None:
            return []
        if self.__id_type == "ORGANIZATION":
            return [self.__ORG_VIEWER_ROLE, self.__VIEWER_ROLE, self.__SECURITY_REVIEWER]
        else:
            return [self.__VIEWER_ROLE, self.__SECURITY_REVIEWER]

