import inspect
import json
import os

import yaml
from jsonschema import validate

SCHEMA_FILE = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/config_schema.json"

CLOUD_TYPE = "AzureCloud"
IDENTIFIER_URL = "https://securityaudit.lacework.net"
PROVIDER_REGISTRATION_LIST_COMPLIANCE = ["Microsoft.KeyVault", "Microsoft.Storage"]
PROVIDER_REGISTRATION_LIST_ACTIVITY = ["microsoft.insights", "Microsoft.EventGrid", "Microsoft.Security"]


class ConfigParser(object):
    @staticmethod
    def parseConfig(configFile):
        config_data = open(configFile, "r").read()
        yml_data = yaml.safe_load(config_data)
        config_schema_data = open(SCHEMA_FILE, "r").read()
        config_schema_json = json.loads(config_schema_data)
        validate(yml_data, config_schema_json)
        ConfigParser.validateConfig(yml_data)
        return yml_data

    @staticmethod
    def validateConfig(config_data):
        auditLogSetup = config_data.get("auditLogSetup");
        if config_data.get("auditLogSetupEnabled") and not auditLogSetup:
            raise ValueError("Audit Config cannot be null if Audit Log Setup is enabled")

        return True
