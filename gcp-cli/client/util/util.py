from __future__ import absolute_import
from .util_api import UtilAPI
from .util_iam import UtilIAM
from .util_dpm import UtilDpm

class Util(UtilAPI, UtilIAM, UtilDpm):
    def __init__(self):
        UtilAPI.__init__(self)
