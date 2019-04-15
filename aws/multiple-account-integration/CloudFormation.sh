#!/bin/bash
die () {
    echo -e >&1 "$@"
    exit 1
}

[ "$#" -eq 4 ] || die  "required 4 argument, $# argument(s) provided. \nPlease follow the pattern :\n./CloudFormation.sh  <configfile.yml> <execution_type> <access_token> <lacework_account_url>\n "
echo $1 | grep -E -q '\.yml+$' || die "Yaml file needed, $1 provided"
echo $2 | grep -E -q  'sync' || $2 | grep -E  'async' || die "allowed inputs are sync | async, $2 provided"
python Executor.py "$1" "$2" "$3" "$4"
