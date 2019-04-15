from botocore import errorfactory
from model import ResultStatus
import time


class StackCreationTracker:

    __stacks = []  # type : lst
    __stacks1 = []  # type : lst
    __result_status = None  # type : model.ResultStatus
    __roll_backed_stacks = []
    __log_helper = None

    def __init__(self, log_helper):
        self.__log_helper = log_helper
        self.__result_status = ResultStatus.ResultStatus()

    def add_stack(self, stack_info):
        self.__stacks.append(stack_info)

    def add_completed(self):
        self.__result_status.completed = self.__result_status.completed + 1

    def add_failed(self):
        self.__result_status.failed = self.__result_status.failed + 1

    def add_failed_exist(self):
        self.__result_status.failed_exist = self.__result_status.failed_exist + 1

    def add_exist(self):
        self.__result_status.exist = self.__result_status.exist + 1

    def start_tracking(self):
        print("---------------------------------------------------------")
        self .__result_status.progress = 0
        stacks = len(self.__stacks)

        for i in range(stacks):
            self.track(self.__stacks[i])

        print("Processing : " + str(self .__result_status.progress))
        print("Successful : " + str(self.__result_status.completed))
        print("Failed : " + str(self.__result_status.failed))

        self.__stacks = self.__stacks1
        self.__stacks1 = []
        time.sleep(5)
        print("#############################################")
        if len(self.__stacks) > 0:
            self.start_tracking()
        else:
            status = "Stack Already Exists : " + str(self.__result_status.exist) + "\n" \
                     "Stack Already Exists in Rollback State  : " + str(self.__result_status.failed_exist) + "\n" \
                     "Stack Creation Successful : " + str(self.__result_status.completed) + "\n" \
                     "Stack Creation Unsuccessful : " + str(self.__result_status.failed)
            self.__log_helper.set_final_status(status)

    def get_desc(self, stack_info):
        try:
            response = stack_info.client.describe_stacks(
                StackName=stack_info.stack_id
            )
            if len(response['Stacks']) > 0:
                stack = response['Stacks'][0]
                return stack

        except errorfactory.ClientError as e:  # boto3 client error
            if e.message.find("Stack with id "+stack_info.stack_id+" does not exist"):
                return -1
            self.__log_helper.add_log(stack_info.stack_index, e.message, self.stack_info.template_type)  # log the error for a user
        except Exception as e:  # unknown exception
            self.__log_helper.add_log(stack_info.stack_index, "Error while checking stack status : "+e.message,
                                      stack_info.template_type)  # log the error for a user
        return None

    def track(self, stack_info):
        desc = self.get_desc(stack_info)
        status = desc['StackStatus']
        if status == -1:
            status = "DELETE_COMPLETE"
            self.__log_helper.add_result(stack_info.stack_index, "Deleted Successfully.", stack_info.template_type, stack_info.stack_id)
            # self.__stacks.remove(stack_info)
        elif status == 'CREATE_IN_PROGRESS' or status == 'DELETE_IN_PROGRESS' or status == 'ROLLBACK_IN_PROGRESS' or \
                status == 'REVIEW_IN_PROGRESS':
            self.__result_status.progress = self .__result_status.progress + 1
            self.__stacks1.append(stack_info)
        elif status == 'CREATE_COMPLETE':
            self.__result_status.completed = self.__result_status.completed + 1
            self.__log_helper.add_result(stack_info.stack_index, "Created Successfully.", stack_info.template_type,
                                         stack_info.stack_id)
            # self.__stacks.remove(stack_info)
        elif status == 'CREATE_FAILED' or status == 'ROLLBACK_COMPLETE' or status == 'DELETE_IN_PROGRESS' \
                or status == 'DELETE_COMPLETE':
            self.__result_status.failed = self.__result_status.failed + 1
            if status == 'ROLLBACK_COMPLETE':
                # self.__stacks.remove(stack_info)
                self.__log_helper.add_result(stack_info.stack_index, "Error : Rollbacked Successfully.", stack_info.template_type,
                                             stack_info.stack_id)
                self.__roll_backed_stacks.append(stack_info)
            else:
                self.__stacks1.append(stack_info)

        self.__log_helper.add_log(stack_info.stack_index, status, stack_info.template_type)
