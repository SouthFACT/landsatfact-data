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

// echo $_POST['datasetName'];
// echo "</br>";
// echo $_POST['startDate'];
// echo "</br>";
// echo $_POST['endDate'];
// echo "</br>";
// echo $_POST['lat_ur'];
// echo "</br>";
// echo $_POST['lng_ur'];
// echo "</br>";
// echo $_POST['lat_ll'];
// echo "</br>";
// echo $_POST['lng_ll'];

function simpleXmlObjectToArray( $xmlObject, $out = array () ) {
    foreach ( (array) $xmlObject as $index => $node )
        $out[$index] = ( is_object ( $node ) || is_array($node) )
        ? simpleXmlObjectToArray ( $node )
        : $node;

    return $out;
}

function getEntityIds($arrayObject, &$entityIds) {
    foreach($arrayObject as $key => $value) {
        if (is_array($value)) {
            getEntityIds($value);
        }
        else {
            if ($key=="entityId") {
                $entityIds[]=$value;
            }
        }
    }
    print_r($entityIds);
}

//* Search function should be next to get a list of entityIDs
//* Potential datasets: LANDSAT_8
$datasetName = $_POST['datasetName'];
$lowerLeft = (object) array('latitude' => $_POST['lat_ll'], 'longitude' => $_POST['lng_ll']);
$upperRight = (object) array('latitude' => $_POST['lat_ur'], 'longitude' => $_POST['lng_ur']);
$startDate = $_POST['startDate'];  
$endDate = $_POST['endDate'];  
$searchResults = getDatasetsForDownload($datasetName, $client, $apiKey, $lowerLeft, $upperRight, $startDate, $endDate);  
// echo $datasetsForDownload;

// attempt to do things recursively w/ array structure
// $soap_resArray = simpleXmlObjectToArray($datasetsForDownload);
// $entityIds = array();
// getEntityIds($soap_resArray, $entityIds);
// var_dump($entityIds);

$sceneIds=array();
foreach ($searchResults->results as $result) {
    $sceneIds[] = $result->entityId;
}
print_r($sceneIds);

foreach($soap_resArray as $key => $value) {
  // echo "$key - $value<br/>";
  if (is_array($value)) {
    foreach($value as $k => $v) {
        // echo "$k - $v<br/>";
        if (is_array($v)) {
          foreach($v as $k1 => $v1) {
            // echo "$k1 - $v1<br/>";
            if ($k1=="entityId") {
                echo "$v1<br/>";
            }
          }
        }         
    }
  }
}



?>