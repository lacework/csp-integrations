import project_logging.logger
from config_parser import ConfigParser
import os, inspect
CONFIG_FILE = "config.json"
from app_manager import AppManager
from interactive import InteractiveClient
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD
import argparse

def fileMain():
    userName, password, clientSecret, config, updatePermissionsForExistingApp = ConfigParser.getParsedData(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/" + CONFIG_FILE)
    appManager = AppManager(userName, password, clientSecret, config, updatePermissionsForExistingApp)
    appManager.run()


def interactiveMain():
    interactive = InteractiveClient(AZURE_PUBLIC_CLOUD)
    interactive.run()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=False, default="INTERACTIVE",
                    help="mode is either INTERACTIVE | CONFIG_FILE")
    args = vars(ap.parse_args())
    mode  = args["mode"]
    if mode == "INTERACTIVE":
        interactiveMain()
    elif mode == "CONFIG_FILE":
        fileMain()

