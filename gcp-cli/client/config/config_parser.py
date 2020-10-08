from future import standard_library
standard_library.install_aliases()
from builtins import object
import json
from jsonschema import validate
import os, inspect
import logging
SCHEMA_FILE = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/config_schema.json"
import yaml

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
        
        if auditLogSetup:
            if auditLogSetup.get("existingBucketName") and not auditLogSetup.get("exports"):
                raise ValueError("For Existing Bucket, exports need to be defined!")
        return True


