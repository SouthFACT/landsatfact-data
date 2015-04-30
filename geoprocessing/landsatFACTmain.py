#! /usr/bin/python
#-------------------------------------------------------------------------------
# Name:        landsatFACTmain.py
# Purpose:
#
# Author:      Brian McLean
#
# Last Updated:     02/25/2015
#
# Licence:
#-------------------------------------------------------------------------------

def main():
    pass

if __name__ == '__main__':
    main()

import os, sys
import landsatFactTools_GDAL
import rasterAnalysis_GDAL
import numpy as np
import psycopg2


reload(landsatFactTools_GDAL)
reload(rasterAnalysis_GDAL)

# =========================================================================
# runList=['LC80160362014297LGN00.tar.gz']#BM's original
# runList=['LC80140352014139LGN00.tar.gz'] #jdm pass1
runList=['LC80140352014299LGN00.tar.gz']#jdm pass2 given that pass1 alread filled in the cc values
for tar in runList:
	# set tar file to analyze
	if not tar[-7:] == '.tar.gz':
		print "incorrect file type"
		sys.exit()
	# set Fmask.exe location
	# Fmaskexe = r'S:\Geospatial\LandsatFACT\Fmask.exe' #BM's original
	fmaskShellCall = r'/var/vsites/landsatfact-data-dev.nemac.org/project/geoprocessing/fmaskLinux/runFmask.sh'
	# set folder location of the quad vector files
	# quadsFolder = r'S:\Geospatial\LandsatFACT\geodata\vector\quads_indv_proj' #BM's original
	quadsFolder = r'quads_indv_proj'
	# set folder locations
	# folder where the tar.gz's are stored
	# tarStorage = r'S:\Geospatial\LandsatFACT\data\tarFiles' #BM's original
	tarStorage = r'/fsdata1/lsfdata/tarFiles'
	# folder where you want the extracted tiff's to be stored, they will automatically be
	# put inside of a subfolder labeled with the scene name
	# tiffsStorage = r'S:\Geospatial\LandsatFACT\data\extractedTars' #BM's original
	tiffsStorage = r'/fsdata1/lsfdata/tarFiles/extractedTars'
	# root folder for the output storage
	# if this path does not exist the script will create it
	# productStorage = r'S:\Geospatial\LandsatFACT\data\20150414' #BM's original
	productStorage = r'/fsdata1/lsfdata/lsfproducts'
	# set output folder locations per product
	# if this path does not exist the script will create it
	outNDVIfolder = os.path.join(productStorage,'ndvi_SR')
	outNDMIfolder = os.path.join(productStorage,'ndmi')
	outb7folder = os.path.join(productStorage,'b7Diff_SR')
	outGAPfolder = os.path.join(productStorage,'gapMask')
	# set cloud cover threshold level, quad scene's with a higher percentage of
	# cloud cover will not be processed.
	cloudCoverThreshold = .50
	# =========================================================================
	# sets full path for the tarfile to be analyzed
	inNewSceneTar = os.path.join(tarStorage, tar)
	# check to see if the tar file has been extracted, if not extract the files
	extractedPath = landsatFactTools_GDAL.checkExisting(inNewSceneTar, tiffsStorage)
	# run Fmask
	# jdm 4/22/15: after spending a couple of days trying to get FMASK installed on cloud4
	# I have not been able to get it to work.  Therefore, for now I am commenting this out
	# rasterAnalysis_GDAL.runFmask(extractedPath,Fmaskexe) #BM's original
	print extractedPath
	rasterAnalysis_GDAL.runFmask(extractedPath,fmaskShellCall)
	# get DN min number from each band in the scene and write to database
	dnminExists = landsatFactTools_GDAL.checkForDNminExist(extractedPath) # May not be needed in final design, used during testing
	if dnminExists == False:
		dnMinDict = rasterAnalysis_GDAL.getDNmin(extractedPath)
		landsatFactTools_GDAL.writeDNminToDB(dnMinDict,extractedPath)
	# create quads from the input scene
	quadPaths = rasterAnalysis_GDAL.cropToQuad(extractedPath,quadsFolder)
	landsatFactTools_GDAL.writeQuadToDB(quadPaths)
	# get cloud cover percentage for each quad
	quadCCDict = landsatFactTools_GDAL.getQuadCCpercent(quadPaths)
	# =========================================================================
	# write input scene quads cloud cover percentage to the landsat_metadata table in the database
	landsatFactTools_GDAL.writeQuadsCCtoDB(quadCCDict,extractedPath)
	# for each quad this finds the closest scene that passes the cloud cover threshold for processing
	quadTiffList2Process = landsatFactTools_GDAL.getNextBestQuad(quadCCDict,cloudCoverThreshold)
	# =========================================================================
	#print "quadTiffList2Process: ", quadTiffList2Process
	# checks the list of quads, if 0 then there were no quads under the cloud cover threshold
	# so there is nothing to process for that scene
	if len(quadTiffList2Process) > 0:
		#print "quadTiffList2Process: ", quadTiffList2Process
		# for each quad pair perform the change analysis
		for compareList in quadTiffList2Process:
			pathList = [os.path.join(tiffsStorage,compareList[0]), os.path.join(tiffsStorage,compareList[1])]
		# =========================================================================
			# sets the scenes in order
			tifPathList = pathList
			#print "tifPathList: ", tifPathList
			if int(os.path.basename(tifPathList[0])[9:13]) > int(os.path.basename(tifPathList[1])[9:13]):
				date1=rasterAnalysis_GDAL.sensorBand(tifPathList[1])
				date2=rasterAnalysis_GDAL.sensorBand(tifPathList[0])
			elif int(os.path.basename(tifPathList[0])[9:13]) < int(os.path.basename(tifPathList[1])[9:13]):
				date1=rasterAnalysis_GDAL.sensorBand(tifPathList[0])
				date2=rasterAnalysis_GDAL.sensorBand(tifPathList[1])
			else:
				if int(os.path.basename(tifPathList[0])[13:16]) > int(os.path.basename(tifPathList[1])[13:16]):
					date1=rasterAnalysis_GDAL.sensorBand(tifPathList[1])
					date2=rasterAnalysis_GDAL.sensorBand(tifPathList[0])
				else:
					date1=rasterAnalysis_GDAL.sensorBand(tifPathList[0])
					date2=rasterAnalysis_GDAL.sensorBand(tifPathList[1])
		# =========================================================================
			# create product name
			outBasename = date1.sceneID + "_" + date2.sceneID
		# =========================================================================
			# creates a gap mask for the scene if it came from Landsat 7 after
			# the ordinal date of 2003151 (5/31/2003) when the SLC went offline
			landsatFactTools_GDAL.gaper(date1,date2,outGAPfolder,outBasename)
			print "here after gapmasker"
			print "date1.sceneID:" , date1.sceneID
			print "date2.sceneID:" , date2.sceneID
		# =========================================================================
			ndvi1 = date1.ndvi("SR")
			ndvi2 = date2.ndvi("SR")
			ndviChange = ndvi2 - ndvi1
			ndviPercentChange = ndviChange / np.absolute(ndvi1)
			ndvi1 = None
			ndvi2 = None
			ndviPercentChange = np.multiply(100,ndviPercentChange)
			rasterAnalysis_GDAL.createOutTiff(date1.geoTiffAtts,ndviPercentChange,os.path.join(outNDVIfolder,outBasename+'_percent'),'ndvi16')
			ndviPercentChange = None
			ndmi1 = date1.ndmi("SR")
			ndmi2 = date2.ndmi("SR")
			ndmiChange = ndmi2 - ndmi1
			ndmiPercentChange = ndmiChange / np.absolute(ndmi1)
			ndmi1 = None
			ndmi2 = None
			ndmiPercentChange = np.multiply(100,ndmiPercentChange)
			rasterAnalysis_GDAL.createOutTiff(date1.geoTiffAtts,ndmiPercentChange,os.path.join(outNDMIfolder,outBasename+'_percent'),'ndmi16')
			ndmiPercentChange = None
			swir1 = date1.SurfaceReflectance(date1.swir2,"swir2")
			swir2 = date2.SurfaceReflectance(date2.swir2,"swir2")
			b7Differencing = np.subtract(swir2,swir1)
			b7DifferencingPercentChange = b7Differencing / np.absolute(swir1)
			b7Differencing = None
			swir1 = None
			swir2 = None
			b7DifferencingPercentChange = np.multiply(100,b7DifferencingPercentChange)
			rasterAnalysis_GDAL.createOutTiff(date1.geoTiffAtts,b7DifferencingPercentChange,os.path.join(outb7folder,outBasename+'_percent'),'b7diff')
			b7DifferencingPercentChange = None
	# =========================================================================
print '\nLandsatFACT Complete'
sys.exit()
