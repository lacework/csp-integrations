# Azure Compliance Integration CLI

### Script Requirements
- Requirements specified in the requirements.txt
- Python 2.7.10

### Installing Dependencies and Running the Script
All dependencies for the script is in requirements.txt and the main script is in app.py. 
``` bash
pip install -r requirements.txt --user
python app.py
```
Note: use pip2 and python2 if you have pip3 and python3 installed as well.

### FAQ

<strong>Q.</strong> Why does the script constantly ask for the configuration information interactively?

<strong>A.</strong> This happens because the file location of the config yaml was not given.
The interactive configuration building happens when the file location of the config yaml is not given.
The script builds the configuration in configCustom.yml at the project root directory.
In order to use the built config yml, the file location must be passed as a parameter.
For example:
``` bash
python app.py --config /Users/john/csp-integrations-internal/azure-cli/configCustom.yml
```

---

<strong>Q.</strong> When and how do I use roll back?

<strong>A.</strong> Roll back is a feature to purge resources on Azure created by the script.
Before creating resources, the script checks which resources need to be created.
When the user calls roll back, the script deletes the resources specified as created in rollback.yml.
It is not recommended to roll back resources created through the script too long ago.
There may be resources utilized by the user in other places even though it has been created through the script.
Due to this, it is recommended to use the roll back feature with extreme caution.
Rolling back will look something like this:
``` bash
python app.py --config /Users/john/config/config.yml --rollback true
```

---

<strong>Q.</strong> Why can't I create a new Log Profile?

<strong>A.</strong> Azure mandates that each Azure subscription have only one log profile.
The user must remove any existing log profiles.
