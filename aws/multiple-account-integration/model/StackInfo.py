
class StackInfo:

    client = None  # type : boto3.Cloudformation Client
    stack_id = None  # type : string
    stack_index = None  # type : int
    template_type = None  # type : string
    role_arn = None  # type : string
    is_created_by_lacework = False  # type : bool

    def __init__(self):
        return

    def get_copy(self):
        stack_info = StackInfo()
        stack_info.stack_index = self.stack_index
        stack_info.stack_id = self.stack_id
        stack_info.template_type = self.template_type
        stack_info.client = self.client
        return stack_info

    def set_created_by_lacework(self, is_created_by_lacework):
        self.is_created_by_lacework = is_created_by_lacework

    def set_role_arn(self, role_arn):
        self.role_arn = role_arn

    def set_stack_id(self, stack_id):
        self.stack_id = stack_id

    def set_stack_index(self, stack_index):
        self.stack_index = stack_index

    def set_template_type(self, template_type):
        self.template_type = template_type

    def set_client(self, client):
        self.client = client
