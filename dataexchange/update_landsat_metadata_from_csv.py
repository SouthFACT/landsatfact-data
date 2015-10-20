#! /usr/bin/python
import urllib
import csv, sys
import psycopg2
from numpy import genfromtxt
lsf_quads = genfromtxt('landsat_quads.csv', delimiter=',', names=True, dtype=int)

sys.path.append("../var")
try:
    from Config import *
except:
    print "Cannot find local settings file 'Config.py'.  You need to create a Config.py file that contains"
    print "settings appropriate for this copy of the project.  You can use the file 'Config.tpl.py'"
    print "as a starting point --- make a copy of that file called 'Config.py', and edit appropriately."
    exit(-1)


if 13035 in lsf_quads['wrs2_code']:
    print "yes"
else:
    print "no"

print type(lsf_quads['wrs2_code'][5])

# Download latest metadata CSVs
# metadataFile = urllib.URLopener()
# metadataFile.retrieve("http://landsat.usgs.gov/metadata_service/bulk_metadata_files/LANDSAT_8.csv", "LANDSAT_8.csv")

# Loop through CSV inserting into PGSQL
# LANDSAT_8 
filename = 'LANDSAT_8.csv'
# LANDSAT_7 
#filename = 'LANDSAT_ETM_SLC_OFF.csv'

#print lsf_quads['wrs2_code']

with open(filename, 'rb') as f:
    reader = csv.reader(f)
    try:
        rowCount = 0
        conn = psycopg2.connect(POSTGIS_CONNECTION_STRING)
        for row in reader:
            if rowCount>0:
                sceneID = row[0]
                sensor = row[1]
                acquisitionDate = row[2]
                browseURL = row[5]
                path = row[6]
                rowNum = row[7]
                rowNum =  rowNum.rjust(3, '0')
                type(rowNum)
                ccFull = row[19]
                ccFullUL = row[20] or None
                ccFullUR = row[21] or None
                ccFullLL = row[22] or None
                ccFullLR = row[23] or None
                dataTypeL1 = row[53]
                cur = conn.cursor()
		#print sceneID
                #print (str(path)+str(rowNum))
                if int(str(path)+str(rowNum)) in lsf_quads['wrs2_code']:
                    # check to see if the record already exist
                    sql = 'SELECT count(*) from landsat_metadata WHERE scene_id = %s;'
                    data=[sceneID]
                    cur.execute(sql,data)
                    result = cur.fetchone()
                    cur.close()
                    print result[0]
                    if result[0]==0:
                        # do the insert
			print "Inserting..." + sceneID
			print str(sceneID)
			cur = conn.cursor()
                        #print (sceneID,sensor,acquisitionDate,browseURL,path,rowNum,ccFull,ccFullUL,ccFullUR,ccFullLL,ccFullLR,dataTypeL1)
			cur.execute("INSERT INTO landsat_metadata VALUES \
				(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", \
				(sceneID,sensor,acquisitionDate,browseURL,path,rowNum,ccFull,ccFullUL,ccFullUR,ccFullLL,ccFullLR,dataTypeL1)) # correct
			conn.commit()
			cur.close()
                    else:
                        print "Already in dere:  " + sceneID
            rowCount = rowCount+1
        conn.close()
    except csv.Error as e:
        sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))
