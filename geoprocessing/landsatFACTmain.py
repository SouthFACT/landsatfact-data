#! /usr/bin/python
#-------------------------------------------------------------------------------
# Name:		landsatFACTmain.py
# Purpose:	LandsatFACT application script that calls needed functions to
#		process TAR compressed files into Vegetation Index products.
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

import os, sys, glob
import landsatFactTools_GDAL
import rasterAnalysis_GDAL
import numpy as np
import psycopg2

reload(landsatFactTools_GDAL)
reload(rasterAnalysis_GDAL)

# =========================================================================
runList = []
os.chdir(r'/lsfdata1/eros_data/')
for file in glob.glob("*.tar.gz"):
    runList.append(file)

for tar in runList:
	# set tar file to analyze
	if not tar[-7:] == '.tar.gz':
		print "incorrect file type"
		sys.exit()
	# set Fmask.exe location
	# Fmaskexe = r'S:\Geospatial\LandsatFACT\Fmask.exe' #BM's original
	fmaskShellCall = r'/var/vsites/landsatfact-data-dev.nemac.org/project/geoprocessing/fmaskLinux/Fmask32/runFmask32.sh'
	# Fmaskexe = r'G:\LandsatFACT\Fmask.exe'
	# set folder location of the quad vector files
	# quadsFolder = r'S:\Geospatial\LandsatFACT\geodata\vector\quads_indv_proj' #BM's original
	quadsFolder = r'/var/lsfdata1/eros_data/quads_indv_proj'
	# set folder locations
	# folder where the tar.gz's are stored
	# tarStorage = r'S:\Geospatial\LandsatFACT\data\tarFiles' #BM's original
	tarStorage = r'/lsfdata1/eros_data'
	# folder where you want the extracted tiff's to be stored, they will automatically be
	# put inside of a subfolder labeled with the scene name
	# tiffsStorage = r'S:\Geospatial\LandsatFACT\data\extractedTars' #BM's original
	tiffsStorage = r'/lsfdata1/eros_data/extractedTars'
	# root folder for the project output storage, intermediate products that could be combined for custom request products
	# if this path does not exist the script will create it
	projectStorage = r'/lsfdata1/project_data'# root folder for the project output storage
	# if this path does not exist the script will create it
	# productStorage = r'S:\Geospatial\LandsatFACT\data\20150414' #BM's original
	productStorage = r'/lsfdata1/products'
	# set output folder locations per product
	# if this path does not exist the script will create it
	outNDVIfolder = os.path.join(productStorage,'ndvi')
	outNDMIfolder = os.path.join(productStorage,'ndmi')
	outSWIRfolder = os.path.join(productStorage,'swir')
	outGAPfolder = os.path.join(productStorage,'gap_mask')
	outFMASKfolder = os.path.join(productStorage,'cloud_mask')
	# set cloud cover threshold level, quad scene's with a higher percentage of
	# cloud cover will not be processed.
	cloudCoverThreshold = 50
	# =========================================================================
	# sets full path for the tarfile to be analyzed
	inNewSceneTar = os.path.join(tarStorage, tar)
	# check to see if the tar file has been extracted, if not extract the files
	print "Checking for: "+tar
	extractedPath = landsatFactTools_GDAL.checkExisting(inNewSceneTar, tiffsStorage)
	# run Fmask
	# jdm 4/22/15: after spending a couple of days trying to get FMASK installed on cloud4
	# I have not been able to get it to work.  Therefore, for now I am commenting this out
	# rasterAnalysis_GDAL.runFmask(extractedPath,Fmaskexe) #BM's original
	print extractedPath
	runFmaskBool = rasterAnalysis_GDAL.runFmask(extractedPath,fmaskShellCall)
	if (runFmaskBool== True):
        # get DN min number from each band in the scene and write to database
		dnminExists = landsatFactTools_GDAL.checkForDNminExist(extractedPath) # May not be needed in final design, used during testing
		if dnminExists == False:
			dnMinDict = rasterAnalysis_GDAL.getDNmin(extractedPath)
			landsatFactTools_GDAL.writeDNminToDB(dnMinDict,extractedPath)
		# create quads from the input scene
		quadPaths = rasterAnalysis_GDAL.cropToQuad(extractedPath,projectStorage,quadsFolder)
		landsatFactTools_GDAL.writeQuadToDB(quadPaths)
		# get cloud cover percentage for each quad
		quadCCDict = landsatFactTools_GDAL.getQuadCCpercent(quadPaths)
		# =========================================================================
		# write input scene quads cloud cover percentage to the landsat_metadata table in the database
		landsatFactTools_GDAL.writeQuadsCCtoDB(quadCCDict,extractedPath)
		# for each quad this finds the closest scene that passes the cloud cover threshold for processing
		quadTiffList2Process = landsatFactTools_GDAL.getNextBestQuad(quadCCDict,cloudCoverThreshold)
		# =========================================================================
		#jdm: Need to make sure the next best quads we are going to be comparing to are actually extracted
		#and pre-processed to a level appropriate for differencing.
		print "quadTiffList2Process: ", quadTiffList2Process
		#TO-DO: create/call a function in landsatFactTools_GDAL called extractProductForCompare()
		#loop through quadTiffList2Process and get unique list of data to download
		for quad_pair in quadTiffList2Process:
			base_quad = quad_pair[1]
			diff_quad = quad_pair[0]
			# The first quad that is determined to be missing from disk sets off a call
			# to extractProductForCompare.  extractProductForCompare then download the tar ball for that
			# scene and presumably the next time through a quad from that given seen will be
			# accounted for.
			if os.path.exists(projectStorage+'/'+diff_quad) == False:
				landsatFactTools_GDAL.extractProductForCompare(diff_quad[:-2],tarStorage,tiffsStorage,fmaskShellCall,quadsFolder,projectStorage)
			else:
				print diff_quad+" already exist in the projectStorage"
		# =========================================================================
		# checks the list of quads, if 0 then there were no quads under the cloud cover threshold
		# so there is nothing to process for that scene
		if len(quadTiffList2Process) > 0:
			#print "quadTiffList2Process: ", quadTiffList2Process
			# for each quad pair perform the change analysis
			for compareList in quadTiffList2Process:
				pathList = [os.path.join(projectStorage,compareList[0]), os.path.join(projectStorage,compareList[1])]
			# =========================================================================
				# sets the scenes in order
				tifPathList = pathList
				#print "tifPathList: ", tifPathList
				if int(os.path.basename(tifPathList[0])[9:13]) > int(os.path.basename(tifPathList[1])[9:13]):
					date1=rasterAnalysis_GDAL.sensorBand(tifPathList[1], tiffsStorage)
					date2=rasterAnalysis_GDAL.sensorBand(tifPathList[0], tiffsStorage)
				elif int(os.path.basename(tifPathList[0])[9:13]) < int(os.path.basename(tifPathList[1])[9:13]):
					date1=rasterAnalysis_GDAL.sensorBand(tifPathList[0], tiffsStorage)
					date2=rasterAnalysis_GDAL.sensorBand(tifPathList[1], tiffsStorage)
				else:
					if int(os.path.basename(tifPathList[0])[13:16]) > int(os.path.basename(tifPathList[1])[13:16]):
						date1=rasterAnalysis_GDAL.sensorBand(tifPathList[1], tiffsStorage)
						date2=rasterAnalysis_GDAL.sensorBand(tifPathList[0], tiffsStorage)
					else:
						date1=rasterAnalysis_GDAL.sensorBand(tifPathList[0], tiffsStorage)
						date2=rasterAnalysis_GDAL.sensorBand(tifPathList[1], tiffsStorage)
			# =========================================================================
				# create product name
				outBasename = date1.sceneID + "_" + date2.sceneID
			# =========================================================================
				# Gap mask
				# creates a gap mask for the scene if it came from Landsat 7 after
				# the ordinal date of 2003151 (5/31/2003) when the SLC went offline
				landsatFactTools_GDAL.gaper(date1,date2,outGAPfolder,outBasename)
				print "here after gapmasker"
				print "date1.sceneID:" , date1.sceneID
				print "date2.sceneID:" , date2.sceneID
			# =========================================================================
				# Cloud mask
				print "Cloud mask folder and date1 location: "+date1.folder+"/"+date1.sceneID+"_MTLFmask.TIF"
				print "Cloud mask folder and date2 location: "+date2.folder+"/"+date2.sceneID+"_MTLFmask.TIF"
				if not os.path.exists(date1.folder+"/"+date1.sceneID+"_MTLFmask.TIF"):
                                    rasterAnalysis_GDAL.runFmask(date1.folder.replace('UR','').replace('UL','').replace('LR','').replace('LL',''),fmaskShellCall)
                                    # create quads from the input scene
                                    quadPaths = rasterAnalysis_GDAL.cropToQuad(date1.folder.replace('UR','').replace('UL','').replace('LR','').replace('LL',''),projectStorage,quadsFolder)
                                    landsatFactTools_GDAL.writeQuadToDB(quadPaths)
                                    # get cloud cover percentage for each quad
                                    quadCCDict = landsatFactTools_GDAL.getQuadCCpercent(quadPaths)
                                    # =========================================================================
                                    # write input scene quads cloud cover percentage to the landsat_metadata table in the database
                                    landsatFactTools_GDAL.writeQuadsCCtoDB(quadCCDict,date1.folder.replace('UR','').replace('UL','').replace('LR','').replace('LL',''))
				if not os.path.exists(date2.folder+"/"+date2.sceneID+"_MTLFmask.TIF"):
				    rasterAnalysis_GDAL.runFmask(date2.folder.replace('UR','').replace('UL','').replace('LR','').replace('LL',''),fmaskShellCall)
                                    # create quads from the input scene
                                    quadPaths = rasterAnalysis_GDAL.cropToQuad(date1.folder.replace('UR','').replace('UL','').replace('LR','').replace('LL',''),projectStorage,quadsFolder)
                                    landsatFactTools_GDAL.writeQuadToDB(quadPaths)
                                    # get cloud cover percentage for each quad
                                    quadCCDict = landsatFactTools_GDAL.getQuadCCpercent(quadPaths)
                                    # =========================================================================
                                    # write input scene quads cloud cover percentage to the landsat_metadata table in the database
                                    landsatFactTools_GDAL.writeQuadsCCtoDB(quadCCDict,date1.folder.replace('UR','').replace('UL','').replace('LR','').replace('LL',''))
                                if os.path.exists(date1.folder+"/"+date1.sceneID+"_MTLFmask.TIF") and os.path.exists(date2.folder+"/"+date2.sceneID+"_MTLFmask.TIF"):
                                    FmaskReclassedArray1 = date1.reclassFmask()
                                    FmaskReclassedArray2 = date2.reclassFmask()
                                    FmaskReclassedArray = FmaskReclassedArray1 * FmaskReclassedArray2
                                    outputTiffName = rasterAnalysis_GDAL.createOutTIFF(date1.geoTiffAtts,FmaskReclassedArray,os.path.join(outFMASKfolder,outBasename),'Fmask')
                                    print "writeProductToDB: "+os.path.basename(outputTiffName)+" ,"+date1.sceneID+" ,"+date2.sceneID+" ,"+'CLOUD'+" ,"+date2.sceneID[9:16]
                                    landsatFactTools_GDAL.writeProductToDB(os.path.basename(outputTiffName),date1.sceneID,date2.sceneID,'CLOUD',date2.sceneID[9:16])
                                else:
                                    print "Apparently the fmask file doesn't exist"
                    # =========================================================================
				# NDVI
				ndvi1 = date1.ndvi("SR")
				ndvi2 = date2.ndvi("SR")
				ndviChange = ndvi2 - ndvi1
				ndviPercentChange = ndviChange / np.absolute(ndvi1)
				ndvi1 = None
				ndvi2 = None
				ndviPercentChange = np.multiply(100,ndviPercentChange)
				wrs2Name = tar[3:9]
				outputTiffName=rasterAnalysis_GDAL.outputChangeProductTIFFs(date1.geoTiffAtts, ndviPercentChange, quadsFolder, outBasename, 'ndvi', outNDVIfolder, wrs2Name)
				print "writeProductToDB: "+os.path.basename(outputTiffName)+" ,"+date1.sceneID+" ,"+date2.sceneID+" ,"+'NDVI'+" ,"+date2.sceneID[9:16]
				landsatFactTools_GDAL.writeProductToDB(os.path.basename(outputTiffName),date1.sceneID,date2.sceneID,'NDVI',date2.sceneID[9:16])
				ndviPercentChange = None
				# NDMI
				ndmi1 = date1.ndmi("SR")
				ndmi2 = date2.ndmi("SR")
				ndmiChange = ndmi2 - ndmi1
				ndmiPercentChange = ndmiChange / np.absolute(ndmi1)
				ndmi1 = None
				ndmi2 = None
				ndmiPercentChange = np.multiply(100,ndmiPercentChange)
				outputTiffName=rasterAnalysis_GDAL.outputChangeProductTIFFs(date1.geoTiffAtts, ndmiPercentChange, quadsFolder, outBasename, 'ndmi', outNDMIfolder, wrs2Name)
				print "writeProductToDB: "+os.path.basename(outputTiffName)+" ,"+date1.sceneID+" ,"+date2.sceneID+" ,"+'NDMI'+" ,"+date2.sceneID[9:16]
				landsatFactTools_GDAL.writeProductToDB(os.path.basename(outputTiffName),date1.sceneID,date2.sceneID,'NDMI',date2.sceneID[9:16])
				ndmiPercentChange = None
				# SWIR
				swir1 = date1.SurfaceReflectance(date1.swir2,"swir2")
				swir2 = date2.SurfaceReflectance(date2.swir2,"swir2")
				swir = np.subtract(swir2,swir1)
				swirPercentChange = swir / np.absolute(swir1)
				swir = None
				swir1 = None
				swir2 = None
				swirPercentChange = np.multiply(100,swirPercentChange)
				outputTiffName=rasterAnalysis_GDAL.outputChangeProductTIFFs(date1.geoTiffAtts, swirPercentChange, quadsFolder, outBasename, 'swir', outSWIRfolder, wrs2Name)
				print "writeProductToDB: "+os.path.basename(outputTiffName)+" ,"+date1.sceneID+" ,"+date2.sceneID+" ,"+'SWIR'+" ,"+date2.sceneID[9:16]
				landsatFactTools_GDAL.writeProductToDB(os.path.basename(outputTiffName),date1.sceneID,date2.sceneID,'SWIR',date2.sceneID[9:16])
				swirPercentChange = None
	else:
		print "There was an issue with FMASK on: "+extractedPath
	# =========================================================================
print '\nLandsatFACT Complete'
sys.exit()
