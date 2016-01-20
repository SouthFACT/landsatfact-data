## LandsatFACT Overview

The primary purpose of the [LandsatFACT][] project is to support efforts to identify and quantify changes in forest cover as they occur across the Southern U.S. and to provide the information to state forestry agencies and partners in a way that helps sustain efficient and effective program delivery.

The project currently lives in four repositories. The other three are:

 - [landsatfact-drupal][]: Drupal project for landsatfact.com
 - [landsatfact-map][]: Forest Change Viewer
 - [landsatfact-sql][]: A collection of SQL functions, views, and types 

---

![LandsatFACT Software Architecture][lsf-arch-img]

---

## Landsatfact-data Overview

This repository contains all back-end code for fetching current landsat imagery, updating imagery metadata, creating and storing forest area change products, as well as [MapServer][] configuration and executable files.

#### Directory Structure

| Item          | Description
| ------------- |:-------------:|
| cgi-bin       | MapServer CGI executable
| dataexchange  | PHP/SOAP API scripts that obtain data from [USGS EROS][]
| geoprocessing | Python scripts that generate products from obtained data (FMASK included) 
| html          | Web-facing form for 
| log           | Logs
| msconfig      | MapServer configuration and associated Python automation scripts 


#### Change Analysis Methods

LandsatFACT utilizes three change analysis methods. They are the Normalized Difference Vegetation Index (NDVI), the Normalized Difference Moisture Index (NDMI), and Shortwave Infrared (SWIR) Band Differencing. Check out the [project methods][] page for more information on these.





[LandsatFACT]: http://www.landsatfact.com/
[MapServer]: http://mapserver.org
[USGS EROS]: http://eros.usgs.gov/
[LandsatFACT Mapviewer]: https://github.com/nemac/landsatfact-map
[landsatfact-drupal]: https://github.com/nemac/landsatfact-drupal
[landsatfact-sql]: https://github.com/nemac/landsatfact-sql
[landsatfact-map]: https://github.com/nemac/landsatfact-map
[lsf-arch-img]: http://www.landsatfact.com/sites/default/files/LandsatFACT_Software_Architecture_1.png
[project methods]: http://www.landsatfact.com/about/project_methods









