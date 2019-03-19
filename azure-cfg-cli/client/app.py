import project_logging.logger
from config_parser import ConfigParser
import os, inspect
CONFIG_FILE = "config.json"
from app_manager import AppManager
from interactive import InteractiveClient
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD
import argparse
from util.credentials.credentials_provider import CREDENTIALS_TYPE_CLI, CREDENTIALS_TYPE_USER_PASS, CREDENTIALS_TYPE_PORTAL

def fileMain():
    config, registerProviders = ConfigParser.getParsedData(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/" + CONFIG_FILE)
    appManager = AppManager(config, registerProviders)
    appManager.run()


def interactiveMain(authType):
    interactive = InteractiveClient(authType,AZURE_PUBLIC_CLOUD)
    interactive.run()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=False, default="INTERACTIVE",
                    help="mode is either INTERACTIVE | CONFIG_FILE")

    ap.add_argument("--authType", required=False, default="USER_PASS",
                    help="mode is either " + CREDENTIALS_TYPE_CLI + " | " +  CREDENTIALS_TYPE_USER_PASS + " | " +  CREDENTIALS_TYPE_PORTAL)



    args = vars(ap.parse_args())
    mode  = args["mode"]

    authType = args["authType"]

    if authType not in [CREDENTIALS_TYPE_CLI, CREDENTIALS_TYPE_USER_PASS, CREDENTIALS_TYPE_PORTAL]:
        raise Exception("Invalid Auth Type")

    if mode == "INTERACTIVE":
        interactiveMain(authType)
    elif mode == "CONFIG_FILE":
        fileMain()

