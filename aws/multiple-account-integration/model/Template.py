class Template:

    # Template body as string
    template_body = "{}"

    # params list mandatory for template
    params = []

    # Template Type
    template_type = None  # type : string

    def __init__(self, template_type):
        self.template_type = template_type

    # add params in required format of boto3 cloud formation client
    def add_param(self, param_name, param_value):
        _param = {'ParameterKey': param_name, 'ParameterValue': param_value}
        self.params.append(_param)
