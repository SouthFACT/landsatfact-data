#! /bin/bash

#going to landsatfact-data production repository and running scripts there
cd /var/vsites/landsatfact-data.nemac.org/project/dataexchange
php update_landsat_metadata.php

php download_landsat_data.php

cd /var/vsites/landsatfact-data.nemac.org/project/geoprocessing
./landsatFACT_LCV.py

cd /var/vsites/landsatfact-data.nemac.org/project/msconfig
./makeviewerconfig.py