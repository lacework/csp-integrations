import getpass
import logging
import uuid

from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD

from client.util.app_util import AppUtil
from client.util.common_util import CommonUtil
from client.util.event_subscription_util import EventSubscriptionUtil
from client.util.monitor_util import MonitorUtil
from client.util.resource_util import ResourceUtil
from client.util.storage_util import StorageUtil
from config.config import Config
from config.config_parser import ConfigParser
from config.config_parser import IDENTIFIER_URL
from config.config_parser import PROVIDER_REGISTRATION_LIST_ACTIVITY
from config.config_parser import PROVIDER_REGISTRATION_LIST_COMPLIANCE
from helpers import yesNoInput
from interactive import InteractiveClient
from lacework_api import getSchema
from lacework_api import getToken
from util.credentials.credentials_provider import CredentialsProviderFactory
from util.provider_util import ProviderUtil


def runIndependentChecks(configFile, interactive):
    configYaml = ConfigParser.parseConfig(configFile)
    if interactive is None:
        interactive = InteractiveClient(configYaml['authType'], AZURE_PUBLIC_CLOUD)
        interactive.getUserNamePasswordCredentials()

    config = Config(
        credentials=interactive.getCredentials(),
        userClientSecret=str(uuid.uuid4()),
        subscriptionId=configYaml['complianceSetup']['subscriptionId'],
        tenantId=configYaml['tenantId'],
        identifierUrl=IDENTIFIER_URL,
        cloudType=AZURE_PUBLIC_CLOUD.name,
        updateApp=False,
        configJson=configYaml
    )

    # Checking if App exists
    config.setIsUpdateApp(interactive.getUpdateApp(config))
    credentialsProvider = CredentialsProviderFactory.getCredentialsProvider(config)
    providerUtil = ProviderUtil(credentialsProvider)

    # Check which providers to register
    toRegister = []
    for provider in PROVIDER_REGISTRATION_LIST_COMPLIANCE:
        if not providerUtil.checkProviderExists(provider, config.getSubscriptionList()[0]):
            toRegister.append(provider)

    if config.isActivityLogSetup():
        for provider in PROVIDER_REGISTRATION_LIST_ACTIVITY:
            if not providerUtil.checkProviderExists(provider, config.getSubscriptionList()[0]):
                toRegister.append(provider)

    return toRegister, config, interactive


def checkLaceworkToken():
    laceworkAccount = None
    while True:
        yesOrNo = yesNoInput("Do you have a valid Lacework API token? (Y/N): \n")

        token = None
        if yesOrNo == "yes" or yesOrNo == "y":
            while True:
                token = getpass.getpass("Enter the Lacework API token: \n")
                if " " in token or token == "":
                    print "Enter a valid API token."
                else:
                    break
        else:
            logging.info("Getting the Lacework API token for this Lacework application.")
            print "Getting the Lacework API token for this Lacework application."
            responseJson, laceworkAccount, result = getToken()
            if result == "valid":
                token = responseJson['data'][0]['token']
            elif result == "authIssue":
                logging.info("Authorization failed. Verify that the specified access key, secret key, and Lacework application (" + laceworkAccount + ") are correct. ")
                print "Authorization failed. Verify that the specified access key, secret key, and Lacework application (" + laceworkAccount + ") are correct. "
                continue
            elif result == "serverIssue":
                logging.info("Unable to connect to the Lacework application or incorrect Lacework application specified (" + laceworkAccount + "). Just specify the myLacework part of the Lacework application URL: myLacework.lacework.net.")
                print "Unable to connect to the Lacework application or incorrect Lacework application specified (" + laceworkAccount + "). Just specify the myLacework part of the Lacework application URL: myLacework.lacework.net."
                continue

        logging.info("Checking the connection to the Lacework application and if the API token is valid.")
        print "Checking the connection to the Lacework application and if the API token is valid."
        laceworkAccount, result = getSchema(token, laceworkAccount, "AZURE_CFG")
        if result == "valid":
            logging.info("Check: Passed! Can connect to Lacework and the API Token is valid.")
            print "Check: Passed! Can connect to Lacework and the API Token is valid."
            return token, laceworkAccount
        elif result == "tokenIssue":
            logging.info("Check: Failed! Specified API Token is invalid. Follow the prompts to get new API token or verify that the specifed Lacework application name " + laceworkAccount + " is correct.")
            print "Check: Failed! Specified API token is invalid. Follow the prompts to get new API token or verify that the specifed Lacework application name " + laceworkAccount + " is correct."
        elif result == "serverIssue":
            logging.info("Check: Failed! Cannot connect to Lacework or specified Lacework application name (" + laceworkAccount + ") is incorrect. ")
            print "Check: Failed! Cannot connect to Lacework or specified Lacework application name (" + laceworkAccount + ") is incorrect. "


def checkCreationRequired(credentialsProvider, saveState):
    __checkAppCreation(credentialsProvider, saveState)
    __checkRoleRelatedCreation(credentialsProvider, saveState)
    __checkResourceGroupCreation(credentialsProvider, saveState)
    __checkStorageAccountAndQueueCreation(credentialsProvider, saveState)
    __checkLogProfileCreation(credentialsProvider, saveState)
    __checkEventGridSubscriptionCreation(credentialsProvider, saveState)


def __checkAppCreation(credentialsProvider, saveState):
    appUtil = AppUtil(credentialsProvider)
    saveState.appId = appUtil.getAppId()
    saveState.createdApp = saveState.appId is None


def __checkRoleRelatedCreation(credentialsProvider, saveState):
    commUtil = CommonUtil(credentialsProvider)
    authClient = commUtil.getAuthorizationManagementClient(saveState.subscriptionId)

    servicePrincipalId = None if saveState.appId is None else commUtil.getServicePrincipalId()
    if servicePrincipalId is None:
        saveState.createdServicePrincipal = True
        saveState.assignedReaderRole = True
        saveState.assignedCustomRole = True

    customRoleDefId = commUtil.getRoleDefinitionId(saveState.subscriptionId, authClient, saveState.roleDefinitionName)
    saveState.createdCustomRole = customRoleDefId is None

    if servicePrincipalId is not None:
        readerRoleId = commUtil.getRoleDefinitionId(saveState.subscriptionId, authClient, "Reader")
        readerRoleAssignment = commUtil.getRoleAssignment(saveState.subscriptionId, servicePrincipalId, readerRoleId, authClient)
        saveState.assignedReaderRole = readerRoleAssignment is None

        customRoleAssignment = commUtil.getRoleAssignment(saveState.subscriptionId, servicePrincipalId, customRoleDefId, authClient)
        saveState.assignedCustomRole = customRoleAssignment is None


def __checkResourceGroupCreation(credentialsProvider, saveState):
    resourceUtil = ResourceUtil(credentialsProvider)
    saveState.createdResourceGroup = not resourceUtil.checkResourceGroupExists(saveState.resourceGroupName, saveState.subscriptionId)


def __checkStorageAccountAndQueueCreation(credentialsProvider, saveState):
    storageUtil = StorageUtil(credentialsProvider)
    saveState.createdStorageAccount = not storageUtil.checkStorageAccountExists(saveState.storageAccountName, saveState.subscriptionId)

    if not saveState.createdStorageAccount:
        storageKeys = storageUtil.getStorageAccountKeys(saveState.resourceGroupName, saveState.storageAccountName, saveState.subscriptionId)
        saveState.createdQueue = not storageUtil.checkQueueExists(saveState.queueName, saveState.storageAccountName, storageKeys['key1'])
    else:
        saveState.createdQueue = True


def __checkLogProfileCreation(credentialsProvider, saveState):
    monitorUtil = MonitorUtil(credentialsProvider)
    saveState.createdLogProfile = not monitorUtil.checkLogProfileExists(saveState.logProfileName, saveState.subscriptionId)


def __checkEventGridSubscriptionCreation(credentialsProvider, saveState):
    eventSubUtil = EventSubscriptionUtil(credentialsProvider)
    storageUtil = StorageUtil(credentialsProvider)

    storageAccount = None
    if not saveState.createdStorageAccount:
        storageAccount = storageUtil.getStorageAccount(saveState.resourceGroupName, saveState.storageAccountName, saveState.subscriptionId)

    saveState.createdEventGridSub = storageAccount is None or not eventSubUtil.checkEventGridSubscriptionExists(saveState.eventSubName, storageAccount.id, saveState.subscriptionId)
