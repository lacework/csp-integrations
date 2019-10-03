SERVICE_ACCOUNT = """
resources:
- name: %serviceAccountName
  type: iam.v1.serviceAccount
  properties:
    accountId: %serviceAccountId
    displayName: %serviceAccountId
"""

BUCKET_CREATION = """
- type: storage.v1.bucket
  name: %bucketName
  accessControl:
    gcpIamPolicy:
      bindings:
      - role: roles/storage.objectViewer
        members:
        - "serviceAccount:$(ref.%serviceAccountName.email)"
      - role: roles/storage.legacyBucketOwner
        members:
        - "projectEditor:%projectId"
        - "projectOwner:%projectId"
      - role: roles/storage.legacyBucketReader
        members:
        - "projectViewer:%projectId"
"""

TOPIC_CREATION = """
- type: pubsub.v1.topic
  name: %topicName
  properties:
    topic: %topicProp
  accessControl:
    gcpIamPolicy:
      bindings:
      - role: roles/pubsub.publisher
        members:
        - "serviceAccount:service-%projectNumber@gs-project-accounts.iam.gserviceaccount.com"
"""

SUBSCRIPTION_CREATION = """
- type: pubsub.v1.subscription
  name: %subscriptionName
  properties:
    subscription: %subscriptionProp
    topic: $(ref.%topicName.name)
    ackDeadlineSeconds: 300
    messageRetentionDuration: 432000s
  accessControl:
    gcpIamPolicy:
      bindings:
      - role: roles/pubsub.subscriber
        members:
        - "serviceAccount:$(ref.%serviceAccountName.email)"
"""

NOTIFICATION_CREATION = """
- name: %notificationName
  type: gcp-types/storage-v1:notifications
  properties:
    bucket: $(ref.%bucketName.name)
    topic:  $(ref.%topicName.name)
    payload_format: JSON_API_V1
    eventType: OBJECT_FINALIZE
  metadata:
    dependsOn:
      - %topicName
"""

SINK_CREATION = """
- type: gcp-types/logging-v2:%resourceTypeAudit.sinks
  name: %sinkName
  properties:
    sink: %sinkProp
    destination: "storage.googleapis.com/$(ref.%bucketName.name)"
    filter: protoPayload.@type=type.googleapis.com/google.cloud.audit.AuditLog AND NOT protoPayload.methodName:'storage.objects'
    uniqueWriterIdentity: true
    %resourceTypeSingle: "%resourceIdAudit"
    includeChildren: true
"""

BUCKET_DEPENDENCY = """
  metadata:
    dependsOn:
      - %bucketName
"""

BUCKET_BINDING = """
- name: %bucketBindingName
  action: gcp-types/storage-v1:storage.buckets.setIamPolicy
  properties:
    bucket: $(ref.%bucketName.name)
    project: %projectId
    bindings:
    - role: roles/storage.objectCreator
      members:
      - "$(ref.%sinkName.writerIdentity)"
    - role: roles/storage.objectViewer
      members:
      - "serviceAccount:$(ref.%serviceAccountName.email)"
    - role: roles/storage.legacyBucketOwner
      members:
      - "projectEditor:%projectId"
      - "projectOwner:%projectId"
    - role: roles/storage.legacyBucketReader
      members:
      - "projectViewer:%projectId"
"""
CUSTOM_ROLE = """
- name: %customRole
  type: gcp-types/iam-v1:%roleType.roles
  properties:
    parent: "%roleParent"
    roleId: %roleId
    role:
      title: %customRole
      stage: ALPHA
      includedPermissions:
      - serviceusage.services.disable
      - serviceusage.services.enable
      - serviceusage.services.get
"""

ASSIGN_ROLE = """
- name: %setupPrefix-custom-role-lacework
  type: gcp-types/cloudresourcemanager-v1:virtual.%resourceType.iamMemberBinding
  properties:
    resource: "%resourceId"
    member: serviceAccount:$(ref.%serviceAccountName.email)
    role: $(ref.%customRole.name)
"""

VIEWER_BINDING = """
- name: %setupPrefix-iam-binding-viewer-lacework
  type: gcp-types/cloudresourcemanager-v1:virtual.%resourceType.iamMemberBinding
  properties:
    resource: "%resourceId"
    member: serviceAccount:$(ref.%serviceAccountName.email)
    role: roles/viewer
"""

SECURITY_REVIEWER_BINDING = """
- name: %setupPrefix-iam-binding-security-reviewer-lacework
  type: gcp-types/cloudresourcemanager-v1:virtual.%resourceType.iamMemberBinding
  properties:
    resource: "%resourceId"
    member: serviceAccount:$(ref.%serviceAccountName.email)
    role: roles/iam.securityReviewer
"""

ORG_VIEWER_BINDING = """
- name: %setupPrefix-iam-binding-organization-viewer-lacework
  type: gcp-types/cloudresourcemanager-v1:virtual.%resourceType.iamMemberBinding
  properties:
    resource: "%resourceId"
    member: serviceAccount:$(ref.%serviceAccountName.email)
    role: roles/resourcemanager.organizationViewer
"""

ACCOUNT_KEY = """
- name: %setupPrefix-service-account-key-lacework
  type: iam.v1.serviceAccounts.key
  properties:
    name: projects/%projectId/serviceAccounts/$(ref.%serviceAccountName.email)/keys/json
    parent: projects/%projectId/serviceAccounts/$(ref.%serviceAccountName.email)
    privateKeyType: TYPE_GOOGLE_CREDENTIALS_FILE
    keyAlgorithm: KEY_ALG_RSA_2048
"""

OUTPUT = "outputs:"

OUTPUT_KEY = """
- name: privateKey
  value: $(ref.%setupPrefix-service-account-key-lacework.privateKeyData)
"""

OUTPUT_SUBSCRIPTION = """
- name: subscription
  value: $(ref.%subscriptionName.name)
"""

OUTPUT_SINK = """
- name: sinkEmail
  value: $(ref.%sinkName.writerIdentity)
"""