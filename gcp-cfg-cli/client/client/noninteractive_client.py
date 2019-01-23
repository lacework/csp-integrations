from client_base import ClientBase
import argparse

def raiseException(ex):
    raise ex

class NonInteractiveClient(ClientBase):

    def __init__(self, config):
        ClientBase.__init__(self, config)


    def initConfig(self):
        ap = argparse.ArgumentParser()
        ap.add_argument("--id-type", required=True, type=(
        lambda x: raiseException(ValueError()) if x is None or x not in ["ORGANIZATION", "PROJECT"] else x),
                        help="id-type is either ORGANIZATION | PROJECT")
        ap.add_argument("--id", required=True,
                        type=(lambda x: raiseException(ValueError()) if x is None or len(x) == 0 else x),
                        help="id is either organization or project id depending on --idType arg")
        ap.add_argument("--sa-project-id", required=False,
                        help="sa-project-id is the id of the project where the service account is to be created")
        ap.add_argument("--enable-api", required=True, type=(
        lambda x: raiseException(ValueError()) if x is None or x not in ["true", "false"] else x),
                        help="enable-api is either true or false")
        ap.add_argument("--set-iam-policy", required=True, type=(
        lambda x: raiseException(ValueError()) if x is None or x not in ["true", "false"] else x),
                        help="set-iam-policy is either true or false")

        args, unknown = ap.parse_known_args()
        args = vars(args)

        self.config.setIdType(args["id_type"])
        self.config.setId(args["id"])

        if self.config.getIdType() == "ORGANIZATION":
            projectId = args.get("sa_project_id")
            if projectId == None or len(projectId) == 0:
                raise Exception("--sa-project-id not specified")
            self.config.setServiceAccountProjectId(projectId)
        else:
            self.config.setServiceAccountProjectId(self.config.getId())

        self.config.setSetIAMPolicy(args["set_iam_policy"] == "true")
        self.config.setEnableApi(args["enable_api"] == "true")
        self.config.setSetIAMPolicy(args["set_iam_policy"] == "true")