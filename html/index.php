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
$loginKey = loginLandsatFACT($client, $ini_array); 

//* 2. Need to know the datasets
//* Note that this is the datasetFullName
//* Potential datasets: L8 OLI/TIRS 
// $datasetFullName = 'L8 OLI/TIRS';
// $availableDatasetsXML = getAvailableDatasetNames($datasetFullName, $client, $loginKey);
// echo $availableDatasetsXML

//* 3. Search function should be next to get a list of entityIDs
//* Potential datasets: LANDSAT_8
// $datasetName = 'LANDSAT_8';
// $datasetsForDownload = getDatasetsForDownload($datasetName, $client, $loginKey);    
// echo $datasetsForDownload

//* 4. Download the data by entityIDs
//* Potential datasets: LANDSAT_ETM_SLC_OFF & LANDSAT_8
$datasetName = 'LANDSAT_8';
$downloadUrls = getDownloadUrls($datasetName, $client, $loginKey);    
echo $downloadUrls


?>
