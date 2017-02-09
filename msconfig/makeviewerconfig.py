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
          identify="true"
          legend="%(LSF_URL)s&amp;SERVICE=WMS&amp;REQUEST=GetLegendGraphic&amp;layer=%(LAYER_NAME)s&amp;VERSION=1.1.1&amp;FORMAT=image/png"
          mask="true"/>""")  

customrequestWMSLayerTemplate = Template(string="""
        <wmsSubgroup label="%(USER_AOI)s">
		<wmsLayer
          lid="%(SWIR_TH_LAYER_LID)s"
          visible="false"
          url="%(SWIRTH_URL)s" 
          srs="EPSG:900913"
          layers="%(SWIR_LAYER_NAME)s"
          name="%(SWIR_TH_LAYER_TITLE)s"
          styles="default" 
          identify="true"
          legend="%(SWIRTH_URL)s&amp;SERVICE=WMS&amp;REQUEST=GetLegendGraphic&amp;layer=%(SWIR_LAYER_NAME)s&amp;VERSION=1.1.1&amp;FORMAT=image/png"
          mask="true"/>
        <wmsLayer
          lid="%(SWIR_AC_LAYER_LID)s"
          visible="false"
          url="%(SWIRAC_URL)s" 
          srs="EPSG:900913"
          layers="%(SWIR_LAYER_NAME)s"
          name="%(SWIR_AC_LAYER_TITLE)s"
          styles="default" 
          identify="true"
          legend="%(SWIRAC_URL)s&amp;SERVICE=WMS&amp;REQUEST=GetLegendGraphic&amp;layer=%(SWIR_LAYER_NAME)s&amp;VERSION=1.1.1&amp;FORMAT=image/png"
          mask="true"/>  
        <wmsLayer
          lid="%(NDVI_LAYER_LID)s"
          visible="false"
          url="%(NDVI_URL)s" 
          srs="EPSG:900913"
          layers="%(NDVI_LAYER_NAME)s"
          name="%(NDVI_LAYER_TITLE)s"
          styles="default" 
          identify="true"
          legend="%(NDVI_URL)s&amp;SERVICE=WMS&amp;REQUEST=GetLegendGraphic&amp;layer=%(NDVI_LAYER_NAME)s&amp;VERSION=1.1.1&amp;FORMAT=image/png"
          mask="true"/>
		<wmsLayer
          lid="%(NDMI_LAYER_LID)s"
          visible="false"
          url="%(NDMI_URL)s" 
          srs="EPSG:900913"
          layers="%(NDMI_LAYER_NAME)s"
          name="%(NDMI_LAYER_TITLE)s"
          styles="default" 
          identify="true"
          legend="%(NDMI_URL)s&amp;SERVICE=WMS&amp;REQUEST=GetLegendGraphic&amp;layer=%(NDMI_LAYER_NAME)s&amp;VERSION=1.1.1&amp;FORMAT=image/png"
          mask="true"/>  
		</wmsSubgroup>""")

def getLSFLayers():
    #automating the latest change layers
    lsfDict = {
       'NDVI' : [],
       'NDMI' : []
    }
    date_and_type_cur = conn.cursor()
    date_and_type_cur.execute("SELECT product_date, product_type FROM vw_archive_product_dates;")
    #date_and_type_cur.execute("SELECT product_date_range, product_type FROM vw_archive_product_date_range;")
         
    for date, type in date_and_type_cur:
        if type in lsfDict.keys():
            #date_string = str(date)
			#uncomment the following two lines to go back to using previous view
            date_string = date.isoformat()
            date_no_hyphens = date.strftime('%Y%m%d')
            #date = date.join(data)
            print date_string
            lid = type+date_no_hyphens
            #lid = type+date_string
            lsfURL = SERVER_URL+"/lsf-"+type+"?TIME="+date_string+"&amp;TRANSPARENT=true"
            lsfDict[type].append({'LAYER_LID' : lid,
                            'LAYER_NAME'      : type+"-archive",
                            'LAYER_TITLE'     : type+" "+date_string,
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
    #date_and_type_cur.execute("SELECT product_date_range, product_type FROM vw_archive_product_date_range;")
         
    for date, type in date_and_type_cur:
        if type in lsfDict.keys():
            #date_string = str(date)
			#uncomment the following two lines to go back to using previous view
            date_string = date.isoformat()
            date_no_hyphens = date.strftime('%Y%m%d')
            #date = date.join(data)
            print date_string
            lid = 'TSH'+type+date_no_hyphens
            #lid = 'TSH'+type+date_string
            lsfURL = SERVER_URL+"/lsf-swir-threshold?TIME="+date_string+"&amp;TRANSPARENT=true"
            lsfDict[type].append({'LAYER_LID' : lid,
                            'LAYER_NAME'      : type+"-archive",
                            'LAYER_TITLE'     : type+" "+date_string,
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
    #date_and_type_cur.execute("SELECT product_date_range, product_type FROM vw_archive_product_date_range;")
         
    for date, type in date_and_type_cur:
        if type in lsfDict.keys():
            #date_string = str(date)
			#uncomment the following two lines to go back to using previous view
            date_string = date.isoformat()
            date_no_hyphens = date.strftime('%Y%m%d')
            #date = date.join(data)
            print date_string
            lid = 'ALC'+type+date_no_hyphens
            #lid = 'ALC'+type+date_string
            lsfURL = SERVER_URL+"/lsf-swir-allchange?TIME="+date_string+"&amp;TRANSPARENT=true"
            lsfDict[type].append({'LAYER_LID' : lid,
                            'LAYER_NAME'      : type+"-archive",
                            'LAYER_TITLE'     : type+" "+date_string,
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
	
def getCustomRequestLayers():
    #automating the latest change layers
    lsfDict = {
	   'CRLAYERS' : []
    }
    request_id_and_aoi_cur = conn.cursor()
    request_id_and_aoi_cur.execute("SELECT DISTINCT request_id, aoi FROM vw_custom_requests_for_viewer ORDER BY request_id;")
         
    for request_id, aoi in request_id_and_aoi_cur:
        #if type in lsfDict.keys():
            print request_id
            lid = request_id
            aoi_id = str(aoi)
            ndmiURL = SERVER_URL+"/lsf-cr-ndmi?AOI_ID="+aoi_id+"&amp;TRANSPARENT=true"
            ndviURL = SERVER_URL+"/lsf-cr-ndvi?AOI_ID="+aoi_id+"&amp;TRANSPARENT=true"
            swirthURL = SERVER_URL+"/lsf-cr-swir-threshold?AOI_ID="+aoi_id+"&amp;TRANSPARENT=true"
            swiracURL = SERVER_URL+"/lsf-cr-swir-allchange?AOI_ID="+aoi_id+"&amp;TRANSPARENT=true"
            lsfDict['CRLAYERS'].append({'USER_AOI' : lid,
                            'NDVI_LAYER_LID' : "NDVI"+lid,
                            'NDMI_LAYER_LID' : "NDMI"+lid,
                            'SWIR_TH_LAYER_LID' : "SWIRTH"+lid,
                            'SWIR_AC_LAYER_LID' : "SWIRAC"+lid,
                            'NDVI_LAYER_NAME'      : "ndvi-archive",
                            'NDMI_LAYER_NAME'      : "ndmi-archive",
                            'SWIR_LAYER_NAME'      : "swir-archive",
                            'NDVI_LAYER_TITLE'     : "NDVI",
                            'NDMI_LAYER_TITLE'     : "NDMI",
                            'SWIR_TH_LAYER_TITLE'     : "SWIR Threshold",
                            'SWIR_AC_LAYER_TITLE'     : "SWIR All Change",
                            'SERVER_URL'      : SERVER_URL,
                            'NDVI_URL'         : ndviURL,
                            'NDMI_URL'         : ndmiURL,
                            'SWIRTH_URL'         : swirthURL,
                            'SWIRAC_URL'         : swiracURL
            })

    layers = {
	   'CRLAYERS' : []
    }
        
    #for type in lsfDict.keys():
    for thing in lsfDict['CRLAYERS']:
        layers['CRLAYERS'].append(customrequestWMSLayerTemplate.render(thing))   
    return layers

def getSWIRAllChangeLayersVRT():
    #automating the latest change layers
    lsfDict = {
       'SWIR' : []
    }
    date_and_type_cur = conn.cursor()
    date_and_type_cur.execute("SELECT product_date, product_type FROM vw_product_list_swir_for_vrt;")
         
    for date, type in date_and_type_cur:
        date_string = date.isoformat()
        date_no_hyphens = date.strftime('%Y%m%d')
        print date_string
        lid = 'ALC'+type+date_no_hyphens
        lsfURL = SERVER_URL+"/lsf-vrt-swir-allchange?TIME="+date_string+"&amp;TRANSPARENT=true"
        lsfDict[type].append({'LAYER_LID' : lid,
                        'LAYER_NAME'      : type+"-archive",
                        'LAYER_TITLE'     : type+" "+date_string,
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

def getSWIRThresholdLayersVRT():
    #automating the latest change layers
    lsfDict = {
       'SWIR' : []
    }
    date_and_type_cur = conn.cursor()
    date_and_type_cur.execute("SELECT product_date, product_type FROM vw_product_list_swir_for_vrt;")
         
    for date, type in date_and_type_cur:
        date_string = date.isoformat()
        date_no_hyphens = date.strftime('%Y%m%d')
        print date_string
        lid = 'TSH'+type+date_no_hyphens
        lsfURL = SERVER_URL+"/lsf-vrt-swir-threshold?TIME="+date_string+"&amp;TRANSPARENT=true"
        lsfDict[type].append({'LAYER_LID' : lid,
                        'LAYER_NAME'      : type+"-archive",
                        'LAYER_TITLE'     : type+" "+date_string,
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

def getLSFLayersVRT():
    #automating the latest change layers
    lsfDict = {
       'NDVI' : [],
       'NDMI' : []
    }
    date_and_type_cur = conn.cursor()
    date_and_type_cur.execute("SELECT product_date, product_type FROM vw_product_list_for_vrt;")
    #date_and_type_cur.execute("SELECT product_date_range, product_type FROM vw_archive_product_date_range;")
         
    for date, type in date_and_type_cur:
        if type in lsfDict.keys():
            #date_string = str(date)
			#uncomment the following two lines to go back to using previous view
            date_string = date.isoformat()
            date_no_hyphens = date.strftime('%Y%m%d')
            #date = date.join(data)
            print date_string
            lid = type+date_no_hyphens
            #lid = type+date_string
            lsfURL = SERVER_URL+"/lsf-vrt-"+type+"?TIME="+date_string+"&amp;TRANSPARENT=true"
            lsfDict[type].append({'LAYER_LID' : lid,
                            'LAYER_NAME'      : type+"-archive",
                            'LAYER_TITLE'     : type+" "+date_string,
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

template = Template("landsatfact_config.tpl.xml")

if not os.path.exists("../html"):
    os.makedirs("../html")

lsfLayers = getLSFLayers()
thresholdLayers = getSWIRThresholdLayers()
allChangeLayers = getSWIRAllChangeLayers()
customRequestLayers = getCustomRequestLayers()
allChangeLayersVRT = getSWIRAllChangeLayersVRT()
thresholdLayersVRT = getSWIRThresholdLayersVRT()
lsfLayersVRT = getLSFLayersVRT()

#End NRT 8 day & drought monitor automation-------------------------------------------------

f = open("../html/landsatfact_config.xml", "w")
f.write(template.render( {
           'SERVER_URL'                             : SERVER_URL,
           #'VIEWER_DEPLOY_DIR_URL'                 : VIEWER_DEPLOY_DIR_URL,
           'LSF_LAYERS_SWIR_THRESH'                 : '\n'.join(thresholdLayers['SWIR']),
		   'LSF_LAYERS_SWIR_ALLCHANGE'              : '\n'.join(allChangeLayers['SWIR']),
           'LSF_LAYERS_NDVI'                        : '\n'.join(lsfLayers['NDVI']),
           'LSF_LAYERS_NDMI'                        : '\n'.join(lsfLayers['NDMI']),
		   'CR_LAYERS'                              : '\n'.join(customRequestLayers['CRLAYERS']),
           'LSF_LAYERS_SWIR_ALLCHANGE_VRT'          : '\n'.join(allChangeLayersVRT['SWIR']),
		   'LSF_LAYERS_SWIR_THRESH_VRT'             : '\n'.join(thresholdLayersVRT['SWIR']),
		   'LSF_LAYERS_NDMI_VRT'                    : '\n'.join(lsfLayersVRT['NDMI']),
		   'LSF_LAYERS_NDVI_VRT'                    : '\n'.join(lsfLayersVRT['NDVI']),
           }))
f.close()
