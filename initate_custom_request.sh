#! /bin/bash

export PGPASSWORD=$(/usr/bin/cat /var/vsites/landsatfact-data-dev.nemac.org/pg) 
/usr/bin/psql -h lsfdb.cqnxz1q9lu2y.us-east-1.rds.amazonaws.com  -U dataonly  -d landsatfact -c 'SELECT COUNT(*) > 0 FROM (SELECT aoi_id as id FROM get_pendingcustomrequests()) as cnt;' -t  -o /var/vsites/landsatfact-data-dev.nemac.org/cr_pending.txt
export PGPASSWORD=''

me=`basename "$0"`
if [[ `ps ax | grep lsf_cron | wc -l` -lt 2 && `ps ax | grep $me | wc -l` -le 3 ]]; then

	hasCR=$(cat /var/vsites/landsatfact-data-dev.nemac.org/cr_pending.txt)
	if [ $hasCR = "t" ]; then
	   cd /var/vsites/landsatfact-data-dev.nemac.org/project/geoprocessing
	   ./customRequest.py > /var/vsites/landsatfact-data-dev.nemac.org/cr_py.log 2>&1
	else
	   /usr/bin/echo 'no pending requests' > /var/vsites/landsatfact-data-dev.nemac.org/cr.txt
	fi

fi
