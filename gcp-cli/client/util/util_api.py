from util_base import UtilBase
import logging

DISABLE_API = "https://serviceusage.googleapis.com/v1/projects/%projectId/services/%serviceId:disable"
ENABLE_API_BATCH = "https://serviceusage.googleapis.com/v1/projects/%projectId/services:batchEnable"
GET_API = "https://serviceusage.googleapis.com/v1/projects/%projectId/services/%serviceId"
HTTP_GET_METHOD = "GET"
HTTP_POST_METHOD = "POST"

class UtilAPI(UtilBase):
    def __init__(self):
        UtilBase.__init__(self)

    def checkApiEnabled(self, projectId, api):
        logging.info("Checking if " + api + " is enabled.")
        url = GET_API.replace("%serviceId", api)
        response = self.getHttpClient().make_request(HTTP_GET_METHOD, url, projectId, None)
        if response['isError']:
            raise Exception("Error checking if " + api + " is enabled!")
        return response['data']['state'] == "ENABLED"

    def __enableApi(self, projectId, apiList):
        body = {"serviceIds": apiList}
        logging.info("For " + projectId + " enabling following API using batch enable: ")
        logging.info(apiList)
        response = self.getHttpClient().make_request(HTTP_POST_METHOD, ENABLE_API_BATCH, projectId, body)
        if response['isError']:
            raise Exception("Error enabling services in project \n" + str(response['defaultErrorObject']))
        return response['data']

    def enableApi(self, userProjectId, apiList):
        try:
            self.__enableApi(userProjectId, apiList)
        except Exception as e:
            raise Exception("Error enabling APIs in the user service account project: " + str(e))

    def disableApi(self, projectId, apiList):
        body = {"disableDependentServices": True}
        logging.info("For " + projectId + " disabling following API: ")
        logging.info(apiList)
        for api in apiList:
            url = DISABLE_API.replace("%serviceId", api)
            response = self.getHttpClient().make_request(HTTP_POST_METHOD, url, projectId, body)
            if response['isError']:
                raise Exception("Error enabling services in project \n" + str(response['defaultErrorObject']))

        return response['data']
