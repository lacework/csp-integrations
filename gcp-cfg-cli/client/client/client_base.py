import uuid
import base64, json
from prettytable import PrettyTable
from app_manager import AppManager
from util.util import Util

PURPLE = '\033[95m'
CYAN = '\033[96m'
DARKCYAN = '\033[36m'
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
END = '\033[0m'


def printColor(color, text):
    print BOLD + text + END


def printBold(text):
    printColor(BOLD, text)


class ClientBase(object):
    def __init__(self, config):
        self.config = config
        self.util = None

    def run(self):
        self.util =  Util(self.config)
        util = self.util
        appManager = AppManager(self.config, util)

        api_success_list, api_error_list, service_account, key = appManager.run()

        if api_success_list and len(api_success_list) != 0:
            self.printProjectList(api_success_list, "Successfully Enabled APIs in following projects")

        if api_error_list and len(api_error_list) != 0:
            self.printProjectErrorList(api_error_list, "Error Enabling APIs in following projects")

        self.printInterationData(service_account, key)

    def validate(self):
        self.util = Util(self.config)
        config = self.config
        if config.getIdType() == "ORGANIZATION" and not config.getId().isdigit():
            raise Exception("Invalid org id")

        # Validate service account project id
        for project in self.util.getProjectList():
            if project['projectId'] == config.getServiceAccountProjectId():
                return True
        raise Exception("Project Id is not valid: " + config.getServiceAccountProjectId())


    def printProjectList(self, projectList, heading):
        printBold(heading)
        prettyTable = PrettyTable(["No.", "Project Id", "Project Name"])
        i = 1
        for project in projectList:
            prettyTable.add_row([str(i), project['projectId'], project['name']])
            i += 1
        print prettyTable

    def printProjectErrorList(self, projectList, heading):
        printBold(heading)
        prettyTable = PrettyTable(["No.", "Project Id", "Project Name", "Error"])
        i = 1
        for project in projectList:
            prettyTable.add_row([str(i), project['projectId'], project['name'], project['errorCause']])
            i += 1
        print prettyTable



    def printInterationData(self, serviceAccount, key):
        config = self.config
        printBold("\nIntegration Data")
        printBold("\nId Type")
        print config.getIdType()
        printBold("Id")
        print config.getId()
        if key:
            base64decodedKey = base64.b64decode(str(key['privateKeyData']))
            key_json = json.loads(base64decodedKey)
            printBold("Client Email")
            print key_json['client_email']
            printBold("Client Id")
            print  key_json["client_id"]
            printBold("Private Key Id")
            print key_json["private_key_id"]
            printBold("Private Key")
            print key_json["private_key"]
