import logging
import time

from common_util import CommonUtil
from credentials.credentials_provider import ResourceCredentialsProvider


class GrantUtil(CommonUtil):

    def __init__(self, credentialsProvider):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        super(GrantUtil, self).__init__(credentialsProvider)

    def grantPermission(self, app_id):
        self.__createServicePrincipal(app_id)

    def waitForServicePrincipal(self, app_id):
        while len([sp for sp in self.getGraphRbacClient().service_principals.list() if sp.app_id == app_id]) <= 0:
            time.sleep(2)

    def __createServicePrincipal(self, app_id):
        for servicePrincipal in self.getGraphRbacClient().service_principals.list():
            if servicePrincipal.app_id == app_id:
                logging.info("Service Principal already exists. Skipping creation of Service Principal.")
                return

        self.getGraphRbacClient().service_principals.create({
            'app_id': app_id,
            'account_enabled': True
        })
