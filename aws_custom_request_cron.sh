#! /bin/bash


export AWS_CONFIG_FILE /var/vsites/landsatfact-data-dev.nemac.org/project/aws.config

/usr/bin/aws s3 cp /lsfdata/products/cr_zips  s3://landsat-cr-products --recursive --include "*.zip" 

