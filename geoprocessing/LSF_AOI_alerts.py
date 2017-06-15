#! /usr/bin/python
#-------------------------------------------------------------------------------
# Name:         LSF_AOI_alerts.py
# Purpose:      LandsatFACT driver of LSF_zonalstats script
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
import os
import LSF, landsatFactTools_GDAL, subprocess
from collections import defaultdict
import csv
import re
import pdb

def writeListToFile (aList, filename):
    with open(filename, "w") as text_file:
        for item in aList:
            text_file.write("%s\n" % item)

def input2Date(swirFilename):
    m=re.search('L\S*SWIR\.tif', swirFilename)
    if m:
        return m.group()[33:40]
    else:
        return None

def writeRemapCSV(csvFilename):
    with open(csvFilename, 'wb') as csvfile:
        fieldnames = ['from lower', 'from upper', 'to']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'from lower': 247, 'from upper': 255, 'to': 4})
        writer.writerow({'from lower': 227, 'from upper': 247, 'to': 3})
        writer.writerow({'from lower': 207, 'from upper': 227, 'to': 2})
        writer.writerow({'from lower': 187, 'from upper': 207, 'to': 1})

def callZonalStats(aoiID, swirs, cloudMasks, gapMasks, statsOutPath):
    print aoiID, swirs, cloudMasks, gapMasks
    in_dir = os.getcwd()
    os.chdir('/tmp')
    print os.getcwd()
    sqlString = 'select st_asgeojson(geom) from aoi_alerts where aoi_id={};'.format(aoiID)
    resultsTup = landsatFactTools_GDAL.postgresCommand(sqlString)
    if resultsTup:
        geo = resultsTup[0][0]
        writeListToFile([geo],'tmpAOIFile')
    
    writeListToFile(map(lambda x: os.path.join(LSF.productStorage, 'swir', x),swirs),'tmpSwirsFile')
    writeListToFile(map(lambda x: os.path.join(LSF.productStorage, 'cloud_mask', x),cloudMasks),'tmpCloudMasksFile')
    writeListToFile(map(lambda x: os.path.join(LSF.productStorage, 'gap_mask', x),gapMasks),'tmpGapMasksFile')
    writeRemapCSV('remap.csv')

    codeIn = [LSF.path_projects + '/geoprocessing/LSF_zonalstats.py', 'tmpAOIFile', 
              'tmpSwirsFile', 'remap.csv', statsOutPath, '-c', 'tmpCloudMasksFile', '-g', 'tmpGapMasksFile']
    process = subprocess.Popen(codeIn,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = process.communicate()
    errcode = process.returncode
    os.chdir(in_dir)
    print out, err

def statsForAOINewProducts():
    """
    # Function to retrieve areas of interest with new products, call a function to determine the amount of
    #  change, and record the statistics for those areas of change in the DB
    # @param None
    # @return None
    """
    aDict = defaultdict(list)

    resultsTup = landsatFactTools_GDAL.postgresCommand('SELECT * FROM vw_aoi_alerts;')
    if resultsTup:
        for k, v in resultsTup:
            aDict[k].append(v)
        for k, v in aDict.iteritems():
            aoi = k
            swirs = list(filter(lambda x: 'SWIR' in x, aDict[k]))
            eventDateString=sorted(map(input2Date, swirs))[-1]
            sqlString='select (date \'{0}-01-01\' + integer \'{1}\' - 1);'.format(eventDateString[:4], eventDateString[-3:])
            resultsTup = landsatFactTools_GDAL.postgresCommand(sqlString)
            dateString = resultsTup[0][0]
            cloudMasks = list(filter(lambda x: 'Fmask' in x, aDict[k]))
            gapMasks = list(filter(lambda x: 'GapMask' in x, aDict[k]))
            sqlString = "SELECT st_area(geom::geography) from aoi_alerts where aoi_id={0}".format(aoi)
            resultsTup = landsatFactTools_GDAL.postgresCommand(sqlString)
            aoiAcres=float(resultsTup[0][0])*0.0002471044
            if aoiAcres > 50000:
                print 'Skipped aoi_id {0} because it is too large, {1} acres'.format(aoi, aoiAcres)
                continue
            sqlString = "SELECT exists (SELECT true FROM aoi_events WHERE aoi_id = {0} AND event_date = \'{1}\');".format(aoi,dateString)
            existingRow = landsatFactTools_GDAL.postgresCommand(sqlString)[0][0]
            if existingRow:
                print 'aoi_event for {0} on {1} has already been run'.format(aoi, dateString)
                continue

            # status = "Process Start"
            sqlString='insert into aoi_events(aoi_event_id, aoi_id, alert_status_id) VALUES(DEFAULT,\'{}\', 2) RETURNING aoi_event_id;'.format(aoi)
            resultsTup = landsatFactTools_GDAL.postgresCommand(sqlString)
            event_id = resultsTup[0][0]
            callZonalStats(aoi, swirs, cloudMasks, gapMasks, 'tmpStatsFile.csv')
            stats=[]
            with open('/tmp/tmpStatsFile.csv', 'rb') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    s=(row['Sum'])
                    if s:
                        h=int(float(s))
                    else:
                        h=0
                    stats.append((int(row['Unique region ID']), float(row['Area in square meters']), 
                                 int(row['Raster value']), h, int(row['Count']), int(row['Count*maxVal'])))
            #sorted_by_region_ID = sorted(stats, key=lambda tup: tup[0])
            def patchVal(v):return filter(lambda tup: tup[2]==v, stats)
            sumArea=reduce(lambda x,y: x+y, map(lambda x: x[1], stats), 0)*0.0002471044
            maxArea=reduce(lambda x,y: max(x,y), map(lambda x: x[1], stats), 0)*0.0002471044
            acresChange=reduce(lambda x,y: x+y, map(lambda x: x[1], patchVal(1)), 0)*0.0002471044
            acresAnalyzed=acresChange + reduce(lambda x,y: x+y, map(lambda x: x[1], patchVal(0)), 0)*0.0002471044
            percentAnalyzed=float(acresChange)/float(aoiAcres)*100
            percentChange=(float(acresChange)/float(acresAnalyzed))*100
            largestPatch=reduce(lambda x,y: max(x,y), map(lambda x: x[1], patchVal(1)), 0)*0.0002471044
            patchCount=len(patchVal(1))
            smallestPatch=reduce(lambda x,y: min(x,y), map(lambda x: x[1], patchVal(1)), 0)*0.0002471044
            sumOfSum=reduce(lambda x,y: x+y, map(lambda x: x[3], patchVal(1)), 0)
            sumOfMax=reduce(lambda x,y: x+y, map(lambda x: x[5], patchVal(1)), 0)
            if sumOfMax: 
                maxPatchSeverity=(float(sumOfSum)/float(sumOfMax))*100
            else: 
                maxPatchSeverity=0
            resultsTup = landsatFactTools_GDAL.postgresCommand('select * from write_aoi_events({0},{1},{2},{3},{4},{5},{6},{7},{8},\'{9}\''.format(
                                                                aoi, acresChange, percentChange, acresAnalyzed, percentAnalyzed,
                                                                smallestPatch, largestPatch, patchCount, event_id, dateString, maxPatchSeverity)+ ',\''+ ','.join(swirs) + '\');')
            if resultsTup[0][0] == False:
                print 'Table update failed'
            else:
                # status = "Process Complete"
                sqlString='UPDATE aoi_events set ("alert_status_id") = (3) where aoi_event_id={0};'.format(event_id)
                resultsTup = landsatFactTools_GDAL.postgresCommand(sqlString)
 

statsForAOINewProducts()
