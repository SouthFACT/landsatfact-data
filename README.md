landsat-fact-geoprocessing
==========================

The backend geoprocessing project for https://github.com/nemac/landsat-fact-viewer

Description of root directory structure/file and associated purpose:

| Item          | Description
| ------------- |:-------------:|
| cgi-bin       | MapServer CGI executable
| dataexchange  | PHP/SOAP API scripts that obtain data from USGS EROS 
| geoprocessing | Python scripts that generate products from obtained data (FMASK included) 
| html          | A web directory 
| log           | logging directory 
| msconfig      | MapServer configuration and associated Python automation scripts 