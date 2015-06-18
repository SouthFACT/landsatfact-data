#! /usr/bin/python
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Brian McLean
# 
# Created:     03/25/2015
# Copyright:   (c) mclebr 2014
# Licence:     
""" This code was developed in the public domain.
This code is provided "as is", without warranty of any kind,
express or implied, including but not limited to the warranties of
merchantability, fitness for a particular purpose and noninfringement.
In no event shall the authors be liable for any claim, damages or
other liability, whether in an action of contract, tort or otherwise,
arising from, out of or in connection with the software or the use or
other dealings in the software."""
#-------------------------------------------------------------------------------

import os, sys, tarfile, shutil, traceback, gzip, subprocess, stat, datetime
from subprocess import PIPE
import psycopg2
from operator import itemgetter
import rasterAnalysis_GDAL



sys.path.append("../var")
try:
    from Config import *
except:
    print "Cannot find local settings file 'Config.py'.  You need to create a Config.py file that contains"
    print "settings appropriate for to the PGSQL DB"
    exit(-1)


reload(rasterAnalysis_GDAL)

def extractProductForCompare(diff_tar,tarStorage,tiffsStorage,fmaskShellCall,quadsFolder):
	print "call to extractProductForCompare with: "+ diff_tar
	# call download_landsat_data_by_sceneid.php
	in_dir = os.getcwd()
	os.chdir('/var/vsites/landsatfact-data-dev.nemac.org/project/dataexchange')
	print os.getcwd()
	# download the scene data
	subprocess.call(["php", "download_landsat_data_by_sceneid.php", diff_tar])
	# now extract the downloaded file accordingly
	inNewSceneTar = os.path.join(tarStorage, diff_tar+".tar.gz")
	extractedPath = checkExisting(inNewSceneTar, tiffsStorage)
	#do the other pre-processing stuff
	os.chdir(in_dir)
	rasterAnalysis_GDAL.runFmask(extractedPath,fmaskShellCall)
	# get DN min number from each band in the scene and write to database
	dnminExists = checkForDNminExist(extractedPath) # May not be needed in final design, used during testing
	if dnminExists == False:
		dnMinDict = rasterAnalysis_GDAL.getDNmin(extractedPath)
		writeDNminToDB(dnMinDict,extractedPath)
	# create quads from the input scene
	quadPaths = rasterAnalysis_GDAL.cropToQuad(extractedPath,quadsFolder)
	writeQuadToDB(quadPaths)
	# get cloud cover percentage for each quad
	quadCCDict = getQuadCCpercent(quadPaths)
	# =========================================================================
	# write input scene quads cloud cover percentage to the landsat_metadata table in the database
	writeQuadsCCtoDB(quadCCDict,extractedPath)	
	print os.getcwd()

def checkExisting(inTarPath, extractFolder):
    """# Check to see if the entered Tar files have already been extracted. If any
    of the files exist it does not re-extract them. This only happens if the extracted
    files are left where the script extracts them orignial relative to the tar file.
    If the extracted root folder is moved from the folder where the Tar file is the Tar
    files will be extracted again """
    L5Rasts = ["_B1", "_B2", "_B3", "_B4", "_B5", "_B6", "_B7"]
    L7Rasts = ["_B1", "_B2", "_B3", "_B4", "_B5", "_B6_VCID_1", "_B6_VCID_2", "_B7"]
    L8Rasts = ["_B1", "_B2", "_B3", "_B4", "_B5", "_B6", "_B7", "_B9", "_B10", "_B11", "_BQA"]
    fmaskFiles = ["_MTL"]#,"_GCP"
    extractedRoot = os.path.join(extractFolder,os.path.basename(inTarPath[0:-7]))
    if os.path.basename(inTarPath).startswith("LE7"):
        sensorType = L7Rasts
    elif os.path.basename(inTarPath).startswith("LT5"):
        sensorType = L5Rasts
    elif os.path.basename(inTarPath).startswith("LC8"):
        sensorType = L8Rasts
    if os.path.exists(extractedRoot) == True:
        existingFiles = os.listdir(extractedRoot)
        neededBands=[]
        for band in sensorType:
            bandFile = os.path.basename(extractedRoot) + band + ".TIF"
            if not bandFile in existingFiles:
                neededBands.append(band)
        for txt in fmaskFiles:
            txtFile = os.path.basename(extractedRoot) + txt + ".txt"
            if not txtFile in existingFiles:
                neededBands.append(txt)
        if len(neededBands) == 0:
            return extractedRoot
        else:
            unzipTIFgap(inTarPath, neededBands, extractedRoot)
            return extractedRoot
    else:
        neededBands = sensorType + fmaskFiles
        unzipTIFgap(inTarPath, neededBands, extractedRoot)
        return extractedRoot
		
def unzipTIFgap(inTar, sensorType, extractPath):
    """Extracts the tar files based on which bands checkExisting tells it to."""
    tar = tarfile.open(inTar)
    checkList = tar.getnames()
    for band in sensorType:
        for tarFileName in checkList:
            if band in tarFileName:
                break
        else:
            # the print statement needs to be replaced with a logger or similar in final server version so the process will know what to do if
            # a corrupt tar is downloaded.  Prob needs to re-trigger a new download or log that the tar is corrupt and can't be processed
            # but needs to restart for the next scene tar that will be processed that night, Terminate this script and trigger another???
            print "\nThe tarfile {0} is corrupt.  Please delete this file and try to re-download it from EROS.\nThe tool will now terminate.\n".format(inTar)
            sys.exit(0)
    for item in tar:
        for band in sensorType:
            if band == str(item.name)[21:-4] or ('gap_mask' in str(item.name) and band in str(item.name)):
                print ("Extracting " + item.name)
                #extractPath=extracted
                tar.extract(item, path=extractPath)
                #jdm 6/11/15 make sure the file you just extract is group and owner 
                file_of_interest = extractPath+'/'+item.name
                print "file_of_interest on which to set file perms: "+file_of_interest
                os.chmod(file_of_interest, 0664)
    gapMaskPath=os.path.join(extractPath,"gap_mask")
    if os.path.exists(gapMaskPath) == True:
        gapFiles = os.listdir(gapMaskPath)
        for f in gapFiles:
            if f.endswith("gz"):
                if not f[0:-3] in gapFiles:
                        inGZfile=gzip.open(os.path.join(gapMaskPath,f),'rb')
                        outGZfile=open(os.path.join(gapMaskPath,f[0:-3]),'wb')
                        outGZfile.write(inGZfile.read())
                        inGZfile.close()
                        outGZfile.close()
	# jdm 6/11/2015: Put the below as a double-check that all unzipped files
	# are indeed accessible to everyone as necessary
	# see http://stackoverflow.com/questions/2853723/whats-the-python-way-for-recursively-setting-file-permissions
	for dirpath, dirnames, filenames in os.walk(gapMaskPath):
		for filename in filenames:
			path = os.path.join(dirpath, filename)
			os.chmod(path, 0o777)
	for dirpath, dirnames, filenames in os.walk(extractPath):
		for filename in filenames:
			path = os.path.join(dirpath, filename)
			os.chmod(path, 0o777)			
			
def gaper(val1, val2, outGAPfolder, baseName):
    # input val are rasterAnalysis_GDAL sensorBand Class objects
    # Creates a gap mask for the scene if it came from Landsat 7 after
    # the ordinal date of 2003151 (5/31/2003) when the SLC went offline
    gapMaskList=[]
    if val1.platformType == "LE7" and val1.ordinalData > 2003151:
        gapMask1=val1.gapMasker()
        gapMaskList.append(gapMask1)
    if val2.platformType == "LE7" and val2.ordinalData > 2003151:
        gapMask2=val2.gapMasker()
        gapMaskList.append(gapMask2)
    if len(gapMaskList) == 2:
        gapMask = gapMask1[0] * gapMask2[0]
        rasterAnalysis_GDAL.createOutTiff(gapMask1[1],gapMask,os.path.join(outGAPfolder,baseName),'gm')
    elif len(gapMaskList) == 1:
        gapMask = gapMaskList[0]
        rasterAnalysis_GDAL.createOutTiff(gapMask[1],gapMask[0],os.path.join(outGAPfolder,baseName),'gm')


def getQuadCCpercent(quadPaths):
    quadCCDict = {}
    for quadPath in quadPaths:
        quadTiffs = os.listdir(quadPath)
        for tiff in quadTiffs:
            if tiff[-12:] == "MTLFmask.TIF":
                FmaskQuadData = rasterAnalysis_GDAL.rast2array(os.path.join(quadPath,tiff))
                ccPer = rasterAnalysis_GDAL.cloudCover(FmaskQuadData[0])
                quadCCDict.update({tiff[0:23]:ccPer})
    return quadCCDict


def writeQuadToDB(pathList):
    # writes extracted quad data to extracted_imagery table in database
    # if the quad_scene already exists it will update the process_date
    for path in pathList:
        quadScene = os.path.basename(path)
        sceneID = quadScene[0:21]
        quadID = quadScene[3:9]+quadScene[-2:]
        tableName = 'extracted_imagery'
        tableColumnList = ['quad_scene','scene_id','quad_id','process_date']
        update = "UPDATE {0} SET {1} = CURRENT_DATE WHERE {2} = '{3}';".format(tableName,tableColumnList[3],tableColumnList[0],quadScene)
        whereClause = "WHERE NOT EXISTS (SELECT 1 FROM {1} WHERE {2} = '{0}')".format(quadScene,tableName,tableColumnList[0])
        statement = "{8} INSERT INTO {0}({1}, {2}, {3}, {4}) SELECT '{5}', '{6}', '{7}', CURRENT_DATE {9}"\
        .format(tableName,tableColumnList[0],tableColumnList[1],tableColumnList[2],tableColumnList[3],quadScene,sceneID,quadID,update,whereClause)
        print statement
        postgresCommand(statement)

def writeProductToDB(product_id,input1,input2,product_type,product_date):
    # writes newly created products to products table in database
	# product_id: LE70270402015145EDC01UR_LE70270402015161EDC00UR_percent_NDVI16.tif
	tableName = 'products'
	normaldate = datetime.datetime(int(product_date[0:4]), 1, 1) + datetime.timedelta(int(product_date[4:7]) - 1)
	normaldate_truncated = datetime.date(normaldate.year, normaldate.month, normaldate.day)
	statement = "INSERT INTO {0}(product_id, input1, input2, product_type, product_date) VALUES ('{1}', '{2}', '{3}', '{4}', '{5}');".format(tableName,product_id,input1,input2,product_type,str(normaldate_truncated))
	print statement
	postgresCommand(statement)
		
def writeDNminToDB(dataDict,path):
    # writes DN min values to minimum_dn table in database
    sceneID = os.path.basename(path)
    for k,v in dataDict.items():
        tableName = 'minimum_dn'
        tableColumnList = ['scene_id','band','minimum_dn']
        statement = "INSERT INTO {0}({1}, {2}, {3}) VALUES ('{4}', '{5}', {6});".format(tableName,tableColumnList[0],tableColumnList[1],tableColumnList[2],sceneID,k,v)
        postgresCommand(statement)


def checkForDNminExist(path):
    # checks to see if DN min has been calculated, if so it skips the calculation step
    # !!!!!!!!!!! ---------- may not be needed in final version but speeds up testing ----- !!!!!!!!
    sceneID = os.path.basename(path)
    tableName = 'minimum_dn'
    tableColumnList = ['scene_id']
    statement = "SELECT exists (SELECT true FROM {1} WHERE {0} = '{2}');".format(tableColumnList[0],tableName,sceneID)
    resultsTup = postgresCommand(statement)[0][0]
    return resultsTup


def writeQuadsCCtoDB(quadCCDict,path):
    # writes the cloud cover percentage to the landsat_metadata table
    tableName = "landsat_metadata"
    sceneID = os.path.basename(path)
    tableColumnList = ["scene_id", "cc_quad_ul","cc_quad_ur","cc_quad_ll","cc_quad_lr"]
    update = "UPDATE {0} SET {1} = {2}, {3} = {4}, {5} = {6}, {7} = {8} WHERE {9} = '{10}';"\
    .format(tableName,tableColumnList[1],quadCCDict[sceneID+'UL'],tableColumnList[2],quadCCDict[sceneID+'UR'],tableColumnList[3],\
    quadCCDict[sceneID+'LL'],tableColumnList[4],quadCCDict[sceneID+'LR'],tableColumnList[0],sceneID)
    print update
    postgresCommand(update)


def getNextBestQuad(quadCCDict,ccThreshold):
    # make list of scene list to compare [[URnew,URolder], [LLnew,LLolder], etc]
    quadTiffList2Process = []
    tableName = "landsat_metadata"
    tableColumnList = ["scene_id", "path", "row"]
    julianDate = 'CAST(substring({0} from 10 for 7) AS integer) AS julian_date'.format(tableColumnList[0])
    subQ = '(SELECT *, {0} FROM {1}) AS other'.format(julianDate,tableName)
    orderBy = 'ORDER BY julian_date DESC LIMIT 1'
    for k,v in quadCCDict.items():
        if v <=ccThreshold:
            ccField = 'cc_quad_'+k[-2:].lower()
            path = k[3:6]
            row = k[6:9]
            sceneID = k[0:21]
            inJdate = int(k[9:16])
            #findNextCommand = "SELECT {0}, {2} FROM {3} WHERE {1} < {4} and {5} = '{6}' and {7} = '{8}' and NOT {0} = '{9}' {10}"\
            #.format(tableColumnList[0],ccField,julianDate,tableName,ccThreshold,tableColumnList[1],path,tableColumnList[2],row,sceneID,orderBy)
            findNextCommand = "SELECT {0}, julian_date FROM {2} WHERE {1} < {4} and {5} = '{6}' and {7} = '{8}' and NOT {0} = '{9}' and julian_date < {11} {10}"\
            .format(tableColumnList[0],ccField,subQ,tableName,ccThreshold,tableColumnList[1],path,tableColumnList[2],row,sceneID,orderBy,inJdate)
            print findNextCommand
            resultsTup = postgresCommand(findNextCommand) #,findNextValues
            #print resultsTup
            if len(resultsTup) > 0:
                quadTiffList2Process.append([resultsTup[0][0]+k[-2:],k])
    print "Quads to process: ", quadTiffList2Process
    return quadTiffList2Process

def getDNminDictfromDB(sceneID):
    # gets the DN minimum number from the database for the 4 needed bands in each scene
    DNminDict = {}
    tableName = 'minimum_dn'
    tableColumnList = ['scene_id','band','minimum_dn']
    statement = "SELECT {1}, {2} FROM {3} WHERE {0} = '{4}';".format(tableColumnList[0],tableColumnList[1],tableColumnList[2],tableName,sceneID)
    resultsTup = postgresCommand(statement)
    for results in resultsTup:
        DNminDict.update({results[0]:results[1]})
    return DNminDict


def postgresCommand(command,values=None):
    """ """
    try:
        # dbConn = psycopg2.connect("dbname=x user=y password=z")
		dbConn = psycopg2.connect(POSTGIS_CONNECTION_STRING)
    except:
        print "Unable to connect to the database"
        sys.exit()
    cur = dbConn.cursor()
    try:
        cur.execute(command)
    except:
        print "failed"
    try:
        resultsTup = cur.fetchall()
        return resultsTup
    except:
        pass
    try:
        dbConn.commit()
    except:
        pass
    cur.close()
    dbConn.close()


def cleanDir(dirPath):
    folderFiles= os.listdir(dirPath)
    for f in folderFiles:
        if not "gap_mask" in f and not "Thumbs" in f and not "movedFrom" in f:
            if not f.endswith(".TIF") and not f.endswith("MTL.txt"):
                moveDir = os.path.join(dirPath,"movedFromRoot")
                if os.path.exists(moveDir) == False:
                    os.mkdir(moveDir)
                shutil.copy(os.path.join(dirPath,f),moveDir)
                os.remove(os.path.join(dirPath,f))






