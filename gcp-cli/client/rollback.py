from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from builtins import range
from .checks import runDependentChecks
from .checks import runIndependentChecks
from .util.util import Util
import os
import json
import logging

def rollbackScript():
    util = Util()
    if os.path.isfile("checks.txt"):
        configFile = None
        toEnable = None
        deploymentExists = None
        rolesProject = None
        rolesOrg = None
        rolesAudit = None
        checksData = open("checks.txt", "r").read()
        checksData = json.loads(checksData)
        if 'configFile' in checksData:
            configFile = checksData['configFile']
        if 'toEnable' in checksData:
            toEnable = checksData['toEnable']
        if 'deploymentExists' in checksData:
            deploymentExists = checksData['deploymentExists']
        if 'rolesProject' in checksData:
            rolesProject = checksData['rolesProject']
        if 'rolesOrg' in checksData:
            rolesOrg = checksData['rolesOrg']
        if 'rolesAudit' in checksData:
            rolesAudit = checksData['rolesAudit']

        if configFile is not None and toEnable is not None:
            config, checkToEnable = runIndependentChecks(configFile, util)
            setupProjectId = config.getSetupProjectId()

            if deploymentExists is not None and rolesProject is not None and rolesOrg is not None and rolesAudit is not None:
                checkDeploymentExists, projectDetails, checkRolesProject, checkRolesOrg, checkRolesAudit = runDependentChecks(config, util, True)
                googleServiceAccount = config.getSetupProjectNumber() + "@cloudservices.gserviceaccount.com"
                rolesRemoveProject = list(set(rolesProject) - set(checkRolesProject))
                if len(rolesRemoveProject) != 0:
                    logging.info("The following roles will be removed from project during the rollback: \n" + str(rolesRemoveProject))
                    print("The following roles will be removed from project during the rollback: \n" + str(rolesRemoveProject))
                    util.removeIamPolicy(setupProjectId, googleServiceAccount, "PROJECT", rolesRemoveProject)
                rolesRemoveOrg = list(set(rolesOrg) - set(checkRolesOrg))
                if len(rolesRemoveOrg) != 0:
                    logging.info("The following roles will be removed from organization during the rollback: \n" + str(rolesRemoveOrg))
                    print("The following roles will be removed from organization during the rollback: \n" + str(rolesRemoveOrg))
                    util.removeIamPolicy(setupProjectId, googleServiceAccount, "ORGANIZATION", rolesRemoveOrg)

                for i in range(len(rolesAudit)):
                    for role in checkRolesAudit:
                        if rolesAudit[i]['id'] == role['id']:
                            del rolesAudit[i]

                rolesRemoveAudit = rolesAudit
                if len(rolesRemoveAudit) != 0:
                    for entry in rolesRemoveAudit:
                        logging.info("The following roles will be removed from " + entry['idType'].lower() + " with id " + entry['id'] + " during the rollback: \n" + str(rolesRemoveAudit))
                        print("The following roles will be removed from " + entry['idType'].lower() + " with id " + entry['id'] + " during the rollback: \n" + str(rolesRemoveAudit))
                        util.removeIamPolicy(entry['id'], googleServiceAccount, entry['idType'], entry['roles'])


            toDisable = list(set(toEnable) - set(checkToEnable))
            if len(toDisable) != 0:
                logging.info("The following APIs will be disabled from project during the rollback: \n" + str(toDisable))
                print("The following APIs will be disabled from project during the rollback: \n" + str(toDisable))
                util.disableApi(config.getSetupProjectId(), toDisable)
