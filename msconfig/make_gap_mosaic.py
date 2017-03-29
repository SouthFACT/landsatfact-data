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
gap_cur = conn.cursor()

#Selects the column that you want
#From Inputs will be replaced with the appropriate view 
gap_cur.execute("select distinct on (last_update) '/lsfdata/products/gdal_vrt_files/gap/gap_'  || last_update || '.vrt' as vrt_files from vw_quad_latest_update where last_update > '2017-01-01' AND last_update > current_date - interval '5' day order by last_update desc;")

#Use this view to create an inital mosaic. You may need to change the # of days in teh view.
#gap_cur.execute("SELECT location FROM vw_initial_mosaic_gap order by max asc;")

#Create empty string 
gap = ' ' 

#loop through data with cursor and attach the data to the empty parameters string
for data in gap_cur:
	gap += data[0] + ' ' 
	print data
print gap

cmd_gap = r'gdalwarp -multi -wm 500 --config GDAL_CACHEMAX 500 -t_srs EPSG:4269 -co COMPRESS=LZW -co TILED=YES -co BIGTIFF=YES -srcnodata 0 -dstnodata 0 ' + productStorage + '/mosaics/southeast_mosaic_gap.tif' + gap + productStorage + "/mosaics/temp/southeast_mosaic_gap.tif"

#Use this command to create a new initial mosaic
#cmd_gap = r'gdalwarp -multi -wm 500 --config GDAL_CACHEMAX 500 -t_srs EPSG:4269 -co COMPRESS=LZW -co TILED=YES -co BIGTIFF=YES -srcnodata 0 -dstnodata 0 ' + gap + productStorage + "/mosaics/temp/southeast_mosaic_gap.tif"

# print cmd_gap

#call gdal command and insert your string parameter	
#Popen(cmd_gap, shell = True)
call(cmd_gap, shell = True)

# Make the changes to the database persistent
conn.commit()

# Close communication with the database
gap_cur.close()
