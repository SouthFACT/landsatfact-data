<?php
include '../dataexchange/usgseros.php';

try{
    // echo "\nRunning Script...\n\n";
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

    //* Login
    $apiKey = loginLandsatFACT($client, $ini_array); 
    $node = 'EE';

	//* Search function should be next to get a list of entityIDs
    //* Potential datasets: LANDSAT_8
    $datasetName = $_POST['datasetName'];
    $lowerLeft = (object) array('latitude' => $_POST['lat_ll'], 'longitude' => $_POST['lng_ll']);
    $upperRight = (object) array('latitude' => $_POST['lat_ur'], 'longitude' => $_POST['lng_ur']);
    $startDate = $_POST['startDate'];  
    $endDate = $_POST['endDate'];  
    $searchResults = getDatasetsForDownload($datasetName, $client, $apiKey, $lowerLeft, $upperRight, $startDate, $endDate);  
    // echo $datasetsForDownload;

    //Did we find anything?
    if ($searchResults->numberReturned > 0) {
        $sceneIds=array();
        foreach ($searchResults->results as $result) {
            $sceneIds[] = $result->entityId;
            $downloadUrls[] = $result->dataAccessUrl;
        }
        // print_r($sceneIds);
        // print_r($downloadUrls);
    }

    //Print out sceneIds as url's:
    for ($i = 0; $i < count($sceneIds); ++$i) {
        echo "<a href='{$downloadUrls[$i]}'>{$sceneIds[$i]}</a>";
        echo "</br>";
        // print_r($sceneIds[$i]);
        // print_r($downloadUrls[$i]);
    }
	//Logout so the API Key cannot be used anymore
	if ($client->logout($apiKey)) {
		// echo "Logged Out\n\n";
	} else {
		// echo "Logout Failed\n\n";
	}    
} catch (Exception $e) {
	die("Error: {$e->getMessage()}\n\n");
}
?>