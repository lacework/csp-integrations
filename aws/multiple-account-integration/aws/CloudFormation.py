import boto3
import json
import time
from botocore import errorfactory
from model import StackInfo

'''
This class is responsible for
1) Creating connection with AWS Cloudformation using given aws credentials
2) Creating Stack using input parameters
'''


class ExecuteCloudFormation:
    _stack_info = None
    _log_helper = None  # type : helper.ErrorHelper

    def __init__(self, credentials, stack_index, log_helper):
        self._stack_info = StackInfo.StackInfo()
        self._stack_info.set_stack_index(stack_index)
        self._log_helper = log_helper
        self._create_client(credentials)

    def is_client_created(self):
        if self._stack_info.client:
            return True
        return False

    def set_template(self, template_type):
        self._stack_info.set_template_type(template_type)

    # creating aws cloudformation client
    def _create_client(self, credentials):

        try:
            if credentials.profile_name:
                # create session using profile name
                session = boto3.Session(
                    profile_name=credentials.profile_name,
                    region_name=credentials.region
                )

                # create cloud formation client
                client = session.client(
                    'cloudformation'
                )
            else:
                # create cloud formation client
                client = boto3.client(
                    'cloudformation',
                    region_name=credentials.region,
                    aws_access_key_id=credentials.aws_access_key_id,
                    aws_secret_access_key=credentials.aws_secret_access_key,
                )
            self._stack_info.set_client(client)
            if credentials.role_arn:
                self._stack_info.set_role_arn(credentials.role_arn)

        except errorfactory.ClientError:  # boto3 client error
            self._log_helper.add_log_result(self._stack_info.stack_index, "Invalid aws credentials.",
                                            "All", "All")  # log the error for a user
        except Exception as e:  # unknown exception
            self._log_helper.add_log_result(self._stack_info.stack_index, e.message,
                                            "All", "All")  # log the error for a user

    def _set_stack_created_by(self, tags):
        for tag in tags:
            if tag['Key'] == 'created_by' and tag['Value'] == 'lacework':
                self._stack_info.set_created_by_lacework(True)
                return
        self._stack_info.set_created_by_lacework(False)

    # check stack is already exist with same stack name
    def _check_stack_name_exist(self, stack_name):
        try:
            if self._stack_info.client:
                response = self._stack_info.client.describe_stacks(
                    StackName=stack_name
                )
                if len(response['Stacks']) > 0:
                    stack = response['Stacks'][0]
                    self._log_helper.add_log_result(self._stack_info.stack_index, "Stack < " +
                                                    stack_name + "> - stack id <" + stack['StackId'] +
                                                    "> already exist with status = " + stack['StackStatus'],
                                                    self._stack_info.template_type, stack_name)
                    self._stack_info.set_stack_id(stack['StackId'])
                    self._set_stack_created_by(stack['Tags'])
                    return stack['StackStatus']
                else:
                    return "0"

        except errorfactory.ClientError as e:  # boto3 client error
            if e.message.find("Stack with id " + stack_name + " does not exist"):
                return "0"
            self._log_helper.add_log_result(self._stack_info.stack_index, e.message,
                                            self._stack_info.template_type, stack_name)
        except Exception as e:  # unknown exception
            self._log_helper.add_log_result(self._stack_info.stack_index, "Error while checking stack exist or not :  "+e.message,
                                            self._stack_info.template_type, stack_name)  # log the error for a user

        return stack_name

    def _is_stack_created(self, stack_name, stack_tracker, execution_type):
        status = self._check_stack_name_exist(stack_name)
        if status == '0':
            return False
        elif status == 'ROLLBACK_COMPLETE':
            if self._stack_info.is_created_by_lacework:
                delete = raw_input("This stack was created by Lacework. "
                                   "Do you want to delete it and create a new one? (Yes/No) \n")
                if delete == "Yes" or delete == "yes":
                    if self._delete_stack(stack_name):
                        self.get_waiter(stack_tracker, True)
                        return False

            stack_tracker.add_failed_exist()
            return True
        elif status == 'CREATE_COMPLETE':
            stack_tracker.add_exist()
            return True
        else:
            if execution_type == 'sync':
                self.get_waiter(stack_tracker, False)
            else:
                stack_tracker.add_stack(self._stack_info.get_copy())
            return True

    def _delete_stack(self, stack_name):
        try:
            self._log_helper.add_log(self._stack_info.stack_index, "Deleting Stack.", self._stack_info.template_type)
            response = self._stack_info.client.delete_stack(
                StackName=stack_name
            )
            return True
        except errorfactory.ClientError as e:
            self._log_helper.add_log_result(self._stack_info.stack_index, "Skipping deletion, "
                                            "Error while deleting stack : " + e.message,
                                            self._stack_info.template_type, stack_name)
        except Exception as e:
            self._log_helper.add_log_result(self._stack_info.stack_index, "Skipping deletion, "
                                            "Error while deleting stack : " + e.message,
                                            self._stack_info.template_type, stack_name)
        return False

    # Creating stack using
    def create_stack(self, stack_name, template, token, tags, stack_tracker, execution_type):
        try:
            print("#############################################")

            if not self._is_stack_created(stack_name, stack_tracker, execution_type):

                if self._stack_info.role_arn:
                    _response = self._stack_info.client.create_stack(
                        StackName=stack_name,  # Stack name
                        TemplateBody=template.template_body,  # template body given by Lacework
                        Parameters=template.params,  # parameters passed in config file
                        Capabilities=[  # necessary for IAM role related changes
                            'CAPABILITY_NAMED_IAM',
                        ],
                        RoleARN=self._stack_info.role_arn,
                        Tags=tags,
                        OnFailure='ROLLBACK',  # on fail needs to rollback
                        ClientRequestToken=token  # unique token to get track of stack creation
                        # and eliminate duplicate stack creation
                    )
                else:
                    _response = self._stack_info.client.create_stack(
                        StackName=stack_name,  # Stack name
                        TemplateBody=template.template_body,  # template body given by Lacework
                        Parameters=template.params,  # parameters passed in config file
                        Capabilities=[  # necessary for IAM role related changes
                            'CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM'
                        ],
                        Tags=tags,
                        OnFailure='ROLLBACK',  # on fail needs to rollback
                        ClientRequestToken=token  # unique token to get track of stack creation
                        # and eliminate duplicate stack creation
                    )
                return self._parse_stack_creation(_response, execution_type, stack_tracker)

        except ValueError as e:
            self._log_helper.add_log_result(self._stack_info.stack_index, "Error while creating stack : " + e.message,
                                            self._stack_info.template_type, stack_name)
        except errorfactory.ClientError as e:
            self._log_helper.add_log_result(self._stack_info.stack_index, "Error while creating stack : " + e.message,
                                            self._stack_info.template_type, stack_name)
        except Exception as e:
            self._log_helper.add_log_result(self._stack_info.stack_index, "Error while creating stack : " + e.message,
                                            self._stack_info.template_type, stack_name)

        return "0"

    def _parse_stack_creation(self, response, execution_type, stack_tracker):

        if 'ResponseMetadata' in response and \
                response['ResponseMetadata']['HTTPStatusCode'] < 300:
            self._log_helper.add_log(self._stack_info.stack_index, "Started Creating stack with id <{}>".format(response['StackId'])
                                     , self._stack_info.template_type)
            self._stack_info.set_stack_id(response['StackId'])
            if execution_type == 'sync':
                self.get_waiter(stack_tracker, False)
            else:
                stack_tracker.add_stack(self._stack_info.get_copy())
            return response['StackId']  # return stack id
        else:
            self._log_helper.add_log(self._stack_info.stack_index, "There was an Unexpected error. response: {0}"
                                     .format(json.dumps(response)), self._stack_info.template_type)

        return "0"

    def get_waiter(self, stack_tracker, track_deleted):
        desc = stack_tracker.get_desc(self._stack_info)

        print("----------")\

        if track_deleted:
            if desc == -1 or desc['StackStatus'] == 'DELETE_COMPLETE':
                self._log_helper.add_log(self._stack_info.stack_index, "Delete complete.",
                                         self._stack_info.template_type)
                return
            self._log_helper.add_log(self._stack_info.stack_index, desc['StackStatus'], self._stack_info.template_type)
        else:
            self._log_helper.add_log(self._stack_info.stack_index, desc['StackStatus'], self._stack_info.template_type)
            if desc['StackStatus'] == 'CREATE_COMPLETE':
                stack_tracker.add_completed()
                self._log_helper.add_log_result(self._stack_info.stack_index,
                                                "Stack created with id <{}>".format(desc['StackId']),
                                                self._stack_info.template_type, desc['StackName'])
                return
            elif desc['StackStatus'] == 'ROLLBACK_COMPLETE':
                self._log_helper.add_log_result(self._stack_info.stack_index,
                                                "Stack creation failed for stackId <{}>".format(desc['StackId']),
                                                self._stack_info.template_type, desc['StackName'])
                stack_tracker.add_failed()
                return
        time.sleep(5)
        self.get_waiter(stack_tracker, track_deleted)
