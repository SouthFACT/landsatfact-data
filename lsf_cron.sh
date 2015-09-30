#! /bin/bash


cd /var/vsites/landsatfact-data-dev.nemac.org/project/dataexchange
php update_landsat_metadata.php

php download_landsat_data.php

cd /var/vsites/landsatfact-data-dev.nemac.org/project/geoprocessing
./landsatFACTmain.py

cd /var/vsites/landsatfact-data-dev.nemac.org/project/msconfig
./make_latest_mosaics.sh

./makeviewerconfig.py