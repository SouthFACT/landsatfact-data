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

import os, sys, re, traceback
import landsatFactTools_GDAL
import rasterAnalysis_GDAL
import numpy as np
import psycopg2
from LSF import *
import localLib
import pdb

DNminDict = {}
tableName = 'vw_failed_dn'
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
        inNewSceneTar = os.path.join(tarStorage, scene + '.tar.gz')
        extractedPath = os.path.join(tiffsStorage, scene)

        productID=landsatFactTools_GDAL.getProductIDForScene(scene)

        print 'Looking for DN in ' + extractedPath

        #make sure file exists for now it should if not we may need to download and re-extract?
        if os.path.exists(extractedPath) == True:
           print "extract DN information from: " + extractedPath
           dnMinDict = rasterAnalysis_GDAL.getDNmin(extractedPath)
           
           landsatFactTools_GDAL.writeDNminToDB(dnMinDict,extractedPath)
           print 'Info: DN for scene ' + scene + ' was updated.'

        else:

           if os.path.exists(inNewSceneTar) == True:
              print 'tar ' + inNewSceneTar + ' exists extracting'
              extractedPath = landsatFactTools_GDAL.checkExisting(inNewSceneTar, tiffsStorage, scene, productID)

              extractedPath = os.path.join(tiffsStorage, scene)
               
              dnMinDict = rasterAnalysis_GDAL.getDNmin(extractedPath)

              landsatFactTools_GDAL.writeDNminToDB(dnMinDict,extractedPath)
              print 'Info: DN information for scene ' + scene + ' was updated.'

           else:
              print 'tar ' + inNewSceneTar + ' does not exist will attempt download '

              landsatFactTools_GDAL.downloadScene( scene )

              print 'check if download completed for ' + inNewSceneTar
              
              if os.path.exists(inNewSceneTar) == True:

                  print 'Download completed for ' + inNewSceneTar
                  extractedPath = landsatFactTools_GDAL.checkExisting(inNewSceneTar, tiffsStorage)
 
		  extractedPath = os.path.join(tiffsStorage, scene)

                  print "extracting DN information from: " + extractedPath
                  dnMinDict = rasterAnalysis_GDAL.getDNmin(extractedPath)
   
                  landsatFactTools_GDAL.writeDNminToDB(dnMinDict,extractedPath)
                  print 'Info: DN information for scene ' + scene + ' was updated.'

                  print 'removing tar ' + inNewSceneTar
                  os.remove(inNewSceneTar)

                  print 'cleaning directory ' + extractedPath
                  landsatFactTools_GDAL.cleanDir(extractedPath)
              else:
                  print 'Warning: The folder (' + extractedPath + ') containing DN information did not exist.  You may need re-download and extract scene '+ scene +'.'

        print ''

    except BaseException as e:
        print "Error in DN"
        print str(e)

print 'Done updating DN'
sys.exit()

