from config.config_parser import ConfigParser
import os, inspect
CONFIG_FILE = "config.json"
import project_logging.logger
import sys
sys.path.insert(0, 'client/app_manager.py')
import logging
from config.config import Config
from client.client_factory import UserClientFactory
import argparse
service_account_credentials_file_location = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/sa_credentials.json"

sa_env_var = os.environ.get("sa_cred_file")
if sa_env_var:
    service_account_credentials_file_location = sa_env_var


def raiseException(ex):
    raise ex

if __name__ == "__main__":

    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=False, default="interactive",
                    help="mode is either interactive | non-interactive")

    args, unknown = ap.parse_known_args()
    args = vars(args)
    mode  = args["mode"]

    credentials_data, project_id, isCloudShell = ConfigParser.getCredentialsFileData(service_account_credentials_file_location)

    config = Config(credentials_data, project_id, isCloudShell, None, None, None, None, None)

    client  = UserClientFactory.getClient(mode, config)
    client.initConfig()
    client.validate()

    client.run()
