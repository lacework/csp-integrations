import json
import os
import urllib
import random
import string
from ParameterHelper import ParameterHelper
from ParameterMapper import ParameterMapper


class TemplateHelper:

    _template_string = None  # type :  string
    _mandatory_params = None  # type :  dict
    _log_helper = None  # type : helper.ErrorHelper
    _parameter_mapper = None  # type : ParameterMapper
    _template_type = None  # type : string
    _extIds = set()

    def __init__(self, template_path, log_helper, template_type, access_token, account):
        try:
            self._log_helper = log_helper
            self._parameter_mapper = ParameterMapper()
            template = None
            if os.path.isfile(template_path):
                # open the file with read permission
                template = open(template_path, 'r')
            else:
                opener = urllib.URLopener()
                opener.addheader('token', access_token)
                template = opener.open(template_path.replace('%account', account))
            # read file content
            self._template_string = template.read().replace('%token', access_token)

            # get parameters to be passes to template

            template_json = json.loads(self._template_string)
            self._mandatory_params = template_json['Parameters']
            # closing the file
            template.close()
        except Exception as e:  # if file is not present or having read permission
            self._log_helper.add_log('All', "Error while reading template file : " + str(e), template_type)

    # get template string
    def get_template(self):
        # return template string
        template_string = self._template_string
        if template_string:
            template_string = self._template_string.replace("%extid", self.get_external_id_for_stack())
        return template_string

    # create param list in template format
    def add_param_list(self, param_list, template, stack_index):
        template.params = []  # reinitializing param list for stack
        if isinstance(param_list, dict):  # check if param_list is valid dict

            # Adding externalid into param list
            param_list.update({"ExternalID": self.get_external_id_for_stack()})
            param_list = self._remove_unnecessary_params(param_list, stack_index)

            if self._validate_param_list(param_list, stack_index):  # check if param_list is not empty
                param_names = param_list.keys()
                for param_name in param_names:
                    template.add_param(param_name, param_list[param_name])  # adding individual params in the template
        else:
            self._log_helper.add_log(stack_index, "Invalid Param List", self._template_type)

        return None

    # remove unnecessary params
    def _remove_unnecessary_params(self, param_lst, stack_index):
        try:
            # get param names from template
            keys = self._mandatory_params.keys()
            new_param_list = {}
            for param in param_lst:
                param_map = self._parameter_mapper.get_template_name(param)
                # check if template param is available for the stack
                if param_map in keys:
                    new_param_list[param_map] = param_lst[param]
        except Exception as e:
            self._log_helper.add_log(stack_index, e.message, self._template_type)

        return new_param_list

    # validate the stack params against template params
    def _validate_param_list(self, param_lst, stack_index):  # param_lst
        try:

            # get param names from template
            keys = self._mandatory_params.keys()
            for param in param_lst:
                # check if template param is available for the stack
                param_helper = ParameterHelper(self._mandatory_params[param], stack_index, self._log_helper)
                if not param_helper.validate_param(param_lst[param], param):
                    return False
                keys.remove(param)

            # missing params
            if len(keys) > 0:
                self._log_helper.add_log(stack_index, "Missing parameters : " + str(keys), self._template_type)
                return False

            return True
        except KeyError as e:
            self._log_helper.add_log(stack_index, e.message + " is missing in parameters.", self._template_type)
            return False
        except ValueError as eex:
            self._log_helper.add_log(stack_index, eex.message + " is missing in parameters.", self._template_type)
            return False
        except Exception as ex:
            self._log_helper.add_log(stack_index, ex.message, self._template_type)
            return False
        
    def create_tag_list(self, tags):
        tag_list = [{"Key": "created_by", "Value": "lacework"}]
        if tags:
            tag_keys = tags.keys()
            for key in tag_keys:
                tag_list.append({"Key": key, "Value": tags[key]})
        return tag_list

    def get_external_id_for_stack(self):
        return self.external_id_generator(random.randint(2, 122))

    def external_id_generator(self, size=10):
        ext_id = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(size))
        if ext_id in self._extIds:
            return self.get_external_id_for_stack()
        else:
            return ext_id