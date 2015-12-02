#! /usr/bin/python
#-------------------------------------------------------------------------------
# Name:		buildQuilt.py
# Purpose:	LandsatFACT application script that calls needed functions to
#		process custom requests for Vegetation Index products.
#
# Author:	LandsatFACT Project Team
#		support@landsatfact.com
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

import os, sys, glob, re
import numpy as np
from itertools import tee, izip
import zipfile, fnmatch
import pdb
import LSF, landsatFactTools_GDAL, rasterAnalysis_GDAL, LSFGeoTIFF
import customRequest

import gdal, sys, traceback, logging

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# GDAL error handler function
# http://pcjericks.github.io/py-gdalogr-cookbook/gdal_general.html#install-gdal-ogr-error-handler
def gdal_error_handler(err_class, err_num, err_msg):
    errtype = {
            gdal.CE_None:'None',
            gdal.CE_Debug:'Debug',
            gdal.CE_Warning:'Warning',
            gdal.CE_Failure:'Failure',
            gdal.CE_Fatal:'Fatal'
    }
    err_msg = err_msg.replace('\n',' ')
    err_class = errtype.get(err_class, 'None')
    logging.error('Error Number: %s' % (err_num))
    logging.error('Error Type: %s' % (err_class))
    logging.error('Error Message: %s' % (err_msg))

# install error handler
gdal.UseExceptions()
gdal.PushErrorHandler(gdal_error_handler)

"""
# Function to build a latest change quilt from the DB
# @param None
# @return a list containing a list of quadscene pair lists, each with 2 members,
#   (e.g., [['LC80140352015286LGN00LL', 'LE70140352015294EDC00LL'], ['LC80140352015286LGN00UL', 'LE70140352015294EDC00UL'], ['LC80140352015286LGN00UR', 'LE70140352015294EDC00UR'],
            ['LC80140352015286LGN00LR', 'LE70140352015294EDC00LR']]
#   from a list of scene pair lists returned by the select query shown in the sqlStatement below
#   (e.g., [['LC80140352015286LGN00', 'LE70140352015294EDC00']]

"""
def getQuadListFromDB():
    sqlStatement = """select scene_id from vw_scenes_less_five where rank=3 OR rank=4 ORDER BY wrs2_code, rank;"""

    #debugList=[['LE70140352013096EDC00', 'LC80140352013312LGN00']]
    #    ['LE70150402015173EDC00', 'LE70150402015189EDC00'],
    #    ['LC80150412014290LGN00', 'LC80150412015021LGN00'],
    #    ['LE70150422015141EDC00', 'LE70150422015285EDC00'],
    #    ['LC80230402014314LGN00', 'LC80230402014330LGN00'],
    #    ['LE70270402015049EDC00', 'LC80270402015057LGN00'],
    #    ['LC80270412014358LGN00', 'LE70270412015049EDC00']]
    #scenePairList=debugList
    scenePairList=[]
    resultsTup = landsatFactTools_GDAL.postgresCommand(sqlStatement)
    if resultsTup:
        for a, b in customRequest.pairwise(resultsTup):
            scenePairList.append([a[0], b[0]])

    quadPairList=[]
    for scenePair in scenePairList:
        quadPairList.append([scenePair[0]+'LL', scenePair[1]+'LL'])
        quadPairList.append([scenePair[0]+'UL', scenePair[1]+'UL'])
        quadPairList.append([scenePair[0]+'UR', scenePair[1]+'UR'])
        quadPairList.append([scenePair[0]+'LR', scenePair[1]+'LR'])

    return quadPairList

######################################################################################################################################
#pdb.set_trace()
######################################################################################################################################
lol=getQuadListFromDB()

if lol:

    # build change products as necessary
    for quadScenePairList in lol:
        try:
            customRequest.compare(quadScenePairList[0], quadScenePairList[1])
        except:
            tb = sys.exc_info()[2]
            tbinfo = traceback.format_tb(tb)[0]
            pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n    " + \
            str(sys.exc_type)+ ": " + str(sys.exc_value) + "\n"
            logging.error(pymsg)
            # try the next comparison
            continue

