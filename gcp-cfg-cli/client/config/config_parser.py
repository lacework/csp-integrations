import uuid
import json
from jsonschema import validate
import os, inspect
import logging
import client_helper
SCHEMA_FILE = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/config_schema.json"
CLOUD_TYPE = "AzureCloud"
IDENTIFIER_URL = "https://securityaudit.lacework.net"
from config import Config
import os.path
import google
from google.oauth2 import service_account

class ConfigParser(object):
    @staticmethod
    def parseConfig(configFile):
        config_data = open(configFile, "r").read()
        config_data_json = json.loads(config_data)
        config_schema_data = open(SCHEMA_FILE, "r").read()
        config_schema_json = json.loads(config_schema_data)
        validate(config_data_json, config_schema_json)
        return config_data_json

    @staticmethod
    def getParsedData(configFile):
        config_data = None
        try:
            config_data = ConfigParser.parseConfig(configFile)
        except Exception as e:
            logging.exception("Invalid Config Provided", e)
            raise e
        credentials_data, project_id, isCloudShell = ConfigParser.getCredentialsFileData(config_data['credentials_file_path'])
        credentials = service_account.Credentials.from_service_account_info(credentials_data, scopes=client_helper.SCOPES)
        return Config(credentials, project_id, isCloudShell, config_data['id_type'], config_data['id'], config_data['enable_api'],config_data['service_account_project_id'] )

    @staticmethod
    def getCredentialsFileData(credentials_file_path):
        if os.path.isfile(credentials_file_path):
            try:
                credentials_data = open(credentials_file_path, "r").read()
                credentials_data = json.loads(credentials_data)
                return service_account.Credentials.from_service_account_info(credentials_data, scopes=client_helper.SCOPES), credentials_data['project_id'], False
            except Exception as e:
                logging.exception("Error reading credentials File", e)
                exit(1)
        else:
            try:
                credentials_tuple = google.auth.default(client_helper.SCOPES)
                return credentials_tuple[0], credentials_tuple[1], True
            except Exception as e:
                logging.exception("Could not authenticate using application default credentials and no credentials file found")
                exit(1)