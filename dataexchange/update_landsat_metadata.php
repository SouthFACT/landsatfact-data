<?php
include 'usgseros.php';

function search($array, $key, $value)
{
    $results = array();
    if (is_array($array)) {
        if (isset($array[$key]) && $array[$key] == $value) {
            $results[] = $array;
        }
        foreach ($array as $subarray) {
            $results = array_merge($results, search($subarray, $key, $value));
        }
    }
    return $results;
}

try{
	// From datasetFields() on SOAP API
	// L8 path/row/cc fieldId's: 10036/10038/10037
	// L7 path/row/cc fieldId's: 3947/3948/3968
	$L8criteriaArray = (object)array(
							'filterType' => 'and',
							'childFilters' => array
								(
									(object)array
										(
											'fieldId' => 10036,
											'filterType' => 'between',
											'firstValue' => '13',
											'secondValue' => '33'
										),
									(object)array
										(
											'fieldId' => 10038,
											'filterType' => 'between',
											'firstValue' => '33',
											'secondValue' => '43'
										),
									(object)array
										(
											'fieldId' => 10037,
											'filterType' => 'value',
											'value' => '8'
										)										
								)
						);	
	$L7criteriaArray = (object)array(
							'filterType' => 'and',
							'childFilters' => array
								(
									(object)array
										(
											'fieldId' => 3947,
											'filterType' => 'between',
											'firstValue' => '13',
											'secondValue' => '33'
										),
									(object)array
										(
											'fieldId' => 3948,
											'filterType' => 'between',
											'firstValue' => '33',
											'secondValue' => '43'
										),
									(object)array
										(
											'fieldId' => 3968,
											'filterType' => 'value',
											'value' => '8'
										)											
								)
						);							
	$ini_array = parse_ini_file("config.ini", true);
    $soapURL = "https://earthexplorer.usgs.gov/inventory/soap?wsdl" ;
    $options = array(
        "trace" => true,
        "encoding" => "utf-8",
    );             
    $client = new SoapClient($soapURL, $options);

    //* Login
    $apiKey = loginLandsatFACT($client, $ini_array); 
    // print_r("apikey: ".$apiKey."\n");
	$node = 'EE';

	// Get current date and previous date
	date_default_timezone_set('US/Eastern');
	$currDate = isset($_GET['date']) ? $_GET['date'] : date('Y-m-d');
	$doy = date('z')+1;
	print_r("doy: ".$doy."\n");
	print('Current Date: ' . $currDate ."\n");
	$prevDate = date('Y-m-d', strtotime($currDate .' -1 day'));
	print('Previous Date: ' . $prevDate ."\n");

	//* Search function should be next to get a list of entityIDs
    // We may want to only utilize the path/rows to identify the scenes of interest, 
	// instead of the lat/lon bbox // We may want to only utilize the path/rows to identify the scenes of interest, 
	// instead of the lat/lon bbox
	// $lowerLeft = (object) array('latitude' => '23.118', 'longitude' => '-109.817');
    // $upperRight = (object) array('latitude' => '39.840', 'longitude' => '-72.420');
    $lowerLeft = null;
    $upperRight = null;	
    $startDate = (string)$prevDate."T00:00:00Z"; 
	print_r("startDate: ".$startDate."\n");	
    $endDate = (string)$currDate."T00:00:00Z";  
	print_r("endDate: ".$endDate."\n");	


	// Get the list of LSF-relevant pathrows into array--------------------------------------
	$csv = array_map('str_getcsv', file('landsat_quads.csv'));	
	$keys = array_shift($csv);
	foreach ($csv as $i=>$row) {
		$csv[$i] = array_combine($keys, $row);
	}
	// End Get the list of LSF-relevant pathrows---------------------------------------------
	
    //* Potential datasets: 
		// LANDSAT_8 - L8 OLI/TIRS
		// LANDSAT_ETM - Landsat 7 Enhanced Thematic Mapper Scan Line Corrector On
		// LANDSAT_ETM_SLC_OFF - Landsat 7 Enhanced Thematic Mapper Scan Line Corrector Off 
    // First lets do L8:-----------------------------------------------
	$datasetName = "LANDSAT_8";
	print_r("Doing LANDSAT_8....\n");	
    $searchResults = getDatasetsForDownload($datasetName, $client, $apiKey, $lowerLeft, $upperRight, $startDate, $endDate, $L8criteriaArray);  
	$sceneIds=array();
	// var_dump($searchResults);
    //Loop through and populate arrays for scene's that are found
    if ($searchResults->numberReturned > 0) {
        foreach ($searchResults->results as $result) {
            $sceneIds[] = $result->entityId;
            // $downloadUrls[] = $result->dataAccessUrl;
        }
        // print_r($sceneIds);
        // print_r($downloadUrls);		
    }
    //Print out sceneIds and url's while populating the $downloadUrls array()
    // e.g. LC80190382015145LGN00
	for ($i = 0; $i < count($sceneIds); ++$i) {
		print_r("scene ID " . $sceneIds[$i]);
		// print_r(" checking for wrs2_code " . substr($sceneIds[$i], 4, 5));
		// print_r( count(search($csv, 'wrs2_code', substr($sceneIds[$i], 4, 5))) );
		if (count(search($csv, 'wrs2_code', substr($sceneIds[$i], 4, 5)))>0) {
			print_r(" getting metadata... ");
		}
		print_r("\n");
    }
	
	
	// End L8 ---------------------------------------------------------
	
	
	// Now do L7: :-----------------------------------------------
	$datasetName = "LANDSAT_ETM_SLC_OFF";
	print_r("Doing LANDSAT_ETM_SLC_OFF....\n");	
    $searchResults = getDatasetsForDownload($datasetName, $client, $apiKey, $lowerLeft, $upperRight, $startDate, $endDate, $L7criteriaArray);  
	$sceneIds=array();
	// var_dump($searchResults);
    //Loop through and populate arrays for scene's that are found
    if ($searchResults->numberReturned > 0) {
        foreach ($searchResults->results as $result) {
            $sceneIds[] = $result->entityId;
            // $downloadUrls[] = $result->dataAccessUrl;
        }
        // print_r($sceneIds);
        // print_r($downloadUrls);		
    }
    //Print out sceneIds and url's while populating the $downloadUrls array()
    for ($i = 0; $i < count($sceneIds); ++$i) {
		print_r("scene ID " . $sceneIds[$i]);
		if (count(search($csv, 'wrs2_code', substr($sceneIds[$i], 4, 5)))>0) {
			print_r(" getting metadata... ");
		}		
		print_r("\n");
    }	
	// End L7 ---------------------------------------------------------
	
	
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