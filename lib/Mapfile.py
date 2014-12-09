#! /usr/bin/python

### This file defines the class Mapfile whose purpose is to read a Mapserver mapfile
### and return information about the names and data files for the layers it contains.
### This is a VERY simplistic implementation that only looks for the NAME and DATA
### keywords in the LAYER sections of the file, and pretty much ignores everything
### else.  In particular, it ignores "include" directives, so it will not work correctly
### on mapfiles that include layers stored in external files.
### 
### Usage is as follows:
### 
###     from Mapfile import Mapfile
### 
###     mapfile = Mapfile("ews.map")
###     for layer in mapfile.layers:
###         print "The layer with NAME=%s has DATA=%s" % (layer.name, layer.data)
###     data = mapfile.findLayerData('EFETAC-NASA_previous1')
###     print "The layer with NAME=EFETAC-NASA_previous1 has DATA=%s" % data
###
### Mark Phillips
### Wed Jan 26 02:11:25 2011

import re

class Layer:
    def __init__(self):
        self.data = None
        self.name = None

class Mapfile:
    def __init__(self,path):
        self.layers = []
        f = open(path, "r")
        layer = None
        depth = 0
        for line in f:
            line = re.sub("#.*$", "", line)
            m = re.match(r'^\s*([a-zA-Z]+)\s*([^\s]+)?', line)
            if (m):
                keyword = m.group(1)
                arg     = m.group(2)
                if layer == None:
                    if keyword == "LAYER":
                        layer = Layer()
                        depth = 0
                else:
                    if keyword == "CLASS":
                        depth = depth + 1
                    elif keyword == "PROJECTION":
                        depth = depth + 1
                    elif keyword == "METADATA":
                        depth = depth + 1
                    elif depth == 0 and keyword == "DATA":
                        layer.data = arg
                    elif depth == 0 and keyword == "NAME":
                        layer.name = arg
                    elif keyword == "END":
                        if depth == 0:
                            self.layers.append(layer)
                            layer = None
                        else:
                            depth = depth - 1
        f.close

    def findLayerData(self,name):
        for layer in self.layers:
            if layer.name == name:
                return layer.data
        return None
