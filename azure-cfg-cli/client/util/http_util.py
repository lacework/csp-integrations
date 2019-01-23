from credentials.credentials_provider import ResourceCredentialsProvider
from requests.adapters import HTTPAdapter, Retry
import requests
import uuid
import logging
import json

class HttpUtil(object):

    def send_post_request(self, url, token, client_id, body, expectedResponseCode):
        session = requests.Session()
        retries = Retry(total=3,
                        backoff_factor=1,
                        status_forcelist=[500, 502, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        try:
            response_json = session.post(url, params=None, data=body, headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
                "x-ms-client-request-id": client_id,
                "x-ms-correlation-id": str(uuid.uuid4())
            })

            if(response_json.status_code != expectedResponseCode):
                logging.error("Invalid Response Code received: "  +str(response_json.status_code)
                              + " Expected: " + str(expectedResponseCode) + " Error:  " + response_json.content);
                raise Exception("Error performing request")
            return response_json.content
        finally:
            session.close()

    def send_get_request(self, url, token, client_id, expectedResponseCode):
        session = requests.Session()
        retries = Retry(total=3,
                        backoff_factor=1,
                        status_forcelist=[500, 502, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        try:
            response_json = session.get(url, params=None, headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
                "x-ms-client-request-id": client_id,
                "x-ms-correlation-id": str(uuid.uuid4())
            })

            if(response_json.status_code != expectedResponseCode):
                logging.error("Invalid Response Code received: "  +str(response_json.status_code)
                              + " Expected: " + str(expectedResponseCode) + " Error:  " + response_json.content);
                raise Exception("Error performing request")
            return json.loads(response_json.content)
        finally:
            session.close()




class TenantUtil(HttpUtil):

    def __init__(self, credentials, tenantId):
        super(TenantUtil, self).__init__()
        self.__credentials = credentials
        self.__tenantId = tenantId


    def getAdProperties(self):
        tenantId =  self.__tenantId
        try:
            credentials = self.__credentials
            access_token = credentials.token["access_token"];
            client_request_id = credentials.token["_client_id"];
            return self.send_get_request("https://graph.windows.net/"+tenantId+"/tenantDetails?api-version=1.6",
                                         access_token, client_request_id, 200)
            logging.info("Successfully Fetched tenant Description for tenantId: " + tenantId)
        except:
            logging.exception("Error fetching tenant properties: " + tenantId)
            raise









