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
        else:
            googleClient = self.config.getHttpClient()
            projectData = googleClient.make_request( HTTP_GET_METHOD, PROJECT_ID_LIST_URL, None, None)
        if projectData['isError']:
            raise Exception("Error fetching Project Information \n" + str(projectData['defaultErrorObject']))
        if 'projects' not in  projectData['data'] or len(projectData['data']['projects'])==0:
            raise Exception("No Projects Found")
        self.__projectList = projectData['data']['projects']
        return self.__projectList

    def validateProjectId(self, projectId):

        projectList = self.getProjectList()
        for project in projectList:
            if project['projectId'] == projectId:
                return True
        return False