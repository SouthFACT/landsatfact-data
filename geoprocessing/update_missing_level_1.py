
#! /usr/bin/python
#-------------------------------------------------------------------------------
# Name:         update_missing_level_1.py
# Purpose:      LandsatFACT application script that calls needed functions to
#               updagte missing records for level 1 meta data
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

import os, sys, re, traceback
import landsatFactTools_GDAL
import rasterAnalysis_GDAL
import numpy as np
import psycopg2
from LSF import *
import localLib
import pdb


runList=[]
extractedList = []
exceptList = []

DNminDict = {}
tableName = 'vw_failed_l1metadata'
tableColumnList = ['scene_id']
statement = "SELECT {0} FROM {1};".format(tableColumnList[0],tableName)
resultsTup = landsatFactTools_GDAL.postgresCommand(statement)

print resultsTup

runList=[]
extractedList = []
exceptList = []

for scene in resultsTup:
    runList.append(scene[0])


for scene in runList:
    try:
        # sets full path for the tarfile to be analyzed
        inNewSceneTar = os.path.join(tarStorage, scene)
        extractedPath = os.path.join(tiffsStorage, scene, scene+ '_MTL.xt')

        print 'Looking for mtl file in ' + extractedPath

        #make sure file exists for now it should if not we may need to download and re-extract?
        if os.path.exists(extractedPath) == True:
           print "extracting MTL level 1 metadata from: " + extractedPath

           mtlFile = rasterAnalysis_GDAL.mtlData(sceneID, extractedPath)           
           print 'Info: level 1 metadata for scene ' + scene + ' was updated.'
        else:
	   print 'Warning: The level 1 metadata file  (' + extractedPath + ') did not exist.  You may need re-download and extract scene '+ scene +'.'
        
        print ''

    except BaseException as e:
        print "Error in updating level 1 metadata"
        print str(e)

print 'Done updating level 1 metadata'

sys.exit()

