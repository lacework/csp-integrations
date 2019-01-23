import logging, json
import time

class AppManager():
    def __init__(self, config, util):
        self.__config = config
        self.util = util
    def run(self):

        checkPrivileges = self.util.validateUserServiceAccountRole()
        if not checkPrivileges:
            logging.info("User Does not have the necessary privileges")
            exit(1)

        if not self.util.validateProjectId(self.__config.getServiceAccountProjectId()):
            logging.info("Service Account Project Id not found: " + self.__config.getServiceAccountProjectId())
            exit(1)

        api_success_list, api_error_list =  self.util.enableApi()

        service_account, key = self.util.createServiceAccountIfNotExists()

        self.util.setIAMPolicy(service_account['email'])
        return api_success_list, api_error_list, service_account, key
