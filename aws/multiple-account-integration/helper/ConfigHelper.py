from yaml import safe_load
from model import Config, AwsCredentials

'''
This class is responsible for
1) Reading config file from the given path
2) Extracting data from config file
3) providing and validating data passed in config file
'''


class ConfigHelper:
    _config = None  # type : dict
    _log_helper = None  # type : helper.ErrorHelper

    def __init__(self, config_path, log_helper):
        try:
            self._log_helper = log_helper

            # safely load the config file from the path
            # if config path is invalid, it will load blank
            self._config = safe_load(open(config_path))
            if not self._config:
                log_helper.add_log('All', "Error occurred while reading config file : Invalid format.", "All")
        except Exception as e:  # if not a valid path of file.
            self._config = None
            log_helper.add_log('All', "Error while reading config file : " + str(e), "All")

    # get all config data
    def get_default_config(self):
        # if config is not initialized, return none
        if not self._config:
            return None

        # Initializing config model
        config = Config.Config()
        # read and set config defaults
        config.defaults = self._get_default_params()
        config.stack_count = self._get_stack_counts()
        config.stack_name = self._get_default_stack_name()
        config.default_credentials = self._get_default_aws_credentials()
        config.urls = self._get_urls()

        # setting name for indexes in log helper
        self._log_helper.get_name_for_indexes(self._get_stacks())

        # no stack passed
        if config.stack_count == 0:
            return None
        return config

    # function to get urls for template files
    def _get_urls(self):
        try:
            # check that config is properly read from the file
            if self._config:
                # check if default is available in the config
                if 'url' not in self._config:
                    self._log_helper.add_log('All', "No urls are specified in config file.", "All")
                else:  # return default params
                    return self._config['url']
            else:
                self._log_helper.add_log('All', "Error while reading config file.", "All")

        except Exception as e:
            self._log_helper.add_log('All', e.message, "All")
        return None

    # function to get stack defaults from the config file
    def _get_default_stack_name(self):
        try:
            # proceed only if config available
            if self._config:
                # check if stack exist in config, its and dict and has stackname variable available
                if 'default-params' not in self._config or type(self._config['default-params']) is not dict \
                        or 'StackName' not in self._config['default-params']:
                    # log an error related to stack name nor exist
                    self._log_helper.add_log('All', "No Stack Default found in config file.", "All")
                    return None
                else:
                    # encode the stackname from unicode to string
                    stack_name = (self._config['default-params']['StackName']).encode('ascii', 'replace')
                    return stack_name

        except Exception as e:
            # unexpected error logging
            self._log_helper.add_log('All', e.message)
        return None

    def get_stack_name_for_index(self, stack_index, default_stack_name, template_type):
        stacks = self._get_stacks()
        stack_name = None
        if stacks and stack_index < len(stacks):
            stack = stacks[stack_index]
            if template_type in stack:
                template = stack[template_type]
                if 'StackName' in template and template['StackName']:
                    stack_name = template['StackName']
                else:
                    stack_name = default_stack_name

            if not stack_name:
                self._log_helper.add_log_result(stack_index, "No StackName found with id - " + stack_index,
                                                 template_type)
                return None
            return stack_name
        else:
            self._log_helper.add_log_result(stack_index, "No stack found at index - " + stack_index, template_type)
            return None

    # It extracts stack list from the config file
    def _get_stacks(self):
        try:
            # check that config is properly read from the file
            if self._config:
                # check if stacks is available in the config, if not, log error
                if 'stacks' not in self._config:
                    self._log_helper.add_log('All', "No stacks are specified in config file.")
                else:
                    # return stack list
                    return self._config['stacks']
            else:
                # log is config is not available
                self._log_helper.add_log('All', "Error while reading config file.")

            return None

        except Exception as e:
            # logging unexpected error
            self._log_helper.add_log('All', e.message)
        return None

    # to get stack names
    def _get_stack_counts(self):
        # get stack list from config
        stacks = self._get_stacks()

        # check stacks is a dict object
        if stacks and isinstance(stacks, list):
            # return stack names
            return len(stacks)
        else:
            return 0

    # function to get default params from the config file
    def _get_default_params(self):
        try:
            # check that config is properly read from the file
            if self._config:
                # check if default is available in the config
                if 'default-params' not in self._config:
                    self._log_helper.add_log('All', "No defaults are specified in config file.", "All")
                else:  # return default params
                    return self._config['default-params']
            else:
                self._log_helper.add_log('All', "Error while reading config file.", "All")

        except Exception as e:
            self._log_helper.add_log('All', e.message, "All")
        return None

    def create_param_list(self, stack, template_type):
        try:
            # getting default params
            param_list = self._get_default_params()
            stacks = self._get_stacks()

            # if default params are not passed in config file
            if not param_list:
                param_list = {}

            # check stack is exist in the config
            if stack < len(stacks) and template_type in stacks[stack]:
                # make param list for stack
                # get params available for the stack
                local = stacks[stack][template_type]
                # stack specific param names
                param_names = local.keys()

                # override / add stack specific params if not empty in param list
                for param_name in param_names:
                    if local[param_name]:  # if stack specific param is not blank/None/empty
                        param_list[param_name] = local[param_name]  # overriding/adding param in list
                return param_list
            else:
                # self._log_helper.add_log_result(stack, "No parameter found for CloudFormation Template.",
                #                                  template_type, "")
                return -1

        except Exception as e:
            self._log_helper.add_log_result(stack, "Error while creating parameter list for stack, " + e.message,
                                            template_type)

        return None

    def create_tag_list(self, stack_index, template_type):

        # getting all default params
        defaults = self._get_default_params()
        default_tags = {}
        # if defaults available, take default tags
        if 'default-tags' in defaults:
            default_tags = defaults['default-tags']

        # stack specific tags
        acc_tags = {}
        # get stack list from config
        stacks = self._get_stacks()

        # check stacks is a dict object and check stack is available in list
        if stacks and isinstance(stacks, dict) and stack_index in stacks:
            # get stack
            stack = stacks[stack_index]
            # check template is available in stack
            if template_type in stack:
                # get template object
                template = stack[template_type]
                # check template has tags in it
                if 'tags' in template:
                    # get template specific stack tags
                    acc_tags = template['tags']

        # creating tag list using default tags
        tag_list = default_tags.copy()
        # overriding default tags with template specific stack tags
        tag_list.update(acc_tags)

        return tag_list

    def _get_default_aws_credentials(self):
        defaults = self._get_default_params()
        aws_credentials = AwsCredentials.AwsCredentials()
        if defaults:
            if 'RoleArn' in defaults:
                aws_credentials.role_arn = defaults['RoleArn']
            if 'region' in defaults:
                aws_credentials.region = defaults['region']
            if 'Profile' in defaults:
                aws_credentials.profile_name = defaults['Profile']
            if 'aws_access_key_id' in defaults:
                aws_credentials.aws_access_key_id = defaults['aws_access_key_id']
            if 'aws_secret_access_key' in defaults:
                aws_credentials.aws_secret_access_key = defaults['aws_secret_access_key']

            # if not aws_credentials.profile_name and (not aws_credentials.aws_secret_access_key
            #                                          or not aws_credentials.aws_access_key_id):
            #     return None
            # if aws_credentials.profile_name and (aws_credentials.aws_secret_access_key
            #                                      or aws_credentials.aws_access_key_id):
            #     self._log_helper.add_log("All", "Profile name ans Aws Credentials "
            #                              "can not be specified together.", "All")
            #     return -1  # to indicate stop execution

        return aws_credentials

    def get_stack_credentials(self, stack_index, default_credentials):
        # getting credentials for stack id/stack id
        aws_credentials = AwsCredentials.AwsCredentials()
        stacks = self._get_stacks()
        if stacks and stack_index < len(stacks):
            stack = stacks[stack_index]
            if 'RoleArn' in stack:
                aws_credentials.role_arn = stack['RoleArn']
            if 'region' in stack:
                aws_credentials.region = stack['region']
            if 'Profile' in stack:
                aws_credentials.profile_name = stack['Profile']
            if 'aws_access_key_id' in stack:
                aws_credentials.aws_access_key_id = stack['aws_access_key_id']
            if 'aws_secret_access_key' in stack:
                aws_credentials.aws_secret_access_key = stack['aws_secret_access_key']

        # if no credentials passed for for stack
        if not aws_credentials.profile_name and (not aws_credentials.aws_secret_access_key
                                                 or not aws_credentials.aws_access_key_id):
            self._log_helper.add_log(stack_index, "account credentials are missing, stack creation will be skipped.",
                                     "All Stacks")
            self._log_helper.add_log_result(stack_index, "account credentials are missing, stack creation is skipped.",
                                            "All Template", "All Stacks")
        if not aws_credentials.region:
            aws_credentials.region = default_credentials.region

        if aws_credentials.profile_name and (aws_credentials.aws_secret_access_key
                                             or aws_credentials.aws_access_key_id):

            self._log_helper.add_log("stack_index", "Profile name and Aws Credentials can not be specified together.",
                                     "All Template", "All Stacks")
            self._log_helper.add_log_result(stack_index, "Profile name and Aws Credentials "
                                                         "can not be specified together.", "All Template", "All Stacks")
            return None
        # if region is not passed in stack level, use default region
        if not aws_credentials.region:
            aws_credentials.region = default_credentials.region
        return aws_credentials
