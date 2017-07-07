#! /usr/bin/python
#-------------------------------------------------------------------------------
# Name:		customRequest.py
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

import os, sys, glob, re, traceback
import numpy as np
import LSF
import landsatFactTools_GDAL
import rasterAnalysis_GDAL
import LSFGeoTIFF
import localLib
from itertools import tee, izip
import zipfile, fnmatch, datetime
import pdb

outCustomRequestFolder = os.path.join(LSF.productStorage,'cr_zips')

"""
The general idea here is to map strings to TIFFs.
If there is no TIFF for a particular string ID, this code knows how to create it.
This code describes the dependencies between the TIFFs in the hopes of recreating a missing TIFF from its dependent parts if possible.
The description of the dependencies resemble rules in a makefile but with the following shape
def target: (stringID)
    dependencies
    command
The target is a TIFF (e.g., gapMask) or collection of TIFFs (e.g., extractedTar, comparisonProduct). The target function checks for the
existence of the dependencies then constructs the target using the command(s).
"""

"""
# Utility function used check the existence of database table rows
# @param rowID (e.g., 'LE70170362013133EDC00')
            tableName (e.g., 'minimum_dn')
            tableColumn (e.g., 'scene_id')
# @return a string that can be tested as a boolean
"""
def rowExists(rowID, tableName, tableColumn):
    # checks to see if there is a row with rowID in table tableName
    statement = "SELECT exists (SELECT true FROM {1} WHERE {0} = '{2}');".format(tableColumn,tableName,rowID)
    resultsTup = landsatFactTools_GDAL.postgresCommand(statement)[0][0]
    return resultsTup

"""
# Utility function used to parse the results of the SQL query below
# @param aList
# @return the members of aList in pairs (e.g., [['LE70220392013008EDC00LL', 'LC80220392015054LGN00LL'],
                                                ['LE70230392012365EDC00LR', 'LE70230392015053EDC00LR'],
                                                ['LE70230392012365EDC00UR', 'LE70230392015053EDC00UR']]

"""
def pairwise(aList):
    a = iter(aList)
    return izip(a, a)

"""
# Function to retrieve pending Custom Requests from the DB
# @param None
# @return a list containing a list of quadscene pair lists, each with 2 members,
#   the request_id, which is the name for the zip file that will contain the comparison product, and
#   the aoi_id
#   (e.g., [[['LC80140352015286LGN00LL', 'LE70140352015294EDC00LL'], ['LC80140352015286LGN00UL', 'LE70140352015294EDC00UL']], '3.zip', '194']
"""
def getCustomRequestFromDB():

    quadPairList=[]
    cr_zip_name=aoi_id=None

    resultsTup = landsatFactTools_GDAL.postgresCommand('select F.aoi_id from ( SELECT * FROM get_pendingcustomrequests() order by aoi_id limit 1) as F;')
    if resultsTup:
        aoi_id = resultsTup[0][0]
        resultsTup = landsatFactTools_GDAL.postgresCommand('select F.request_id from (SELECT * FROM get_customrequestsquads({}) limit 1) AS F;'.format(aoi_id))
        cr_zip_name = resultsTup[0][0]
        resultsTup = landsatFactTools_GDAL.postgresCommand('select concat(F.scene_id, quad_location) from (SELECT * FROM get_customrequestsquads({}) order by quad_id) AS F;'.format(aoi_id))
        for a, b in pairwise(resultsTup):
            quadPairList.append([a[0], b[0]])
    return [quadPairList, cr_zip_name, aoi_id]

"""
# Lowest level target function. Guarantees that the level 1 product tar file for sceneID now exists in /lsfdata/eros_data
# @param sceneID (e.g., 'LE70170362013133EDC00')
#
"""
def tar(sceneID):
    # if no tar for sceneID in tarStorage, go get it
    if not(re.search(sceneID, ' '.join(glob.glob(os.path.join(LSF.tarStorage, '*.gz'))))):
        # writes to extracted_imagery, minimum_dn, and landsat_metadata
        print "Begin extractProductForCompare " + str(datetime.datetime.now())
        productID = landsatFactTools_GDAL.getProductIDForScene(sceneID)
        landsatFactTools_GDAL.extractProductForCompare(sceneID, LSF.tarStorage,LSF.tiffsStorage,LSF.fmaskShellCall,LSF.quadsFolder,LSF.projectStorage, productID)
        print "End extractProductForCompare " + str(datetime.datetime.now())
    # if the tar's been processed, should at least be a row in minimum_dn
    # note if the row is missing
    else:
        resultRowExists = rowExists(sceneID, 'minimum_dn', 'scene_id')
        if resultRowExists == False:
            print "No row for {} in minimum_dn".format(sceneID)


"""
# Function that guarantees that the sceneID directory (e.g., 'LE70170362013133EDC00') is present in tiffStorage, /lsfdata/eros_data/extractedTars,
# and that the level 1 product band files have been extracted into it
# @param quadsceneID (e.g., 'LE70170362013133EDC00UR')
#
"""
def extractedTar(quadsceneID):
    sceneID=quadsceneID[:-2]
    # guarantee that level 1 product tar file for sceneID now exists in /lsfdata/eros_data/extractedTars
    tar(sceneID)
    # if /lsfdata/extractedTars/sceneID doesn't contain the level 1 product band files, extract them from the tar file
    #
    if not(re.search(sceneID, ' '.join(glob.glob(os.path.join(LSF.tiffsStorage, '*', '*.TIF*'))))):
        # make sure that the existing tar is valid
        existingTar=os.path.join(LSF.tarStorage, sceneID+".tar.gz")
        err=localLib.validTar(existingTar)
        if err:
            raise Exception(err)
        # for now use checkExisting. change to use tarHandling class when completed
        productID = landsatFactTools_GDAL.getProductIDForScene(sceneID)
        extractedPath = landsatFactTools_GDAL.checkExisting(existingTar, LSF.tiffsStorage, sceneID, productID)
        rasterAnalysis_GDAL.cloudMask(extractedPath)
        # get DN min number from each band in the scene and write to database
        dnminExists = landsatFactTools_GDAL.checkForDNminExist(extractedPath) # May not be needed in final design, used during testing
        if dnminExists == False:
            dnMinDict = rasterAnalysis_GDAL.getDNmin(extractedPath)
            # fix bug introduced by me in commit de5df07c4ca3ff71ae4d7da27b6018fe1bc2df04
            landsatFactTools_GDAL.writeDNminToDB(dnMinDict,extractedPath)
        # awkward but make sure mtl file has been read and put into the DB if necessary
        rasterAnalysis_GDAL.mtlData(sceneID,os.path.join(LSF.tiffsStorage,sceneID,sceneID+'_MTL.txt'))


"""
# Function that guarantees that the quadsceneID directory (e.g., 'LE70170362013133EDC00UL') is present in projectStorage, /lsfdata/project_data,
# and that cropped level 1 product band files are in it
# @param quadsceneID (e.g., 'LE70170362013133EDC00UL')
#
"""
def quadScene(quadsceneID):
    # this function is a little more complicated because it tries to take one of two possible shortcuts.
    # if there are clipped TIFFs, the previous work artifacts can safely no longer be there.
    # if the clipped TIFFs aren't there, look for unclipped TIFFs in tiffsStorage first.
    # if the unclipped TIFFs aren't there, the extractedTar "target" function will cause the tar to be downloaded

    sceneID=quadsceneID[:-2]
    if not(re.search(quadsceneID, ' '.join(glob.glob(os.path.join(LSF.projectStorage, '*'))))):
        # if the band files for quadsceneID in are not in projectStorage, get them from tiffsStorage, if possible, and clip them
        if not (re.search(sceneID, ' '.join(glob.glob(os.path.join(LSF.tiffsStorage, '*', '*.TIF*'))))):
            extractedTar(quadsceneID)
        # below is redundant code if exractedTar() called tar(). 
        # tar() calls extractProductForCompare() which includes the code below.
        # TO DO refactor extractProductForCompare to not populate both extractedTars and project_data.
        # the refactored code would fit in better with custom requests.
        quadPaths = rasterAnalysis_GDAL.cropToQuad(os.path.join(LSF.tiffsStorage, sceneID), LSF.projectStorage, LSF.quadsFolder)
        landsatFactTools_GDAL.writeQuadToDB(quadPaths)
        # get cloud cover percentage for each quad
        quadCCDict = landsatFactTools_GDAL.getQuadCCpercent(quadPaths)
        # =========================================================================
        # write input scene quads cloud cover percentage to the landsat_metadata table in the database
        landsatFactTools_GDAL.writeQuadsCCtoDB(quadCCDict,os.path.join(LSF.tiffsStorage, sceneID))

    # if the quad's been processed, should at least be a row in extracted_imagery
    # note if the row is missing
    else:
        resultRowExists = rowExists(quadsceneID, 'extracted_imagery', 'quad_scene')
        if resultRowExists == False:
            print "No row for {} in extracted_imagery".format(quadsceneID)

"""
# Utility function to create a sensorBand for a particular date
# @param quadsceneID (e.g.,'LE70170362013133EDC00UR')
# @return an instance of sensorBand
"""
def dateFn(quadsceneID):
    # check for clipped TIFFs first, because if they exist, the previous work artifacts could safely no longer be there
    quadScene(quadsceneID)
    return rasterAnalysis_GDAL.sensorBand(os.path.join(LSF.projectStorage, quadsceneID), LSF.tiffsStorage)

"""
# Function that guarantees the presence of a cirrus mask product TIFF (e.g., LC80180332015250LGN00LL_LE70180332015258EDC00LL_CirrusMask.tif)
# in the productStorage, /lsfdata/products/cirrus_mask
# @param 2 sensorBand instances
#
"""
def cirrusMask(date1, date2):
    # dateFns have completed therefore assume that, at least, the
    # quadscenes have been created in projectStorage
    # (i.e., sceneID1U*, sceneID1L*, sceneID2U*, and sceneID2L* directories are populuated)
    # eros_data may or may not be present

    outBasename = date1.sceneID + "_" + date2.sceneID
    outputTiffName=os.path.join(os.path.join(LSF.productStorage, 'cirrus_mask'), outBasename + '_CirrusMask.tif')
    if not os.path.exists(outputTiffName):
        landsatFactTools_GDAL.cirrusMask(date1,date2,LSF.outCIRRUSfolder,outBasename,LSF.quadsFolder,date2.sceneID[3:9],'LCV')

"""
# Function that guarantees the presence of a gap mask product TIFF (e.g., LC80180332015250LGN00LL_LE70180332015258EDC00LL_GapMask.tif)
# in the productStorage, /lsfdata/products/gap_mask
# @param 2 sensorBand instances
#
"""
def gapMask(date1, date2):
    # dateFns have completed therefore assume that, at least, the
    # quadscenes have been created in projectStorage
    # (i.e., sceneID1U*, sceneID1L*, sceneID2U*, and sceneID2L* directories are populuated)
    # eros_data may or may not be present

    outBasename = date1.sceneID + "_" + date2.sceneID
    outputTiffName=os.path.join(os.path.join(LSF.productStorage, 'gap_mask'), outBasename + '_GapMask.tif')
    if not os.path.exists(outputTiffName):
        landsatFactTools_GDAL.gaper(date1, date2, os.path.join(LSF.productStorage, 'gap_mask'), date1.sceneID + "_" + date2.sceneID, LSF.quadsFolder,date2.sceneID[3:9], 'CR')

"""
# Function that guarantees the presence of a NDVI product TIFF (e.g., LC80180332015250LGN00LR_LE70180332015258EDC00LR_percent_NDVI.tif)
# in the productStorage, /lsfdata/products/ndvi
# @param 2 sensorBand instances
#
"""
def ndvi(date1, date2):
	outBasename = date1.sceneID + "_" + date2.sceneID + '_percent_NDVI.tif'
	wrs2Name=date1.sceneID[3:9]
	outputTiffName=os.path.join(LSF.outNDVIfolder, outBasename)
	if not os.path.exists(outputTiffName):
	   ndvi1 = date1.ndvi("SR")
	   ndvi2 = date2.ndvi("SR")
	   ndviChange = ndvi2 - ndvi1
	   ndviPercentChange = ndviChange / np.absolute(ndvi1)
	   ndvi1 = None
	   ndvi2 = None
	   ndviPercentChange = np.multiply(100,ndviPercentChange)
	   shpName=os.path.join(LSF.quadsFolder, 'wrs2_'+ wrs2Name + date1.folder[-2:]+'.shp')
	   LSFGeoTIFF.Unsigned8BitLSFGeoTIFF.fromArray(ndviPercentChange, date1.geoTiffAtts).write(outputTiffName, shpName)
	   landsatFactTools_GDAL.writeProductToDB(os.path.basename(outputTiffName),date1.sceneID,date2.sceneID,'NDVI',date2.sceneID[9:16], 'CR')
	   ndviPercentChange = None
	else:
	   resultRowExists = rowExists(outBasename, 'products', 'product_id')
	   if resultRowExists == False:
            print "No row for {} in products".format(outBasename)

"""
# Function that guarantees the presence of a NDMI product TIFF (e.g., LC80180332015250LGN00LR_LE70180332015258EDC00LR_percent_NDMI.tif)
# in the productStorage, /lsfdata/products/ndmi
# @param 2 sensorBand instances
#
"""
def ndmi(date1, date2):
	outBasename = date1.sceneID + "_" + date2.sceneID+ '_percent_NDMI.tif'
	wrs2Name=date1.sceneID[3:9]
	outputTiffName=os.path.join(LSF.outNDMIfolder, outBasename )
	if not os.path.exists(outputTiffName):
	   ndmi1 = date1.ndmi("SR")
	   ndmi2 = date2.ndmi("SR")
	   ndmiChange = ndmi2 - ndmi1
	   ndmiPercentChange = ndmiChange / np.absolute(ndmi1)
	   ndmi1 = None
	   ndmi2 = None
	   ndmiPercentChange = np.multiply(100,ndmiPercentChange)
	   shpName=os.path.join(LSF.quadsFolder, 'wrs2_'+ wrs2Name + date1.folder[-2:]+'.shp')
	   LSFGeoTIFF.Unsigned8BitLSFGeoTIFF.fromArray(ndmiPercentChange, date1.geoTiffAtts).write(outputTiffName, shpName)
	   landsatFactTools_GDAL.writeProductToDB(os.path.basename(outputTiffName),date1.sceneID,date2.sceneID,'NDMI',date2.sceneID[9:16], 'CR')
	   ndmiPercentChange = None
	else:
	   resultRowExists = rowExists(outBasename, 'products', 'product_id')
	   if resultRowExists == False:
            print "No row for {} in products".format(outBasename)

"""
# Function that guarantees the presence of a SWIR product TIFF (e.g., LC80180332015250LGN00LL_LE70180332015258EDC00LL_percent_SWIR.tif)
# in the productStorage, /lsfdata/products/swir
# @param 2 sensorBand instances
#
"""
def swir(date1, date2):
	outBasename = date1.sceneID + "_" + date2.sceneID + '_percent_SWIR.tif'
	wrs2Name=date1.sceneID[3:9]
	outputTiffName=os.path.join(LSF.outSWIRfolder, outBasename)
	if not os.path.exists(outputTiffName):
	   swir1 = date1.SurfaceReflectance(date1.swir2,"swir2")
	   swir2 = date2.SurfaceReflectance(date2.swir2,"swir2")
	   swir = np.subtract(swir2,swir1)
	   swirPercentChange = swir / np.absolute(swir1)
	   swir = None
	   swir1 = None
	   swir2 = None
	   swirPercentChange = np.multiply(100,swirPercentChange)
   	   shpName=os.path.join(LSF.quadsFolder, 'wrs2_'+ wrs2Name + date1.folder[-2:]+'.shp')
	   LSFGeoTIFF.Unsigned8BitLSFGeoTIFF.fromArray(swirPercentChange, date1.geoTiffAtts).write(outputTiffName, shpName)
	   landsatFactTools_GDAL.writeProductToDB(os.path.basename(outputTiffName),date1.sceneID,date2.sceneID,'SWIR',date2.sceneID[9:16], 'CR')
	   swirPercentChange = None
    # if the product's been created, should  be a row in products
    # note if the row is missing
	else:
	   resultRowExists = rowExists(outBasename, 'products', 'product_id')
	   if resultRowExists == False:
            print "No row for {} in products".format(outBasename)

"""
# Function that guarantees the presence of a cloud mask product TIFF (e.g., LC80180332015250LGN00LL_LE70180332015258EDC00LL_Fmask.tif)
# in the productStorage, /lsfdata/products/cloud_mask
# @param 2 sensorBand instances
#
"""
def cloudMask(date1, date2):
    # dateFns have completed therefore assume that, at least, the
    # quadscenes have been created in projectStorage
    # (i.e., sceneID1U*, sceneID1L*, sceneID2U*, and sceneID2L* directories are populuated)
    # eros_data may or may not be present
	# cloudMask dependencies are on files in tiffStorage, /lsfdata/eros_data/extractedTars/

    outBasename = date1.sceneID + "_" + date2.sceneID + '_Fmask.tif'
    wrs2Name=date1.sceneID[3:9]

    if not os.path.exists(date1.folder+"/"+date1.sceneID+"_MTLFmask.TIF"):
	   rasterAnalysis_GDAL.cloudMask(os.path.join(LSF.tiffsStorage, date1.sceneID[:-2]))
	   # create quads from the input scene
	   quadPaths = rasterAnalysis_GDAL.cropToQuad(os.path.join(LSF.tiffsStorage, date1.sceneID[:-2]), LSF.projectStorage, LSF.quadsFolder)
	   landsatFactTools_GDAL.writeQuadToDB(quadPaths)
	   # get cloud cover percentage for each quad
	   quadCCDict = landsatFactTools_GDAL.getQuadCCpercent(quadPaths)
	   # =========================================================================
	   # write input scene quads cloud cover percentage to the landsat_metadata table in the database
	   landsatFactTools_GDAL.writeQuadsCCtoDB(quadCCDict,date1.folder.replace('UR','').replace('UL','').replace('LR','').replace('LL',''))
    if not os.path.exists(date2.folder+"/"+date2.sceneID+"_MTLFmask.TIF"):
	   rasterAnalysis_GDAL.cloudMask(os.path.join(LSF.tiffsStorage, date2.sceneID[:-2]))
	   # create quads from the input scene
	   quadPaths = rasterAnalysis_GDAL.cropToQuad(os.path.join(LSF.tiffsStorage, date2.sceneID[:-2]), LSF.projectStorage, LSF.quadsFolder)
	   landsatFactTools_GDAL.writeQuadToDB(quadPaths)
	   # get cloud cover percentage for each quad
	   quadCCDict = landsatFactTools_GDAL.getQuadCCpercent(quadPaths)
	   # =========================================================================
	   # write input scene quads cloud cover percentage to the landsat_metadata table in the database
	   landsatFactTools_GDAL.writeQuadsCCtoDB(quadCCDict,date1.folder.replace('UR','').replace('UL','').replace('LR','').replace('LL',''))

    outputTiffName=os.path.join(LSF.outFMASKfolder,outBasename)
    if not os.path.exists(outputTiffName):
	   if os.path.exists(date1.folder+"/"+date1.sceneID+"_MTLFmask.TIF") and os.path.exists(date2.folder+"/"+date2.sceneID+"_MTLFmask.TIF"):
             qaTiffName=os.path.join(LSF.tiffsStorage, date1.sceneID[:-2], date1.sceneID[:-2]) + "_BQA.TIF"
             if os.path.exists(qaTiffName):
               cloud_mask_type='BQA'
             else:
               cloud_mask_type='FMASK'
             FmaskReclassedArray1 = date1.cloudMaskArray()
             FmaskReclassedArray2 = date2.cloudMaskArray()
             FmaskReclassedArray = FmaskReclassedArray1 * FmaskReclassedArray2
             FmaskReclassedArrayPlus1 = FmaskReclassedArray + 1
             shpName=os.path.join(LSF.quadsFolder, 'wrs2_'+ wrs2Name + date1.folder[-2:]+'.shp')
             LSFGeoTIFF.Unsigned8BitLSFGeoTIFF.fromArray(FmaskReclassedArrayPlus1, date1.geoTiffAtts).write(outputTiffName, shpName)
             landsatFactTools_GDAL.writeProductToDB(os.path.basename(outputTiffName),date1.sceneID,date2.sceneID,'CLOUD',date2.sceneID[9:16], 'CR',cloud_mask_type)
    # if the product's been created, should  be a row in products
    # note if the row is missing
    else:
	   resultRowExists = rowExists(outBasename, 'products', 'product_id')
	   if resultRowExists == False:
             print "No row for {} in products".format(outBasename)


"""
# Function that assembles zip file, using the file name provided in the request_id field in the custom_request table
# in productStorage, /lsfdata/products/cr_zips
# @param the zipFile in /lsfdata/products/cr_zips
#       pattern to match this particular product (e.g., 'LC80140352015286LGN00LL_LE70140352015294EDC00LL_*.tif'
#
"""
def packageProduct(zipFile, pattern):

    for base, dirs, files in os.walk(LSF.productStorage):
        goodfiles = fnmatch.filter(files, pattern)
        for fileName in goodfiles:
            zipFile.write(os.path.join(base, fileName))

"""
# Function that assembles the custom request product, using the file name provided in the request_id field in the custom_request table
# in the productStorage, /lsfdata/products/cr_zips
# @param 2 sensorBand instances
# @param the name of the zip to put into /lsfdata/products/cr_zips
#
"""
def comparisonProduct(quadsceneID1, quadsceneID2):
    # potentially less functionally elegant but rather than call each change product target function with function arguments
    # cache the returns from the dateFn calls and reuse them since they can safely be shared between all products for the same dates

    print "Begin scene processing " + str(datetime.datetime.now())
    date1=dateFn(quadsceneID1)
    date2=dateFn(quadsceneID2)
    gapMask(date1, date2)
    # comment out the line below o remove the Cirrus product
    cirrusMask(date1, date2)
    cloudMask(date1, date2)
    ndvi(date1, date2)
    ndmi(date1, date2)
    swir(date1, date2)
    print "End scene processing " + str(datetime.datetime.now())


"""
# Top level function to begin custom request processing
# @param 2 quadsceneIDs (e.g., 'LE70170362013133EDC00UR' and 'LE70170362013149EDC00UR')
#
"""
def compare(quadsceneID1, quadsceneID2):
    if int(quadsceneID1[9:16]) > int(quadsceneID2[9:16]):
        comparisonProduct(quadsceneID2, quadsceneID1)
    else:
        comparisonProduct(quadsceneID1, quadsceneID2)


# process one change request

customRequestInfo=getCustomRequestFromDB()
lol=customRequestInfo[0]
request_id=customRequestInfo[1]
aoi_id=customRequestInfo[2]
if lol:
    # status = "Process Start"
    landsatFactTools_GDAL.postgresCommand('insert into custom_request_dates (aoi_id, custom_request_date, custom_request_status_id) VALUES(\'{}\', now(), 2);'.format(aoi_id))
    # keep track of the number of times we process comparisons error free so that we can send partial zips if need be
    successfulComparisons=0

    if not os.path.exists(os.path.join(outCustomRequestFolder, request_id)):
        # build change products as necessary
        for quadScenePairList in lol:
         try:
            compare(quadScenePairList[0], quadScenePairList[1])
            successfulComparisons+=1
         except:
            tb = sys.exc_info()[2]
            tbinfo = traceback.format_tb(tb)[0]
            pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n    " + \
            str(sys.exc_type)+ ": " + str(sys.exc_value) + "\n"
            print pymsg
            # try the next comparison
            continue

        # invoke zip to package up any completed products
        if successfulComparisons:
            crZip=zipfile.ZipFile(os.path.join(outCustomRequestFolder,request_id), 'w')
            for quadScenePairList in lol:
                if int(quadScenePairList[0][9:16]) > int(quadScenePairList[1][9:16]):
                    packageProduct(crZip, quadScenePairList[1] + "_" + quadScenePairList[0] +'_*.tif*')
                else:
                    packageProduct(crZip, quadScenePairList[0] + "_" + quadScenePairList[1] +'_*.tif*')
            # add layer files
            for base, dirs, files in os.walk(os.path.join(LSF.productStorage, 'layer_files')):
                for fileName in files:
                    crZip.write(os.path.join(base, fileName))

            crZip.close()

            # status = "Process Complete"
            landsatFactTools_GDAL.postgresCommand('insert into custom_request_dates (aoi_id, custom_request_date, custom_request_status_id) VALUES(\'{}\', now(), 3);'.format(aoi_id))

