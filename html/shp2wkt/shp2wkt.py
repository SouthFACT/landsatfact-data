from osgeo import ogr
import os, sys

shapefile = "CherokeeCounty.shp"
driver = ogr.GetDriverByName("ESRI Shapefile")
dataSource = driver.Open(shapefile, 0)
layer = dataSource.GetLayer()

for feature in layer:
    geom = feature.GetGeometryRef()
    x = geom.GetEnvelope()

print x 