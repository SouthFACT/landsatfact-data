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

statement = """
		WITH dups as (SELECT
			substring(scene_id,1,19) as base_scene,
			max(substring(scene_id,20,2)::integer) as max_scene_count,
			count(*)
		FROM landsat_metadata 
		--WHERE scene_id LIKE 'LE70190332017062EDC%'
		GROUP BY 
			substring(scene_id,1,19)
		HAVING count(*) > 1
			--substring(scene_id,20,2)::integer
		ORDER BY substring(scene_id,1,19)) 
			DELETE
			FROM landsat_metadata as lsm
				USING dups
			WHERE
					substring(lsm.scene_id,1,19) = dups.base_scene AND
					substring(scene_id,20,2)::integer < max_scene_count"""

resultsTup = landsatFactTools_GDAL.postgresCommand(statement)

print resultsTup

print 'Done removing dup scenes'
sys.exit()

