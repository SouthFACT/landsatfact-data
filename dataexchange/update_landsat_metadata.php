<?php
include 'usgseros.php';

// Global DB connection variables:
$lsf_database = "";

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

//PGSQL DB 
function lsf_db_init() {
	global $database, $lsf_database;
	$config_info = parse_ini_file("config.ini",true);
	$username = $config_info["pgsql_connection"]["username"];
	$password = $config_info["pgsql_connection"]["password"];
	$host = $config_info["pgsql_connection"]["host"];
	$port = $config_info["pgsql_connection"]["port"];
	$driver = $config_info["pgsql_connection"]["driver"];
	$database = $config_info["pgsql_connection"]["database"];
	$lsf_database = "host=".$host." port=".$port." dbname=".$database." user=".$username." password=".$password."";
}

try{
	// From datasetFields() on SOAP API
	// L8 path/row/cc fieldId's: 10036/10038/10037
	// L7 path/row/cc fieldId's: 3947/3948/3968
	// Where cc is cloud cover and 0 is Less than 10%
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
											'value' => '0'
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
											'value' => '0'
										)											
								)
						);							
	//Initialize the database connection
	lsf_db_init();
	
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
			print_r(" getting metadata... \n");
			//Update landsat_metadata table accordingly
			$metadataResult = getDatasetMetadata($client, $datasetName, "EE", $sceneIds[$i], $apiKey);
			foreach ($metadataResult as $response) {
				// E.g. LE70180342015146EDC00
				print_r("\n");
				print_r($response->entityId);
				print_r("\n");
				// sensor not available on metadata result
				// "OLI_TIRS"
				$acquireDate = date("Y-m-d", strtotime($response->acquisitionDate));
				print_r($acquireDate);
				print_r("\n");
				print_r($response->browseUrl);
				print_r("\n");
				// path
				$path = substr($response->entityId, 3, 3);
				print_r($path);
				print_r("\n");
				// row
				$row = substr($response->entityId, 6, 3);
				print_r($row."\n");
				//type not available on metadata result

				//Update landsat_metadata:
				$lsf_conn = pg_connect($lsf_database);
				if (!$lsf_conn) {
				  echo "An error occurred on lsf_conn.\n";
				}
				$select_result=pg_query($lsf_conn, "SELECT * FROM landsat_metadata WHERE scene_id='".$sceneIds[$i]."';");
				if  (!$select_result) {
					print_r("query did not execute\n");
				}
				if (pg_num_rows($select_result) > 0) {
					print_r("Matching records found : ".pg_num_rows($select_result)."\n");
				}
				else {
					print_r("inserting record...\n");
					$insert_result = pg_query($lsf_conn, "INSERT INTO landsat_metadata(scene_id,acquire_date,browse_url,path,row) 
					  VALUES('".$sceneIds[$i]."','".$acquireDate."','".$response->browseUrl."','".$path."','".$row."');");
				}			
				pg_close($lsf_conn);
				//End of update landsat_metadata
			}			
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
			//Get Metadata and update table accordingly
			print_r(" getting metadata... \n");
			//Update landsat_metadata table accordingly
			$metadataResult = getDatasetMetadata($client, $datasetName, "EE", $sceneIds[$i], $apiKey);
			foreach ($metadataResult as $response) {
				// E.g. LE70180342015146EDC00
				print_r("\n");
				print_r($response->entityId);
				print_r("\n");
				// sensor not available on metadata result
				// "OLI_TIRS"
				$acquireDate = date("Y-m-d", strtotime($response->acquisitionDate));
				print_r($acquireDate);
				print_r("\n");
				print_r($response->browseUrl);
				print_r("\n");
				// path
				$path = substr($response->entityId, 3, 3);
				print_r($path);
				print_r("\n");
				// row
				$row = substr($response->entityId, 6, 3);
				print_r($row);
				//type not available on metadata result
				
				//Update landsat_metadata:
				$lsf_conn = pg_connect($lsf_database);
				if (!$lsf_conn) {
				  echo "An error occurred on lsf_conn.\n";
				}
				$select_result=pg_query($lsf_conn, "SELECT * FROM landsat_metadata WHERE scene_id='".$sceneIds[$i]."';");
				if  (!$select_result) {
					print_r("query did not execute\n");
				}
				if (pg_num_rows($select_result) > 0) {
					print_r("Matching records found : ".pg_num_rows($select_result)."\n");
				}
				else {
					print_r("inserting record...\n");
					$insert_result = pg_query($lsf_conn, "INSERT INTO landsat_metadata(scene_id,acquire_date,browse_url,path,row) 
					  VALUES('".$sceneIds[$i]."','".$acquireDate."','".$response->browseUrl."','".$path."','".$row."');");
				}			
				pg_close($lsf_conn);
				//End of update landsat_metadata								
			}				
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