
tag="$1"

if [ -z "$tag" ]
then
      echo "tag is empty"
      exit
fi

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

docker build -t lacework/azure-cfg-cli:$tag $parent_path