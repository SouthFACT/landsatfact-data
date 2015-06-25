#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mclebr
#
# Created:     03/10/2014
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


import sys, os, subprocess, math
from subprocess import PIPE
from osgeo import gdal, gdalconst
import numpy as np
import numpy.ma as ma
import landsatFactTools_GDAL

#import socket, errno

reload(landsatFactTools_GDAL)


# Landsat 8 doesn't use Esun values
EsunData = {"LT5":{"red":1536,"nir":1031,"swir1":220.0,"swir2":83.44},"LE7":{"red":1533,"nir":1039,"swir1":230.8,"swir2":84.90}}

# The distance the earth is from the sun.  This is a constant used in the TOArelectance and Surface Reflectance formula
# This is harvested directtly from LC8 MTL file for landsat 8 but NOT from LT5 or LE7 (which is why its here)
# EROS has plans to add it to the MTL's for 5 & 7, once that happens we can adjust the SR def
# FYI: the earth sun distance values are different for L5/7 vs L8
earthSunDistance = {1: 0.98331, 2: 0.9833, 3: 0.9833, 4: 0.9833, 5: 0.9833, 6: 0.98332, 7: 0.98333, 8: 0.98335, 9: 0.98338, 10: 0.98341, 11: 0.98345,\
 12: 0.98349, 13: 0.98354, 14: 0.98359, 15: 0.98365, 16: 0.98371, 17: 0.98378, 18: 0.98385, 19: 0.98393, 20: 0.98401, 21: 0.9841, 22: 0.98419, 23: 0.98428,\
  24: 0.98439, 25: 0.98449, 26: 0.9846, 27: 0.98472, 28: 0.98484, 29: 0.98496, 30: 0.98509, 31: 0.98523, 32: 0.98536, 33: 0.98551, 34: 0.98565,\
   35: 0.9858, 36: 0.98596, 37: 0.98612, 38: 0.98628, 39: 0.98645, 40: 0.98662, 41: 0.9868, 42: 0.98698, 43: 0.98717, 44: 0.98735, 45: 0.98755, 46: 0.98774,\
    47: 0.98794, 48: 0.98814, 49: 0.98835, 50: 0.98856, 51: 0.98877, 52: 0.98899, 53: 0.98921, 54: 0.98944, 55: 0.98966, 56: 0.98989, 57: 0.99012, 58: 0.99036,\
     59: 0.9906, 60: 0.99084, 61: 0.99108, 62: 0.99133, 63: 0.99158, 64: 0.99183, 65: 0.99208, 66: 0.99234, 67: 0.9926, 68: 0.99286, 69: 0.99312, 70: 0.99339,\
      71: 0.99365, 72: 0.99392, 73: 0.99419, 74: 0.99446, 75: 0.99474, 76: 0.99501, 77: 0.99529, 78: 0.99556, 79: 0.99584, 80: 0.99612, 81: 0.9964, 82: 0.99669,\
       83: 0.99697, 84: 0.99725, 85: 0.99754, 86: 0.99782, 87: 0.99811, 88: 0.9984, 89: 0.99868, 90: 0.99897, 91: 0.99926, 92: 0.99954, 93: 0.99983, 94: 1.00012,\
        95: 1.00041, 96: 1.00069, 97: 1.00098, 98: 1.00127, 99: 1.00155, 100: 1.00184, 101: 1.00212, 102: 1.0024, 103: 1.00269, 104: 1.00297, 105: 1.00325,\
         106: 1.00353, 107: 1.00381, 108: 1.00409, 109: 1.00437, 110: 1.00464, 111: 1.00492, 112: 1.00519, 113: 1.00546, 114: 1.00573, 115: 1.006,\
          116: 1.00626, 117: 1.00653, 118: 1.00679, 119: 1.00705, 120: 1.00731, 121: 1.00756, 122: 1.00781, 123: 1.00806, 124: 1.00831, 125: 1.00856,\
           126: 1.0088, 127: 1.00904, 128: 1.00928, 129: 1.00952, 130: 1.00975, 131: 1.00998, 132: 1.0102, 133: 1.01043, 134: 1.01065, 135: 1.01087,\
            136: 1.01108, 137: 1.01129, 138: 1.0115, 139: 1.0117, 140: 1.01191, 141: 1.0121, 142: 1.0123, 143: 1.01249, 144: 1.01267, 145: 1.01286,\
             146: 1.01304, 147: 1.01321, 148: 1.01338, 149: 1.01355, 150: 1.01371, 151: 1.01387, 152: 1.01403, 153: 1.01418, 154: 1.01433, 155: 1.01447,\
              156: 1.01461, 157: 1.01475, 158: 1.01488, 159: 1.015, 160: 1.01513, 161: 1.01524, 162: 1.01536, 163: 1.01547, 164: 1.01557, 165: 1.01567,\
               166: 1.01577, 167: 1.01586, 168: 1.01595, 169: 1.01603, 170: 1.0161, 171: 1.01618, 172: 1.01625, 173: 1.01631, 174: 1.01637, 175: 1.01642,\
                176: 1.01647, 177: 1.01652, 178: 1.01656, 179: 1.01659, 180: 1.01662, 181: 1.01665, 182: 1.01667, 183: 1.01668, 184: 1.0167, 185: 1.0167,\
                 186: 1.0167, 187: 1.0167, 188: 1.01669, 189: 1.01668, 190: 1.01666, 191: 1.01664, 192: 1.01661, 193: 1.01658, 194: 1.01655, 195: 1.0165,\
                  196: 1.01646, 197: 1.01641, 198: 1.01635, 199: 1.01629, 200: 1.01623, 201: 1.01616, 202: 1.01609, 203: 1.01601, 204: 1.01592, 205: 1.01584,\
                   206: 1.01575, 207: 1.01565, 208: 1.01555, 209: 1.01544, 210: 1.01533, 211: 1.01522, 212: 1.0151, 213: 1.01497, 214: 1.01485, 215: 1.01471,\
                    216: 1.01458, 217: 1.01444, 218: 1.01429, 219: 1.01414, 220: 1.01399, 221: 1.01383, 222: 1.01367, 223: 1.01351, 224: 1.01334, 225: 1.01317,\
                     226: 1.01299, 227: 1.01281, 228: 1.01263, 229: 1.01244, 230: 1.01225, 231: 1.01205, 232: 1.01186, 233: 1.01165, 234: 1.01145, 235: 1.01124,\
                      236: 1.01103, 237: 1.01081, 238: 1.0106, 239: 1.01037, 240: 1.01015, 241: 1.00992, 242: 1.00969, 243: 1.00946, 244: 1.00922, 245: 1.00898,\
                       246: 1.00874, 247: 1.0085, 248: 1.00825, 249: 1.008, 250: 1.00775, 251: 1.0075, 252: 1.00724, 253: 1.00698, 254: 1.00672, 255: 1.00646,\
                        256: 1.0062, 257: 1.00593, 258: 1.00566, 259: 1.00539, 260: 1.00512, 261: 1.00485, 262: 1.00457, 263: 1.0043, 264: 1.00402, 265: 1.00374,\
                         266: 1.00346, 267: 1.00318, 268: 1.0029, 269: 1.00262, 270: 1.00234, 271: 1.00205, 272: 1.00177, 273: 1.00148, 274: 1.00119, 275: 1.00091,\
                          276: 1.00062, 277: 1.00033, 278: 1.00005, 279: 0.99976, 280: 0.99947, 281: 0.99918, 282: 0.9989, 283: 0.99861, 284: 0.99832, 285: 0.99804,\
                           286: 0.99775, 287: 0.99747, 288: 0.99718, 289: 0.9969, 290: 0.99662, 291: 0.99634, 292: 0.99605, 293: 0.99577, 294: 0.9955, 295: 0.99522,\
                            296: 0.99494, 297: 0.99467, 298: 0.9944, 299: 0.99412, 300: 0.99385, 301: 0.99359, 302: 0.99332, 303: 0.99306, 304: 0.99279, 305: 0.99253,\
                             306: 0.99228, 307: 0.99202, 308: 0.99177, 309: 0.99152, 310: 0.99127, 311: 0.99102, 312: 0.99078, 313: 0.99054, 314: 0.9903, 315: 0.99007,\
                              316: 0.98983, 317: 0.98961, 318: 0.98938, 319: 0.98916, 320: 0.98894, 321: 0.98872, 322: 0.98851, 323: 0.9883, 324: 0.98809, 325: 0.98789,\
                               326: 0.98769, 327: 0.9875, 328: 0.98731, 329: 0.98712, 330: 0.98694, 331: 0.98676, 332: 0.98658, 333: 0.98641, 334: 0.98624, 335: 0.98608,\
                                336: 0.98592, 337: 0.98577, 338: 0.98562, 339: 0.98547, 340: 0.98533, 341: 0.98519, 342: 0.98506, 343: 0.98493, 344: 0.98481, 345: 0.98469,\
                                 346: 0.98457, 347: 0.98446, 348: 0.98436, 349: 0.98426, 350: 0.98416, 351: 0.98407, 352: 0.98399, 353: 0.98391, 354: 0.98383, 355: 0.98376,\
                                  356: 0.9837, 357: 0.98363, 358: 0.98358, 359: 0.98353, 360: 0.98348, 361: 0.98344, 362: 0.9834, 363: 0.98337, 364: 0.98335, 365: 0.98333,\
                                   366: 0.98331}

# Platform band number and band type ID dictionary
platformSensorBands={"LT5":{"red":["_B3","BAND_3"],"nir":["_B4","BAND_4"],"swir1":["_B5","BAND_5"],"tir":["_B6","BAND_6"],"swir2":["_B7","BAND_7"]},\
"LE7":{"red":["_B3","BAND_3"],"nir":["_B4","BAND_4"],"swir1":["_B5","BAND_5"],"tir":["_B6_VCID_2","BAND_6_VCID_2"],"swir2":["_B7","BAND_7"]},\
"LC8":{"red":["_B4","BAND_4"],"nir":["_B5","BAND_5"],"swir1":["_B6","BAND_6"],"tir":["_B10","BAND_10"],"swir2":["_B7","BAND_7"]}}

def bandID(folder, band):
        """Band Options: red, nir, swir1, tir, swir2"""
        bID = os.path.join(folder,os.path.basename(folder)+(platformSensorBands[os.path.basename(folder)[0:3]][band][0])+'.TIF')
        dsInfo = rast2array(bID)
        #format of return -- [dsArray, attList] returned from rast2array
        return dsInfo


class sensorBand:
    def __init__(self, folder):
        self.folder = folder
        self.platformType = os.path.basename(self.folder)[0:3]
        self.ordinalData = os.path.basename(self.folder)[9:16]
        self.sceneID = os.path.basename(self.folder)
        self.mtlFile = mtlData(os.path.join(os.path.dirname(self.folder), self.sceneID[0:21],self.sceneID[0:21] + '_MTL.txt'),self.platformType)
        self.mtlDataDict = self.mtlFile.getMtlData()
        redData = bandID(self.folder,'red')
        self.red = redData[0]
        #self.redma = ma.masked_equal(self.red,0)
        self.nir = bandID(self.folder,'nir')[0]
        #self.nirma = ma.masked_equal(self.nir,0)
        self.swir1 = bandID(self.folder,'swir1')[0]
        self.swir2 = bandID(self.folder,'swir2')[0]
        self.geoTiffAtts = redData[1]
        self.DNminDict = landsatFactTools_GDAL.getDNminDictfromDB(self.sceneID[0:21])

    def radiometricCalibrationType(self, array, typ, band):
        if typ == "TOAradiance":
            r = self.TOAradiance(array, band)
        elif typ == "TOAreflectance":
            r = self.TOAreflectance(array, band)
        elif typ == "SR":
            r = self.SurfaceReflectance(array, band)
        elif typ == "DN":
            r = array
        return r

    
    def reclassFmask(self):
	    """ """
	    FmaskQuad = os.path.join(self.folder,self.sceneID+"_MTLFmask.TIF")
	    FmaskArray = rast2array(FmaskQuad)[0]
	    FmaskArray[FmaskArray == 0] = 10
	    FmaskArray[(FmaskArray == 1) | (FmaskArray == 2) | (FmaskArray == 3) | (FmaskArray == 4) |(FmaskArray == 255)] = 0
	    FmaskArray[FmaskArray == 10] = 1
	    return FmaskArray	
	
    def TOAradiance(self, array, band, Ml="Grescale", Al="Brescale"):
        """ """
        # Same formula for Landsat 5, 7 & 8
        # Ly = Ml * DN + Al
        # print "Ml", self.mtlDataDict[band][Ml]
        # print "Al: ", self.mtlDataDict[band][Al]
        #print "array: ", array
        product = np.multiply(array, self.mtlDataDict[band][Ml])
        TOArad = np.add(product, self.mtlDataDict[band][Al])
        return TOArad

    def TOAreflectance(self, array, band):
        """ """
        # L7 -- pi * Ly * d^2 / ESUN * cos Theta(s)
        # L8 -- (Mp * DN + Ap) / ESUN * cos Theta(s)
        thetaZ = math.radians(90 - self.mtlFile.sunElevation())
        if self.platformType == "LE7" or self.platformType == "LT5":
            d = earthSunDistance[int(str(self.ordinalData)[-3:])]
            tc = (math.pi * (d**2))
            Esun = EsunData[self.platformType][band]
            bc = math.cos(thetaZ) * Esun
            TOArad = self.TOAradiance(array,band)
            product = np.multiply(TOArad,tc)
            TOArad = None
            TOAref = np.divide(product,bc)
        elif self.platformType == "LC8":
            TOArad = self.TOAradiance(array,band,"Mp","Ap")
            TOAref = np.divide(TOArad,math.cos(thetaZ))
        return TOAref

    def SurfaceReflectance(self, array, band):
        """Calculates surface reflectance based on the DOS1 method (Moran et al., 1992)"""
        # sr = pi * (Ly - Lp) * d^2 / ESUN * cos Theta(s)
        if self.platformType == "LE7" or self.platformType == "LT5":
            Esun = EsunData[self.platformType][band]
            d = earthSunDistance[int(str(self.ordinalData)[-3:])]
        elif self.platformType == "LC8":
            d = self.mtlFile.distance()
            # print "d:", d
            Esun = (math.pi * (d**2)) * self.mtlDataDict[band]["RadMax"] / self.mtlDataDict[band]["RefMax"]
            # print "Esun", Esun
        TOArad = self.TOAradiance(array,band)
        # print "TOArad done"
        thetaZ = math.radians(90 - self.mtlFile.sunElevation())
        tc = (math.pi * (d**2))
        bc = math.cos(thetaZ) * Esun
        Lp = self.pathRadiance(band)
        # print "Lp done"
        Ldiff = np.subtract(TOArad, Lp)
        TOArad = None
        product = np.multiply(Ldiff,tc)
        Ldiff = None
        SR = np.divide(product,bc)
        return SR

    def pathRadiance(self, band):
        """Calculates the path radiance for the DOS1 formula"""
        # Lp = ML * DN min + AL - 0.01 * ESUN * cos Theta(s) / (pi * d^2)
        d = earthSunDistance[int(str(self.ordinalData)[-3:])]
        DNmin = self.DNminDict[band]
        thetaZ = math.radians(90 - self.mtlFile.sunElevation())
        if self.platformType == "LE7" or self.platformType == "LT5":
            Esun = EsunData[self.platformType][band]
        elif self.platformType == "LC8":
            Esun = (math.pi * (d**2)) * (self.mtlDataDict[band]["RadMax"] / self.mtlDataDict[band]["RefMax"])
        Lp = (self.mtlDataDict[band]["Grescale"] * DNmin) + self.mtlDataDict[band]["Brescale"] - (0.01 * (Esun * math.cos(thetaZ))/(math.pi * (d**2)))
        return Lp

    def gapMasker(self):
        """ """
        gapFolder = os.path.join(self.folder,"gap_mask")
        gapPath = os.path.join(gapFolder,os.path.basename(self.folder))
        b3 = rast2array(gapPath + "_GM_B3.TIF")
        b4 = rast2array(gapPath + "_GM_B4.TIF")
        b5 = rast2array(gapPath + "_GM_B5.TIF")
        b6 = rast2array(gapPath + "_GM_B6_VCID_2.TIF")
        b7 = rast2array(gapPath + "_GM_B7.TIF")
        gapMask = b3[0] * b4[0] * b5[0] * b6[0] * b7[0]
        return [gapMask,b7[1]]

    def ndvi(self, dataType):
        """dataType: SR, TOAradiance or TOAreflectance """
        r = self.radiometricCalibrationType(self.red,dataType,"red")
        n = self.radiometricCalibrationType(self.nir,dataType,"nir")

        # NDVI calculation -- (nir - red) / (nir + red)
        ndvi = np.divide(n.astype(np.float32) - r.astype(np.float32),
                 n.astype(np.float32) + r.astype(np.float32))
        return ndvi

    def ndmi(self, dataType):
        """dataType: SR, TOAradiance or TOAreflectance """
        s1 = self.radiometricCalibrationType(self.swir1,dataType,"swir1")
        n = self.radiometricCalibrationType(self.nir,dataType,"nir")

        # NDMI calculation -- (nir - swir1) / (nir + swir1)
        ndmi = np.divide(n.astype(np.float32) - s1.astype(np.float32),
                 n.astype(np.float32) + s1.astype(np.float32))
        return ndmi


class mtlData:
    def __init__(self, mtlFile, pltType):
        mtlDoc = open(mtlFile,'r')
        mtl = mtlDoc.readlines()
        mtlDoc.close()
        self.mtl = mtl
        self.pltType = pltType

    def getMtlData(self):
        dataDict = {}
        #dataDict.update({"mtl":{"sunElevation":self.sunElevation()}})
        for k,v in platformSensorBands[self.pltType].items():
            if self.pltType == "LE7" or self.pltType == "LT5":
                dataDict.update({k:{"Brescale":self.Brescale(k),"Grescale":self.Grescale(k)}})
            elif self.pltType == "LC8":
                dataDict.update({k:{"Brescale":self.Brescale(k),"Grescale":self.Grescale(k),\
                "Mp":self.Mp(k),"Ap":self.Ap(k),"RadMax":self.RadMax(k),"RefMax":self.RefMax(k)}})
        return dataDict

    def getMTLobject(self, att, band = None):
        for obj in self.mtl:
            if att in obj:
                cleanedObj = obj.strip()
                indx =  cleanedObj.index('=')
                if band != None:
                    b = cleanedObj[cleanedObj.index('B'):indx-1]
                    if band.upper() == b:
                        break
        return float(cleanedObj[indx+2:])

    def sunElevation(self):
        return self.getMTLobject('SUN_ELEVATION')

    def distance(self):
        # only available in L8 mtl currently
        return self.getMTLobject('EARTH_SUN_DISTANCE')

    def Grescale(self, band):
        bandNum = platformSensorBands[self.pltType][band][1]
        return self.getMTLobject('RADIANCE_MULT_BAND_', bandNum)

    def Brescale(self, band):
        bandNum = platformSensorBands[self.pltType][band][1]
        return self.getMTLobject('RADIANCE_ADD_BAND_', bandNum)

    def Mp(self, band):
        # LC8 only
        bandNum = platformSensorBands[self.pltType][band][1]
        return self.getMTLobject('REFLECTANCE_MULT_BAND_', bandNum)

    def Ap(self, band):
        # LC8 only
        bandNum = platformSensorBands[self.pltType][band][1]
        return self.getMTLobject('REFLECTANCE_ADD_BAND_', bandNum)

    def RadMax(self, band):
        # LC8 only
        bandNum = platformSensorBands[self.pltType][band][1]
        return self.getMTLobject('RADIANCE_MAXIMUM_BAND_', bandNum)

    def RefMax(self, band):
        # LC8 only
        bandNum = platformSensorBands[self.pltType][band][1]
        return self.getMTLobject('REFLECTANCE_MAXIMUM_BAND_', bandNum)



def getDNmin(folder):
    # calculates the min DN value for each band based on the equal to or less than .01% method
    #print folder
    DNminDict = {}
    for band in ['red','nir','swir1','swir2']:
        openBand = bandID(folder,band)
        bandArray = openBand[0]
        bandXsize = openBand[1][0]
        bandYsize = openBand[1][1]
        zeros = (bandArray == 0).sum()
        totalData = bandXsize * bandYsize
        goodData = totalData - zeros
        aList = np.unique(bandArray).tolist()
        stDN = 0
        for dn in aList:
            if not dn == 0:
                val = (bandArray == dn).sum()
                stDN = stDN + val
                percentage = float(stDN) / float(goodData)
                if percentage >= .0001:
                    DNmin = dn
                    break
        bandArray = None
        DNminDict.update({band:DNmin})
        #print band, DNmin
    return DNminDict

def rast2array(inBand):
    """ """
    #print "inBand rast2array: ", inBand
    ds = gdal.Open(inBand, gdal.GA_ReadOnly)
    dsBand = ds.GetRasterBand(1)
    dsArray = dsBand.ReadAsArray()
    x_size = ds.RasterXSize
    y_size = ds.RasterYSize
    geoTransform = ds.GetGeoTransform()
    proj = ds.GetProjection()
    attList = [x_size, y_size, geoTransform, proj]
    ds = None
    return [dsArray, attList]

def createOutTiff(dsList,array,of,outType):
    """attList, array, outFolder, outType--'ndvi','ndmi','gm','cloud',b7diff' """
    outTypeDict={"ndvi":["_NDVI.tif",gdal.GDT_Float32],"swir":["_swir.tif",gdal.GDT_Float32],"sr":["_sr.tif",gdal.GDT_Float32],"ndmi":["_NDMI.tif",gdal.GDT_Float32],"ndvi16":["_NDVI16.tif",gdal.GDT_Int16], "ndmi16":["_NDMI16.tif",gdal.GDT_Int16],\
    "gm":["_GapMask.tif",gdal.GDT_Byte],"cloud":["_CloudMask.tif",gdal.GDT_Byte],"b7diff":["_b7diff.tif",gdal.GDT_Int16],"ndviPer":["_NDVIper8bit.tif",gdal.GDT_Byte],"Fmask":["_Fmask.tif",gdal.GDT_Byte]}
    #print "dsList: ", dsList
    driver = gdal.GetDriverByName("GTiff")
    outputTiffName = of + outTypeDict[outType][0]
    #print "outputTiffName:  ", outputTiffName

    if os.path.exists(outputTiffName):
        os.remove(outputTiffName)
    if not os.path.exists(os.path.dirname(outputTiffName)):
        os.makedirs(os.path.dirname(outputTiffName))

    outputDataset = driver.Create(outputTiffName,dsList[0], dsList[1], 1, outTypeDict[outType][1])
    outBand = outputDataset.GetRasterBand(1)
    outBand.WriteArray(array)
    outBand.FlushCache()
    #print "dsList[2] tuple %s" % (dsList[2],)
    #print "dsList[3] tuple  %s" % (dsList[3],)
    outputDataset.SetGeoTransform(dsList[2])
    outputDataset.SetProjection(dsList[3])
    return outputTiffName

def cropToQuad(inRastFolder, quadsFolder):
    """ """
    sceneQuadList = []
    wrs2 = os.path.basename(inRastFolder)[3:9]
    #quadsFolder = r"S:\Geospatial\LandsatFACT\geodata\vector\quads_AEA"
    quadFiles = os.listdir(quadsFolder)
    tiffsFolder = os.listdir(inRastFolder)
    for quad in quadFiles:
        if quad[-4:] == ".shp" and quad [5:11] == wrs2:
            #print "Cropping Quad: ", quad[0:-4]
            sceneQuadFolder = os.path.join(os.path.dirname(inRastFolder),os.path.basename(inRastFolder) + quad[-6:-4])
            if sceneQuadFolder not in sceneQuadList:
                sceneQuadList.append(sceneQuadFolder)
            if os.path.exists(sceneQuadFolder) == False:
                os.makedirs(sceneQuadFolder)
            for tiff in tiffsFolder:
                if tiff[-4:] == ".TIF":
                    tiffFull = os.path.join(inRastFolder, tiff)
                    quadFull = os.path.join(quadsFolder, quad)
                    #srs = os.path.join(quadsFolder, os.path.basename(quad)[:-4] + ".prj")
                    outraster = os.path.join(sceneQuadFolder, tiff[0:21] + quad[-6:-4] + tiff[21:-4] + ".TIF")
                    if os.path.exists(outraster) == False:
                        codeIn = ['gdalwarp', tiffFull, outraster,'-cutline', quadFull,'-crop_to_cutline','-tr','15','15','-tap','-overwrite'] #'-dstnodata','0',
                        process = subprocess.Popen(codeIn,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        out,err = process.communicate()
                        errcode = process.returncode
                        print out, err
                        print errcode
                elif 'gap_mask' in tiff:
                    sceneQuadGmFolder = os.path.join(sceneQuadFolder, "gap_mask")
                    if os.path.exists(sceneQuadGmFolder) == False:
                        os.makedirs(sceneQuadGmFolder)
                    gapFiles = os.listdir(os.path.join(inRastFolder, tiff))
                    for gm in gapFiles:
                        if gm[-4:] == ".TIF":
                            gmFull = os.path.join(inRastFolder, "gap_mask", gm)
                            quadFull = os.path.join(quadsFolder, quad)
                            outraster = os.path.join(sceneQuadGmFolder, gm[0:21] + quad[-6:-4] + gm[21:-4] + ".TIF")
                            if os.path.exists(outraster) == False:
                                subprocess.call(['gdalwarp', gmFull, outraster,'-cutline', quadFull,'-crop_to_cutline','-tr','15','15','-tap','-overwrite']) #'-dstnodata','0',
    return sceneQuadList


def runFmask(tiffFolder,fmaskShellCall):
	""" """
	try:
		return_value = True;
		print "In runFmask checking for: "+os.path.join(tiffFolder,os.path.basename(tiffFolder) + "_MTLFmask.TIF")
		print "fmaskShellCall: "+fmaskShellCall
                if os.path.exists(os.path.join(tiffFolder,os.path.basename(tiffFolder) + "_MTLFmask.TIF")) == False:
			print "Running Fmask"
			print "tiffFolder: "+tiffFolder
			landsatFactTools_GDAL.cleanDir(tiffFolder)
			print("working dir:" + os.getcwd() + "\n")
			process = subprocess.Popen([fmaskShellCall],cwd=tiffFolder,stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			out,err = process.communicate()
			errcode = process.returncode 
			os.rename(os.path.join(tiffFolder,os.path.basename(tiffFolder)+"_MTLFmask"), os.path.join(tiffFolder,os.path.basename(tiffFolder)+"_MTLFmask.TIF"))
		else:
			print "Mask already created for: "+tiffFolder
		return return_value
	except:
		if out in vars() or out in globals():
			print("Fmask Execution failed:"+str(out)+"/n"+str(err)+"/n"+str(errcode))
		return_value = False;
		return return_value
		
def cloudCover(FmaskData):
    """ """
    #print "Computing Cloud Cover"
    clearLand = float(np.sum(FmaskData == 0))
    clearWater = float(np.sum(FmaskData == 1))
    cloudShadow = float(np.sum(FmaskData == 2))
    snow = float(np.sum(FmaskData == 3))
    cloud = float(np.sum(FmaskData == 4))
    noData = float(np.sum(FmaskData == 255))
    ccPercent = round((cloud + snow + cloudShadow)/(clearLand + clearWater + cloudShadow + cloud + snow)*100,2)
    return ccPercent












# old
##def bitScale(rast):
##    """rast """
##    folder_8bit =os.path.dirname(rast)+"8bit"
##    out_rasterdataset = os.path.join(folder_8bit,os.path.basename(rast)[0:23] + "8bit" + os.path.basename(rast)[23:]) # index changed for quad name from 21 to 23
##    rast = rast[0:-3]+"tif"
##    if os.path.exists(folder_8bit) == True:
##        existingFiles = os.listdir(folder_8bit)
##        if not os.path.basename(out_rasterdataset) in existingFiles:
##            #print "converting file: ", rast
##            proc = subprocess.Popen(['gdal_translate','-ot', 'Byte','-scale','0','65535','0','255','-strict', rast, out_rasterdataset], stdout=PIPE, stderr=PIPE)
##            output, error_output = proc.communicate()
##            if proc.returncode:
##                print("error")
##                print error_output
##    else:
##        os.makedirs(folder_8bit)
##        #print "makeing 8-bit dir"
##        subprocess.check_call(['gdal_translate','-ot', 'Byte','-scale','0','65535','0','255','-strict' ,rast, out_rasterdataset])

##def cropTo_wrs2(inRast,cropF):
##    """ """
##    wrs2 = os.path.basename(inRast)[3:9]
##    print wrs2
##    cropPath = r"H:\SPA_Secure\Geospatial\LandsatFACT\geodata\vector\wrs2\individual_AEA"
##    inshape = os.path.join(cropPath,"wrs2_"+ str(wrs2) + ".shp")
##    if "gap_mask" in inRast:
##        folder_crop = os.path.join(cropF,"gap_mask")
##    else:
##        folder_crop = cropF
##    print "folder_crop: ", folder_crop
##    outraster = os.path.join(folder_crop,os.path.basename(inRast)[0:21] + "crop" + os.path.basename(inRast)[21:])
##    print "outraster: ", outraster
##    if os.path.exists(folder_crop) == True:
##        existingFiles = os.listdir(folder_crop)
##        if not os.path.basename(outraster) in existingFiles:
##            print "converting file: ", inRast
##            subprocess.call(['gdalwarp', inRast, outraster, '-cutline', inshape,'-crop_to_cutline','-overwrite'])
##    else:
##        os.makedirs(folder_crop)
##        print "makeing crop dir"
##        subprocess.call(['gdalwarp', inRast, outraster, '-cutline', inshape,'-crop_to_cutline','-overwrite'])


