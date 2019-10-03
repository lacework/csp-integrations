API_LIST = [
    "serviceusage.googleapis.com",
    "pubsub.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "deploymentmanager.googleapis.com"
]

PROJECT_PERMISSIONS = [
    "deploymentmanager.deployments.create",
    "deploymentmanager.deployments.delete",
    "deploymentmanager.deployments.get",
    "deploymentmanager.manifests.get",
    "deploymentmanager.manifests.list",
    "resourcemanager.projects.get",
    "resourcemanager.projects.getIamPolicy",
    "resourcemanager.projects.setIamPolicy",
    "serviceusage.services.disable",
    "serviceusage.services.enable",
    "serviceusage.services.get"
]

ORG_PERMISSIONS = [
    "resourcemanager.organizations.get",
    "resourcemanager.organizations.getIamPolicy",
    "resourcemanager.organizations.setIamPolicy"
]

AUDIT_PERMISSIONS = [
    "resourcemanager.projects.get",
    "resourcemanager.projects.getIamPolicy",
    "resourcemanager.projects.setIamPolicy"
]

BUCKET_PERMISSIONS = [
    "storage.buckets.create",
    "storage.buckets.delete",
    "storage.buckets.list"
]

BUCKET_SINK_ROLES = [
    "roles/storage.objectCreator"
]

BUCKET_ROLES = [
    "roles/storage.objectViewer"
]

ROLES = [
    "roles/deploymentmanager.typeViewer",
    "roles/deploymentmanager.viewer",
    "roles/deploymentmanager.editor",
    "roles/pubsub.admin",
    "roles/owner"
]

AUDIT_ROLES = [
    "roles/logging.admin"
]

ORG_ROLES = [
    "roles/resourcemanager.organizationViewer",
    "roles/resourcemanager.organizationAdmin",
    "roles/iam.organizationRoleAdmin"
]

class Config(object):
    def __init__(self, config_json):
        self.__config_json = config_json
        self.__id_type = "PROJECT"
        self.__projectNumber = None
        self.__deploymentName = None
        self.__toIntegrate = None
        self.__laceworkAccount = None
        self.__laceworkToken = None
        self.__bucketParent = None

    def getSetupPrefix(self):
        return self.__config_json.get("setupPrefix")

    def isAuditLogSetup(self):
        return self.__config_json.get("auditLogSetupEnabled")

    def getSetupProjectId(self):
        return self.__config_json.get("setupProjectId")

    def setSetupProjectNumber(self, projectNumber):
        self.__projectNumber = projectNumber

    def getSetupProjectNumber(self):
        return self.__projectNumber

    def getGoogleServiceAccountNumber(self):
        return self.__config_json.get("googleServiceAccountNumber")

    def getComplianceSetupType(self):
        return self.__config_json.get("complianceSetup").get("idType")

    def getComplianceSetupId(self):
        return self.__config_json.get("complianceSetup").get("id")

    def isComplianceSetupEnableApi(self):
        return self.__config_json.get("complianceSetup").get("enableApi")

    def isComplianceSetupSetIAMPolicy(self):
        return self.__config_json.get("complianceSetup").get("setIamPolicy")

    def getAuditLogSetupExports(self):
        return self.__config_json.get("auditLogSetup").get("exports")

    def getAuditSetupType(self):
        return self.__config_json.get("auditLogSetup").get("exports").get("idType")

    def getAuditSetupId(self):
        return self.__config_json.get("auditLogSetup").get("exports").get("id")

    def doesBucketExist(self):
        if self.isAuditLogSetup():
            if "existingBucketName" in self.__config_json.get("auditLogSetup"):
                return True
            else:
                return False
        else:
            return False

    def getExistingBucketName(self):
        return self.__config_json.get("auditLogSetup").get("existingBucketName")

    def setDeploymentName(self, deploymentName):
        self.__deploymentName = deploymentName

    def getDeploymentName(self):
        return self.__deploymentName

    def setToIntegrate(self, toIntegrate):
        self.__toIntegrate = toIntegrate

    def getToIntegrate(self):
        return self.__toIntegrate

    def setLaceworkToken(self, laceworkToken):
        self.__laceworkToken = laceworkToken

    def getLaceworkToken(self):
        return self.__laceworkToken

    def setLaceworkAccount(self, laceworkAccount):
        self.__laceworkAccount = laceworkAccount

    def getLaceworkAccount(self):
        return self.__laceworkAccount

    def setIntegrationName(self, integrationName):
        self.__integrationName = integrationName

    def getIntegrationName(self):
        return self.__integrationName

    def setBucketParent(self, bucketParent):
        self.__bucketParent = bucketParent

    def getBucketParent(self):
        return self.__bucketParent

    def customRole(self):
        if "customRole" in self.__config_json:
            return self.__config_json['customRole']
        else:
            return True
