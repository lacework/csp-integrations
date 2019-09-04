import logging, json
import time

class AppManager():
    def __init__(self, config, util):
        self.__config = config
        self.util = util
    def run(self):

        if not self.__config.isCloudShell():
            checkPrivileges = self.util.validateUserServiceAccountRole()
            if not checkPrivileges:
                logging.info("User Service Account does not have the necessary privileges")
                exit(1)

        if not self.util.validateProjectId(self.__config.getServiceAccountProjectId()):
            logging.info("Service Account Project Id not found: " + self.__config.getServiceAccountProjectId())
            exit(1)

        api_success_list, api_error_list =  self.util.enableApi()

        service_account, key = self.util.createServiceAccountIfNotExists()

        setIamPolicy = True
        try:
            max = 3
            for i in range(1, max):
                try:
                    self.util.setIAMPolicy(service_account['email'])
                    setIamPolicy = True
                    break
                except Exception as e:
                    if i == max - 1:
                        setIamPolicy = False
                        raise e
                    logging.warn("Could not Set IAM Policy Attempt: " + str(i) + " Retrying.")
                    time.sleep(i + 2)
        except:
            logging.exception("Could not set IAM Policy")
        return api_success_list, api_error_list, service_account, key, setIamPolicy
