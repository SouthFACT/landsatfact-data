<?php
include 'usgseros.php';

function custom_put_contents($source_url='',$local_path=''){
	// This is a custom function to get around a file size download 
	// limit inherent within the PHP configuration.
	// see http://stackoverflow.com/questions/12264253/allowed-memory-size-of-134217728-bytes-exhausted/29236639#29236639
    $time_limit = ini_get('max_execution_time');
    $memory_limit = ini_get('memory_limit');
    set_time_limit(0);
    ini_set('memory_limit', '-1');      
    $remote_contents=file_get_contents($source_url);
    $response=file_put_contents($local_path, $remote_contents);
    set_time_limit($time_limit);
    ini_set('memory_limit', $memory_limit); 
    return $response;
}

try{
    $ini_array = parse_ini_file("config.ini", true);
    $soapURL = "https://earthexplorer.usgs.gov/inventory/soap?wsdl" ;
    $options = array(
        "trace" => true,
        "encoding" => "utf-8",
    );             
    $client = new SoapClient($soapURL, $options);

    //* Login
    $apiKey = loginLandsatFACT($client, $ini_array); 
    $node = 'EE';

	//Delete any of the old downloaded tars
	print("Delete old tars...\n");
	array_map('unlink', glob("/fsdata1/lsfdata/tarFiles/*.gz"));
	
	// Get current date and previous date
	date_default_timezone_set('US/Eastern');
	$currDate = isset($_GET['date']) ? $_GET['date'] : date('Y-m-d');
	$doy = date('z')+1;
	print_r("doy: ".$doy."\n");
	print('Current Date: ' . $currDate ."\n");
	$prevDate = date('Y-m-d', strtotime($currDate .' -1 day'));
	print('Previous Date: ' . $prevDate ."\n");

	//* Search function should be next to get a list of entityIDs
    //* Potential datasets: LANDSAT_8
    $datasetName = "LANDSAT_8";
    $lowerLeft = (object) array('latitude' => '23.118', 'longitude' => '-109.817');
    $upperRight = (object) array('latitude' => '39.840', 'longitude' => '-72.420');
    // $startDate = "2015-05-05T00:00:00Z";  
    // $endDate = "2015-05-06T00:00:00Z";  
    $startDate = (string)$prevDate."T00:00:00Z"; 
	print_r("startDate: ".$startDate."\n");	
    $endDate = (string)$currDate."T00:00:00Z";  
	print_r("endDate: ".$endDate."\n");	
    $searchResults = getDatasetsForDownload($datasetName, $client, $apiKey, $lowerLeft, $upperRight, $startDate, $endDate);  
	// var_dump($searchResults);
    //Loop through and populate arrays for scene's that are found
    if ($searchResults->numberReturned > 0) {
        $sceneIds=array();
        foreach ($searchResults->results as $result) {
            $sceneIds[] = $result->entityId;
            // $downloadUrls[] = $result->dataAccessUrl;
        }
        // print_r($sceneIds);
        // print_r($downloadUrls);		
    }

    //Print out sceneIds and url's while populating the $downloadUrls array()
    for ($i = 0; $i < count($sceneIds); ++$i) {
        // echo "<a href='{$downloadUrls[$i]}'>{$sceneIds[$i]}</a>";
        // echo "</br>";
		print_r("Downloading " . $sceneIds[$i]);
		$downloadUrl = getDownloadUrl($datasetName, $client, $apiKey, $sceneIds[$i]);
		custom_put_contents($downloadUrl->item,'/fsdata1/lsfdata/tarFiles/'.$sceneIds[$i].'.tar.gz');
		// $tarDownload = file_get_contents($downloadUrl->item);
		// file_put_contents($sceneIds[$i].'.tar.gz', $tarDownload);			
		print_r("\n");
    }

	
	//Logout so the API Key cannot be used anymore
	if ($client->logout($apiKey)) {
		print_r("Logged Out\n\n");
	} else {
		print_r("Logout Failed\n\n");
	}    
} catch (Exception $e) {
	die("Error: {$e->getMessage()}\n\n");
}
?>