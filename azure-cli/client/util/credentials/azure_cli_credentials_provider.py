from msrestazure.azure_active_directory import AADMixin
import json
import codecs
import os
import requests
from datetime import datetime as dt

class AzureEnvironmentSessionCredentials(AADMixin):
    '''Get an Azure authentication token from CLI's cache.

       Will only work if CLI local cache has an unexpired auth token (i.e. you ran 'az login'
           recently), or if you are running in Azure Cloud Shell (aka cloud console)
   '''
    def __init__(self,
                 client_id=None, secret=None, **kwargs):
        if not client_id:
            # Default to Client ID of cli.
            client_id = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'
        super(AzureEnvironmentSessionCredentials, self).__init__(client_id, None)
        self._configure(**kwargs)
        self.secret = secret
        self.set_token()


    def set_token(self):
        """Get token using Azure cli token or azure session
        """
        super(AzureEnvironmentSessionCredentials, self).set_token()
        try:

            # If running in cloud shell send resource and get token directly for the cloud shell
            token, isCloudShell = self.get_access_token_from_cli(self.resource)
            if token is None:
                raise Exception("Error Fetching token from cli or portal client")
            if not isCloudShell:
                token = self._context.acquire_token_with_refresh_token(token['refreshToken'], self.id,
                                         self.resource, client_secret=None)
            token['_client_id'] = self.id;
            self.token = self._convert_token(token)
        except Exception as err:
            raise err

    def get_access_token_from_cli(self, resource):
        '''Get an Azure authentication token from CLI's cache.

        Will only work if CLI local cache has an unexpired auth token (i.e. you ran 'az login'
            recently), or if you are running in Azure Cloud Shell (aka cloud console)

        Returns:
            An Azure authentication token string.
            A boolean indicating if running in cloud shell
        '''

        # check if running in cloud shell, if so, pick up token from MSI_ENDPOINT
        if 'ACC_CLOUD' in os.environ and 'MSI_ENDPOINT' in os.environ:
            endpoint = os.environ['MSI_ENDPOINT']
            headers = {'Metadata': 'true'}
            body = {"resource": resource }
            ret = requests.post(endpoint, headers=headers, data=body)
            return ret.json(), True

        else:  # not running cloud shell
            home = os.path.expanduser('~')
            sub_username = ""

            # 1st identify current subscription
            azure_profile_path = home + os.sep + '.azure' + os.sep + 'azureProfile.json'
            if os.path.isfile(azure_profile_path) is False:
                print('Error from get_access_token_from_cli(): Cannot find ' + azure_profile_path)
                return None, False
            with codecs.open(azure_profile_path, 'r', 'utf-8-sig') as azure_profile_fd:
                subs = json.load(azure_profile_fd)
            for sub in subs['subscriptions']:
                if sub['isDefault'] == True:
                    sub_username = sub['user']['name']
            if sub_username == "":
                print('Error from get_access_token_from_cli(): Default subscription not found in ' + \
                      azure_profile_path)
                return None, False

            # look for acces_token
            access_keys_path = home + os.sep + '.azure' + os.sep + 'accessTokens.json'
            if os.path.isfile(access_keys_path) is False:
                print('Error from get_access_token_from_cli(): Cannot find ' + access_keys_path)
                return None, False
            with open(access_keys_path, 'r') as access_keys_fd:
                keys = json.load(access_keys_fd)

            # loop through accessTokens.json until first unexpired entry found
            for key in keys:
                if key['userId'] == sub_username:
                    if 'accessToken' not in keys[0]:
                        print('Error from get_access_token_from_cli(): accessToken not found in ' + \
                              access_keys_path)
                        return None, False
                    if 'tokenType' not in keys[0]:
                        print('Error from get_access_token_from_cli(): tokenType not found in ' + \
                              access_keys_path)
                        return None, False
                    if 'expiresOn' not in keys[0]:
                        print('Error from get_access_token_from_cli(): expiresOn not found in ' + \
                              access_keys_path)
                        return None, False
                    expiry_date_str = key['expiresOn']

                    # check date and skip past expired entries
                    if 'T' in expiry_date_str:
                        exp_date = dt.strptime(key['expiresOn'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    else:
                        exp_date = dt.strptime(key['expiresOn'], '%Y-%m-%d %H:%M:%S.%f')
                    if exp_date < dt.now():
                        continue
                    else:
                        return key, False

            # if dropped out of the loop, token expired
            print('Error from get_access_token_from_cli(): token expired. Run \'az login\'')
            return None, False