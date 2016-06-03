#! /usr/bin/python

import psycopg2
import sys
import os
from subprocess import call, Popen

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'geoprocessing'))
from LSF import *

sys.path.append("../var")
try:
    from Config import *
    from datetime import timedelta
    from datetime import datetime    
except:
    print "Cannot find local settings file 'Config.py'.  You need to create a Config.py file that contains"
    print "settings appropriate for this copy of the LandsatFACT project.  You can use the file 'Config.tpl.py'"
    print "as a starting point --- make a copy of that file called 'Config.py', and edit appropriately."
    exit(-1)
	
conn_string = (POSTGIS_CONNECTION_STRING)
 
# print the connection string we will use to connect
print "Connecting to database\n	->%s" % (conn_string)
 
# get a connection, if a connect cannot be made an exception will be raised here
conn = psycopg2.connect(conn_string)
 
print "Connected!\n"

# conn.cursor will return a cursor object, you can use this cursor to perform queries
swir_cur = conn.cursor()

#Selects the column that you want
#From Inputs will be replaced with the appropriate view 
swir_cur.execute("select location from vw_tile_index_swir,vw_last_days_products where substr(vw_tile_index_swir.location::text, 24,47) =  substr(vw_last_days_products.product_id::text,1,47) and product_type = 'SWIR';")

#Use this view to create an inital mosaic. You may need to change the # of days in teh view.
#swir_cur.execute("SELECT location FROM vw_initial_mosaic_swir order by max asc;")

#Create empty string 
swir = ' ' 

#loop through data with cursor and attach the data to the empty parameters string
for data in swir_cur:
	swir += data[0] + ' ' 
	print data
print swir

cmd_swir = r'gdalwarp -multi -wm 500 --config GDAL_CACHEMAX 1000 -t_srs EPSG:4269 -co COMPRESS=LZW -co TILED=YES -co BIGTIFF=YES -srcnodata 0 -dstnodata 0  ' + productStorage + '/mosaics/southeast_mosaic_swir.tif' + swir + productStorage + "/mosaics/temp/southeast_mosaic_swir.tif"

#cmd_swir = r'gdalwarp -multi -wm 500 --config GDAL_CACHEMAX 1000 -t_srs EPSG:4269 -co COMPRESS=LZW -co TILED=YES -co BIGTIFF=YES -srcnodata 0 -dstnodata 0  ' + productStorage + '/mosaics/southeast_mosaic_swir.tif' + swir + productStorage + "/mosaics/temp/temp2/temp3/southeast_mosaic_swir.tif"

#Use this command to create a new initial mosaic
#cmd_swir = r'gdalwarp -multi -wm 500 --config GDAL_CACHEMAX 1000 -t_srs EPSG:4269 -co COMPRESS=LZW -co TILED=YES -co BIGTIFF=YES -srcnodata 0 -dstnodata 0 ' + swir + productStorage + "/mosaics/temp/southeast_mosaic_swir.tif"

# print cmd_swir

#call gdal command and insert your string parameter	
#Popen(cmd_swir, shell = True)

call(cmd_swir, shell = True)

# Make the changes to the database persistent
conn.commit()

# Close communication with the database
swir_cur.close()
