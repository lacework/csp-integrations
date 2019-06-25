from msrestazure.azure_active_directory import UserPassCredentials
from util.credentials.credentials_provider import CredentialsProviderFactory
from util.app_util import AppUtil
from app_manager import AppManager
from azure.mgmt.resource import SubscriptionClient
from config_parser import PROVIDER_REGISTRATION_LIST
from config_parser import IDENTIFIER_URL
import uuid
import logging
from prettytable import PrettyTable
from util.http_util import TenantUtil
from util.config import Config
import getpass
from config_parser import IDENTIFIER_URL
from util.credentials.credentials_provider import CREDENTIALS_TYPE_USER_PASS
from util.credentials.credentials_provider import KEY_USERNAME, KEY_PASSWORD

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
        self.__selectedSubscriptionList = []
        self.__registerProviders = None
        self.__allSubscriptions = False
        self.__authType = authType
        self.__config = Config(None, str(uuid.uuid4()), [], True, None, IDENTIFIER_URL, self.__cloudType.name, [], False)
        self.__credentials = None
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

    def run(self):
        self.getUserNamePasswordCredentials()
        # self.getClientSecret()
        self.selectTenants()
        self.getUpdateApp()
        self.selectSubscriptions()
        if len(self.__selectedSubscriptionList) > 0:
            self.shouldRegisterProviders()
        self.review()
        cont = self.getYesNoPrompt("Do You Want to continue? (YES/NO)")
        if not cont:
            print "Aborting.."
            exit(1)
        self.runApp()

    def getUserNamePasswordCredentials(self):
        credentials = {"type": self.__authType}
        credentials[KEY_USERNAME] = self.__getInput("Enter UserName")
        if self.__authType == CREDENTIALS_TYPE_USER_PASS:
            credentials[KEY_PASSWORD] = self.__getPasswordInput("Enter Password")
        self.__credentials = credentials
        self.__config.setCredentials(credentials)


    def getUpdateApp(self):
        credentialsProvider = CredentialsProviderFactory.getCredentialsProvider(self.__config);
        appUtil = AppUtil(credentialsProvider)
        appId = appUtil.getAppId()

        if appId!=None:
            print "\n\nYou already have a Lacework App Setup"
            self.__config.setIsUpdateApp(self.getYesNoPrompt("Do You Want to update an existing app? (YES/NO)"))
            if not self.__config.isUpdateApp():
                print "Please delete the existing App to create a new one. Aborting for now..."
                exit(1)


    def getClientSecret(self):
        name = raw_input("Get Client Secret (Optional). Not used for existing Apps: ")
        type(name)
        if len(name.strip()) == 0:
            self.__clientSecret = str(uuid.uuid4())
        elif name.strip() == "exit":
            exit(0)
        elif len(name.strip()) < 10:
            self.getClientSecret()

    def review(self):
        printBold(
            "\n\n------------------------------------------------------------------------------------------------------------------")
        printBold("\n\nOverview")
        self.printTenants([self.__tenantObject])
        printBold("\n\nSelected Subscriptions: ")
        self.printSubscriptions(self.__selectedSubscriptionList)
        printBold("\n\nUpdate Permission for existing App: ")
        print str(self.__config.isUpdateApp())
        if len(self.__selectedSubscriptionList) > 0:
            printBold("\n\nProviders Required")
            self.printProviders()
        printBold(
            "\n\n------------------------------------------------------------------------------------------------------------------")

    def shouldRegisterProviders(self):
        print "\n\nWe need some providers to be registered in the selected subscriptions in order to add compliance evaluations for them: \n"
        self.printProviders()
        self.__registerProviders = self.getYesNoPrompt("Do you Want to register the providers? (YES/NO)")

    def printProviders(self):
        print "\nList Of Providers Required\n"
        prettyTable = PrettyTable(["No.", "Namespace"])
        i = 1
        for provider in PROVIDER_REGISTRATION_LIST:
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
            self.getYesNoPrompt(line)

    def selectSubscriptions(self):
        self.fetchSubscriptions()
        self.printSubscriptions(self.__subscriptionList)
        self.__selectSubscriptions()

    def fetchSubscriptions(self):
        self.__subscriptionClient = SubscriptionClient(
            credentials=CredentialsProviderFactory.getCredentialsForResource(self.__config, self.__managementResource))
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
            print "\n No Subscriptions found in tenant: " + self.__config.getTenantId()
            return
        line = "\n Please provide comma separated Subscription No. (eg. 1,3,4) or 'ALL' for all subscriptions"
        subString = self.__getInput(line)
        if subString == "ALL":
            self.__allSubscriptions = True
            self.__selectedSubscriptionList = self.__subscriptionList
            self.__config.setAllSubscriptions(True)
        else:
            self.__config.setAllSubscriptions(False)
            try:
                subsIndexList = [x.strip() for x in subString.split(',')]
                for index in subsIndexList:
                    indexNum = int(index)
                    if indexNum < 1 or indexNum > len(self.__subscriptionList):
                        self.__selectSubscriptions()
                        return
                for index in subsIndexList:
                    indexNum = int(index)
                    if indexNum >= 1 and indexNum <= len(self.__subscriptionList):
                        self.__selectedSubscriptionList.append(self.__subscriptionList[indexNum - 1])
                        self.__config.getSubscriptionList().append(self.__subscriptionList[indexNum - 1].subscription_id)
            except Exception as e:
                self.__selectSubscriptions()

    def selectTenants(self):
        self.fetchTenants()
        self.printTenants(self.__tenantIdList)
        self.__selectTenant()

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
                self.__config.setTenantId(self.__tenantObject["tenant"])
                print "\n Selected tenant: " + self.__config.getTenantId()
                return
            else:
                self.__selectTenant()
        except:
            self.__selectTenant()

    def fetchTenants(self):
        config = Config(self.__credentials, None, [], True, None, "", self.__cloudType.name, [], True);
        self.__subscriptionClient = SubscriptionClient(CredentialsProviderFactory.getCredentialsForResource(config, self.__managementResource))
        for tenant in self.__subscriptionClient.tenants.list():
            config = Config(self.__credentials, None, [], True, str(tenant.tenant_id), "", self.__cloudType.name, [], True);

            tenantId = config.getTenantId();
            credentials = CredentialsProviderFactory.getCredentialsForResource(config, self.__graphResource)

            tenantUtil = TenantUtil(credentials, tenantId)

            tenantProperties = tenantUtil.getAdProperties();
            if tenantProperties:
                self.__tenantIdList.append({"tenant": tenantId, "details": tenantProperties})
            else:
                logging.warn("Could not get Tenant description for tenant Id: " + tenantId)
        if len(self.__tenantIdList) == 0:
            print "No Tenants Found"
            exit(1)

    def runApp(self):
        config = self.__config
        appManager = AppManager(config, self.__registerProviders)
        appManager.run()

