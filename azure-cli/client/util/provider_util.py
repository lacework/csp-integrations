import logging
import time

from common_util import CommonUtil
from credentials.credentials_provider import ResourceCredentialsProvider


class ProviderUtil(CommonUtil):

    def __init__(self, credentialsProvider):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        super(ProviderUtil, self).__init__(credentialsProvider)

    def __registerProviderWaitUntilCompletion(self, namespace, subscription):
        resourceManagementClient = self.getResourceManagementClient(subscription.subscription_id)
        resourceManagementClient.providers.register(namespace)
        while True:
            if self.checkProviderExists(namespace, subscription):
                logging.info("Successfully Registered Provider: " + namespace + " In subscription Id: " + subscription.subscription_id + " Name: " + subscription.display_name)
                return
            time.sleep(5)

    def checkProviderExists(self, namespace, subscription):
        provider = self.__getProvider(namespace, subscription)
        if provider is None or provider.registration_state != "Registered":
            if provider is not None:
                logging.info("Provider Namespace: " + namespace + " State: " + provider.registration_state)
            else:
                raise Exception("Provider with Namespace: " + namespace + "Not Found in Subscription: " + subscription.subscription_id)
            return False
        return True

    def __getProvider(self, namespace, subscription):
        resourceManagementClient = self.getResourceManagementClient(subscription)
        for provider in resourceManagementClient.providers.list():
            if provider.namespace == namespace:
                return provider
        return None

    def registerAllResourceProviders(self, namespaces, subscription):
        resourceManagementClient = self.getResourceManagementClient(subscription)

        for namespace in namespaces:
            resourceManagementClient.providers.register(namespace)
            logging.info("Registered Resource Provider with Name: " + namespace)

    def unregisterAllResourceProviders(self, namespaces, subscription):
        resourceManagementClient = self.getResourceManagementClient(subscription)

        for namespace in namespaces:
            resourceManagementClient.providers.unregister(namespace)
            logging.info("Unregistered Resource Provider with Name: " + namespace)

    def getNotRegisteredResourceProviders(self, namespaces, subscription):
        resourceManagementClient = self.getResourceManagementClient(subscription)

        def __valid(provider, toRegister):
            return provider.namespace in toRegister and provider.registration_state != "Registered"

        return [p.namespace for p in resourceManagementClient.providers.list() if __valid(p, namespaces)]

    def waitUntilRegistered(self, namespaces, subscription):
        not_registered = self.getNotRegisteredResourceProviders(namespaces, subscription)
        while len(not_registered) > 0:
            logging.info("not registered > 0: " + ', '.join(map(str, not_registered)))
            logging.info("sleeping 5")
            time.sleep(5)
            not_registered = self.getNotRegisteredResourceProviders(not_registered, subscription)
