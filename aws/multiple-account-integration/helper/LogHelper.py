class ErrorHelper:

    _logs = None  # type : Dict
    _final_status = None  # type : string
    _stack_names = []  # type : lst

    def __init__(self):
        self._logs = {}

    def get_name_for_indexes(self, stack_list):
        index = 0
        for stack in stack_list:
            if stack['Name']:
                self._stack_names.append(stack['Name'])
            else:
                self._stack_names.append("Stack Index " + str(index + 1))
            index = index + 1

    def add_log(self, stack_index, log, template_type):
        if stack_index != 'All':
            stack_index = self._stack_names[stack_index]
        print("["+str(stack_index)+"] ("+str(template_type)+") - " + log+" \n")

    def add_log_result(self, stack_index, log, template_type, stack_name):
        if not template_type:
            template_type = "All"
        self.add_log(stack_index, log, template_type)
        self.add_result(stack_index, log, template_type, stack_name)

    def add_result(self, stack_index, log, template_type, stack_name):
        stack_index = self._stack_names[stack_index]
        if stack_index not in self._logs:
            self._logs[stack_index] = {}
        if template_type not in self._logs[stack_index]:
            self._logs[stack_index][template_type] = ""
        self._logs[stack_index][template_type] = ("(" + stack_name + ")  - "+log)

    def set_final_status(self, result):
        self._final_status = result

    def print_result(self):
        print("----------------------------------- Completed -----------------------------------")
        stack_indexes = self._logs.keys()
        for index in stack_indexes:
            print(" {} : \n".format(index))
            stack_types = self._logs[index].keys()
            for stack_type in stack_types:
                if stack_type and self._logs[index][stack_type]:
                    print("        - ["+stack_type+"]" + self._logs[index][stack_type])
        print(self._final_status)
        # print("---------------------------------------------------------------------------------")
