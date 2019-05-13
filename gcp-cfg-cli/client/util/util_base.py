PROJECT_ID_LIST_URL = "https://cloudresourcemanager.googleapis.com/v1/projects"
HTTP_GET_METHOD = "GET"

class UtilBase(object):

    def __init__(self, config):
        self.config = config
        self.__projectList = None

    def getProjectList(self):
        if self.__projectList != None:
            return self.__projectList
        projectData = None
        if self.config.getIdType() == "PROJECT":
            googleClient = self.config.getHttpClient()
            singleprojectData = googleClient.make_request( HTTP_GET_METHOD, PROJECT_ID_LIST_URL + "/" + self.config.getId(), None, None)
            if singleprojectData['isError']:
                projectData = singleprojectData
            else:
                projectData= {
                    'isError': singleprojectData.get("isError"),
                    'defaultErrorObject':singleprojectData.get("defaultErrorObject"),
                    "data": {
                        'projects': [singleprojectData.get("data")]
                    }
                }
                if singleprojectData["data"].get('lifecycleState') != "ACTIVE":
                    raise Exception("Project Lifecycle state is: " + str(projectData['lifecycleState']))
        else:
            projectData = {
                'isError': False,
                'defaultErrorObject': {},
                "data": {
                    'projects': self.__get_Project_List(None, True)
                }
            }
        if projectData['isError']:
            raise Exception("Error fetching projects")
        projectList = projectData['data']['projects']
        projectList = [project for project in projectList if project['lifecycleState'] == "ACTIVE"]
        self.__projectList = projectList
        return self.__projectList

    def __get_Project_List(self, pageToken, isBegin):
        if pageToken is None and not isBegin:
            return []
        googleClient = self.config.getHttpClient()
        url = PROJECT_ID_LIST_URL
        if pageToken is not None:
            url = url + "?pageToken=" + pageToken + "&pageSize=100"
        else:
            url = url  + "?pageSize=100"

        projectData = googleClient.make_request(HTTP_GET_METHOD, url, None, None)
        if projectData['isError']:
            raise Exception("Error fetching Project Information \n" + str(projectData['defaultErrorObject']))
        if 'projects' not in projectData['data'] or len(projectData['data']['projects']) == 0:
            raise Exception("No Projects Found")
        projectList = projectData['data']['projects']
        if 'nextPageToken' in projectData['data']:
            nextPageToken = str(projectData['data']['nextPageToken'])
            projectList = projectList + (self.__get_Project_List(nextPageToken, False))
        return projectList



    def validateProjectId(self, projectId):

        projectList = self.getProjectList()
        for project in projectList:
            if project['projectId'] == projectId:
                return True
        return False
