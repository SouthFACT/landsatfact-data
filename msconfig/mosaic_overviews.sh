#! /bin/bash

###
###  This is the script invoked by make_latest_mosaics;
###  it simply creates gdal overviews on the latest change mosaics.
###

cd /lsfdata/products/mosaics/temp

for f in *.tif
do
   gdaladdo -ro --config COMPRESS_OVERVIEW LZW "$f" 2 4 8 16
done
