<?php
include '../dataexchange/usgseros.php';

//* Get user account info from ini file stored locally
$ini_array = parse_ini_file("../dataexchange/config.ini", true);
$soapURL = "https://earthexplorer.usgs.gov/inventory/soap?wsdl" ;
$options = array(
    "trace" => true,
    "encoding" => "utf-8",
);             
$client = new SoapClient($soapURL, $options);

//* The following show the method signature(s):
// var_dump($client->__getFunctions())

//* 1. Need to know the datasets
$apiKey = loginLandsatFACT($client, $ini_array); 

//* 2. Need to know the datasets
//* Note that this is the datasetFullName
//* Potential datasets: L8 OLI/TIRS 
// $datasetFullName = '';
// $availableDatasetsXML = getAvailableDatasetNames($datasetFullName, $client, $apiKey);
// echo $availableDatasetsXML

//* 3. Search function should be next to get a list of entityIDs
//* Potential datasets: LANDSAT_8
// $datasetName = 'LANDSAT_8';
// $datasetsForDownload = getDatasetsForDownload($datasetName, $client, $apiKey);    
// echo $datasetsForDownload

/** 4. Search for other meta-data fields
getDatasetMetadata($client, $datasetName, $node, $entityId, $apiKey)
*/
// $datasetName = 'LANDSAT_8';
// $node = 'EE'; 
// $entityId = 'LC80150362013223LGN00';
// $datasetMetadata = getDatasetMetadata($client, $datasetName, $node, $entityId, $apiKey);    
// echo $datasetMetadata

//* 5. Download the data by entityIDs
//* Potential datasets: LANDSAT_ETM_SLC_OFF & LANDSAT_8
// $datasetName = 'LANDSAT_8';
// $downloadUrls = getDownloadUrls($datasetName, $client, $apiKey);    
// echo $downloadUrls

?>


<form method="post" action="results.php">
    Select Dataset:
    <select name="datasetName"> 
        <option VALUE="LANDSAT_8"> L8 OLI/TIRS</option>
        <option VALUE="LANDSAT_ETM_SLC_OFF"> Landsat ETM Scan Line Corrector Off </option>
    </select>
    </br>
    Enter Date Range:
    </br>
    &nbsp;&nbsp;&nbsp;&nbsp;<label for="date">Start Date</label> <input type="date" name="startDate" value="2013-08-05T00:00:00Z">     
    &nbsp;&nbsp;&nbsp;&nbsp;<label for="date">End Date</label> <input type="date" name="endDate" value="2013-09-05T23:59:59Z">         
    </br>
    Enter Upper Right Coordinates:
    </br>
    &nbsp;&nbsp;&nbsp;&nbsp;<label for="lat">Latitude</label>
    &nbsp;&nbsp;&nbsp;&nbsp;<input type="text" name="lat_ur" value="35.27101" />
    &nbsp;&nbsp;<label for="lng">Longitude</label>
    &nbsp;&nbsp;<input type="text" name="lng_ur" value="-76.88" />     
    </br>
    Enter Lower Left Coordinates:
    </br>
    &nbsp;&nbsp;&nbsp;&nbsp;<label for="lat">Latitude</label>
    &nbsp;&nbsp;&nbsp;&nbsp;<input type="text" name="lat_ll" id="lat" value="33.93" />
    &nbsp;&nbsp;<label for="lng">Longitude</label>
    &nbsp;&nbsp;<input type="text" name="lng_ll" value="-79.40" />     
    </br>
    <INPUT TYPE="submit" name="submit" />
</form>