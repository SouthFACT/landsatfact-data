#! /usr/bin/python
#**********************************************************************
# Description:
#    Check that gzipped tarballs in the input directory are valid.
#    Returns a return code of 1 for True and 0  for False. Removes the zip if false.
#    Returns 0 if any of the gz's were invalid, 1 if they were all valid.
#    A negative return code indicates an error.
#
# Arguments:
#  0 - Input file (inTarDir)
#
#**********************************************************************
import os, sys, traceback, logging, glob, localLib

inTarDir = sys.argv[1]

try:
    errCode=1
    os.chdir(inTarDir)
    for tar in glob.glob('*.gz'):
        print tar
        err=localLib.validTar(tar)
        if err:
            errCode=0
            localLib.removeTar(tar)
except:
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n    " + \
            str(sys.exc_type)+ ": " + str(sys.exc_value) + "\n"
    logging.error(pymsg)
    errCode = -1

sys.exit(errCode)

