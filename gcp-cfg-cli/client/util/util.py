from util_api import UtilAPI
from util_iam import UtilIAM
from util_service_account import UtilServiceAccount

class Util(UtilAPI, UtilServiceAccount, UtilIAM):

    def __init__(self, config):
       UtilAPI.__init__(self, config)