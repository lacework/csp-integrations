from google.auth.transport.requests import AuthorizedSession
import json

SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

class ClientHelper(object):
    def __init__(self, credentials):
        self.client = AuthorizedSession(credentials)

    def make_request(self, method, url, projectId, body, headers=None):
        if projectId is not None:
            url = url.replace("%projectId", projectId)

        if body is not None:
            body = json.dumps(body)

        val = self.client.request(method=method, url=url, data=body, headers=headers)
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
                "error": " Body: " + resp.text,
                "status": resp.status_code,
                "resource": path
            }
            respTemplate['isError'] = True
            return respTemplate
