#! /bin/bash

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

cd $path_projects
./make_vrt.py

cd $path_products/gdal_vrt_files/ndvi

while IFS=, read -r -a input; do 
 gdalbuildvrt -overwrite -addalpha -hidenodata -srcnodata 0 -vrtnodata 0 $path_products/gdal_vrt_files/ndvi/ndvi_${input[0]}.vrt ${input[1]}
done < ndvi.txt

cd $path_products/gdal_vrt_files/ndmi

while IFS=, read -r -a input; do
 gdalbuildvrt -overwrite -addalpha -hidenodata -srcnodata 0 -vrtnodata 0 $path_products/gdal_vrt_files/ndmi/ndmi_${input[0]}.vrt ${input[1]}
done < ndmi.txt

cd $path_products/gdal_vrt_files/swir

while IFS=, read -r -a input; do
 gdalbuildvrt -overwrite -addalpha -hidenodata -srcnodata 0 -vrtnodata 0 $path_products/gdal_vrt_files/swir/swir_${input[0]}.vrt ${input[1]}
done < swir.txt

cd $path_products/gdal_vrt_files/cloud

while IFS=, read -r -a input; do
 gdalbuildvrt -overwrite -addalpha -hidenodata -srcnodata 0 -vrtnodata 0 $path_products/gdal_vrt_files/cloud/cloud_${input[0]}.vrt ${input[1]}
done < cloud.txt

cd $path_products/gdal_vrt_files/gap

while IFS=, read -r -a input; do
 gdalbuildvrt -overwrite -addalpha -hidenodata -srcnodata 0 -vrtnodata 0 $path_products/gdal_vrt_files/gap/gap_${input[0]}.vrt ${input[1]}
done < gap.txt

