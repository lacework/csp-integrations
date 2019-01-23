# Azure Compliance Integration CLI
 In order create an integration with azure for compliance, there needs to be an App with permissions to
all the subscriptions in the tenant that is to be monitored.
### Permission Requirements for the user running the Script
- User should have non interactive login enabled.
- The user needs to have Global Administrator role in the tenant’s directory
- Additionally, the user needs to have Owner role in all the subscriptions that he wants to monitor.
### Permission Requirements for the Integration
- Access to the graph API, KeyVault API and the Storage API.
- Restricted access to the Windows Active Directory API.(Read Directory Data access)
- Reader role for all subscriptions that the user wants to monitor
- List keys and list secrets for all the Keys and secrets in the keyvault
### Script Requirements
- Requirements specified in the requirement.txt
- Python 2.7.10
### Required Params
- userName: The email of the user
- Password: The password of the user
- tenantId: The tenant Id of the Ad in which the App is to be created.
- updatePermissionsForExistingApp:  true or false. If there already an app created, the user can set this to true to add new subscriptions that he needs to monitor. Does not create new credentials if there is an existing App.
- tenantId: The tenant Id of the AD.
- subscriptionList: The user can provide a subset of subscriptions ids or names
- allSubscriptions: true or false. If set to true all subscriptions will be considered and the subscriptionList will be ignored
- registerProviders: true or false. The App requires access to the following providers:
    - Microsoft.KeyVault
    - Microsoft.Storage
They are not registered by default. In order for the to access information related to these providers, the app needs to have access to their APIs. The app cannot be granted permission to access these APIs unless the providers are registered.  If the user chooses not to register them at that moment, he will have to give consent to the App later when he does register them.

### AppModes
#### Interactive
##### Command:
```./run.sh --mode INTERACTIVE ```
- In the interactive Mode the Cli will prompt the user to enter the necessary details.
- It will also ask the user to review entered details before beginning to execute the App Creation.
- Enter exit if you need to abort on any input prompt.
- The password input will be masked. It will show a warning if it is unable to mask the password input.
- It will detect if an app already exists and prompt you if you need to update an App.
#### Config File
##### Command:
```./run.sh --mode CONFIG_FILE```
In this mode the user place the config at the following path:
 ```client/config.json```
in the container in the following format:
```
    {
     "credentials": {
       "userName": "",
       "password": ""
     },
     "clientSecret": "",
     "updatePermissionsForExistingApp": true,
     "tenantId": "",
     "subscriptionList": [],
     "allSubscriptions": true,
     "registerProviders": false
    }
```
### License
This project is made available under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).
