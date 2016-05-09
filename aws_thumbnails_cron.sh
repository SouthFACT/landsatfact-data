#! /bin/bash

#get the config file and make sure it will not do something delete all...
configfile='./bash_config.cfg'
configfile_secured='./tmp_bash_config.cfg'

# check if the file contains something we don't want
if egrep -q -v '^#|^[^ ]*=[^;]*' "$configfile"; then
  echo "Config file is unclean, cleaning it..." >&2
  # filter the original to a new file
  egrep '^#|^[^ ]*=[^;&]*'  "$configfile" > "$configfile_secured"
  configfile="$configfile_secured"
fi

#  now source it, either the original or the filtered variant
source "$configfile"

export AWS_CONFIG_FILE=$path_projects/aws.config
/usr/bin/python $path_projects/dataexchange/make_thumbnails.py

