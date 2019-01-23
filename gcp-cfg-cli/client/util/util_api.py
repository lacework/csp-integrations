import logging
ENABLE_API_BATCH = "https://serviceusage.googleapis.com/v1/projects/%projectId/services:batchEnable"
HTTP_GET_METHOD = "GET"
HTTP_POST_METHOD = "POST"
from util_base import UtilBase

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
        for project in self.getProjectList():
            try:
                self.__enableApi(project['projectId'])
                success_list.append(project)
            except Exception as e:
                project['billingErrorCause']  = e.message
                error_list.append(project)
        return success_list, error_list

