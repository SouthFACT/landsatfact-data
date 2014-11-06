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


$loginKey = loginLandsatFACT($client, $ini_array); 

$availableDatasetsXML = getAvailableDatasets($client, $loginKey);
echo $availableDatasetsXML

// Search function should be next to get a list of entityIDs
    
    

?>
