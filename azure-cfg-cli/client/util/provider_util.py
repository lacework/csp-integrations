from common_util import CommonUtil
from credentials.credentials_provider import ResourceCredentialsProvider
import logging
import time

class ProviderUtil(CommonUtil):

    def __init__(self, credentialsProvider):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        super(ProviderUtil, self).__init__(credentialsProvider)
        self.__providerRegistrationList = credentialsProvider.getConfig().getProviderRegistrationList()

    def registerProvider(self):
        for subscription in self.getSubscriptions():
            self.__registerProviderInSubscription(subscription)

    def __registerProviderInSubscription(self, subscription):
        for namespace in self.__providerRegistrationList:
            result = self.__checkProviderExists(namespace,subscription)
            if result:
                logging.info("Provider Exists: " + namespace + " In subscription Id: " + subscription.subscription_id  + " Name: " + subscription.display_name)
                continue
            self.__registerProviderWaitUntilCompletion(namespace, subscription)


    def __registerProviderWaitUntilCompletion(self, namespace, subscription):
        resourceManagementClient = self.getResourceManagementClient(subscription.subscription_id)
        resourceManagementClient.providers.register(namespace)
        while True:
            if self.__checkProviderExists(namespace,subscription):
                logging.info("Successfully Registered Provider: " + namespace + " In subscription Id: " + subscription.subscription_id  + " Name: " + subscription.display_name)
                return
            time.sleep(5)


    def __checkProviderExists(self, namespace, subscription):
        provider = self.__getProvider(namespace, subscription)
        if provider == None or provider.registration_state != "Registered":
            if provider!=None:
                logging.info("Provider Namespace: " + namespace + " State: " + provider.registration_state)
            else:
                raise Exception("Provider with Namespace: " + namespace + "Not Found in Subscription: " + subscription.subscription_id)
            return False
        return True

    def __getProvider(self, namespace, subscription):
        resourceManagementClient = self.getResourceManagementClient(subscription.subscription_id)
        for provider in resourceManagementClient.providers.list():
            if provider.namespace == namespace:
                return provider
        return None
