#! /bin/bash

###
###  This is the script invoked by make_latest_mosaics;
###  it simply creates gdal overviews on the latest change mosaics.
###


DIRECTORY=`dirname $0`
echo $DIRECTORY

cd $DIRECTORY
cd ..

#get the config file and make sure it will not do something delete all...
configfile=./bash_config.cfg
configfile_secured=./tmp_bash_config.cfg

# check if the file contains something we don't want
if egrep -q -v '^#|^[^ ]*=[^;]*' "$configfile"; then
  # filter the original to a new file
  egrep '^#|^[^ ]*=[^;&]*'  "$configfile" > "$configfile_secured"
  configfile="$configfile_secured"
fi

#  now source it, either the original or the filtered variant
source "$configfile"

cd $path_products/mosaics/temp

for f in *.tif
do
   gdaladdo -ro --config COMPRESS_OVERVIEW LZW "$f" 2 4 8 16
done
