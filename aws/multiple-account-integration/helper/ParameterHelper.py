import re
from model import Parameter


class ParameterHelper:

    parameter = None  # type : model.Parameter
    _stack_index = None  # type : string
    _log_helper = None  # type : helper.ErrorHelper

    def __init__(self, parameter, stack_index, log_helper):
        self._stack_index = stack_index
        self._log_helper = log_helper
        self.parameter = Parameter.Parameter()
        self.parameter.extract_data(parameter)

    def validate_param(self, param_value, param_name):

        if self.parameter.min_length is not None and len(param_value) < int(self.parameter.min_length):
            self._log_helper.add_log(self._stack_index, param_name + " must have min length " + self.parameter.min_length)
            return False

        if self.parameter.max_length is not None and len(param_value) > int(self.parameter.max_length):
            self._log_helper.add_log(self._stack_index, param_name + " must have max length " + self.parameter.max_length)
            return False

        if self.parameter.allowed_pattern is not None:
            self.parameter.allowed_pattern = self.parameter.allowed_pattern.encode('ascii', 'replace')
            pattern = re.compile(self.parameter.allowed_pattern)
            if not pattern.match(param_value):
                if self.parameter.message:
                    self._log_helper.add_log(self._stack_index, param_name + ": " + self.parameter.message)
                else:
                    self._log_helper.add_log(self._stack_index, "Invalid " + param_name +
                                             " value. Must match pattern " + self.parameter.allowed_pattern)
                return False

        return True
