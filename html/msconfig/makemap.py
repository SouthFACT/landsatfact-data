#! /usr/bin/python

###
### imports
###

from osgeo import gdal, osr
import sys, os, subprocess, datetime, re, shutil, traceback;


sys.path.append("../var")
try:
    from Config import *
except:
    print "Cannot find local settings file 'Config.py'.  You need to create a Config.py file that contains"
    print "settings appropriate for this copy of the FSWMS project.  You can use the file 'Config.tpl.py'"
    print "as a starting point --- make a copy of that file called 'Config.py', and edit appropriately."
    exit(-1)

###
### function definitions
###


class Template:
    def __init__(self, file):
        f = open(file, "r")
        self.contents = ""
        for line in f:
            self.contents = self.contents + line
        f.close
    def render(self, dict):
        return self.contents % dict

mapfilesWritten = []

def openMapfileForWriting(filename):
    mapfilesWritten.append(filename)
    return open(filename, "w");
    
### Beginning of run-time code -------************************************

os.system("chmod a+w ../var/log");
os.system("chmod a+w ../var/log/*.log > /dev/null 2>&1");
os.system("chmod g-w ../html/*");

###
### Create the vlayers.map file:
###
template = Template("vlayers.tpl.map")
f_new = openMapfileForWriting("vlayers.map")
f_new.write( template.render( {
            'POSTGIS_CONNECTION_STRING' : POSTGIS_CONNECTION_STRING,
            'SERVICE_URL'  : "%s/%s" % (SERVER_URL, "vlayers")
            } ) )
f_new.close()

###
### Create the rlayers.map file:
###
template = Template("rlayers.tpl.map")
f_new = openMapfileForWriting("rlayers.map")
f_new.write( template.render( {
            'SERVICE_URL'  : "%s/%s" % (SERVER_URL, "rlayers")
            } ) )
f_new.close()
