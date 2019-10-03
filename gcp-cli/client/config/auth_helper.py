import google
from google.oauth2 import service_account
import logging
import os
import json
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']
CREDENTIALS_FILE_PATH = "/Users/mobeentariq/Lacework/csp-integrations-internal/gcp-cli/client/credentials.json"

class AuthHelper(object):

    @staticmethod
    def getCredentials():
        try:
            credentials = AuthHelper.getCredentialsFileData(CREDENTIALS_FILE_PATH)
            return credentials
        except Exception as e:
            print "Could not authenticate using application default credentials and no credentials file found"
            logging.exception(
                "Could not authenticate using application default credentials and no credentials file found")
            exit(1)

    @staticmethod
    def getCredentialsFileData(credentials_file_path):
        if os.path.isfile(credentials_file_path):
            try:
                credentials_data = open(credentials_file_path, "r").read()
                credentials_data = json.loads(credentials_data)
                return service_account.Credentials.from_service_account_info(credentials_data,
                                                                             scopes=SCOPES)
            except Exception as e:
                print "Error reading credentials File" + str(e)
                logging.exception("Error reading credentials File", e)
                exit(1)
        else:
            try:
                credentials, project = google.auth.default(SCOPES)
                return credentials
            except Exception as e:
                print "Could not authenticate using application default credentials and no credentials file found"
                logging.exception(
                    "Could not authenticate using application default credentials and no credentials file found")
                exit(1)
