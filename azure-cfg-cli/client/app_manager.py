from util.credentials.credentials_provider import CredentialsProviderFactory
from util.app_util import AppUtil
from util.grant_util import GrantUtil
from util.credential_test_util import CredentialsTestUtil
from util.role_util import RoleUtil
from util.keyvault_util import KeyVaultUtil
from util.validator_util import ValidatorUtil
from util.provider_util import ProviderUtil
from util.config import Config
import logging, json
import time
APP_NAME = "LaceworkSAAudit"


class AppManager(object):
    def __init__(self, userName, password, clientSecret, config, registerProviders):
        if not isinstance(config, Config):
            raise Exception("Invalid Config Object")
        self.__registerProviders = registerProviders
        self.__config = config
        self.__clientSecret = clientSecret
        self.__credentialsProvider = CredentialsProviderFactory.getUserCredentialsProvider(userName, password,
                                                                                           config)
        self.__appUtil = AppUtil(self.__credentialsProvider)
        self.__grantUtil = GrantUtil(self.__credentialsProvider)
        self.__validatorUtil = ValidatorUtil(self.__credentialsProvider)
        self.__providerUtil = ProviderUtil(self.__credentialsProvider)

    def run(self):
        updateApp = self.__config.isUpdateApp();
        appExists = self.__appUtil.getAppId() != None
        if appExists and not updateApp:
            logging.info("App already exists and UpdatePermissionsForExistingApp is " + str(updateApp))
            exit(1)
        elif not appExists and updateApp:
            logging.info("App does not exist and UpdatePermissionsForExistingApp is " + str(updateApp) + " Nothing to Update")
            exit(1)

        if self.__registerProviders:
            self.__registerProvider()
        self.__createOrUpdateApp()

        if not appExists:
            self.__testCredentials()
        else:
            logging.info("App Updated Successfully. New Client Secret Not generated")
            self.__clientSecret = None
        self.__printCredentials()

    def __registerProvider(self):
        self.__providerUtil.registerProvider()

    def __createOrUpdateApp(self):
        self.__validatorUtil.validateUserPermissions()
        appId = self.__appUtil.createAppIfNotExist(self.__clientSecret, APP_NAME);
        self.__grantUtil.grantPermission(appId);
        roleUtil = RoleUtil(appId, self.__credentialsProvider)
        roleUtil.makeRoleAssignments()
        keyVaultUtil = KeyVaultUtil(self.__credentialsProvider)
        keyVaultUtil.setKeyVaultPolicy()

    def __testCredentials(self):
        exception = None
        for i in range(1,5):
            try:
                appId = self.__appUtil.getAppId()
                appCredentialsProvider = CredentialsProviderFactory.getAppCredentialsProvider(appId,
                                                                                              self.__clientSecret,
                                                                                              self.__config)
                credentialsTestUtil = CredentialsTestUtil(appCredentialsProvider)
                credentialsTestUtil.listKeys()
                exception = None
                break
            except Exception as e:
                logging.warn("Error testing credentials: Retrying test" + str(e.message))
                exception = e
                time.sleep(5)
        if exception != None:
            logging.error("Error testing credentials: " + exception)

    def __printCredentials(self):
        appId = self.__appUtil.getAppId()
        map = {"CLIENT_ID": appId, "CLIENT_SECRET": self.__clientSecret, "TENANT_ID": self.__config.getTenantId()}
        logging.info("\n" + json.dumps(map, sort_keys=True, indent=4, separators=(',', ': ')))
