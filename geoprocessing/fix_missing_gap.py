#! /usr/bin/python
#-------------------------------------------------------------------------------
# Name:         update_missing_dn.py
# Purpose:      LandsatFACT application script that calls needed functions to
#               updagte missing records for dn
#
# Author:       LandsatFACT Project Team
#               support@landsatfact.com
'''This code was developed in the public domain.  This code is provided as is, without warranty of any kind,
 express or implied, including but not limited to the warranties of
 merchantability, fitness for a particular purpose and noninfringement.
 In no event shall the authors be liable for any claim, damages or
 other liability, whether in an action of contract, tort or otherwise,
 arising from, out of or in connection with the software or the use or
 other dealings in the software.'''
#-----------------------------------------------------------------------------
def main():
    pass

if __name__ == '__main__':
    main()


from osgeo import gdal, gdal_array
from osgeo.gdalnumeric import *
from osgeo.gdalconst import *

import os, sys, re, traceback
import numpy as np
import landsatFactTools_GDAL
import rasterAnalysis_GDAL
import psycopg2
from LSF import *
import localLib
import pdb

DNminDict = {}
tableName = 'vw_missing_gap'
tableColumnList = ['product_id','product_type','swir','gap']
statement = "SELECT {0},{1},{2},{3} FROM {4};".format(tableColumnList[0],tableColumnList[1],tableColumnList[2],tableColumnList[3],tableName )
resultsTup = landsatFactTools_GDAL.postgresCommand(statement)



for file in resultsTup:

    if os.path.exists(file[2]) == True:

        print 'Adding missing gap ' + file[2]
        ds1 = file[2]

        ds = gdal.Open(ds1)
        b1 = ds.GetRasterBand(1)
        arr = b1.ReadAsArray()

        # apply equation
        data = (arr <= 0) * 0 + (arr > 2) * 2

        output = file[3]

        gdal_array.SaveArray(data.astype("byte"), output, "GTIFF", ds)



        outfile = file[3]

        finish = outfile.rfind("/")
        inputs = outfile[finish+1:]
        finish = inputs.rfind("_")
        inputs = inputs[:finish]

        finish = inputs.rfind("_")
        input1 = inputs[:finish]
        input2 = inputs[finish+1:]

        statement = "INSERT INTO products VALUES('" + inputs + "_GapMask.tif','" + input1 + "','" + input2 + "','GAP','2017-08-18','LCV','','2017-11-06','2017-11-06','ADD MISSING GAP','YES');"

        try:
           resultsTup = landsatFactTools_GDAL.postgresCommand(statement)
        except BaseException as e:
           print "Error updating product " + file[1]

    else:
        print file[2] + ' missing'

        #statement = "SELECT update_is_on_disk('{0}', '{1}')".format(file[1],'YES')
        #try:
        #    resultsTup = landsatFactTools_GDAL.postgresCommand(statement)
        #except BaseException as e:
        #    print "Error updating product " + file[1]

    #else:
    #    print 'file ' + file[0] + ' does NOT exist!'
    #    statement = "SELECT update_is_on_disk('{0}', '{1}')".format(file[1],'NO')
    #    try:
    #        resultsTup = landsatFactTools_GDAL.postgresCommand(statement)
    #    except BaseException as e:
    #        print "Error updating product " + file[1]

sys.exit()

