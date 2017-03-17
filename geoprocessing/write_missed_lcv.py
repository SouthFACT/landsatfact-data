#! /usr/bin/python
#-------------------------------------------------------------------------------
# Name:         landsatFACT_LCV.py
# Purpose:      LandsatFACT application script that calls needed functions to
#               process TAR compressed files into Vegetation Index products.
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

import os, sys, tarfile, shutil, traceback, gzip, subprocess, stat, datetime, time
import landsatFactTools_GDAL
import rasterAnalysis_GDAL
import numpy as np
import psycopg2
from LSF import *
import localLib
import pdb
from subprocess import PIPE


statement = "SELECT scene_id, message_level FROM vw_failed_lcv_quads WHERE message_level = 'ERROR' AND (scene_id <> 'LC80170342017072LGN00' OR scene_id <> 'LE70250352017072EDC00')  GROUP BY scene_id, message_level LIMIT 3;"
resultsTup = landsatFactTools_GDAL.postgresCommand(statement)

print resultsTup

runList=[]

for scene in resultsTup:
    runList.append(scene[0])

outfile = os.path.join(path_projects, 'dataexchange',  'missed_lcv.txt')
print 'writing missed scenes to ' + outfile

file = open( outfile, "w")
file.write('Array'  +  '\n')
file.write('('  +  '\n')

for index, scene in enumerate(runList, start=0):
    inNewSceneTar = os.path.join(tarStorage, scene + '.tar.gz')

    print 'Checking for ' + inNewSceneTar 
    if os.path.exists(inNewSceneTar) == False:
      print 'downloading scene ' + inNewSceneTar
      in_dir = os.getcwd()
      os.chdir(api_project_base)
      print os.getcwd()

      # download the scene data
      errcode=subprocess.call(["node", "download_landsat_data.js", scene])
      os.chdir(in_dir)
        
    file.write('    [' + str(index) + '] => '+ inNewSceneTar  +  '\n')

file.write(')'  +  '\n')
file.close()
print 'done writting missed scenes'

sys.exit()
