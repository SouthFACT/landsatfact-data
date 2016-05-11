#-------------------------------------------------------------------------------
# Name:		LSF.py
# Purpose:	LandsatFACT application script that defines global variables which govern the location
#           of LSF files on disk.
#
# Author:	LandsatFACT Project Team
#		support@landsatfact.com
'''This code was developed in the public domain.  This code is provided as is, without warranty of any kind,
 express or implied, including but not limited to the warranties of
 merchantability, fitness for a particular purpose and noninfringement.
 In no event shall the authors be liable for any claim, damages or
 other liability, whether in an action of contract, tort or otherwise,
 arising from, out of or in connection with the software or the use or
 other dealings in the software.'''
#-----------------------------------------------------------------------------
def main():
    pass

if __name__ == '__main__':
    main()

import os, sys


# =========================================================================
#set base directory for project
path_base = r'/var/vsites/landsatfact-data.nemac.org'

# set Fmask.exe location
# Fmaskexe = r'S:\Geospatial\LandsatFACT\Fmask.exe' #BM's original
fmaskShellCall = r'/var/vsites/landsatfact-data.nemac.org/project/geoprocessing/fmaskLinux/FmaskSentinel/run_fmask_auto.sh'

#set path for the project directory
path_projects = r'/var/vsites/landsatfact-data.nemac.org/project'

#set path for website 
path_website = r'/var/vsites/www.landsatfact.com'

# Fmaskexe = r'G:\LandsatFACT\Fmask.exe'
# set folder location of the quad vector files
# quadsFolder = r'S:\Geospatial\LandsatFACT\geodata\vector\quads_indv_proj' #BM's original
quadsFolder = r'/lsfdata/eros_data/quads_indv_proj'
# set folder locations
# folder where the tar.gz's are stored
# tarStorage = r'S:\Geospatial\LandsatFACT\data\tarFiles' #BM's original
tarStorage = r'/lsfdata/eros_data'
# folder where you want the extracted tiff's to be stored, they will automatically be
# put inside of a subfolder labeled with the scene name
# tiffsStorage = r'S:\Geospatial\LandsatFACT\data\extractedTars' #BM's original
tiffsStorage = r'/lsfdata/eros_data/extractedTars'
# root folder for the project output storage, intermediate products that could be combined for custom request products
# if this path does not exist the script will create it
projectStorage = r'/lsfdata/project_data'# root folder for the project output storage
# if this path does not exist the script will create it
# productStorage = r'S:\Geospatial\LandsatFACT\data\20150414' #BM's original
productStorage = r'/lsfdata/products'
# set output folder locations per product
# if this path does not exist the script will create it
outNDVIfolder = os.path.join(productStorage,'ndvi')
outNDMIfolder = os.path.join(productStorage,'ndmi')
outSWIRfolder = os.path.join(productStorage,'swir')
outGAPfolder = os.path.join(productStorage,'gap_mask')
outFMASKfolder = os.path.join(productStorage,'cloud_mask')
# set cloud cover threshold level, quad scene's with a higher percentage of
# cloud cover will not be processed.
cloudCoverThreshold = 50

