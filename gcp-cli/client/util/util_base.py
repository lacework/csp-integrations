from builtins import str
from builtins import object
from client.config.auth_helper import AuthHelper
from client.config.client_helper import ClientHelper
import logging
PROJECT_SERVICE_URL = "https://www.googleapis.com/storage/v1/projects/%projectId/serviceAccount"
PROJECT_ID_LIST_URL = "https://cloudresourcemanager.googleapis.com/v1/projects"
PROJECT_ID_DESC_URL = "https://cloudresourcemanager.googleapis.com/v1/projects/%projectId"
FOLDER_ID_LIST_URL = "https://cloudresourcemanager.googleapis.com/v2/folders"
BUCKET_LIST_URL = "https://www.googleapis.com/storage/v1/b"
BUCKET_DESC_URL = "https://www.googleapis.com/storage/v1/b/%bucketName"
HTTP_GET_METHOD = "GET"
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

class UtilBase(object):
    def __init__(self):
        self.__httpClient = ClientHelper(AuthHelper.getCredentials())
        self.__projectDetails = None

    def getHttpClient(self):
        return self.__httpClient

    def getProjectServiceAccount(self, projectId):
        googleClient = self.__httpClient
        logging.info("Making request to get storage service account for project: " + projectId)
        serviceAccount = googleClient.make_request(HTTP_GET_METHOD, PROJECT_SERVICE_URL, projectId, None)
        if not serviceAccount['isError']:
            return serviceAccount['data']
        else:
            raise Exception("Error fetching project service account: \n" + str(serviceAccount['defaultErrorObject']))


    def getProjectDetails(self, id):
        if self.__projectDetails is not None:
            return self.__projectDetails

        projectData = self.__get_Project_Details(PROJECT_ID_DESC_URL, id)

        self.__projectDetails = projectData['data']
        return self.__projectDetails

    def __get_Project_Details(self, url, id):
        googleClient = self.__httpClient
        logging.info("Making request to get project details for id: " + id)
        singleprojectData = googleClient.make_request(HTTP_GET_METHOD, url, id, None)
        if not singleprojectData['isError']:
            if singleprojectData["data"].get('lifecycleState') != "ACTIVE":
                raise Exception("Project Lifecycle state is: " + str(singleprojectData['lifecycleState']))
            return singleprojectData
        else:
            raise Exception("Error fetching project: \n" + str(singleprojectData['defaultErrorObject']))

    def getProjectList(self, filter=None):
        projectList = self.__get_Project_List(None, True, filter)
        if projectList is None:
            return projectList
        projectList = [project for project in projectList if project['lifecycleState'] == "ACTIVE"]
        if len(projectList) == 0:
            return None
        return projectList

    def __get_Project_List(self, pageToken, isBegin, filter):
        if pageToken is None and not isBegin:
            return []
        googleClient = self.__httpClient
        url = PROJECT_ID_LIST_URL
        if pageToken is not None:
            url = url + "?pageToken=" + pageToken + "&pageSize=100"
        else:
            url = url  + "?pageSize=100"

        if filter is not None and filter != "":
            url = url + "&filter=" + filter

        projectData = googleClient.make_request(HTTP_GET_METHOD, url, None, None)
        if projectData['isError']:
            raise Exception("Error fetching Project Information \n" + str(projectData['defaultErrorObject']))
        if 'projects' not in projectData['data'] or len(projectData['data']['projects']) == 0:
            return None
        projectList = projectData['data']['projects']
        if 'nextPageToken' in projectData['data']:
            nextPageToken = str(projectData['data']['nextPageToken'])
            projectList = projectList + (self.__get_Project_List(nextPageToken, False, filter))
        return projectList

    def getFolderList(self, parent):
        folderList = self.__get_Folder_List(None, True, parent)
        if folderList is None:
            return folderList
        folderList = [folder for folder in folderList if folder['lifecycleState'] == "ACTIVE"]
        if len(folderList) == 0:
            return None
        return folderList

    def __get_Folder_List(self, pageToken, isBegin, parent):
        if pageToken is None and not isBegin:
            return []
        googleClient = self.__httpClient
        url = FOLDER_ID_LIST_URL
        if pageToken is not None:
            url = url + "?pageToken=" + pageToken + "&pageSize=100"
        else:
            url = url  + "?pageSize=100"

        if parent is not None and parent != "":
            url = url + "&parent=" + parent

        folderData = googleClient.make_request(HTTP_GET_METHOD, url, None, None)
        if folderData['isError']:
            raise Exception("Error fetching Folder Information \n" + str(folderData['defaultErrorObject']))
        if 'folders' not in folderData['data'] or len(folderData['data']['folders']) == 0:
            return None
        folderList = folderData['data']['folders']
        if 'nextPageToken' in folderData['data']:
            nextPageToken = str(folderData['data']['nextPageToken'])
            folderList = folderList + (self.__get_Folder_List(nextPageToken, False, parent))
        return folderList

    def getBucket(self, bucketName):
        googleClient = self.__httpClient
        logging.info("Making request to get bucket details for bucket name: " + bucketName)
        url = BUCKET_DESC_URL.replace("%bucketName", bucketName)
        bucketData = googleClient.make_request(HTTP_GET_METHOD, url, None, None)
        if not bucketData['isError']:
            return bucketData['data']
        else:
            raise Exception("Error fetching bucket: \n" + str(bucketData['defaultErrorObject']))

    def getBucketList(self, projectId):
        bucketList = self.__get_Bucket_List(None, True, projectId)
        if bucketList is None:
            return bucketList
        if len(bucketList) == 0:
            return None
        return bucketList

    def __get_Bucket_List(self, pageToken, isBegin, projectId):
        if pageToken is None and not isBegin:
            return []
        googleClient = self.__httpClient
        url = BUCKET_LIST_URL
        if pageToken is not None:
            url = url + "?pageToken=" + pageToken + "&maxResults=100"
        else:
            url = url  + "?maxResults=100"

        if projectId is not None and projectId != "":
            url = url + "&project=" + projectId

        bucketData = googleClient.make_request(HTTP_GET_METHOD, url, None, None)
        if bucketData['isError']:
            raise Exception("Error fetching Bucket Information \n" + str(bucketData['defaultErrorObject']))
        if 'items' not in bucketData['data'] or len(bucketData['data']['items']) == 0:
            return None
        bucketList = bucketData['data']['items']
        if 'nextPageToken' in bucketData['data']:
            nextPageToken = str(bucketData['data']['nextPageToken'])
            bucketList = bucketList + (self.__get_Bucket_List(nextPageToken, False, projectId))
        return bucketList

    def validateProjectId(self, projectId):
        projectList = self.getProjectList("PROJECT", projectId)
        for project in projectList:
            if project['projectId'] == projectId:
                return True
        return False
