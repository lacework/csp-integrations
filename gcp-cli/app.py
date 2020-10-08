from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from client.util.util import Util
from client.checks import runDependentChecks
from client.checks import runIndependentChecks
from client.checks import checkApiEnablement
from client.user_input import getConfigInput
from client.lacework_api import createLaceworkIntegration
from client.rollback import rollbackScript
import logging
import argparse
import time
import json
import sys

SLEEP_SECS = 30

if __name__ == "__main__":
    try:

############################################## INITIALIZING LOG FILE ################################################################
        logging.basicConfig(filename="laceworkIntegrationScript.log", level=logging.DEBUG, filemode="w", format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                            datefmt='%Y-%m-%d:%H:%M:%S',)

############################################## PARSING ARGS #####################################################################
        ap = argparse.ArgumentParser()
        ap.add_argument("--rollback", help="Check if need to roll back or not!")
        ap.add_argument("--config", help="Path to the config file")
        args, unknown = ap.parse_known_args()

############################################## CHECKING IF NEED TO ROLLBACK ################################################################
        rollBack = False
        if args.rollback is not None and args.rollback == "true":
            rollBack = True

        if rollBack:
            rollbackScript()
            logging.info("Rollback has been completed!")
            sys.exit("Rollback has been completed!")

############################################## CHECKING FOR CONFIG FILE ################################################################
        if args.config is None:
            configFile = getConfigInput()
        else:
            args = vars(args)
            configFile = args["config"]

        config = None
        try:

############################################## RUNNING ALL INDEPENDENT TESTS AND LISTING ASSUMPTIONS #######################################################
            util = Util()
            config, toEnable = runIndependentChecks(configFile, util)
            setupProjectId = config.getSetupProjectId()
            deploymentName = config.getDeploymentName()
            with open("checks.txt", "w") as checksFile:
                json.dump({"configFile":configFile, "toEnable":toEnable}, checksFile)

############################################## ENABLING API NEEDED TO RUN DEPENDENT TESTS ################################################################
            if len(toEnable) != 0:
                logging.info("Enabling needed api in setup project")
                # If the project is new we need to enable api manually for the deployment to work properly
                util.enableApi(setupProjectId, toEnable)
                while True:
                    print("Needed API are being enabled, sleeping script for 30 seconds before moving forward!")
                    time.sleep(SLEEP_SECS)
                    if len(checkApiEnablement(setupProjectId, util)) == 0:
                        break

############################################## RUNNING ALL DEPENDENT TESTS ################################################################
            deploymentExists, projectDetails, rolesProject, rolesOrg, rolesAudit = runDependentChecks(config, util)
            if not deploymentExists:
                checksData = open("checks.txt", "r").read()
                checksData = json.loads(checksData)
                checksData['deploymentExists'] = deploymentExists
                checksData['rolesProject'] = rolesProject
                checksData['rolesOrg'] = rolesOrg
                checksData['rolesAudit'] = rolesAudit
                with open("checks.txt", "w") as checksFile:
                    json.dump(checksData, checksFile)
                googleServiceAccount = config.getSetupProjectNumber() + "@cloudservices.gserviceaccount.com"

############################################## SETTING PROPER PERMISSIONS NEEDED ################################################################
                logging.info("Setting proper IAM policies for setup project")
                # The project requires sepcific IAM roles to deploy and create the resources
                util.setIAMPolicy(setupProjectId, googleServiceAccount, "PROJECT", rolesProject)
                if len(rolesOrg) != 0:
                    logging.info("Setting proper IAM policies for organization level integration")
                    # If someone wants organization level integration we would need extra permissions
                    util.setIAMPolicy(config.getComplianceSetupId(), googleServiceAccount, config.getComplianceSetupType(), rolesOrg)
                if len(rolesAudit) != 0:
                    for entry in rolesAudit:
                        logging.info("IAM policies being set for: " + entry['id'])
                        # Each audit log project, folder or organization needs to give logging role so service account
                        # can access and copy logs to the bucket
                        util.setIAMPolicy(entry['id'], googleServiceAccount, entry['idType'], entry['roles'])

############################################## CREATING DEPLOYMENT BASED ON CONFIG ################################################################
                logging.info("Creating deployment based on config")
                util.createDeployment(config, deploymentName)
                logging.info("Checking created deployment status")
                deploymentOutput = util.deploymentWait(setupProjectId, deploymentName)
                if deploymentOutput is None:
                    print("Deployment Failed, Deleting created resources and rolling back script")
                    time.sleep(SLEEP_SECS)
                    rollbackScript()
                    raise Exception("Deployment failed with above error!\n")

                createLaceworkIntegration(deploymentOutput, config, util)

        except Exception as e:
            print("Exception:", str(e))
            logging.exception(str(e))
    except Exception as e:
        print("Exception:", str(e))
        logging.exception(str(e))


