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

# now source it, either the original or the filtered variant
source "$configfile"

me=`basename "$0"`
if [ `ps ax | grep $me | wc -l` -le 3 ]; then
        COUNTER=0
        until [[ `ps ax | grep initate_custom_ | wc -l` -lt 2 || $COUNTER -eq 10 ]]; do
                sleep 120
                let COUNTER=COUNTER+1
        done
        if [ $COUNTER -lt 10 ]; then
		cd $path_projects
		./lsf_cron.sh > $path_log/lsf_cron.log 2>&1
	fi
fi
