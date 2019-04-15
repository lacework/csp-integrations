import sys
from helper import TemplateHelper, ConfigHelper, LogHelper, StackCreationTracker
from model import Template
from aws import CloudFormation

'''
This class is executor class. It uses models and helper classes to create cloud formation stacks.
1) Initializing models
2) Initializing Helpers
3) check for error occurred while reading config/template and stop executing
4) Iterate through all the stacks added in config file and create cloud formation for them
'''


class Executor:

    def __init__(self):
        return

    @staticmethod
    def execute(config_path, execution_type, access_token, account):

        try:
            # initializing error handlers
            log_helper = LogHelper.ErrorHelper()

            # initializing config helpers
            config_helper = ConfigHelper.ConfigHelper(config_path, log_helper)
            # getting config model
            config = config_helper.get_default_config()
            # If error occurred while reading config file
            if not config or not config.urls or config.stack_count == 0 or config.default_credentials == -1:
                return

            template_types = config.urls.keys()

            # Initializing Template models
            template_models = {}
            for template_type in template_types:
                template_models[template_type] = Template.Template(template_type)

            # initializing template helper
            template_helpers = {}
            for template_type in template_types:
                template_helpers[template_type] = TemplateHelper.TemplateHelper(config.urls[template_type], log_helper, template_type, access_token, account)
                template_models[template_type].template_body = template_helpers[template_type].get_template()
                # if error occurred while reading template file
                if not template_models[template_type].template_body:
                    # print(log_helper.get_all_errors())
                    return

            # get stack count specifies in config
            stack_count = config.stack_count

            stack_tracker = StackCreationTracker.StackCreationTracker(log_helper)

            # for every stack, create a cloudformation stack
            for stack_index in range(stack_count):

                # getting aws credentials for the account
                credentials = config_helper.get_stack_credentials(stack_index, config.default_credentials)
                # if credentials not found for the account then skip the account
                # Errors are already logged while getting credential data
                if not credentials:
                    stack_tracker.add_failed()
                    continue

                # create cloudformation object with account's aws credentials
                cloudformation = CloudFormation.ExecuteCloudFormation(credentials, stack_index, log_helper)
                if not cloudformation.is_client_created():
                    stack_tracker.add_failed()
                    continue

                # fetch parameters for the account from the config file
                # this operation gets all default params and override it using account specific variable if specified
                for template_type in template_types:
                    param = config_helper.create_param_list(stack_index, template_type)

                    # only run the config for account if its enable for them
                    if not param:
                        stack_tracker.add_failed()
                        continue
                    if param == -1:
                        #  stack_tracker.add_skipped()
                        continue

                    # get stack name for the config
                    # if stack name not specified per stack, use the default stack
                    stack_name = config_helper.get_stack_name_for_index(stack_index, config.stack_name, template_type)
                    if not stack_name:
                        stack_tracker.add_failed()
                        continue

                    # adding config parameters in the template specific format
                    # This operation validates the params according to the template and logs error if any occurred
                    # It also validates for any unnecessary input given in the config file and raises an error
                    template_helpers[template_type].add_param_list(param, template_models[template_type], stack_index)

                    # get tags to be added while stack creation
                    # This step involve 2 steps
                    # 1) getting tags from config
                    # 2) convert them in template specific format
                    tag_lst = config_helper.create_tag_list(stack_index, template_type)
                    tag_lst = template_helpers[template_type].create_tag_list(tag_lst)

                    # if template params are set properly
                    if template_models[template_type].params:
                        # Creating stack for the account with token = "token-account"
                        # token helps to get track of stack creation and prevents duplicate stack creation from template
                        # if error occurred, it returns 0
                        cloudformation.set_template(template_type)
                        stack_id = cloudformation.create_stack(stack_name, template_models[template_type],
                                                               template_type + "-" + str(stack_index), tag_lst,
                                                               stack_tracker, execution_type)

                        # if stack is created successfully, logging stack id
                        # if stack_id != "0":
                        #     log_helper.add_log(stack_index, "Stack creation started with id - " + stack_id,
                        #                        template_type)

            stack_tracker.start_tracking()
            log_helper.print_result()
            # printing all the errors / success status
            # print(json.dumps(log_helper.get_all_errors(), sort_keys=True, indent=4))
        except KeyboardInterrupt:
            print("Stopping process, Interrupted by user.")
            exit(1)
        except Exception as e:
            print("Error while Execution: {}".format(e.message))


if __name__ == "__main__":
    try:
        Executor.execute(*sys.argv[1:])
    except Exception as e:
        print("Error while Execution: {}".format(e.message))
