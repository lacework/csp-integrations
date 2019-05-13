import logging
ENABLE_API_BATCH = "https://serviceusage.googleapis.com/v1/projects/%projectId/services:batchEnable"
HTTP_GET_METHOD = "GET"
HTTP_POST_METHOD = "POST"
import time
from util_base import UtilBase
import logging
MAX_SERVICE_USAGE_MUTATE_QUOTA_PER_MINUTE = 120

class UtilAPI(UtilBase):

    def __init__(self, config):
        UtilBase.__init__(self, config)

    def __enableApi(self, projectId):
        body = { "serviceIds" : self.config.getApiList() }
        response = self.config.getHttpClient().make_request(HTTP_POST_METHOD, ENABLE_API_BATCH, projectId, body)
        if response['isError']:
            raise Exception("Error enabling services in project \n" + str(response['defaultErrorObject']))
        return response['data']

    def enableApi(self):
        if not self.config.getEnableApi():
            logging.info("Skipping Api Enablement")
            return [],[]
        success_list = []
        error_list  = []
        projectList = self.getProjectList()

        try:
            self.__enableApi(self.config.getUserServiceAccountProjectId())
        except Exception as e:
            None
            # raise Exception("Error enabling APIs in the user service account project: " + str(self.config.getUserServiceAccountProjectId()))


        api_count = len(self.config.getApiList())
        apiEnableRequestsPerMinute = MAX_SERVICE_USAGE_MUTATE_QUOTA_PER_MINUTE/api_count
        i=0

        for project in projectList:
            try:
                i += 1
                self.__enableApi(project['projectId'])
                success_list.append(project)
                logging.info("Enabled Apis in project: " + project['projectId'])
            except Exception as e:
                project['errorCause'] = e.message.rstrip()
                error_list.append(project)
                logging.info("Could not Enable Apis in project: " + project['projectId'])
            if i%apiEnableRequestsPerMinute == 0:
                time.sleep(60)

        return success_list, error_list

