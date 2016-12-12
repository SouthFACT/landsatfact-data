#! /bin/bash

./make_vrt.py

cd /lsfdata-dev/products/gdal_vrt_files/ndvi

while IFS=, read -r -a input; do 
 gdalbuildvrt -overwrite -addalpha -hidenodata -srcnodata 0 -vrtnodata 0 /lsfdata-dev/products/gdal_vrt_files/ndvi/ndvi_${input[0]}.vrt ${input[1]}
done < ndvi.txt

cd /lsfdata-dev/products/gdal_vrt_files/ndmi

while IFS=, read -r -a input; do
 gdalbuildvrt -overwrite -addalpha -hidenodata -srcnodata 0 -vrtnodata 0 /lsfdata-dev/products/gdal_vrt_files/ndmi/ndmi_${input[0]}.vrt ${input[1]}
done < ndmi.txt

cd /lsfdata-dev/products/gdal_vrt_files/swir

while IFS=, read -r -a input; do
 gdalbuildvrt -overwrite -addalpha -hidenodata -srcnodata 0 -vrtnodata 0 /lsfdata-dev/products/gdal_vrt_files/swir/swir_${input[0]}.vrt ${input[1]}
done < swir.txt

cd /lsfdata-dev/products/gdal_vrt_files/cloud

while IFS=, read -r -a input; do
 gdalbuildvrt -overwrite -addalpha -hidenodata -srcnodata 0 -vrtnodata 0 /lsfdata-dev/products/gdal_vrt_files/cloud/cloud_${input[0]}.vrt ${input[1]}
done < cloud.txt

cd /lsfdata-dev/products/gdal_vrt_files/gap

while IFS=, read -r -a input; do
 gdalbuildvrt -overwrite -addalpha -hidenodata -srcnodata 0 -vrtnodata 0 /lsfdata-dev/products/gdal_vrt_files/gap/gap_${input[0]}.vrt ${input[1]}
done < gap.txt

