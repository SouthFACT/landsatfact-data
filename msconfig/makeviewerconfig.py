#! /usr/bin/python

import sys, re, os, getopt, psycopg2
from subprocess import Popen
import time
 
print "Connected!\n"

sys.path.append("../var")
try:
    from Config import *
    from datetime import timedelta
    from datetime import datetime    
except:
    print "Cannot find local settings file 'Config.py'.  You need to create a Config.py file that contains"
    print "settings appropriate for this copy of the FSWMS project.  You can use the file 'Config.tpl.py'"
    print "as a starting point --- make a copy of that file called 'Config.py', and edit appropriately."
    exit(-1)

conn = psycopg2.connect(POSTGIS_CONNECTION_STRING)    

print "Connecting to database\n   ->%s" % (POSTGIS_CONNECTION_STRING)
    
# from LegendConfig import *
opts, args = getopt.getopt(sys.argv[1:],"al")

# conn.cursor will return a cursor object, you can use this cursor to perform queries

    

class Template:
    def __init__(self, file=None, **args):
        if file is None and 'string' in args:
            self.contents = args['string']
        else:
            f = open(file, "r")
            self.contents = ""
            for line in f:
                self.contents = self.contents + line
            f.close
    def render(self, dict):
        return self.contents % dict

#change product template    
lsfWMSLayerTemplate = Template(string="""
        <wmsLayer
          lid="%(LAYER_LID)s"
          visible="false"
          url="%(LSF_URL)s" 
          srs="EPSG:900913"
          layers="%(LAYER_NAME)s"
          name="%(LAYER_TITLE)s"
          styles="default" 
          identify="false"
          legend="%(LSF_URL)s&amp;SERVICE=WMS&amp;REQUEST=GetLegendGraphic&amp;layer=%(LAYER_NAME)s&amp;VERSION=1.1.1&amp;FORMAT=image/png"
          mask="true"/>""")  
          


def getLSFLayers():
    #automating the latest change layers
    lsfDict = {
       'NDVI' : [],
       'NDMI' : []
    }
    date_and_type_cur = conn.cursor()
    date_and_type_cur.execute("SELECT product_date, product_type FROM vw_archive_product_dates;")
         
    for date, type in date_and_type_cur:
        if type in lsfDict.keys():
            date_string = date.isoformat()
            date_no_hyphens = date.strftime('%Y%m%d')
            #date = date.join(data)
            print 'The date is ' + date_string + type
            lid = type+date_no_hyphens
            lsfURL = "http://landsatfact-data-dev.nemac.org/lsf-"+type+"?TIME="+date_string+"&amp;TRANSPARENT=true"
            lsfDict[type].append({'LAYER_LID' : lid,
                            'LAYER_NAME'      : type+"-archive",
                            'LAYER_TITLE'     : type+date_no_hyphens,
                            'SERVER_URL'      : SERVER_URL,
                            'LSF_URL'         : lsfURL
            })

    layers = { 
        'NDVI' : [],
        'NDMI' : []
    }
        
    for type in lsfDict.keys():
        for thing in lsfDict[type]:
            layers[type].append(lsfWMSLayerTemplate.render(thing))   
    return layers
	
def getSWIRThresholdLayers():
    #automating the latest change layers
    lsfDict = {
       'SWIR' : []
    }
    date_and_type_cur = conn.cursor()
    date_and_type_cur.execute("SELECT product_date, product_type FROM vw_archive_product_dates;")
         
    for date, type in date_and_type_cur:
        if type in lsfDict.keys():
            date_string = date.isoformat()
            date_no_hyphens = date.strftime('%Y%m%d')
            #date = date.join(data)
            print 'The date is ' + date_string + type
            lid = type+date_no_hyphens
            lsfURL = "http://landsatfact-data-dev.nemac.org/lsf-swir-threshold?TIME="+date_string+"&amp;TRANSPARENT=true"
            lsfDict[type].append({'LAYER_LID' : lid,
                            'LAYER_NAME'      : type+"-archive",
                            'LAYER_TITLE'     : type+date_no_hyphens,
                            'SERVER_URL'      : SERVER_URL,
                            'LSF_URL'         : lsfURL
            })

    layers = { 
        'SWIR' : []
    }
        
    for type in lsfDict.keys():
        for thing in lsfDict[type]:
            layers[type].append(lsfWMSLayerTemplate.render(thing))   
    return layers
	
def getSWIRAllChangeLayers():
    #automating the latest change layers
    lsfDict = {
       'SWIR' : []
    }
    date_and_type_cur = conn.cursor()
    date_and_type_cur.execute("SELECT product_date, product_type FROM vw_archive_product_dates;")
         
    for date, type in date_and_type_cur:
        if type in lsfDict.keys():
            date_string = date.isoformat()
            date_no_hyphens = date.strftime('%Y%m%d')
            #date = date.join(data)
            print 'The date is ' + date_string + type
            lid = type+date_no_hyphens
            lsfURL = "http://landsatfact-data-dev.nemac.org/lsf-swir-allchange?TIME="+date_string+"&amp;TRANSPARENT=true"
            lsfDict[type].append({'LAYER_LID' : lid,
                            'LAYER_NAME'      : type+"-archive",
                            'LAYER_TITLE'     : type+date_no_hyphens,
                            'SERVER_URL'      : SERVER_URL,
                            'LSF_URL'         : lsfURL
            })

    layers = { 
        'SWIR' : []
    }
        
    for type in lsfDict.keys():
        for thing in lsfDict[type]:
            layers[type].append(lsfWMSLayerTemplate.render(thing))   
    return layers

template = Template("landsatfact_config.tpl.xml")

if not os.path.exists("../html"):
    os.makedirs("../html")

lsfLayers = getLSFLayers()
thresholdLayers = getSWIRThresholdLayers()
allChangeLayers = getSWIRAllChangeLayers()
#End NRT 8 day & drought monitor automation-------------------------------------------------

f = open("../html/landsatfact_config.xml", "w")
f.write(template.render( {
           'SERVER_URL'                         : SERVER_URL,
           #'VIEWER_DEPLOY_DIR_URL'             : VIEWER_DEPLOY_DIR_URL,
           'LSF_LAYERS_SWIR_THRESH'           : '\n'.join(thresholdLayers['SWIR']),
		   'LSF_LAYERS_SWIR_ALLCHANGE'        : '\n'.join(allChangeLayers['SWIR']),
           'LSF_LAYERS_NDVI'                    : '\n'.join(lsfLayers['NDVI']),
           'LSF_LAYERS_NDMI'                    : '\n'.join(lsfLayers['NDMI'])
           }))
f.close()
