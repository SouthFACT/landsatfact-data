#-------------------------------------------------------------------------------
# Name:        library
# Purpose:     Reduce code duplication
#
# Author:      olouda
#
# Created:     27/08/2015
# Copyright:   (c) olouda 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import osgeo, ogr, os, osr, subprocess, StringIO, logging
import tarfile, glob, re
import shlex, zipfile

def checkZip(inZip):
    # tests inZip for validity: is it in zip format and does it contain a .dbf, .prj, .shp, and .shx
    inFile=file(inZip)
    if zipfile.is_zipfile(inFile):
        zippedFile = zipfile.ZipFile(inZip)
        ret=zippedFile.testzip()
        if ret is not None:
            return ret
        else:
            contents=zippedFile.namelist()
            if (len(contents) >= 4):
                contentStr=' '.join(contents)
                # i really ought to be able to do this test with one regex search but i'm incapable
                m=re.search('(\w+)(\.shp)', contentStr)
                base=m.group().split('.')[0]
                if (base+'.dbf' in contentStr and base+'.shp' in contentStr and base+'.shx' in contentStr and base+'.prj' in contentStr):
                    return ''

    return 'Invalid zip'

def validTar(inTar):
    """If a valid tar, this function returns an empty string. If it's invalid, it returns the first missing component which is
        an enumeration of the members defined below, such as "gap_mask/.*B1", "_B2", "_B3", "_B4", "_B5", "_B6_VCID_1", "_B6_VCID_2",
        "_B7", "_MTL", "_B9", "_B10", "_B11", "_BQA","Invalid tar" which means it couldn't be opened, or the text of an exception
        raised trying to read the tar"""
    if os.path.basename(inTar).startswith("LE7"):
        members = ["^[^g].*_B1\D", "^[^g].*_B2", "^[^g].*_B3", "^[^g].*_B4", "^[^g].*_B5", "^[^g].*_B6_VCID_1",
                "^[^g].*_B6_VCID_2", "^[^g].*_B7", "_MTL",
                "gap_mask/.*B1", "gap_mask/.*B2", "gap_mask/.*B3", "gap_mask/.*B4", "gap_mask/.*B5", "gap_mask/.*B6",
                "gap_mask/.*B7", "gap_mask/.*B8", "gap_mask/.*B6_VCID_1", "gap_mask/.*B6_VCID_2"]
    elif os.path.basename(inTar).startswith("LT5"):
        members = ["_B1\D", "_B2", "_B3", "_B4", "_B5", "_B6", "_B7", "_MTL"]
    elif os.path.basename(inTar).startswith("LC8"):
        members = ["_B1\D", "_B2", "_B3", "_B4", "_B5", "_B6", "_B7", "_B9", "_B10", "_B11", "_BQA", "_MTL"]


    if tarfile.is_tarfile(inTar):
        tar = tarfile.open(inTar)
        checkList = tar.getnames()
        for subStr in members:
            filtered=filter(lambda tarFileName: re.search(subStr, tarFileName), checkList)
            if not filtered:
                return subStr
        return ''
    else:
        return 'Invalid tar'

def removeTar(inTar):
    os.remove(inTar)

def removeZip(inZip):
    os.remove(inZipip)

def checkSpatialRef(inShp):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(inShp, 0)
    layer = dataSource.GetLayer(0)
    source_srs = layer.GetSpatialRef()
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(4326)
    return (target_srs.IsSame(source_srs))

def countVertices(inShp):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(inShp, 1)
    layer = dataSource.GetLayer()
    source_srs = layer.GetSpatialRef()
    logging.debug( ('Should be only one layer and there is {} layer(s)'.format(dataSource.GetLayerCount())))
    layer = dataSource.GetLayer(0)
    logging.debug(layer.GetName(), ' contains ', layer.GetFeatureCount(), ' features')
    feature = layer.GetFeature(0)
    geom = feature.GetGeometryRef()
    # Get Geometry inside Geometry
    ring = geom.GetGeometryRef(0)
    logging.debug(geom.GetGeometryName(), ' contains the Geometry', ring.GetGeometryName())

    ring = geom.GetGeometryRef(0)
    logging.debug('It contains', ring.GetPointCount(), ' points in a ', ring.GetGeometryName())
    return (ring.GetPointCount())

def reprojectShp(inShp):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(inShp, 0)
    layer = dataSource.GetLayer(0)
    source_srs = layer.GetSpatialRef()

    logging.debug(('Should be only one layer and there is {} layer(s)'.format(dataSource.GetLayerCount())))
    logging.debug(layer.GetName(), ' contains ', layer.GetFeatureCount(), ' features')
    feature = layer.GetFeature(0)
    geom = feature.GetGeometryRef()

    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(4326)
    # create the CoordinateTransformation
    coordTrans = osr.CoordinateTransformation(source_srs, target_srs)
    # create a temporary output file for the new projected file
    outShp = os.path.join( os.path.split(inShp)[0],'PRJ_' + os.path.basename(inShp))
    if os.path.exists(outShp):
        driver.DeleteDataSource(outShp)
    outDataSet = driver.CreateDataSource(outShp)
    outLayer = outDataSet.CreateLayer("poly", geom_type=ogr.wkbMultiPolygon)

    # add fields, i think there should only be one
    inLayerDefn = layer.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)

    # get the output layer's feature definition
    outLayerDefn = outLayer.GetLayerDefn()
    # reproject the input geometry
    geom.Transform(coordTrans)
    # create a new feature
    outFeature = ogr.Feature(outLayerDefn)
    # set the geometry and attribute
    outFeature.SetGeometry(geom)
    for i in range(0, outLayerDefn.GetFieldCount()):
        outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), feature.GetField(i))
    # add the feature to the shapefile
    outLayer.CreateFeature(outFeature)
    # create an ESRI.prj file, https://pcjericks.github.io/py-gdalogr-cookbook/projection.html
    target_srs.MorphToESRI()
    prj=os.path.join(os.path.split(outShp )[0],os.path.splitext(os.path.basename(outShp))[0] + '.prj')
    file = open(prj, 'w')
    file.write(target_srs.ExportToWkt())
    file.close()

    # Close DataSources and clean up so that inShp can be overwritten
    outFeature.Destroy
    outDataSet.Destroy()
#    feature.Destroy()
    dataSource=source_srs=target_srs=layer=feature=geom=coordTrans=outDataSet=inLayerDefn=None
    outLayer=fieldDefn=outFeature=outLayerDefn=file=None

    # then move the temporary (PRJ_*) shapefile to inShp
    driver.DeleteDataSource(inShp)
    dataSource = driver.Open(outShp)
    outDS=driver.CopyDataSource(dataSource, inShp)
    dataSource=outDS=None
    driver.DeleteDataSource(outShp)

def geoJSONToShp(inJSON):
    # assumes WGS 84
    # read poly from json
    poly= ogr.CreateGeometryFromJson(inJSON)
    # create a new shapefile to insert the new geometry into
    # https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html#create-a-new-shapefile-and-add-data
    driver = ogr.GetDriverByName('ESRI Shapefile')
    tmp_dir = '/var/vsites/landsatfact-dev.nemac.org/project/html/sites/all/modules/lsf_subscription/cgi-bin/shp_tmp/'
#    tmp_dir=r'H:\SPA_Secure\Geospatial\LandsatFACT\code\reduce\shapes'
    outShp=os.path.join(tmp_dir, 'tmp.shp')

    if os.path.exists(outShp):
        driver.DeleteDataSource(outShp)

    # Create the output shapefile
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(4326)
    dataSource = driver.CreateDataSource(outShp)
    outLayer = dataSource.CreateLayer("tmp", target_srs, geom_type=ogr.wkbMultiPolygon)

    # Add an ID field
    idField = ogr.FieldDefn("id", ogr.OFTInteger)
    outLayer.CreateField(idField)

    # Create the feature and set values
    featureDefn = outLayer.GetLayerDefn()
    feature = ogr.Feature(featureDefn)
    feature.SetGeometry(poly)
    feature.SetField("id", 0)
    outLayer.CreateFeature(feature)

    # create an ESRI.prj file, https://pcjericks.github.io/py-gdalogr-cookbook/projection.html
    target_srs.MorphToESRI()
    prj=os.path.join(os.path.split(outShp)[0],os.path.splitext(os.path.basename(outShp))[0] + '.prj')
    file = open(prj, 'w')
    file.write(target_srs.ExportToWkt())
    # Close and clean up neeeded to make sure shp is written
    file.close()
    dataSource.Destroy()
    # be careful with the order of clean (e.g., can't destroy feature until poly is dereferenced)
    geom=poly=driver=dataSource=target_srs=outLayer=file=feature=featureDefn=None
    return (countVertices(outShp))

def shpToGeoJSON(inShp):
    inDriver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = inDriver.Open(inShp, 0)
    layer = dataSource.GetLayer()
    logging.debug ('Should be only one layer and there is {} layer(s)'.format(dataSource.GetLayerCount()))
    layer = dataSource.GetLayer(0)
    logging.debug(layer.GetName(), ' contains ', layer.GetFeatureCount(), ' features')
    feature = layer.GetFeature(0)
    geom = feature.GetGeometryRef()
    geoJSON=geom.ExportToJson()
#    import pdb
#    pdb.set_trace()
    return geoJSON

def shpToPostGIS(inShp):
    # assumes ogr2ogr utility is on the path
    # output SpatialReference
    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(4326)
    # check to see if the input shapefile is WGS 84
    if not checkSpatialRef(inShp):
        # if not reproject it
        reprojectShp(inShp)
    # invoke shp2pgsql
    shp2sqlArgs = shlex.split('ogr2ogr --config PG_USE_COPY YES -f PGDump  /dev/stdout '+ inShp)
    process = subprocess.Popen(shp2sqlArgs,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = process.communicate()
    errcode = process.returncode
#    print out, err
    if not errcode:
        # edit the output string to remove superflous information
        # return only the insert value for the geom field
        # search for 'FROM stdin' in output. Return up from next tab up to end of next line
        buf=StringIO.StringIO(out)
        geomString = ''
        begunInsert=finishedInsert=False;
        for line in buf.readlines():
            if begunInsert and not finishedInsert:
                # return from tab to the end of line
                geomString = line.split()[0]
                finishedInsert=True
            if 'COPY \"public' in line:
                # parse the next line
                begunInsert=True

        geoJSON = shpToGeoJSON(inShp)
        results = [geomString, geoJSON]
    else:
        results=err
    return results


