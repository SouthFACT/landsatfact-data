#! /usr/bin/python

import psycopg2
import sys
import os
from subprocess import call, Popen

#sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'geoprocessing'))
#from LSF import *

sys.path.append("./var")
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
 
#print "Connected!\n"

# conn.cursor will return a cursor object, you can use this cursor to perform queries
ndvi_cur = conn.cursor()
ndmi_cur = conn.cursor()
swir_cur = conn.cursor()
cloud_cur = conn.cursor()
gap_cur = conn.cursor()

#Selects the column that you want
#From Inputs will be replaced with the appropriate view 
ndvi_cur.execute("select vrt_name, product_list from vw_product_list_ndvi_for_vrt WHERE vrt_date > current_date - interval '5' day")
ndmi_cur.execute("select vrt_name, product_list from vw_product_list_ndmi_for_vrt WHERE vrt_date > current_date - interval '5' day")
swir_cur.execute("select vrt_name, product_list from vw_product_list_swir_for_vrt WHERE vrt_date > current_date - interval '5' day")
cloud_cur.execute("select vrt_name, product_list from vw_product_list_cloud_for_vrt WHERE vrt_date > current_date - interval '5' day")
gap_cur.execute("select vrt_name, product_list from vw_product_list_gap_for_vrt WHERE vrt_date > current_date - interval '5' day")

f = open((DATA_DIR)+'/products/gdal_vrt_files/ndvi/ndvi.txt', 'w')
for row in ndvi_cur:
    f.write(str(row[0]) + ',' + row[1] + '\n')
f.close()

f = open((DATA_DIR)+'/products/gdal_vrt_files/ndmi/ndmi.txt', 'w')
for row in ndmi_cur:
    f.write(str(row[0]) + ',' + row[1] + '\n')
f.close()

f = open((DATA_DIR)+'/products/gdal_vrt_files/swir/swir.txt', 'w')
for row in swir_cur:
    f.write(str(row[0]) + ',' + row[1] + '\n')
f.close()

f = open((DATA_DIR)+'/products/gdal_vrt_files/cloud/cloud.txt', 'w')
for row in cloud_cur:
    f.write(str(row[0]) + ',' + row[1] + '\n')
f.close()

f = open((DATA_DIR)+'/products/gdal_vrt_files/gap/gap.txt', 'w')
for row in gap_cur:
    f.write(str(row[0]) + ',' + row[1] + '\n')
f.close()
