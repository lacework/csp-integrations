import uuid
import base64, json
from prettytable import PrettyTable
from client_base import ClientBase
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


class InteractiveClient(ClientBase):
    def __init__(self, config):
        ClientBase.__init__(self, config)

    def __getInput(self, line, allowedValues):
        name = raw_input(line + ": ")
        type(name)
        if len(name.strip()) == 0:
            return self.__getInput(line, allowedValues)
        elif name.strip() == "exit":
            exit(0)
        else:
            if allowedValues and name not in allowedValues:
                return self.__getInput(line, allowedValues)
            return name

    def __getNumberInput(self, line, allowedValues):
        number = self.__getInput(line,  allowedValues)
        try:
            return int(number)
        except:
            self.__getNumberInput(line,  allowedValues)

    def initConfig(self):
        config = self.config
        idType = self.__getInput("What do you want to integrate (ORGANIZATION/PROJECT)", ["ORGANIZATION", "PROJECT"])
        config.setIdType(idType)
        id = self.__getInput("Enter your " + idType + " Id ", None)
        config.setId(id)
        util = Util(config)
        if idType == "ORGANIZATION":
            self.printProjectList(util.getProjectList(), "\nProjects")
            serviceAccountProjectId = self.__getInput("Enter the projectId where you want to create the Service Account", None)
            config.setServiceAccountProjectId(serviceAccountProjectId)
        else:
            config.setServiceAccountProjectId(id)



        self.printAPI("\nAPIs to be enabled")
        self.printProjectList(util.getProjectList(), "\nProjects")

        enableApi = self.getYesNoPrompt("Do You want to enable APIs in the projects(yes/no)")
        config.setEnableApi(enableApi)

        self.printRole("\nRoles Required")
        modifyIamPolicy = self.getYesNoPrompt("Do you want to modify "+ config.getIdType() + " IAM Policy(yes/no)")

        config.setSetIAMPolicy(modifyIamPolicy);

        self.review(util)
        flag = self.getYesNoPrompt("\nDo You Want to continue(yes/no)")
        if not flag:
            exit(1)


    def getYesNoPrompt(self, line):
        input = self.__getInput(line, None)
        if input.lower() == "yes":
            return True
        elif input.lower() == "no":
            return False
        else:
            self.getYesNoPrompt(line)

    def review(self, util):
        config = self.config
        printBold("\n\n------------------------------------------------------------------------------------------------------------------")
        printBold("\n\nOverview")
        printBold("\nIntegration Scope")
        print config.getIdType()
        printBold("\n" + config.getIdType() + " Id")
        print config.getId()
        printBold("\nService Account Project Id")
        print config.getServiceAccountProjectId()
        if config.getEnableApi():
            self.printAPI("\nAPIs to be enabled")
            self.printProjectList(util.getProjectList(), "\nEnable API in following project")

        self.printRole("\nRoles Required")
        printBold("\nModify " + config.getIdType() + " IAM Policy")
        print config.getSetIAMPolicy()
        printBold("\n\n------------------------------------------------------------------------------------------------------------------")

    def printAPI(self, heading):
        printBold(heading)
        prettyTable = PrettyTable(["No.", "API"])
        i = 1
        for api in self.config.getApiList():
            prettyTable.add_row([str(i), api])
            i += 1
        print prettyTable

    def printRole(self, heading):
        printBold(heading)
        prettyTable = PrettyTable(["No.", "Role"])
        i = 1
        for role in self.config.getServiceAccountRoleList():
            prettyTable.add_row([str(i), role])
            i += 1
        print prettyTable


    def printProjectList(self, projectList, heading):
        printBold(heading)
        prettyTable = PrettyTable(["No.", "Project Id", "Project Name"])
        i = 1
        for project in projectList:
            prettyTable.add_row([str(i), project['projectId'], project['name']])
            i += 1
        print prettyTable
