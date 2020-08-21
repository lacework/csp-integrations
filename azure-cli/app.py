import argparse
import logging
import random
import string
import sys

from client.checks import runIndependentChecks, checkCreationRequired, checkLaceworkToken
from client.config.rollback import Rollback
from client.lacework_api import createLaceworkIntegration
from client.rollback_helper import RollbackHelper
from client.user_input import getConfigInput
from client.util.app_util import AppUtil
from client.util.credentials.credentials_provider import CredentialsProviderFactory
from client.util.event_subscription_util import EventSubscriptionUtil
from client.util.keyvault_util import KeyVaultUtil
from client.util.monitor_util import MonitorUtil
from client.util.provider_util import ProviderUtil
from client.util.resource_util import ResourceUtil
from client.util.role_util import RoleUtil
from client.util.storage_util import StorageUtil

SLEEP_SECS = 5
APP_NAME = "LaceworkSAAudit"
LACEWORK = "Lacework"
LACEWORK_LOWER = LACEWORK.lower()


def getRandSuffix():
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(5))


if __name__ == "__main__":
    try:
        ############################################## INITIALIZING LOG FILE ################################################################

        logging.basicConfig(
            filename="laceworkIntegrationScript.log",
            level=logging.DEBUG,
            filemode="w",
            format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S'
        )

        ############################################## PARSING ARGS #####################################################################
        ap = argparse.ArgumentParser()
        ap.add_argument("--rollback", help="Check if a rollback is required.")
        ap.add_argument("--config", help="Path to the config file")
        args, unknown = ap.parse_known_args()

        ############################################## CHECKING FOR CONFIG FILE ################################################################
        interactive = None
        config = None
        if args.config is None:
            configFile, interactive = getConfigInput()
        else:
            configFile = args.config

        try:
            ############################################## RUNNING ALL INDEPENDENT TESTS AND LISTING ASSUMPTIONS #######################################################
            toRegister, config, interactive = runIndependentChecks(configFile, interactive)

            credentialsProvider = CredentialsProviderFactory.getCredentialsProvider(config)

            ############################################## CHECKING IF NEED TO ROLLBACK ################################################################

            rollbackHelper = RollbackHelper(credentialsProvider)

            if args.rollback is not None and args.rollback == "true":
                rollbackHelper.performRollback()
                logging.info("The rollback is complete.")
                sys.exit("The rollback is complete.")

            ###################################################### REGISTERING ALL NEEDED RESOURCE PROVIDERS ######################################################

            providerUtil = ProviderUtil(credentialsProvider)
            providerUtil.registerAllResourceProviders(toRegister, config.getSubscriptionList()[0])

            print "Waiting until all providers are registered"
            providerUtil.waitUntilRegistered(toRegister, config.getSubscriptionList()[0])
            print "Finished registering all needed resource providers!"

            ###################################################### RUNNING ALL REQUIRED VALIDATIONS ######################################################

            appUtil = AppUtil(credentialsProvider)
            appId = appUtil.getAppId()

            if appId is None:
                suffix = getRandSuffix()

                resourceGroupName = config.getSetupPrefix() + LACEWORK + "ResourceGroup"
                storageAccountName = config.getSetupPrefix().replace("-", "") + LACEWORK_LOWER + "storage" + suffix
                queueName = config.getSetupPrefix().replace("-", "") + LACEWORK_LOWER + "queue"
                logProfileName = config.getSetupPrefix() + LACEWORK + "LogProfile"
                eventSubName = config.getSetupPrefix() + LACEWORK + "EventSub"
                roleDefinitionName = config.getSetupPrefix() + LACEWORK + "RoleDef" + suffix.upper()
                subscriptionId = config.getSubscriptionList()[0]
                clientSecret = config.getUserClientSecret()

                saveState = Rollback(resourceGroupName, storageAccountName, queueName, logProfileName,
                    eventSubName, roleDefinitionName, subscriptionId)

                checkCreationRequired(credentialsProvider, saveState)
                rollbackHelper.saveRollbackToFile(saveState)

            elif interactive.getRollForward():
                saveState = rollbackHelper.getSaveState()

                resourceGroupName = saveState.resourceGroupName
                storageAccountName = saveState.storageAccountName
                queueName = saveState.queueName
                logProfileName = saveState.logProfileName
                eventSubName = saveState.eventSubName
                roleDefinitionName = saveState.roleDefinitionName
                subscriptionId = saveState.subscriptionId

                clientSecret, exists = interactive.getClientSecret()

                if not exists:
                    print "New client secret created! Keep for future reference: {}\n".format(clientSecret)
                    appUtil.addClientSecret(clientSecret)

                config.setUserClientSecret(clientSecret)

            else:
                print "Must delete old application if not rolling forward!"
                raise Exception("Must delete old application if not rolling forward!")

            ###################################################### CREATING APP IF NONEXISTENT ######################################################

            appId = appUtil.createAppIfNotExist(clientSecret, APP_NAME)

            ###################################################### GIVING APP PROPER PERMISSIONS FOR COMPLIANCE ######################################################

            roleUtil = RoleUtil(appId, credentialsProvider)
            roleUtil.makeRoleAssignment("Reader", subscriptionId)
            print "Reader Role: DONE"

            keyVaultUtil = KeyVaultUtil(credentialsProvider)
            keyVaultUtil.setKeyVaultPolicy()

            ###################################################### CREATING RESOURCES FOR ACTIVITY LOG IF ENABLED ######################################################

            queueUrl = None
            if config.isActivityLogSetup():
                resourceUtil = ResourceUtil(credentialsProvider)
                resourceUtil.createResourceGroup(resourceGroupName, 'westus2', subscriptionId)
                print "Resource Group ({}): DONE".format(resourceGroupName)

                storageUtil = StorageUtil(credentialsProvider)
                storageAccount = storageUtil.createStorageAccount(resourceGroupName, storageAccountName, 'westus2', subscriptionId)
                print "Storage Account ({}): DONE".format(storageAccountName)
                # Get storage key and create a queue
                storageKeys = storageUtil.getStorageAccountKeys(resourceGroupName, storageAccountName, subscriptionId)

                storageUtil.createQueue(queueName, resourceGroupName, storageAccountName, storageKeys['key1'], subscriptionId)
                queueUrl = "https://" + storageAccountName + ".queue.core.windows.net/" + queueName
                print "Storage Queue ({}): DONE".format(queueName)

                monitorUtil = MonitorUtil(credentialsProvider)
                monitorUtil.createLogProfile(logProfileName, storageAccount.id, subscriptionId)
                print "Log Profile ({}): DONE".format(logProfileName)

                eventSubUtil = EventSubscriptionUtil(credentialsProvider)
                eventSubUtil.createEventGridSubscription(eventSubName, storageAccount.id, queueName, subscriptionId)
                print "Event Subscription ({}): DONE".format(eventSubName)

                roleUtil.createCustomRoleDefinition(roleDefinitionName, subscriptionId)
                print "Custom Role Definition ({}): DONE".format(roleDefinitionName)

                roleUtil.makeRoleAssignment(roleDefinitionName, subscriptionId)
                print "Custom Role Assignment: DONE"

            print "\nGo to the Azure Active Directory in the Azure Portal and grant admin consent for the application.\n"

            interactive.waitForGrantedAdminConsent()

            if interactive.getCreateLaceworkIntegration():
                token, laceworkAccount = checkLaceworkToken()
                config.setLaceworkToken(token)
                config.setLaceworkAccount(laceworkAccount)
                config.setIntegrationName(config.getSetupPrefix() + LACEWORK + "AzureIntg")

                try:
                    createLaceworkIntegration(appId, queueUrl, config)
                except Exception as e:
                    print "\nClient ID: " + appId
                    print "Client Secret: " + clientSecret
                    print "Tenant ID: " + config.getTenantId()

                    if config.isActivityLogSetup():
                        print "Queue URL: " + queueUrl
                    print ""
                    sys.exit("Programmatically creating integration failed. Use the below credentials to manually create an integration.")
                print "\nLacework Integrations: DONE"

                print "\nKeep for future use. Using API token: {}\n".format(token)
            else:
                print "\nClient ID: " + appId
                print "Client Secret: " + clientSecret
                print "Tenant ID: " + config.getTenantId()

                if config.isActivityLogSetup():
                    print "Queue URL: " + queueUrl
                print ""

        except Exception as e:
            logging.exception(str(e))
            sys.exit("Something went wrong! Check the logs for more detail.")
    except Exception as e:
        logging.exception(str(e))
        sys.exit("Something went wrong! Check the logs for more detail.")

    sys.exit("Finished script successfully!")
