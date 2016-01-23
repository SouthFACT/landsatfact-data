#! /bin/bash


export AWS_CONFIG_FILE=/var/vsites/landsatfact-data-dev.nemac.org/project/aws.config
/usr/bin/aws s3 sync /lsfdata/products/cr_zips  s3://landsat-cr-products --include "*.zip" 

#remove custom requests over a 45 days old.
find /lsfdata/products/cr_zips/*.zip -mtime +45  -exec rm {} \;

