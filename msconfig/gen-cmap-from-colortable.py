#! /usr/bin/python
import os, re, gd

#Begin category1----------------------------------------------------
colortab = [{'catid':'11','color':'0,0,255'},
            {'catid':'21','color':'205,137,102'},
            {'catid':'22','color':'255,190,190'},
            {'catid':'23','color':'255,84,127'},
            {'catid':'24','color':'255,0,0'},
            {'catid':'31','color':'204,204,204'},
            {'catid':'41','color':'71,186,92'},
            {'catid':'42','color':'76,115,0'},
            {'catid':'43','color':'114,137,68'},
            {'catid':'52','color':'171,205,102'},
            {'catid':'71','color':'235,245,122'},
            {'catid':'81','color':'205,205,102'},
            {'catid':'82','color':'172,235,0'},
            {'catid':'90','color':'0,127,132'}]

cmap = open("cmaps/landcover_06.cmap","w")
catCount = 0
FONT = "FreeSans.ttf" #should be in cur dir
fontSize = 12
os.environ["GDFONTPATH"] = "." #look in cur dir for fonts
for n in range(0, len(colortab)):
    cmap.write('CLASS\n')
    cmap.write("\tEXPRESSION ([pixel] = "+colortab[n]['catid']+")\n")
    rgblist = colortab[n]['color'].split(',')
    cmap.write("\tCOLOR " + "\t"+rgblist[0] + "\t"+rgblist[1] + "\t"+rgblist[2]+"\n")
    cmap.write('END\n')
    catCount = catCount + 1
cmap.close()
