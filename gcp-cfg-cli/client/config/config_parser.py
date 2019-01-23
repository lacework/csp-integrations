import uuid
import json
from jsonschema import validate
import os, inspect
import logging

SCHEMA_FILE = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/config_schema.json"
CLOUD_TYPE = "AzureCloud"
IDENTIFIER_URL = "https://securityaudit.lacework.net"
from config import Config

PROVIDER_REGISTRATION_LIST = ["Microsoft.KeyVault", "Microsoft.Storage"]


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
        credentials_data = ConfigParser.getCredentialsFileData(config_data['credentials_file_path'])
        return Config(credentials_data, config_data['id_type'], config_data['id'], config_data['enable_api'],config_data['service_account_project_id'] )


    @staticmethod
    def getCredentialsFileData(credentials_file_path):
        try:
            credentials_data = open(credentials_file_path, "r").read()
            credentials_data = json.loads(credentials_data)
            return credentials_data
        except Exception as e:
            logging.exception("Error reading credentials File", e)
            raise e