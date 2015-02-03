#! /usr/bin/python

import sys, re, os

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

template = Template("landsatfact_config.tpl.xml")

f = open("../html/landsatfact_config.xml", "w+")
f.write(template.render( {
            'SERVER_URL'                            : SERVER_URL
            }))
f.close()
