from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account
import json

SCOPES = ['https://www.googleapis.com/auth/cloud-platform']


class ClientHelper(object):
    def __init__(self, credentials):
        service_account_credentials = service_account.Credentials.from_service_account_info(credentials, scopes=SCOPES)
        self.client = AuthorizedSession(service_account_credentials)

    def make_request(self, method, url, projectId, body):

        if projectId is not None:
            url = url.replace("%projectId", projectId)

        if body is not None:
            body = json.dumps(body)
        val = self.client.request(method=method, url=url, data=body)
        val = self.__get_processed_response(val)
        return val

    def __get_processed_response(self, resp):
        respTemplate = {
            "isError": False,
            "errorMessage": None,
            "defaultErrorObject": None,
            "data": None
        }

        if resp.status_code >= 200 and resp.status_code <= 299:
            respTemplate["data"] = json.loads(resp.text)
            return respTemplate
        else:
            path = str(resp.url)
            respTemplate["defaultErrorObject"] = {
                "error": "Status Code: " + str(resp.status_code) + " Body: " + resp.text,
                "resource": path
            }
            respTemplate['isError'] = True
            return respTemplate
