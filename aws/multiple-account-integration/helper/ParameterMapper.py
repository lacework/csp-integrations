class ParameterMapper:

    _parameter_map = None  # type : dict

    def __init__(self):
        self._create_parameter_map()

    def _create_parameter_map(self):
        self._parameter_map = {
            "CreateNewCloudTrail": "CreateTrail"
        }

    def get_template_name(self, param_name):
        if param_name in self._parameter_map:
            return self._parameter_map[param_name]
        else:
            return param_name
