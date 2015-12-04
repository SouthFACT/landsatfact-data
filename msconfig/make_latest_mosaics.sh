#! /bin/bash

###
###  This is the script invoked by lsf_cron;
###  it simply runs each mosaic python script, creates overviews, and then moves the files to the appropriate directory.
###

#run individual scripts concurrently that each run gdalwarp to create mosaics in temp
# ./make_swir_mosaic.py&
# ./make_ndvi_mosaic.py&
# ./make_ndmi_mosaic.py&
# ./make_cloud_mosaic.py&
# ./make_gap_mosaic.py&
# wait

#run script that creates overviews
#./mosaic_overviews.sh

#copy previous-day mosaics to archive
#cp /lsfdata/products/mosaics/* /lsfdata/products/mosaics/archive

#move new mosaics and overwrite previous mosaics
#mv -f /lsfdata/products/mosaics/temp/* /lsfdata/products/mosaics