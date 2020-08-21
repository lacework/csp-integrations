class Rollback(object):
    def __init__(self, resourceGroupName, storageAccountName, queueName, logProfileName,
            eventSubName, roleDefinitionName, subscriptionId):
        self.createdApp = False
        self.createdServicePrincipal = False
        self.assignedReaderRole = False
        self.setKeyVaultPolicy = False
        self.createdResourceGroup = False
        self.createdStorageAccount = False
        self.createdQueue = False
        self.createdLogProfile = False
        self.createdEventGridSub = False
        self.createdCustomRole = False
        self.assignedCustomRole = False

        self.appId = None
        self.resourceGroupName = resourceGroupName
        self.storageAccountName = storageAccountName
        self.queueName = queueName
        self.logProfileName = logProfileName
        self.eventSubName = eventSubName
        self.roleDefinitionName = roleDefinitionName
        self.subscriptionId = subscriptionId
