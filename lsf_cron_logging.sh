#! /bin/bash

me=`basename "$0"`
if [ `ps ax | grep $me | wc -l` -le 3 ]; then
        COUNTER=0
        until [[ `ps ax | grep initate_custom_ | wc -l` -lt 2 || $COUNTER -eq 10 ]]; do
                sleep 120
                let COUNTER=COUNTER+1
        done
        if [ $COUNTER -lt 10 ]; then
		cd /var/vsites/landsatfact-data.nemac.org/project
		./lsf_cron.sh > /var/vsites/landsatfact-data.nemac.org/project/var/log/lsf_cron.log 2>&1
	fi
fi
