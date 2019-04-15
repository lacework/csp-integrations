
class AwsCredentials:
    # AWS Credentials to connect with AWS and create Stack

    # aws_secret_access_key in config
    aws_secret_access_key = None  # type : string

    # aws_access_key_id in config
    aws_access_key_id = None  # type : string

    # profile in config
    profile_name = None  # type : string

    # RoleArn in config
    role_arn = None  # type : string

    # region for stack creation
    region = None  # type : string

    def __init__(self):
        return

