#! /bin/bash

(
cd /var/vsites/landsatfact-data-dev.nemac.org/project
./lsf_cron.sh
) > /var/vsites/landsatfact-data-dev.nemac.org/lsf_cron.log 2>&1
