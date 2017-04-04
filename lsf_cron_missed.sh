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

#going to landsatfact-data production repository and running scripts there
cd $path_projects/dataexchange

cd $path_projects/geoprocessing
#create missed lcv scenes file
./write_missed_lcv.py

#pass the file containing the list of downloaded tars to LCV
./landsatFACT_LCV.py $path_projects/dataexchange/missed_lcv.txt
