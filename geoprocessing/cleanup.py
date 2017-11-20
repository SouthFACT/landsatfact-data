#! /usr/bin/python
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      olouda
#
# Created:     14/07/2016
# Copyright:   (c) olouda 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import shutil, fnmatch, os, copy
import LSF, landsatFactTools_GDAL
import glob
from datetime import datetime, timedelta

import pdb

southeastPathRows=['013035', '013036', '014034', '014035', '014036', '015033', '015034', '015035', '015036', '015037',
    '015040','015041', '015042','015043', '016033', '016034', '016035', '016036', '016037', '016038', '016039', '016040',
    '016041', '016042', '016043', '017033', '017034', '017035','017036', '017037', '017038', '017039', '017040', '017041',
    '018033', '018034', '018035', '018036', '018037', '018038', '018039', '018040', '019033','019034', '019035', '019036',
    '019037', '019038', '019039', '020033', '020034', '020035', '020036', '020037', '020038', '020039', '021033', '021034',
    '021035', '021036', '021037', '021038', '021039', '021040', '022034', '022035', '022036', '022037', '022038', '022039',
    '022040', '023034','023035','023036','023037','023038','023039','023040','024035','024036','024037', '024038','024039',
    '024040', '025035','025036','025037', '025038','025039','025040','026034','026035','026036','026037','026038','026039',
    '026040','026041','026042','027034','027035','027036','027037','027038','027039','027040','027041','027042','028034','028035',
    '028036','028037','028038','028039','028040','028041','029034','029035','029036','029037','029038','029039','029040','030034',
    '030035', '030036','030037','030038','030039','030040','031034','031035','031036','031037','031038','031039','031040','032034',
    '032035','032038','032039','033038']

"""
# Remove elements of a list of scenes, used by custom requests, from a dictionary of scenes
# keyed by pathRow and values of julian dates of the format indicated below.
# The effect is to leave scenes still required by custom requests on disk.
#
# returns the modified scene dictionary
#
# @param scenesOnDiskDictionary
#           a dictionary with pathrow keys and a list of dates present as the value
#               e.g., {'029034': ['2016146','2016162','2016002','2016170']}
# @param scenesToRemainList
#           a list of Landsat scene identifiers of the format LXSPPPRRRYYYYDDDGSIVV
#               where pathRow is PPPRRR where PPP = WRS path and RRR = WRS row
#               and date is YYYYDDD where YYYY = Year and DDD = Julian day of year
"""
def filterScenesInDictionary(scenesOnDiskDictionary, scenesToRemainList):

    for scene in scenesToRemainList:
        if scenesOnDiskDictionary[scene[3:9]] and (scene[9:16] in scenesOnDiskDictionary[scene[3:9]]):
            scenesOnDiskDictionary[scene[3:9]].remove(scene[9:16])
    return scenesOnDiskDictionary


"""
# Construct a dictionary of scenes specified by their path rows and dates
# from a list of either directories or files of the specified format
# returns a dictionary with pathrow keys and a list of dates present as the value
# e.g., {'029034': ['2016146','2016162','2016002','2016170']}
# @param diskList
#           a list of either directories or files of the specified format
#               pathRow is PPPRRR where PPP = WRS path and RRR = WRS row
#               date is YYYYDDD where YYYY = Year and DDD = Julian day of year
# On at least 2 occasions, scenes outside the southeast (i.e., not in southeastPathRows)
#  have been downloaded from USGS. While we won't clip to quads or make products with the scenes,
#  they can show up in extractedTars. This code handles that error by recognizing the exception and
#  removing the offender from tiffsStorage.
"""
def sceneDictionary(diskList):
    scenesDict=dict.fromkeys(southeastPathRows)
    for dirOrFile in diskList:
        pathRow=dirOrFile[3:9]
        scenes=None
        try:
            scenes=scenesDict[pathRow]
        except:
            cleanPathRowDate(pathRow, '???????', LSF.tiffsStorage)
            print (pathRow+'??????? is in error, deleted it')
            continue
        if not scenes:
            scenesDict[pathRow] = [dirOrFile[9:16]]
        elif (dirOrFile[9:16] not in scenes):
            scenes.insert(0, dirOrFile[9:16])
    return scenesDict

"""
# Clean up data (directories or files) for an individual scene having the specified pathRowString and dateString
# stored on disk below the given rootDir
# @param pathRowString
#           pathRowString PPPRRR where PPP = WRS path and RRR = WRS row
# @param dateString
#           dateString YYYYDDD where YYYY = Year and DDD = Julian day of year
# @param rootDir
#           parent directory e.g.,'/lsfdata/products/'
"""
def cleanPathRowDate(pathRowString, dateString, rootDir):
    """remove all directories  and files for a particular path/row date, e.g,
    pathRowString = '014035'
    dateString = '2015294'
    pathRowDateString = '???0140352015294?????*'
    removes subdirectory LC80140352015286LGN00 from extractedTars root directory,
    LC80140352015286LGN00LL and LC80140352015286LGN00UL subdirectories from project_data, and
    LC80140352015286LGN00LL_LE70140352015294EDC00LL_Fmask.tif and LC80140352015286LGN00LL_LE70140352015294EDC00LL_GapMask.tif from products"""

    pathRowDateString='???'+pathRowString+dateString+'?????*'
    for path, dirs, files in os.walk(os.path.abspath(rootDir)):
        # delete either the directory or file which matches the pathRowDateString
        # this function is looking either a list of directories or files, depending on the rootDir
        # walk finds dirs first, deletes the tree and any files beneath are no longer found
        for dirname in fnmatch.filter(dirs, pathRowDateString):
            #print 'Would have deleted directory:' + os.path.join(path, dirname)
            shutil.rmtree(os.path.join(path, dirname))
        for filename in fnmatch.filter(files, pathRowDateString):
            #print 'Would have deleted filename:' + os.path.join(path, filename)
            os.remove(os.path.join(path, filename))

"""
# Remove all directories for a particular path/row leaving the most recent remainder on disk below the given rootDir
# @param pathRow
#           pathRow PPPRRR where PPP = WRS path and RRR = WRS row, e.g., '029034'
# @param dateList
#           list sorted earliest to most recent e.g., ['2016002','2016146','2016162','2016170','2016178'
#               '2016186','2016194']
# @param remainder
#           number of dates undeleted e.g., 2 from the previous list would leave'0290342016186' and '0290342016194'
# @param rootDir
#           parent directory e.g.,'/lsfdata/products/'
"""
def cleanPathRowDirectories(pathRow, dateList, remainder, rootDir):
    """"""
    if len(dateList) > remainder:
        # delete the oldest date and shrink the list
        cleanPathRowDate(pathRow, dateList.pop(), rootDir)
        # recurse through the rest of the list. NB dateList has been modified by pop().
        cleanPathRowDirectories(pathRow, dateList, remainder, rootDir)

"""
# Update the disk_status field for a particular path/row leaving the most recent remainder on disk below the given rootDir
# @param pathRow
#           pathRow PPPRRR where PPP = WRS path and RRR = WRS row, e.g., '029034'
# @param dateList
#           list sorted earliest to most recent e.g., ['2016002','2016146','2016162','2016170','2016178'
#               '2016186','2016194']
# @param remainder
#           number of dates undeleted e.g., 2 from the previous list would leave'0290342016186' and '0290342016194'
# @param rootDir
#           parent directory e.g.,'/lsfdata/products/'
"""
def updateProductsDiskStatus(pathRow, dateList, remainder, rootDir):
    """"""
    if len(dateList) > remainder:
        # update the disk_status of the product rows
        # build up the arguments to the postgres SIMILAR TO operator which does regular expression type matching on fields
        # by specifying the unique scene identifiers defined by a combination of path/row and a date		
        similarClause='|'.join(map(lambda x: pathRow + x, dateList))
        commandString = r"update products set disk_status = '' where input1 similar to {};".format("'%("+similarClause+")%'")
        resultsTup = landsatFactTools_GDAL.postgresCommand(commandString)

"""
# Execute a list of functions on all but the latest (remainder number) path/row and date combinations on disk below the given rootDir
# @param scenesDict
#           dictionary of scenes defined as a path/row on a given date, irrespective of the sensor, satellite, ground station identifier,
#               and archive version number e.g., {'029034': ['2016002','2016146','2016162','2016170']}
# @param remainder
#           number of dates undeleted
# @param rootDir
#           parent directory e.g.,'/lsfdata/products/'
# @param functionList
#           list of function pointers
"""
def operateOnPathRows(scenesDict, remainder, rootDir, functionList):
    """ """
    for (k,v) in scenesDict.items():
        # order the date values in scenesDict
        if v:
            vSorted = sorted(v, reverse=True)
            # call each function in functionList with the args provided to this function
            for f in functionList:
              # the list of dates, vSorted, will be modified by the recursive function so pass a shallow copy to each function  
              f(k, copy.copy(vSorted), remainder, rootDir)

"""
# Clean up the eros_data directory, printing a warning if any of the tars in the list aren't there
# @param processedList
#           a list containing tars in eros_data
"""
def cleanProcessedTars(processedList):
    """['LE70290342016194EDC00.tar.gz', 'LE70290362016194EDC00.tar.gz',
    'LE70290352016194EDC00.tar.gz', 'LC80210352016194LGN00.tar.gz', 'LC80210392016194LGN00.tar.gz',
    'LC80210372016194LGN00.tar.gz', 'LC80210362016194LGN00.tar.gz', 'LC80210382016194LGN00.tar.gz',
    'LE70290392016194EDC00.tar.gz', 'LE70130352016194EDC00.tar.gz', 'LE70130362016194EDC00.tar.gz']"""
    print ('cleanProcessedTars ', processedList)
    in_dir = os.getcwd()
    os.chdir(LSF.tarStorage)
    for t in processedList:
        try:
            print t
            if not os.path.isdir(t):
            #if os.path.exists(t): print 'Would have deleted filename:' + t
               os.remove(t)
        except OSError:
            pass
    os.chdir(in_dir)

"""
# Clean up the extractedTars directory, leaving no dates for each path row
# For example, directory LC80150332016184LGN00 could be left for the 015033 path row.
# @param processedSceneList
#           a list containing all the directories in extractedTars
# @param crScenesToKeep
#           a list containing scenes which are in use by custom requests
"""
def cleanExtractedTarContents(processedSceneList, crScenesToKeep):
    """processedSceneList is the list of directories in extractedTars
    e.g.,['LC80130352016154LGN00', 'LC80130352016170LGN00', 'LC80130352016186LGN00','LC80130352016202LGN00']
    path/row = 'LC80130352016202LGN00'[3:9]
    date = 'LC80130352016202LGN00'[9:16]"""
    print ('cleanExtractedTarContents ', processedSceneList)
    in_dir = os.getcwd()
    os.chdir(LSF.tiffsStorage)
    # populate a dictionary of scenes defined as a path/row on a given date, irrespective of the sensor, satellite,
    # ground station identifier, and archive version number e.g., {'029034': ['2016002','2016146','2016162','2016170']}
    southeastPathRowDates=filterScenesInDictionary(sceneDictionary(processedSceneList), crScenesToKeep)
    operateOnPathRows(southeastPathRowDates, 0, LSF.tiffsStorage, [cleanPathRowDirectories])
    os.chdir(in_dir)

"""
# Clean up the project_data directory, leaving the last 5 dates for each path row
# For example, directories LC80150332016184LGN00U* and LC80150332016200LGN00* could be left for the 015033 path row.
# @param processedQuadList
#           a list containing all the directories in project_data
# @param crScenesToKeep
#           a list containing scenes which are in use by custom requests
"""
def cleanIntermediateTIFFsForProducts(processedQuadList, crScenesToKeep):
    """processedQuadList is the list of directories in project_data
    e.g.,['LC80300342016001LGN00UL', 'LC80300342016001LGN00UR', 'LC80300342016001LGN00LL','LC80300342016001LGN00LR']
    path/row = 'LC80300342016001LGN00UR'[3:9]
    date = 'LC80300342016001LGN00UR'[9:16]"""

    print ('cleanIntermediateTIFFsForProducts', processedQuadList, crScenesToKeep)
    in_dir = os.getcwd()
    os.chdir(LSF.projectStorage)
    # populate a dictionary of scenes defined as a path/row on a given date, irrespective of the sensor, satellite,
    # ground station identifier, and archive version number e.g., {'029034': ['2016002','2016146','2016162','2016170']}
    southeastPathRowDates=filterScenesInDictionary(sceneDictionary(processedQuadList), crScenesToKeep)
    operateOnPathRows(southeastPathRowDates, 5, LSF.projectStorage, [cleanPathRowDirectories])
    os.chdir(in_dir)

"""
# Clean up the products directory, leaving the last 11 dates for each path row
# @param productTIFFsList
#           a list containing all the product TIFFs in product directory
# @param crScenesToKeep
#           a list containing scenes which are in use by custom requests
"""
def cleanProductTIFFs(productTIFFsList, crScenesToKeep):
    print ('cleanProductTIFFs ', productTIFFsList, crScenesToKeep)
    in_dir = os.getcwd()
    os.chdir(LSF.productStorage)
    # populate dictionary of scenes defined as a path/row on a given date, irrespective of the sensor, satellite,
    # ground station identifier, and archive version number e.g., {'029034': ['2016002','2016146','2016162','2016170']}
    # then remove scenes that are still being used by custom requests from the dictionary of scenes available for deletion
    southeastPathRowDates=filterScenesInDictionary(sceneDictionary(productTIFFsList), crScenesToKeep)
    operateOnPathRows(southeastPathRowDates, 11, LSF.productStorage, [cleanPathRowDirectories, updateProductsDiskStatus])
    os.chdir(in_dir)

"""
# Returns a list of scene_ids used by Custom Requests satisfying the where clause
#
"""
def customRequestWhere(whereClause):
    """ """
    sceneList=[]
    commandString = r"SELECT scene_id FROM custom_request_scenes where aoi_id in (select aoi_id from custom_request_dates {});".format(whereClause)
    resultsTup = landsatFactTools_GDAL.postgresCommand(commandString)
    if resultsTup:
        for tup in resultsTup:
            sceneList.append(tup[0])
    return sceneList

"""
# Clean up Custom Request (CR) remnants after 45 days
# returns a List of scenes used by a CR older than 45 days
"""
def getOldCustomRequestFromDB():
    """ """
    whereClause= "where custom_request_status_id=4 and custom_request_date < (now() - interval '45 days')"
    return customRequestWhere(whereClause)

"""
# Leave Custom Request (CR) which have completed within the last 45 days
# returns a List of scenes used by a CR newer than 45 days
"""
def getNewCustomRequestFromDB():
    """ """
    whereClause= "where custom_request_status_id=4 and custom_request_date > (now() - interval '45 days')"
    return customRequestWhere(whereClause)
	
"""
# Find files in a directory matching a simple pattern using Unix shell-style wildcards.
# returns a List
# @param directory
#           a relative or absolute root of a directory tree to be searched top-down
# @param pattern
#           the pattern string
"""
def findFilesMatchingPattern(directory, pattern):
    answerList =[]
    for root, directories, files in os.walk(directory):
        for filename in fnmatch.filter(files, pattern):
            answerList.append(filename)
    return answerList

"""
# Filter files in a list returning those older than the given date.
# returns a List
# @param directory
#           a relative or absolute root of a directory tree to be searched top-down
# @param date
#           datetime 
"""
def filterOlderFiles(fileList, date):
    answerList =[]
    for filename in fileList:
        if (datetime.fromtimestamp(os.path.getmtime(filename)) < date):
            answerList.append(filename)
    return answerList

# Removes old CR tars in eros_data. 
# CR products for the requesting user are kept in cr_zip and that directory is cleaned separately.
newScenes = getNewCustomRequestFromDB()
cleanProcessedTars(filterOlderFiles(glob.glob(LSF.tarStorage+'/*.gz'),datetime.now() - timedelta(days=3)))

cleanExtractedTarContents(os.listdir(LSF.tiffsStorage), [])
cleanIntermediateTIFFsForProducts(os.listdir(LSF.projectStorage), [])
cleanProductTIFFs(findFilesMatchingPattern(LSF.productStorage, 'L*.tif'), [])

