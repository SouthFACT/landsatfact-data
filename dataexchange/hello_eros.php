<?php

//* Get user account info from ini file stored locally
$ini_array = parse_ini_file("config.ini", true);
$soapURL = "https://earthexplorer.usgs.gov/inventory/soap?wsdl" ;
$options = array(
    "trace" => true,
    "encoding" => "utf-8",
);             
$client = new SoapClient($soapURL, $options);

//* The following show the method signature(s):
// var_dump($client->__getFunctions())

//* 1. Login:
try {
    $loginKey = $client->login($ini_array["user_info"]["user"], $ini_array["user_info"]["pass"]);
    // echo $client->__getLastResponse() . "\n";
}
catch (Exception $e) {
    $error_xml =  $client->__getLastRequest() . "\n";
    echo $error_xml;
    echo "\n\n".$e->getMessage();
}

//* 2. Get the available datasets:
//* datasets(string $datasetName, 
//*            Service_Class_Coordinate $lowerLeft, 
//*            Service_Class_Coordinate $upperRight, 
//*            string $startDate, 
//*            string $endDate, 
//*            string $node, 
//*            string $apiKey)
//*Notes: the coordinates are lat,lon format
//*Result of e.g. LANDSAT_ETM_SLC_OFF
// try {
    // $datasets = $client->datasets('','33.69388,-79.44522','35.52052,-76.77163','1/1/2009','1/1/2014','EE',$loginKey);
    // echo $client->__getLastResponse() . "\n";
// }
// catch (Exception $e) {
    // $error_xml =  $client->__getLastRequest() . "\n";
    // echo $error_xml;
    // echo "\n\n".$e->getMessage();
// }

//* 4. Get download options
//*downloadOptions(string $datasetName, 
//*                  string $apiKey, 
//*                  string $node, 
//*                  string $entityId, 
//*                  ArrayOfString $entityIds)
//*Notes: result of E.G. STANDARD, which is the Level 1 Product
// try {
    // $downloadOptions = $client->downloadOptions('LANDSAT_ETM_SLC_OFF',$loginKey,'EE','LE70150362014298EDC00','');
    // echo $client->__getLastResponse() . "\n";
// }
// catch (Exception $e) {
    // $error_xml =  $client->__getLastRequest() . "\n";
    // echo $error_xml;
    // echo "\n\n".$e->getMessage();
// }

//* 4. Get a specific product based on dates
//* ArrayOfString download(string $datasetName, 
//*                            string $apiKey, 
//*                            string $node, 
//*                            ArrayOfString $entityIds, 
//*                            ArrayOfString $products)
//*Notes: 
try {
    $downloadURLs = $client->download('LANDSAT_ETM_SLC_OFF',$loginKey,'EE', array('LE70150362014298EDC00'),array('STANDARD'));
    echo $client->__getLastResponse() . "\n";
}
catch (Exception $e) {
    $error_xml =  $client->__getLastRequest() . "\n";
    echo $error_xml;
    echo "\n\n".$e->getMessage();
}

?>