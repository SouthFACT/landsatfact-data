#! /bin/bash

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

export AWS_CONFIG_FILE=$path_projects/aws.config
/usr/bin/aws s3 sync $path_cr_zips  s3://landsat-cr-products --include "*.zip" 

#remove custom requests over a 45 days old.
find $path_cr_zips/*.zip -mtime +45  -exec rm {} \;

