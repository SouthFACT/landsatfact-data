
Things that you will need to change:

landsatFACTmain.py
- line # 29; this is the list of incoming scene id's.  This will need to be changed to a parameter at some point, however you want/need to set it up.
- line # 40; path to the Fmask.exe file
- line # 43; folder location for all of the vector shapefiles of the quads.
- line # 47; folder location for the tar files
- line # 51; folder location for the extracted tar folders
- line # 55; root folder for the output product storage
- line # 59 - 62; location of individual product type storage folders per output type
- line # 66; cloud cover threshold value

landsatFactTools_GDAL.py
- line # 213; change the connection string to the correct dbname, user and password for the postgresql database

rasterAnalysis_GDAL.py
- none


additional python libs
-psycopg2
-gdal
-gdal bindings

subprocess calls
-All of the subprocess calls were written for windows OS, it very possible that they may have to be rewritten to work on the Linux OS.