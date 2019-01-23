from msrestazure.azure_active_directory import UserPassCredentials
from util.credentials.credentials_provider import UserPasswordCredentialsProvider
from util.app_util import AppUtil
from app_manager import AppManager
from azure.mgmt.resource import SubscriptionClient
from config_parser import PROVIDER_REGISTRATION_LIST
from config_parser import IDENTIFIER_URL
import uuid
from prettytable import PrettyTable
from util.http_util import TenantUtil
from util.config import Config
import getpass
from config_parser import IDENTIFIER_URL

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
    def __init__(self, cloudType):
        self.__cloudType = cloudType
        self.__managementResource = cloudType.endpoints.management
        self.__graphResource = cloudType.endpoints.active_directory_graph_resource_id
        self.__userName = None
        self.__password = None
        self.__tenantIdList = []
        self.__tenantId = None
        self.__tenantObject = None
        self.__subScriptionIdList = []
        self.__subscriptionClient = None
        self.__subscriptionList = []
        self.__selectedSubscriptionList = []
        self.__registerProviders = None
        self.__clientSecret = str(uuid.uuid4())
        self.__allSubscriptions = False
        self.__updateApp = False

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
        self.getUserNamePassword()
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

    def getUserNamePassword(self):
        self.__userName = self.__getInput("Enter UserName")
        self.__password = self.__getPasswordInput("Enter Password")

    def getUpdateApp(self):
        config = Config([], True, str(self.__tenantId), IDENTIFIER_URL, self.__cloudType.name, [], True);

        credentialsProvider = UserPasswordCredentialsProvider(self.__userName, self.__password, config);
        appUtil = AppUtil(credentialsProvider)
        appId = appUtil.getAppId()

        if appId!=None:
            print "\n\nYou already have a Lacework App Setup"
            self.__updateApp = self.getYesNoPrompt("Do You Want to update an existing app? (YES/NO)")
            if not self.__updateApp:
                print "Please delete the existing App to create a new one. Aborting for now..."
                exit(1)
        else:
            self.__updateApp = False

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
        print str(self.__updateApp)
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
            credentials=self.getCredentialsForResource(self.__tenantId, self.__managementResource))
        for subscription in self.__subscriptionClient.subscriptions.list():
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
            print "\n No Subscriptions found in tenant: " + self.__tenantId
            return
        line = "\n Please provide comma separated Subscription No. (eg. 1,3,4) or 'ALL' for all subscriptions"
        subString = self.__getInput(line)
        if subString == "ALL":
            self.__allSubscriptions = True
            self.__selectedSubscriptionList = self.__subscriptionList
        else:
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
                        self.__subScriptionIdList.append(self.__subscriptionList[indexNum - 1].subscription_id)
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
                self.__tenantId = self.__tenantObject["tenant"]
                print "\n Selected tenant: " + self.__tenantId
                return
            else:
                self.__selectTenant()
        except:
            self.__selectTenant()

    def fetchTenants(self):
        self.__subscriptionClient = SubscriptionClient(self.getCredentialsForResource(None, self.__managementResource))
        for tenant in self.__subscriptionClient.tenants.list():
            config = Config([], True, str(tenant.tenant_id), "", self.__cloudType.name, [], True);

            # credentialsProvider = UserPasswordCredentialsProvider(self.__userName, self.__password, config);
            tenantId = config.getTenantId();
            credentials = self.getCredentialsForResource(tenantId, self.__graphResource)

            tenantUtil = TenantUtil(credentials, tenantId)
            self.__tenantIdList.append({"tenant": tenantId, "details": tenantUtil.getAdProperties()})
        if len(self.__tenantIdList) == 0:
            print "No Tenants Found"
            exit(1)

    def runApp(self):
        config = Config(self.__subScriptionIdList, self.__allSubscriptions, str(self.__tenantId), IDENTIFIER_URL,
                        self.__cloudType.name, PROVIDER_REGISTRATION_LIST, self.__updateApp)
        appManager = AppManager(self.__userName, self.__password, self.__clientSecret, config, self.__registerProviders)
        appManager.run()

    def getCredentialsForResource(self, tenantId, resource):
        if tenantId!=None:
            return UserPassCredentials(self.__userName, self.__password, tenant=tenantId, resource=resource)
        else:
            return UserPassCredentials(self.__userName, self.__password, resource=resource)
