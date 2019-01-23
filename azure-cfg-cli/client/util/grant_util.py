from credentials.credentials_provider import ResourceCredentialsProvider
from requests.adapters import HTTPAdapter, Retry
import requests
import uuid
import logging

class GrantUtil(object):

    def __init__(self, credentialsProvider):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        self.__credentialsProvider = credentialsProvider


    def grantPermission(self, app_id):
        credentials = self.__credentialsProvider.getGrantResourceCredentials()
        access_token = credentials.token["access_token"];
        client_request_id = credentials.token["_client_id"];
        self.__send_post_request(            "https://main.iam.ad.ext.azure.com/api/RegisteredApplications/" + app_id + "/Consent?onBehalfOfAll=true",
            access_token, client_request_id, "")

    def __send_post_request(self, url, token, client_id, body):
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

            if(response_json.status_code != 204):
                logging.error("Error granting consent to application" + response_json.content);
                raise Exception("Error granting consent to application")
            else:
                logging.info("Successfully Granted Permission to App")
            return response_json
        finally:
            session.close()