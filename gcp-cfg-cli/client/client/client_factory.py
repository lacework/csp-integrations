from interactive_client import  InteractiveClient
from noninteractive_client import  NonInteractiveClient

class UserClientFactory(object):

    @staticmethod
    def getClient(mode, config):

        if mode == "interactive":
            return InteractiveClient(config)
        elif mode  == "non-interactive":
            return NonInteractiveClient(config)
        else:
            raise ValueError("Invalid Mode: " + mode)