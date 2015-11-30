#!/bin/bash
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
echo 'run cron' > /var/vsites/landsatfact-data-dev.nemac.org/project/var/log/test_process_check.log 2>&1