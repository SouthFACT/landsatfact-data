DIRECTORY=`dirname $0`
echo $DIRECTORY

#get the config file and make sure it will not do something delete all...
configfile=$DIRECTORY/bash_config.cfg
configfile_secured=$DIRECTORY/tmp_bash_config.cfg

# check if the file contains something we don't want
if egrep -q -v '^#|^[^ ]*=[^;]*' "$configfile"; then
  # filter the original to a new file
  egrep '^#|^[^ ]*=[^;&]*'  "$configfile" > "$configfile_secured"
  configfile="$configfile_secured"
fi

#  now source it, either the original or the filtered variant
source "$configfile"


cd $path_node_projects
./node.sh write_missed_products.js > $path_log/write_missed_products.js.log 2>&1

