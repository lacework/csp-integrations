# Introduction
The CLI creates an integration for GCP compliance at the project level or organization level.
# Organization
The script creates a service account in the specified project and grants permissions to the service account at the organization level.
### Requirements of the User Service Account
Input Service Account with the following roles at the Organization Level:
- roles/owner
- roles/resourcemanager.organizationAdmin
### Requirements of the Integration Service Account
Integration Service Account has the following roles at the Organization Level:
- roles/Viewer - Read access to all resources
- roles/iam.securityReviewer - Permissions to get any IAM policy
- roles/resourcemanager.organizationViewer - Access only to view an Organization
### Requirements of the Service Account Project
The project must have the following API enabled.
- iam.googleapis.com
### Script Output
The cli creates a Service Account with email  lacework-cfg-sa@<projectid>.iam.gserviceaccount.com in the specified project.
It does not create a new service account key for an existing service account.

# Project
The script creates a service account in the specified project and grants permissions to the service account at the project level.
### Requirements of the User Service Account
(Using a service Account with privileges at org level does not work for project level integrations.)
Input Service Account with the following roles at the Project Level:
- roles/owner
### Requirements of the Integration Service Account
Integration Service Account has the following roles at the Project Level:
- roles/Viewer - Read access to all resources
- roles/iam.securityReviewer - Permissions to get any IAM policy
### Requirements of the Service Account Project
The project must have the following API enabled.
- iam.googleapis.com
### Script Requirements
- Requirements specified in the requirement.txt
- Python 2.7.10
### Script Output
The cli creates a Service Account with email  lacework-cfg-sa@<projectid>.iam.gserviceaccount.com in the specified project.
It does not create a new service account key for an existing service account.

# CLI Command
### Script Parameters
- ID_TYPE
    ORGANIZATION :- If you want to integrate an organization
    PROJECT:- If you want to integrate a project.
- ID
    Project or organization Id depending on the id type
- SERVICE_ACCOUNT_PROJECT_ID
    If you are integrating a project it will be the same project Id. If you are integrating an organization, you will have to select one of the projects in which we will create a service account.
- ENABLE_API
    The script will prompt you whether you want to enable the following APIs in the project:
    - iam.googleapis.com
    - cloudkms.googleapis.com
    - cloudresourcemanager.googleapis.com
    - compute.googleapis.com
    - dns.googleapis.com
    - monitoring.googleapis.com
    - logging.googleapis.com
    - storage-component.googleapis.com
- MODIFY_IAM_POLICY
    If the user grants consent to the application, the CLI will modify the project or Org IAM policy, depending on the ID_TYPE.
### Interactive

Command
```./run.sh  --mode interactive```
The service account credentials file needs to be in the path ```client/sa_credentials.json```

### NonInteractive

```./run.sh --mode non-interactive --id-type <ORGANIZATION|PROJECT> --id <ORG/PROJECT ID> --sa-project-id <SA_PROJECT_ID> --enable-api false --set-iam-policy true```

The service account credentials file needs to be in the path ```client/sa_credentials.json```
- Id-type : ORGANIZATION or PROJECT
- Id: Project or Organization Id
- sa-project-id: Service Account Project Id
- enable-api: Enable APIs in the project (true/false)
- set-iam-policy: Set Iam policy in org or project (true/false)

### License

This project is made available under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).