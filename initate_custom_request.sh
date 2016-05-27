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

export PGPASSWORD=$(/usr/bin/cat $path_sites/pg) 
/usr/bin/psql -h $rds_server  -U dataonly  -d landsatfact -c 'SELECT COUNT(*) > 0 FROM (SELECT aoi_id as id FROM get_pendingcustomrequests()) as cnt;' -t  -o $path_log/cr_pending.txt
export PGPASSWORD=''

if [[ `ps ax | grep "[l]andsatFACT_LCV.py" | wc -l` -lt 1 ]]; then
  if [[ `ps ax | grep "[d]ownload_landsat_data.php" | wc -l` -lt 1 ]]; then
    if [[ `ps ax | grep "[c]ustomRequest.py" | wc -l` -lt 1 ]]; then
	hasCR=$(cat $path_log/cr_pending.txt)
	if [ $hasCR = "t" ]; then
	   cd $path_projects/geoprocessing
	   ./customRequest.py > $path_log/cr_py.log 2>&1
	else
	   /usr/bin/echo 'no pending requests' > $path_log/cr.txt
	fi
    else
      /usr/bin/echo 'Cannot run a Custom Request is processing' > $path_log/cr.txt
    fi
  else
    /usr/bin/echo 'Cannot run a CR or LCV is downloading data and about to process' > $path_log/cr.txt
  fi 
else
  /usr/bin/echo 'Cannot run LCV is  blocking request' > $path_log/cr.txt
fi
