import uuid
import json
from jsonschema import validate
import os,inspect
SCHEMA_FILE = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/config_schema.json"
CLOUD_TYPE = "AzureCloud"
IDENTIFIER_URL = "https://securityaudit.lacework.net"
from util.config import Config
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
        config_data = ConfigParser.parseConfig(configFile)
        clientSecret =  str(config_data.get("clientSecret"))
        if clientSecret == None:
            clientSecret = str(uuid.uuid4())
        tenantId = str(config_data["tenantId"])
        subscriptionList = config_data["subscriptionList"]
        allSubscriptions = config_data["allSubscriptions"]
        updatePermissionsForExistingApp = config_data["updatePermissionsForExistingApp"]
        registerProviders = config_data["registerProviders"]
        credentials = config_data["credentials"]
        providerRegistrationNamespaceList = PROVIDER_REGISTRATION_LIST
        config = Config(credentials, clientSecret, subscriptionList, allSubscriptions, tenantId, IDENTIFIER_URL, CLOUD_TYPE, providerRegistrationNamespaceList, updatePermissionsForExistingApp)
        return config, registerProviders
