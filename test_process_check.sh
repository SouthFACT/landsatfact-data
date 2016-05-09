#!/bin/bash

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

# now source it, either the original or the filtered variant
source "$configfile"

#comma delemited list of processes
LSF_PROC="landsatFACTmain.py,make_latest_mosaics.sh,makeviewerconfig.py,lsf_cron.sh"
?
#loop through list and check if something is running
for process in $(echo $LSF_PROC | tr "," " "); do
?
  #check if process is running
  if ps ax | grep -v grep | grep $process > /dev/null
  then	
    #if process is running exit with non zero code
    echo "$process is running exiting..."
    exit 1
  fi
done
?
#none of the processes are unnin so add the actuall meat of the job here 
echo 'run cron' > $path_log/test_process_check.log 2>&1
