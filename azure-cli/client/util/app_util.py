import datetime
import json
import logging
import time

from azure.graphrbac import GraphRbacManagementClient
from azure.graphrbac.models import ApplicationCreateParameters, PasswordCredential

from common_util import CommonUtil
from credentials.credentials_provider import ResourceCredentialsProvider

SERVICE_PRINCIPALS_LIST = ["Microsoft Graph", "Azure Key Vault", "Azure Storage", "Windows Azure Active Directory"];

import os, inspect

resourceAccessFilePath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/resource_access.json"


class AppUtil(CommonUtil):
    def __init__(self, credentialsProvider):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        super(AppUtil, self).__init__(credentialsProvider)
        self.__identifierUrl = credentialsProvider.getConfig().getIdentifierUrl()

    def createAppWithRetry(self, key, appName, retry):
        if retry <= 0:
            raise Exception("App Creation Failed")
        logging.info("Attempting to create App: " + appName + ". Retries Remaining: " + str((retry - 1)))
        appId = self.createApp(key, appName)
        for i in range(1, 4):
            time.sleep(5)
            logging.info("Attempting to fetch App Id   Attempt " + str((i)))
            appId = self.getAppId()
            if appId is not None:
                return appId
        if appId is None:
            return self.createAppWithRetry(key, appName, retry - 1)
        return appId

    def createApp(self, key, appName):
        passwordCredential = PasswordCredential(start_date=datetime.datetime.now(),
            end_date="2299-12-31T06:08:04.0863895Z",
            value=key
        )

        resourceAccess = self.__getResourceAccessJson();

        if len(resourceAccess) == 0:
            raise Exception("No resource accesses found")
        parameters = ApplicationCreateParameters(available_to_other_tenants=False,
            display_name=appName,
            homepage=self.__identifierUrl,
            identifier_uris=[self.__identifierUrl],
            required_resource_access=resourceAccess,
            password_credentials=[passwordCredential]
        )
        application = self.getGraphRbacClient().applications.create(parameters)

        logging.info("Created App with id: " + application.app_id)
        return application.app_id

    def createAppIfNotExist(self, key, appName):
        appId = self.getAppId()
        logging.info("Attempting to create App: " + appName)
        if appId is None:
            logging.info("App not found creating app")
            appId = self.createAppWithRetry(key, appName, 3)
        else:
            logging.info("App already exists: " + appId)
        if appId is None:
            logging.exception("Error Creating App")
            raise Exception("Error creating app")
        return appId;

    def deleteAppIfExist(self):
        objId = self.getAppObjId()
        if objId is None:
            logging.debug("Could not find Application.")
            return
        self.getGraphRbacClient().applications.delete(objId)

    def addClientSecret(self, key):
        appObjId = self.getAppObjId()

        if appObjId is None:
            return

        passwordCredential = PasswordCredential(
            start_date=datetime.datetime.now(),
            end_date="2299-12-31T06:08:04.0863895Z",
            value=key
        )

        credentials = [c for c in self.getGraphRbacClient().applications.list_password_credentials(appObjId)]
        credentials.append(passwordCredential)
        self.getGraphRbacClient().applications.update_password_credentials(appObjId, credentials)

    def __getAppObjId(self, identifierUrl):
        isinstance(self.__graphRbacClient, GraphRbacManagementClient)
        for app in self.__graphRbacClient.applications.list():
            if identifierUrl in app.identifier_uris:
                return app.id
        return None

    def __getResourceAccessJson(self):
        servicePrincipalList = self.__getAvailableServicePrincipals()
        resourceAccessJson = self.__getResourceAccessFile()
        resourceAccess = []
        for key, val in resourceAccessJson.iteritems():
            if key in servicePrincipalList:
                resourceAccess.append(val)
        return resourceAccess

    def __getResourceAccessFile(self):
        resourceAccessString = ""
        try:
            with open(resourceAccessFilePath, 'r') as myfile:
                resourceAccessString = myfile.read().replace('\n', '')
        except Exception as e:
            logging.error("Error resource access json file", e);
            raise e
        return json.loads(resourceAccessString)

    def __getAvailableServicePrincipals(self):
        servicePrincialList = []
        for sp in self.getGraphRbacClient().service_principals.list():
            displayName = sp.display_name
            if displayName in SERVICE_PRINCIPALS_LIST:
                servicePrincialList.append(displayName)
        return servicePrincialList
