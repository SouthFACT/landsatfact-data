import os, sys, re

### CGIUtils.py
### 
### Utility functions to support MapServer CGI wrapper scripts for FSWMS.
###
### by Mark Phillips
### Fri Sep 23 11:10:18 EDT 2011

###
### Return True iff this computer is running CentOS
###
def this_computer_is_running_centos():
    f = open("/etc/redhat-release", "r")
    centos = False
    for line in f.readlines():
        if re.search("CentOS",  line):
            centos = True
            break
    f.close()
    return centos

###
### Inject a mapfile path into the query string of a MapServer CGI
### request, and pass control on to the MapServer executable.  This
### function does not normally return --- it invokes the MapServer
### binary with os.execv(), which replaces this process with the
### MapServer process.
###
### This function handles both GET and POST requests.  It translates
### POST requests into GET requests, however, so that the invoked
### MapServer process always receives a GET request.
###
def mapserv_inject_mapfile(mapfile, mapserv):
    if os.environ["REQUEST_METHOD"] == "GET":
        ### 
        ### If we have a GET request, modify the QUERY_STRING
        ### environment variable to prepend "map=MAPFILE&" to it.
        ### 
        if os.environ["QUERY_STRING"] == "":
            QUERY_STRING = "map=%s" % mapfile
        else:
            QUERY_STRING = "map=%s&%s" % (mapfile,os.environ["QUERY_STRING"])
        os.putenv("QUERY_STRING", QUERY_STRING)
        os.execv(mapserv, [])
    elif os.environ["REQUEST_METHOD"] == "POST":
        ### 
        ### If we have a POST request, the data of the request is
        ### passed via stdin.  The number of bytes is passed in the
        ### CONTENT_LENGTH environment variable, so read that variable
        ### first, then read that many bytes from stdin, and set the
        ### QUERY_STRING environment variable by prepending
        ### "map=MAPFILE&" to the data read from stdin.  Also reset
        ### the REQUEST_METHOD environment variable to "GET".
        ### 
        CONTENT_LENGTH = int(os.environ["CONTENT_LENGTH"])
        QUERY_STRING = sys.stdin.read(CONTENT_LENGTH)
        if QUERY_STRING == "":
            QUERY_STRING = "map=%s" % mapfile
        else:
            QUERY_STRING = "map=%s&%s" % (mapfile,QUERY_STRING)
        os.putenv("QUERY_STRING", QUERY_STRING)
        os.putenv("REQUEST_METHOD", "GET")
        os.execv(mapserv, [])
    else:
        print "Content-type: text/plain\n"
        print "Error: I only understand GET or POST requests"
        sys.exit(1)
