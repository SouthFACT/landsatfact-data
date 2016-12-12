# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 14:13:00 2015

@author: olouda
"""

import os, subprocess
import gdal, gdalconst
import numpy as np


"""
# Class to encapsulate LandsatFACT (LSF) Georeferenced Tagged Image File Format (GeoTIFF) file operations
# @fromFile
#           Full path of a TIFF file
#           Currently only works for 1 band images, but just in case that needs to change
# @fromArray
#           numpy array
#           Number of raster bands, defaults to 1
"""

class ReadableLSFGeoTIFF(object):

    """
    # Instance creation comes in two varieties, create instance from a file or from a numpy array

    # Instance creation class method.
    # @param cls, filename, rasterBands
    #           Full path of a TIFF file
    #           Number of raster bands, defaults to 1
    """
    @classmethod
    def fromFile(cls, filename, rasterBands=1):
        return cls(None, None, filename, rasterBands)

    """
    # Instance creation class method
    # @param cls, array, rasterBands
    #           numpy array
    #           geoAttrList is a list of spatial attributes, [x_size, y_size, geoTransform, proj]
    #           Number of raster bands, defaults to 1
    """
    @classmethod
    def fromArray(cls, inArray, geoAttrList, rasterBands=1):
        return cls(inArray, geoAttrList, None, rasterBands)

    """
    # Initializer method
    # @param self, array, geoAttrList, filename, rasterBands
    #           numpy array
    #           geoAttrList is a list of spatial attributes, [x_size, y_size, geoTransform, proj]
    #           Full path of a TAR file
    #           Number of raster bands, defaults to 1
    """
    def __init__(self, inArray, geoAttrList, filename, rasterBands=1):
        if inArray is not None:
            self.inArray = inArray
        if geoAttrList is not None:
            self.geoAttrList = geoAttrList
        if filename is not None:
            self.filename=filename
        self.rasterBands=rasterBands

    """
    # Method to retrieve the pixel values and the information to georeference them
    # @param self
    #
    # @return list with 2 elements
    #           list[0] is the numpy array. list[1] is a list of spatial attributes, [x_size, y_size, geoTransform, proj]
    #           geoTransform is a list of six elements, [top left x, w-e pixel resolution, w-e pixel resolution, top left y, rotation, 0 if image is "north up", n-s pixel resolution]
    """
    def georeferencedArrayFromFile(self):

        # open my filename
        ds = gdal.Open(self.filename, gdal.GA_ReadOnly)
        # read my band1 into a numpy array
        dsBand = ds.GetRasterBand(1)
        self.inArray = dsBand.ReadAsArray()
        # collect spatial information from the band
        x_size = ds.RasterXSize
        y_size = ds.RasterYSize
        geoTransform = ds.GetGeoTransform()
        proj = ds.GetProjection()
        self.geoAttrList = [x_size, y_size, geoTransform, proj]
        ds = None
        return [self.inArray, self.geoAttrList]

    """
    # Method to populate my input numpy array and the information to georeference it
    # @param self
    #
    """
    def getInArray(self):
        # if my inArray is not set yet, assume it needs to be read from my filename
       try:
            self.inArray
       except:
            self.inArray=self.georeferencedArrayFromFile()[0]


    """
    # Method to retrieve the pixel values and the information to georeference them
    # @param self
    #
    # @return list with 2 elements
    #           list[0] is the numpy array. list[1] is a list of spatial attributes, [minVal, maxVal, x_size, y_size, geoTransform, proj]
    #           geoTransform is a list of six elements, [top left x, w-e pixel resolution, w-e pixel resolution, top left y, rotation, 0 if image is "north up", n-s pixel resolution]
    """
    def asGeoreferencedArray(self):

        # get my numpy array
        self.getInArray()
        return [self.inArray, self.geoAttrList]


"""
# Abstract Superclass to encapsulate LandsatFACT (LSF) Georeferenced Tagged Image File Format (GeoTIFF) output operations
# Subclasses Unsigned8BitLSFGeoTIFF, Signed8BitLSFGeoTIFF, Signed16BitLSFGeoTIFF, and Signed32BitFloatLSFGeoTIFF do the actual work
#

"""
class ReadWriteLSFGeoTIFF(ReadableLSFGeoTIFF):

    """
    # Initializer method
    # @param self, array, filename, rasterBands
    #           numpy array
    #           Full path of a TAR file
    #           Number of raster bands, defaults to 1
    """
    def __init__(self, inArray, geoAttrList, filename, rasterBands=1):
        super(ReadWriteLSFGeoTIFF, self).__init__(inArray, geoAttrList, filename, rasterBands)
        # Instance variables used in the subclasses' write method and in the private writeOutTIFFDataset method
        outputPath=outArray=gdalDataType=None

    """
    # Method to crop the extent of the LSFGeoTIFF to the extent of the shape
    # @param self, shape, outputPath, dstnodataValue
    #           Full path of a OGR supported datasource
    #           Full path for the LSFGeoTIFF to be written
    #           Nodata values for the output band. A value of None will default to the intrinsic nodata settings on the source dataset.
    """
    def crop(self, shape, outputPath, dstnodataValue=None):
        print("crop file {} args, outputPath {}, shape {} dstnodataValue {} ".format(self.filename, outputPath, shape, dstnodataValue))

        # dstnodataValue is ignored right now because the default behavior of gdalwarp is to set NoData to the value in the self.filename
        # the files from EROS use 0 as NoData which is what we want to use for MapServer. Could use gdal SetNoDataValue and RasterizeLayer if necessary?
        codeIn = ['gdalwarp', '-t_srs', 'EPSG:102008', self.filename, outputPath,'-cutline', shape,'-crop_to_cutline','-tr','30','30','-tap','-overwrite', '-co', 'COMPRESS=LZW']
        process = subprocess.Popen(codeIn,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = process.communicate()
        errcode = process.returncode
        print out, err
        # non-zero is error
        return errcode

    """
    # Default method to to output the LSFGeoTIFF. Overridden in subclasses where bit depth is constrained
    # @param self, outputPath
    #           Full path for the LSFGeoTIFF to be written
    """
    def write(self, outputPath, shapePath=None):

        self.outputPath=outputPath
        # read my filename into a numpy array
        result=self.asGeoreferencedArray()
        # by default don't compress the range. all reasonable values should fit.
        self.outArray=np.rint(self.inArray)
        # Write the TIFF out as signed 16 bit
        self.writeOutTIFFDataset()
        if shapePath is not None:
            self.setNoData(outputPath, shapePath)
        self.calculateStatisticsForArcGIS(outputPath)


    """
    # Private method to write the GeoTIFF. Used by the public write method.
    # @param self
    #
    """
    def writeOutTIFFDataset(self):
        if not (self.outArray==None or self.outputPath==None or self.geoAttrList==None):
            if os.path.exists(self.outputPath):
                os.remove(self.outputPath)
            if not os.path.exists(os.path.dirname(self.outputPath)):
                os.makedirs(os.path.dirname(self.outputPath))
            driver = gdal.GetDriverByName("GTiff")
            dataset = driver.Create(self.outputPath, self.geoAttrList[0], self.geoAttrList[1], 1, self.gdalDataType)
            transform=self.geoAttrList[2]
            projection=self.geoAttrList[3]
            outBand = dataset.GetRasterBand(1)
            outBand.WriteArray(self.outArray)
            outBand.FlushCache()
            dataset.SetGeoTransform(transform)
            dataset.SetProjection(projection)
        else:
            print("Can't output file {} ".format(self.filename))

    def calculateStatisticsForArcGIS(self, path):
        """gdal_translate -of HFA -co AUX=YES -co STATISTICS=YES xxx.tif xxx.aux"""
        print("calculateStatisticsForArcGIS args path {}".format(path))
        codeIn = ['gdal_translate','-of',  'HFA', '-co', 'STATISTICS=YES', path, path + '.aux']
        process = subprocess.Popen(codeIn,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = process.communicate()
        errcode = process.returncode
        print out, err
        # will genereate exception if the file doesn't exist
        os.remove(path+'.aux')
        # non-zero is error
        return errcode


    """
    # Private method used to set "collar" cells to NoData. Used by the public write method.
    # @param self, inRasterPath, shapePath, dstnodataValue
    #           Full path for the LSFGeoTIFF to be modified
    #           Full path for shape whose outline is used to set NoData values. if no shapePath is provided,
    #               the TIFF will be created without a "collar"
    #           The NoData value defaulats to 0
    """
    def setNoData(self, inRasterPath, shp, dstnodataValue=0):
    # use gdal_rasterize to burn in the nodata value outside of the shape provided

        print("setNoData args inRasterPath {}, shp {}, dstnodataValue {}".format(inRasterPath, shp, str(dstnodataValue)))
        codeIn = ['gdal_rasterize','-burn', str(dstnodataValue),'-i', '-l', os.path.splitext(os.path.basename(shp))[0], shp, inRasterPath]
        process = subprocess.Popen(codeIn,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = process.communicate()
        errcode = process.returncode
        print out, err
        # non-zero is error
        return errcode
"""
# Subclass to encapsulate LandsatFACT (LSF) Georeferenced Tagged Image File Format (GeoTIFF) output to a unsigned 8 bit file
#

"""
class Unsigned8BitLSFGeoTIFF(ReadWriteLSFGeoTIFF):

    """
    # Initializer method
    # @param self, array, filename, rasterBands
    #           numpy array
    #           Full path of a TAR file
    #           Number of raster bands, defaults to 1
    """
    def __init__(self, inArray, geoAttrList, filename, rasterBands=1):
        super(Unsigned8BitLSFGeoTIFF, self).__init__(inArray, geoAttrList, filename, rasterBands)
        # Instance variable used in write method
        self.gdalDataType=gdal.GDT_Byte

    """
    # Method to output the LSFGeoTIFF as an unsigned 8 bit GeoTIFF
    # @param self, outputPath, shapePath
    #           Full path for the LSFGeoTIFF to be written
    #           Full path for shape whose outline is used to set NoData values. if no shapePath is provided,
    #               the TIFF will be created without a "collar"
    """
    def write(self, outputPath, shapePath=None):

        # read my filename into a numpy array
        self.asGeoreferencedArray()
        self.outputPath=outputPath
        # in order to fit into the unsigned bit range of 0 - 255, take the values of interest and compress them to fit the range
        if (self.inArray.max()>127 or self.inArray.min()<-127):
            # Index the array and re-assign values greater than 127 and less than -127
            # http://docs.scipy.org/doc/numpy/user/basics.indexing.html#boolean-or-mask-index-arrays
            a1=self.inArray>127.0
            self.inArray[a1]=127.0
            a2=self.inArray<-127.0
            self.inArray[a2]=-127.0
            # make the range 1 to 255
            self.inArray+=128
        # Round everything else to the nearest integer. Unfortunately, this copies the entire array.
        # astype and, I think, the cast to GDT_Byte just truncates
        self.outArray=np.rint(self.inArray)
        # Write the TIFF out as unsigned 8 bit
        self.writeOutTIFFDataset()
        if shapePath is not None:
            self.setNoData(outputPath, shapePath)
        self.calculateStatisticsForArcGIS(outputPath)



"""
# Subclass to encapsulate LandsatFACT (LSF) Georeferenced Tagged Image File Format (GeoTIFF) output to a signed 8 bit file
#

"""
class Signed8BitLSFGeoTIFF(ReadWriteLSFGeoTIFF):
    """
    # Initializer method
    # @param self, array, filename, rasterBands
    #           numpy array
    #           Full path of a TAR file
    #           Number of raster bands, defaults to 1
    """
    def __init__(self, inArray, geoAttrList, filename, rasterBands=1):
        super(Signed8BitLSFGeoTIFF, self).__init__(inArray, geoAttrList, filename, rasterBands)
        # Instance variable used in write method
        self.gdalDataType=gdal.GDT_Byte

    """
    # Method to output the LSFGeoTIFF as a signed 8 bit GeoTIFF
    # @param self, outputPath, shapePath
    #           Full path for the LSFGeoTIFF to be written
    #           Full path for shape whose outline is used to set NoData values. if no shapePath is provided,
    #               the TIFF will be created without a "collar"
    """
    def write(self, outputPath, shapePath=None):

        # read my filename into a numpy array
        self.asGeoreferencedArray()
        self.outputPath=outputPath
        # in order to fit into the signed bit range of -127 - 127, take the values of interest and compress them to fit the range
        # Index the array and re-assign values greater than 127 and less than -127
        # http://docs.scipy.org/doc/numpy/user/basics.indexing.html#boolean-or-mask-index-arrays
        a1=self.inArray>127.0
        self.inArray[a1]=127.0
        a2=self.inArray<-127.0
        self.inArray[a2]=-127.0
        # Round everything else to the nearest integer
        a3=np.rint(self.inArray)
        # as suggested in https://trac.osgeo.org/gdal/ticket/3151
        # convert the resulting array to signed int
        a4=a3.astype('int8')
        # then to unsigned int. it appears that if you don't do this last step, negatives are lost
        self.outArray = np.cast['uint8'](a4)
        self.writeOutTIFFDataset()
        if shapePath is not None:
            self.setNoData(outputPath, shapePath)
        self.calculateStatisticsForArcGIS(outputPath)



    """
    # Private method to write the GeoTIFF. Used by the public write method.
    # @param self
    #
    """
    def writeOutTIFFDataset(self):
        if not (self.outArray==None or self.outputPath==None or self.geoAttrList==None):
            if os.path.exists(self.outputPath):
                os.remove(self.outputPath)
            if not os.path.exists(os.path.dirname(self.outputPath)):
                os.makedirs(os.path.dirname(self.outputPath))
            driver = gdal.GetDriverByName("GTiff")
            # as suggested in https://trac.osgeo.org/gdal/ticket/3151
            # write the tiff out as pixeltype 8-bit signed
            dataset = driver.Create(self.outputPath, self.geoAttrList[0], self.geoAttrList[1], 1, self.gdalDataType, ['PIXELTYPE=SIGNEDBYTE'])
            transform=self.geoAttrList[2]
            projection=self.geoAttrList[3]
            outBand = dataset.GetRasterBand(1)
            outBand.WriteArray(self.outArray)
            outBand.FlushCache()
            dataset.SetGeoTransform(transform)
            dataset.SetProjection(projection)
        else:
            print("Can't output file {} ".format(self.filename))


"""
# Subclass to encapsulate LandsatFACT (LSF) Georeferenced Tagged Image File Format (GeoTIFF) output to a signed 16 bit file
#

"""
class Signed16BitLSFGeoTIFF(ReadWriteLSFGeoTIFF):

    """
    # Initializer method
    # @param self, array, filename, rasterBands
    #           numpy array
    #           Full path of a TAR file
    #           Number of raster bands, defaults to 1
    """
    def __init__(self, inArray, geoAttrList, filename, rasterBands=1):
        super(Signed16BitLSFGeoTIFF, self).__init__(inArray, geoAttrList, filename, rasterBands)
        # Instance variable used in write method
        self.gdalDataType=gdal.GDT_Int16


"""
# Subclass to encapsulate LandsatFACT (LSF) Georeferenced Tagged Image File Format (GeoTIFF) output to a signed 32 bit file
#

"""
class Signed32BitFloatLSFGeoTIFF(ReadWriteLSFGeoTIFF):

    """
    # Initializer method
    # @param self, array, filename, rasterBands
    #           numpy array
    #           Full path of a TAR file
    #           Number of raster bands, defaults to 1
    """
    def __init__(self, inArray, geoAttrList, filename, rasterBands=1):
        super(Signed32BitFloatLSFGeoTIFF, self).__init__(inArray, geoAttrList, filename, rasterBands)
        # Instance variable used in write method
        self.gdalDataType=gdal.GDT_Float32


    """
    # Default method to to output the LSFGeoTIFF. Overridden in subclasses where bit depth is constrained
    # @param self, outputPath, shapePath
    #           Full path for the LSFGeoTIFF to be written
    #           Full path for shape whose outline is used to set NoData values. if no shapePath is provided,
    #               the TIFF will be created without a "collar"
    """
    def write(self, outputPath, shapePath=None):

        self.outputPath=outputPath
        # read my filename into a numpy array
        result=self.asGeoreferencedArray()
        # don't compress the range. all values should fit.
        self.outArray= self.inArray.astype(np.float32)
        # Write the TIFF out as signed 32 bit float
        self.writeOutTIFFDataset()
        if shapePath is not None:
            self.setNoData(outputPath, shapePath)
        self.calculateStatisticsForArcGIS(outputPath)


