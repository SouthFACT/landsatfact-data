#! /usr/bin/python
#-------------------------------------------------------------------------------
# Name:         LSF_zonalstats.py.py
# Purpose:      LandsatFACT application script that derives statitics on changes witin an Area of Interest
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


import sys, os, fnmatch, glob
from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import numpy as np
import subprocess
import argparse, csv
import pdb


# Utility function to provide the command line arguments to the script
#  SWIR product, gap, or cloud mask
# @param
#     None
# @return None
# Example call: [aoi, swirTIFFsFile, reclassTable, cloudMasksFile, gapMasksFile, statsResultTable] = parse_cmd_line()
def parse_cmd_line():
    """
    Will parse the arguments provided on the command line.
    aoi, swirTIFFs, reclassTable, and statsResultTable are mandatory.
    cloudMasks and gapMasks are optional. default is None.
    if cloudMasks and gapMasks are not None, the lists must have a prefix in common
    with the swir e.g., LE70200342017069EDC00LL_LC80200342017077LGN02LL.
    """

    parser = argparse.ArgumentParser(description='Tabulate statistics on swir values within the area of interest.')
    parser.add_argument('aoi', help='Area of interest vector file')
    parser.add_argument('swirTIFFFile', help='File containing list of swir product TIFFs')
    parser.add_argument('reclassTable', help='CSV file to reclass swirs')
    parser.add_argument('statsResultTable', help='CSV file path to contain the results')
    parser.add_argument('-c', dest='cloudMasksFile', default=None, help='File containing list of cloud_mask products or None')
    parser.add_argument('-g', dest='gapMasksFile', default=None, help='File containing list of gap_maks products or None')
    ns = parser.parse_args()

    return [ns.aoi, ns.swirTIFFFile, ns.reclassTable, ns.cloudMasksFile, ns.gapMasksFile, ns.statsResultTable]

# Utility function to retrieve the portion of a string which identifies the wrs2_code/quad_ids used to construct a
#  SWIR product, gap, or cloud mask
# @param
#     [fname] - full path to the raster mask or product
# @return key string
# Example call: keyFromFilename('G:\\LE70190352017062EDC01UL_LE70190352017078EDC00UL_GapMask.tif')
def keyFromFilename(fname):
    valueIncKey=os.path.basename(fname)[:47]
    return valueIncKey

# Utility function used to create/write-out a raster with attributes set using GDALDataset Class and numpy array
# @param
#     [array] - numpy array object to be used to create raster values
#     [outpath] - full path to the raster to be created
#     [transform] - set the affine transformation coefficients
#     [projection] - set the coordinate system
# @return none
# Example call: writeArrayAsTIFF(npArray, 'temp.tif', srcRaster.RasterXSize, srcRaster.RasterYSize, gdal.GDT_Byte, srcRaster.GetGeoTransform(), srcRaster.GetProjection()))

def writeArrayAsTIFF(array, outpath, rasterXSize, rasterYSize, gdalType, transform, projection):
    """
    For testing, to visually assess the masked TIFFs, and to generate disk files as necessary.
    """
    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(outpath, rasterXSize, rasterYSize, 1, gdalType)
    outBand = dataset.GetRasterBand(1)
    outBand.WriteArray(array)
    dataset.SetGeoTransform(transform)
    dataset.SetProjection(projection)
    outBand.FlushCache()

# Utility function to add a key/value pair to a dictionary where the key is part of the value
# @param
#     [dictionary] - an existing dictionary
#     [valueIncKey] - a string value including a substring that'll be used as a key to access the string value
# @return none
# Example call: addToDictionary(gapMasksDict, 'G:\\LE70190352017062EDC01UL_LE70190352017078EDC00UL_Fmask.tif')
def addToDictionary(dictionary, valueIncKey):
    """
    Add a key/value pair (e.g.,
    'LE70190352017062EDC01UL_LE70190352017078EDC00UL': 'G:\\LE70190352017062EDC01UL_LE70190352017078EDC00UL_Fmask.tif')
     to the dictionary using a porton of the valueIncKey parameter as a key.
    """
    dictionary[keyFromFilename(valueIncKey)]=valueIncKey

# Utility function to mask a numpy array with a raster where values less than 2 indicate values to be ignored
# @param
#     [array] - a numpy array
#     [maskFile] - full path to the raster mask
# @return masked numpy array or the source array if raster mask is None
# Example call: maskArray(npArray, 'G:\\LE70190352017062EDC01UL_LE70190352017078EDC00UL_Fmask.tif')
def maskArray(array, maskFile):
    """
    Apply the values in raster named maskFile to mask array.
    """
    if maskFile:
        try:
            maskRaster = gdal.Open(maskFile)
            band = maskRaster.GetRasterBand(1)
            maskArray = band.ReadAsArray()
            masked = np.where(maskArray<2, 0, array)
            return masked
        except BaseException as e:
            print ' Problem with mask ' + maskFile
            print str(e)
            return array
    else:
        return array

# Utility function to apply cloud and gap masks to a raster, when supplied
# @param
#     [array] - a numpy array
#     [cloudMaskFile] - full path to the raster mask or None
#     [gapMaskFile] - full path to the raster mask or None
# @return masked numpy array or the source array if both raster masks are None
# Example call: applyMasks(srcBandArray, 'G:\\LE70190352017062EDC01UL_LE70190352017078EDC00UL_Fmask.tif', 'G:\\LE70190352017062EDC01UL_LE70190352017078EDC00UL_GapMask.tif')
def applyMasks(srcArray, cloudMaskFile, gapMaskFile):
    """
    Apply a cloud mask then a gap mask, if they have been supplied.
    """
    return maskArray(maskArray(srcArray, cloudMaskFile), gapMaskFile)

# Utility function to threshold the product raster based on a CSV file
# @param
#     [srcArray] - a numpy array
#     [reclassTable] - full path to the raster mask or None
# @return None
# Example call: reclass(srcBandArray, 'C:\Users\olouda\remap.csv')
def reclass(srcArray, reclassTable):
    """
    reclassTable is a CSV file which can contain the simplest reclassification table syntax (e.g., Explicit input ranges
     from (http://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-analyst-toolbox/using-reclassification-tables.htm).
     The code assusmes the CSV file has headers.
    """
    lowerLimitList = []
    upperLimitList = []
    toValueList = []

    with open(reclassTable, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            #from lower, from upper, to
            fromLower = int(row['from lower'])
            fromUpper = int(row['from upper'])
            toValue = int(row['to'])
            lowerLimitList.append(fromLower)
            upperLimitList.append(fromUpper)
            toValueList.append(toValue)
    # reclassification
    sortedLower= sorted(lowerLimitList)
    sortedUpper = sorted(upperLimitList, reverse=True)
    lowest=sortedLower[0]
    highest=sortedUpper[0]
    #if (lowest >= srcArray.min()):
    srcArray[(srcArray <= lowest)] = 0
    #if (highest <= srcArray.max()):
    srcArray[(srcArray >= highest)] = 0
    srcArray[(srcArray > fromLower) & (srcArray <= fromUpper)] = toValue
    for fromLower, fromUpper, toValue in zip (lowerLimitList, upperLimitList, toValueList):
        srcArray[(srcArray > fromLower) & (srcArray <= fromUpper)] = toValue
    return srcArray

# Utility function to mosaic a list of rasters
# @param
#     [inRasterList] - a list of rasters
#     [outRasterPath] - full path to the output raster
# @return None
# Example call: mosaic(reclassedTIFFs, 'mosaic.tif')
def mosaic(inRasterList, outRasterPath):

    # gdal_merge.py -o out.tif bar.tif temp.tif
    codeIn = ['gdal_merge.py','-o', outRasterPath] + reclassedTIFFs
    process = subprocess.Popen(codeIn,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = process.communicate()
    errcode = process.returncode
    if errcode:
        try:
            os.remove(outRasterPath)
        except OSError:
            pass

# Utility function to project and convert a WGS84 geoJSON to a NA Albers Equal Area Conic shapefile
# @param
#     [geojsonFile] -  path to a file containing the geoJSON geoemtry from postgis
#     [outShapePath] - full path to the output shapefile
# @return None
# Example call: translateAOI('testAEC.json', 'aoi.shp')
def translateAOI(geojsonFile, outShapePath):
    """
    Reproject AOI and convert to shapefile
    """

    # ogr2ogr -f "ESRI Shapefile" -t_srs EPSG:102008 aoiProj.shp test.json
    codeIn = ['ogr2ogr', '-f','ESRI Shapefile','-t_srs','EPSG:102008', outShapePath, geojsonFile]
    process = subprocess.Popen(codeIn,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = process.communicate()
    errcode = process.returncode
    if errcode:
        raise RuntimeError('Error return code {0} in translateAOI.\n{1}\n{2}'.format(errcode, out, err))

# Utility function to group connected pixels into regions/patches/zones
# @param
#     [inRasterPath] -  full path to the raster reclassed into different threshold values
#     [aoiVectorPath] - full path to the AOI shapefile
#     [aoiRegionsPath] - full path to the output regions shapefile clipped to the AOI
# @return None
# Example call: regionGroup('mosaic.tif', 'aoi.shp', 'aoiRegionGrouped.shp')
def regionGroup(inRasterPath, aoiVectorPath, aoiRegionsPath):
    """
    Polygonize raster into threholded regions, clip polygons to AOI.
    """
    # gdal_polygonize.py -nomask temp.tif -b 1 bar.gml
    codeIn = ['gdal_polygonize.py','-nomask', '-f', 'ESRI Shapefile', inRasterPath, '-b', '1', 'rg.shp']
    process = subprocess.Popen(codeIn,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = process.communicate()
    errcode = process.returncode
    if errcode:
        try:
            map(lambda x: os.remove(x), glob.glob('rg.*'))
        except OSError:
            pass
        raise RuntimeError('Error return code {0} in regionGroup gdal_polygonize.\n{1}\n{2}'.format(errcode, out, err))

    else:
        # ogr2ogr -clipsrc aoiProj.shp rgClip.shp rg.shp
        codeIn = ['ogr2ogr', '-clipsrc', aoiVectorPath, aoiRegionsPath, 'rg.shp']
        process = subprocess.Popen(codeIn,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = process.communicate()
        errcode = process.returncode
        map(lambda x: os.remove(x), glob.glob('rg.*'))
        if errcode:
            raise RuntimeError('Error return code {0} in regionGroup ogr2ogr.\n{1}\n{2}'.format(errcode, out, err))


# Utility function to collect statistics on a shapefile
# @param
#     [shape] - full path to the area to be summarized
#     [statsResultTable] - full path to RCSV results
# @return None
# Example call: regionGroup('mosaic.tif', 'aoi.shp', 'aoiRegionGrouped.shp')
def zonalStats(shape, statsResultTable):

    l = []
    sqlString = "SELECT FID, OGR_GEOM_AREA, DN FROM {0} WHERE DN > 0 ORDER BY OGR_GEOM_AREA DESC".format(os.path.splitext(os.path.basename(shape))[0])
    ds = ogr.Open(shape)
    layer = ds.ExecuteSQL(sqlString)

    for feature in layer:
        l.append((feature.GetField("FID"), feature.GetField("OGR_GEOM_AREA"), feature.GetField("DN")))

    f = open(statsResultTable,'wt')
    try:
        writer = csv.writer(f)
        writer.writerow( ('Unique region ID', 'Area in square meters', 'Raster value') )
        for tup in l:
            writer.writerow(tup)
    finally:
        f.close()



"""
usage: LSF_zonalstats.py [-h] [-c CLOUDMASKSFILE] [-g GAPMASKSFILE]
                         aoi swirTIFFFile reclassTable statsResultTable
example:
./LSF_zonalstats.py test.json swirs.txt remap.csv stats.csv -c cloudMasks.txt -g gapMasks.txt

Overall steps:
1. apply masks, if specified, to swir TIFFs
2. reclass (masked) values
3. mosaic all reclassed for an AOI
4. group connected pixels into regions/patches/zones
5. collect raster stats on regions/patches/zones
"""
cloudMasksDict={}
gapMasksDict={}
reclassedTIFFs = []

try:

    [aoi, swirTIFFsFile, reclassTable, cloudMasksFile, gapMasksFile, statsResultTable] = parse_cmd_line()

    # swirTIFFsFile is a required parameter so by the time we're here, there is a filename
    # if swirTIFFsFile, is empty, not readable, or in the wrong format an exception will be raised 
    with open(swirTIFFsFile) as f:
        swirTIFFs = f.readlines()
    # remove whitespace characters like `\n` at the end of each line
    swirTIFFs = [x.strip() for x in swirTIFFs]
    if cloudMasksFile:
        with open(cloudMasksFile) as f:
            cloudMasks = f.readlines()
        cloudMasks = [x.strip() for x in cloudMasks]
        map(lambda x: addToDictionary(cloudMasksDict, x), cloudMasks)
    if gapMasksFile:
        with open(gapMasksFile) as f:
            gapMasks = f.readlines()
        gapMasks = [x.strip() for x in gapMasks]
        map(lambda x: addToDictionary(gapMasksDict, x), gapMasks)

    #pdb.set_trace()
    for tiffFilename in swirTIFFs:
        srcRaster = gdal.Open(tiffFilename)
        band = srcRaster.GetRasterBand(1)
        srcBandArray = band.ReadAsArray()
        k=keyFromFilename(tiffFilename)
        maskedArray = applyMasks(srcBandArray, cloudMasksDict.get(k), gapMasksDict.get(k))
        reclassedArray = reclass(maskedArray, reclassTable)
        writeArrayAsTIFF(reclassedArray, k+'temp.tif', srcRaster.RasterXSize, srcRaster.RasterYSize,
                          gdal.GDT_Byte, srcRaster.GetGeoTransform(), srcRaster.GetProjection())
        reclassedTIFFs.append(k+'temp.tif')

    translateAOI(aoi, 'aoi.shp')
    mosaic(reclassedTIFFs, 'mosaic.tif')
    regionGroup('mosaic.tif', 'aoi.shp', 'aoiRegionGrouped.shp')
    stats=zonalStats('aoiRegionGrouped.shp', statsResultTable)
    # clean up temporary files
    os.remove('mosaic.tif')
    map(lambda x: os.remove(x), reclassedTIFFs)
    map(lambda x: os.remove(x), glob.glob('aoi.*'))
    map(lambda x: os.remove(x), glob.glob('aoiRegionGrouped.*'))
except BaseException as(e):
    print e
    sys.exit()

print open(statsResultTable, 'rt').read()

