import getpass
import logging
import time
import uuid

# from app_manager import AppManager
from azure.mgmt.resource import SubscriptionClient
from prettytable import PrettyTable

from config.config_parser import PROVIDER_REGISTRATION_LIST_COMPLIANCE
from util.app_util import AppUtil
from util.credentials.credentials_provider import CREDENTIALS_TYPE_USER_PASS
from util.credentials.credentials_provider import CredentialsProviderFactory
from util.credentials.credentials_provider import KEY_USERNAME, KEY_PASSWORD
from util.http_util import TenantUtil

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


class InteractiveClient(object):
    def __init__(self, authType, cloudType):
        self.__cloudType = cloudType
        self.__managementResource = cloudType.endpoints.management
        self.__graphResource = cloudType.endpoints.active_directory_graph_resource_id
        self.__tenantIdList = []
        self.__tenantObject = None
        self.__subscriptionClient = None
        self.__subscriptionList = []
        self.__selectedSubscriptionId = None
        self.__registerProviders = None
        self.__authType = authType
        self.__isUpdateApp = False
        self.__clientSecret = None
        self.__credentials = None

    def getCredentials(self):
        return self.__credentials

    def __getInput(self, line):
        name = raw_input(line + ": ")
        type(name)
        if len(name.strip()) == 0:
            return self.__getInput(line)
        elif name.strip() == "exit":
            exit(0)
        else:
            return name

    def __getPasswordInput(self, line):
        name = getpass.getpass(prompt=line + ": ")
        type(name)
        if len(name.strip()) == 0:
            return self.__getPasswordInput(line)
        elif name.strip() == "exit":
            exit(0)
        else:
            return name

    def __getNumberInput(self, line):
        number = self.__getInput(line)
        try:
            return int(number)
        except:
            self.__getNumberInput(line)

    def getUserNamePasswordCredentials(self):
        credentials = {"type": self.__authType}
        credentials[KEY_USERNAME] = self.__getInput("Enter UserName")
        if self.__authType == CREDENTIALS_TYPE_USER_PASS:
            credentials[KEY_PASSWORD] = self.__getPasswordInput("Enter Password")
        self.__credentials = credentials

    def getUpdateApp(self, config):
        credentialsProvider = CredentialsProviderFactory.getCredentialsProvider(config)
        appUtil = AppUtil(credentialsProvider)
        appId = appUtil.getAppId()

        if appId is not None:
            print "\n\nYou have an existing Lacework App Setup"
            self.__isUpdateApp = self.getYesNoPrompt("Do you want to use the existing app? (YES/NO)")
            if not self.__isUpdateApp:
                print "Please delete the existing App to create a new one. Aborting for now..."
                exit(1)

        return self.__isUpdateApp

    def getRollForward(self):
        return self.getYesNoPrompt("Roll forward? (YES/NO)")

    def waitForGrantedAdminConsent(self):
        response = False
        while not response:
            response = self.getYesNoPrompt("Already granted admin consent on Azure Portal? (YES/NO)")
        time.sleep(10)

    def getCreateLaceworkIntegration(self):
        return self.getYesNoPrompt("Do you want to programmatically create Lacework integration? (YES/NO)")

    def getClientSecret(self):
        name = raw_input("Input known client secret if rolling forward (Optional): ")
        name = name.strip()
        if len(name) == 0:
            self.__clientSecret = str(uuid.uuid4())
            return self.__clientSecret, False
        elif name == "exit":
            exit(0)

        return name, True

    def shouldRegisterProviders(self):
        print "\n\nWe need some providers to be registered in the selected subscriptions in order to add compliance evaluations for them: \n"
        self.printProviders()
        self.__registerProviders = self.getYesNoPrompt("Do you Want to register the providers? (YES/NO)")

    def printProviders(self):
        print "\nList Of Providers Required\n"
        prettyTable = PrettyTable(["No.", "Namespace"])
        i = 1
        for provider in PROVIDER_REGISTRATION_LIST_COMPLIANCE:
            prettyTable.add_row([str(i), provider])
            i += 1
        print prettyTable
        if self.__registerProviders != None:
            printBold("\n\nRegister Providers : ")
            print str(self.__registerProviders)

    def getYesNoPrompt(self, line):
        input = self.__getInput(line)
        if input.lower() == "yes":
            return True
        elif input.lower() == "no":
            return False
        else:
            return self.getYesNoPrompt(line)

    def selectSubscriptions(self):
        self.fetchSubscriptions()
        self.printSubscriptions(self.__subscriptionList)
        self.__selectSubscriptions()
        return self.__selectedSubscriptionId

    def fetchSubscriptions(self):
        self.__subscriptionClient = SubscriptionClient(
            credentials=CredentialsProviderFactory.getCredentialsForResource(self.__credentials, self.__tenantObject["tenant"], self.__managementResource))
        for subscription in self.__subscriptionClient.subscriptions.list():
            if str(subscription.state) == 'SubscriptionState.enabled':
                self.__subscriptionList.append(subscription)

    def printSubscriptions(self, subscriptionList):
        prettyTable = PrettyTable(["No.", "Subscription Id", "Display Name"])
        i = 1
        print "\nList Of Available Subscriptions\n"
        for subscription in subscriptionList:
            prettyTable.add_row([str(i), subscription.subscription_id, subscription.display_name])
            i += 1
        print prettyTable

    def __selectSubscriptions(self):
        if len(self.__subscriptionList) == 0:
            print "\nNo Subscriptions found in tenant: " + self.__tenantObject["tenant"]
            return
        line = "\nPlease provide Subscription No. (eg. 1)"
        subString = self.__getInput(line)

        try:
            indexNum = int(subString.strip())

            if indexNum < 1 or indexNum > len(self.__subscriptionList):
                self.__selectSubscriptions()
                return

            self.__selectedSubscriptionId = str(self.__subscriptionList[indexNum - 1].subscription_id)
        except Exception:
            self.__selectSubscriptions()

    def selectTenants(self):
        self.fetchTenants()
        self.printTenants(self.__tenantIdList)
        self.__selectTenant()
        return self.__tenantObject["tenant"]

    def printTenants(self, tenantIdList):
        prettyTable = PrettyTable(["No.", "Tenant Id", "DisplayName"])
        i = 1
        print "\nTenants\n"
        for tenant in tenantIdList:
            prettyTable.add_row([str(i), tenant["tenant"], tenant["details"]["value"][0]["displayName"]])
            i += 1
        print prettyTable

    def __selectTenant(self):
        tenantNo = self.__getNumberInput(
            "\nSelect Tenant No. from " + str(1) + " - " + str(len(self.__tenantIdList)))
        try:
            if tenantNo >= 1 and tenantNo <= len(self.__tenantIdList):
                tenantNo = tenantNo - 1
                self.__tenantObject = self.__tenantIdList[tenantNo]
                print "\nSelected tenant: " + self.__tenantObject["tenant"]
                return
            else:
                self.__selectTenant()
        except:
            self.__selectTenant()

    def fetchTenants(self):
        self.__subscriptionClient = SubscriptionClient(CredentialsProviderFactory.getCredentialsForResource(self.__credentials, None, self.__managementResource))
        for tenant in self.__subscriptionClient.tenants.list():
            tenantId = str(tenant.tenant_id)
            credentials = CredentialsProviderFactory.getCredentialsForResource(self.__credentials, tenantId, self.__graphResource)

            tenantUtil = TenantUtil(credentials, tenantId)

            tenantProperties = tenantUtil.getAdProperties();
            if tenantProperties:
                self.__tenantIdList.append({"tenant": tenantId, "details": tenantProperties})
            else:
                logging.warn("Could not get Tenant description for tenant Id: " + tenantId)
        if len(self.__tenantIdList) == 0:
            print "No Tenants Found"
            exit(1)
