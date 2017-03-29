#! /bin/bash

###
###  This is the script invoked by lsf_cron;
###  it simply runs each mosaic python script, creates overviews, and then moves the files to the appropriate directory.
###

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


#run individual scripts concurrently that each run gdalwarp to create mosaics in temp
 ./make_swir_mosaic.py&
 ./make_ndvi_mosaic.py&
 ./make_ndmi_mosaic.py&
 ./make_cloud_mosaic.py&
 ./make_gap_mosaic.py&
 wait

#run script that creates overviews
./mosaic_overviews.sh

#move new mosaics and overwrite previous mosaics
mv -f $path_products/mosaics/temp/* $path_products/mosaics
