import logging

from azure.mgmt.eventgrid.models import EventSubscriptionFilter, EventSubscription, StorageQueueEventSubscriptionDestination
from msrestazure.azure_exceptions import CloudError

from common_util import CommonUtil
from credentials.credentials_provider import ResourceCredentialsProvider


class EventSubscriptionUtil(CommonUtil):
    def __init__(self, credentialsProvider):
        isinstance(credentialsProvider, ResourceCredentialsProvider)
        super(EventSubscriptionUtil, self).__init__(credentialsProvider)

    def createEventGridSubscription(self, eventSubscriptionName, storageAccountId, queueName, subscriptionId):
        logging.info("Creating new event grid subscription with name: " + eventSubscriptionName + " in subscription: " + subscriptionId)

        eventGridClient = self.getEventGridManagementClient(subscriptionId)

        scope = storageAccountId

        destination = StorageQueueEventSubscriptionDestination(
            resource_id=storageAccountId,
            queue_name=queueName
        )

        subscriptionFilter = EventSubscriptionFilter(
            # By default, "All" event types are included
            subject_begins_with='/blobServices/default/containers/insights-operational-logs/',
            included_event_types=['Microsoft.Storage.BlobCreated']
        )

        event_subscription_info = EventSubscription(destination=destination, filter=subscriptionFilter)

        event_subscription_async = eventGridClient.event_subscriptions.create_or_update(scope, eventSubscriptionName, event_subscription_info)
        event_subscription = event_subscription_async.result()

        logging.info("Event grid subscription created successfully with name: " + eventSubscriptionName + " in subscription: " + subscriptionId)
        self.__log_item(event_subscription)

    def checkEventGridSubscriptionExists(self, eventSubscriptionName, storageAccountId, subscriptionId):
        eventGridClient = self.getEventGridManagementClient(subscriptionId)
        self.__checkEventGridSubscriptionExists(eventSubscriptionName, storageAccountId, eventGridClient)

    def __checkEventGridSubscriptionExists(self, eventSubscriptionName, storageAccountId, eventGridClient):
        try:
            event_subscription = eventGridClient.event_subscriptions.get(storageAccountId, eventSubscriptionName)
            return event_subscription is not None
        except CloudError:
            return False

    def deleteEventGridSubscription(self, eventSubscriptionName, storageAccountId, subscriptionId):
        logging.info("Deleting Event Subscription with Name: " + eventSubscriptionName)

        eventGridClient = self.getEventGridManagementClient(subscriptionId)
        scope = "/subscriptions/{}".format(subscriptionId)

        found = self.__checkEventGridSubscriptionExists(eventSubscriptionName, storageAccountId, eventGridClient)
        if not found:
            logging.debug("Event Grid Subscription not found.")
            return

        eventGridClient.event_subscriptions.delete(scope, eventSubscriptionName)

    @staticmethod
    def __log_item(group):
        logging.debug("\tName: {}".format(group.name))
        logging.debug("\tId: {}".format(group.id))
        if hasattr(group, 'location'):
            logging.debug("\tLocation: {}".format(group.location))

        props = getattr(group, 'properties', None)

        if props and hasattr(props, 'provisioning_state'):
            logging.debug("\tProperties:")
            logging.debug("\t\tProvisioning State: {}".format(props.provisioning_state))
        logging.debug("\n\n")
