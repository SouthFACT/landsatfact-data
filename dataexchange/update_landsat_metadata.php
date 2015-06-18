<?php
/* Name: jdmorgan
   Purpose: To download and update latest Landsat scene metadata.
   Create : 04/01/2015
   License: This code was developed in the public domain. This code is provided "as is", without warranty of any kind,
	express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement.
	In no event shall the authors be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise,
	arising from, out of or in connection with the software or the use or other dealings in the software. 
*/

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

function xml_attribute($object, $attribute)
{
    if(isset($object[$attribute]))
        return (string) $object[$attribute];
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
				// metadataUrl
				print_r("\n");
				print_r($response->metadataUrl);
				print_r("\n");
				$fullMetadata = file_get_contents($response->metadataUrl);
				$xmlparser = xml_parser_create();
				xml_parse_into_struct($xmlparser,$fullMetadata,$values);
				xml_parser_free($xmlparser);
				// var_dump($values);
				// Clouds
				// Cloud coverage (percent) of a WRS scene
				// 0.00 - 100.00
				$cc_full = $values[66]['value'];
				print_r("cloud cover : ". $cc_full ."\n");				
				//Data Type Level 1 or data_type_l1 in PGSQL
				$data_type_l1 = $values[48]['value'];
				print_r("data_type_l1 : ". $data_type_l1."\n");				
				// E.g. LE70180342015146EDC00
				print_r("\n");
				print_r($response->entityId);
				print_r("\n");
				// sensor always the same as "OLI_TIRS"
				$sensor = "OLI_TIRS";
				$acquisitionDate = date("Y-m-d", strtotime($response->acquisitionDate));
				print_r($acquisitionDate);
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
					$insert_result = pg_query($lsf_conn, "INSERT INTO landsat_metadata(scene_id,sensor,acquisition_date,browse_url,path,row,cc_full,data_type_l1) 
					  VALUES('".$sceneIds[$i]."','".$sensor."','".$acquisitionDate."','".$response->browseUrl."','".$path."','".$row."','".$cc_full."','".$data_type_l1."');");
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
				// metadataUrl
				print_r("\n");
				print_r($response->metadataUrl);
				print_r("\n");
				$fullMetadata = file_get_contents($response->metadataUrl);
				$xmlparser = xml_parser_create();
				xml_parse_into_struct($xmlparser,$fullMetadata,$values);
				xml_parser_free($xmlparser);
				// var_dump($values);
				
				// Clouds
				// Cloud coverage (percent) of a WRS scene
				// 0.00 - 100.00
				// Sometimes the quad data comes in as PROCESSING REQUIRED
				// For these we will set to 0 for now
				$cc_full = $values[42]['value'];
				print_r("cloud cover : ". $cc_full."\n");					
				// ul is 45
				if ($values[45]['value'] != 'PROCESSING REQUIRED') {
					$cc_quad_ul = $values[45]['value'];
				}
				else {
					$cc_quad_ul = '0.0';
				}
				print_r("ul cloud cover : ". $cc_quad_ul."\n");		
				// ur is 48
				if ($values[48]['value'] != 'PROCESSING REQUIRED') {
					$cc_quad_ur = $values[48]['value'];
				}
				else {
					$cc_quad_ur = '0.0';
				}				
				print_r("ur cloud cover : ". $cc_quad_ur."\n");		
				// ll is 51
				if ($values[51]['value'] != 'PROCESSING REQUIRED') {
					$cc_quad_ll = $values[51]['value'];
				}
				else {
					$cc_quad_ll = '0.0';
				}				
				print_r("ll cloud cover : ". $cc_quad_ll."\n");		
				// lr is 54
				if ($values[54]['value'] != 'PROCESSING REQUIRED') {
					$cc_quad_lr = $values[54]['value'];
				}
				else {
					$cc_quad_lr = '0.0';
				}					
				print_r("lr cloud cover : ". $cc_quad_lr."\n");		
				//Data Type Level 1 or data_type_l1 in PGSQL
				$data_type_l1 = preg_split('/\s+/', $values[60]['value'])[1];
				print_r("data_type_l1 : ". $data_type_l1."\n");
				// E.g. LE70180342015146EDC00
				print_r("\n");
				print_r($response->entityId);
				print_r("\n");
				// sensor always the same as "LANDSAT_ETM_SLC_OFF"
				$sensor = "LANDSAT_ETM_SLC_OFF";
				$acquisitionDate = date("Y-m-d", strtotime($response->acquisitionDate));
				print_r($acquisitionDate);
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
				print_r("\n");
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
					$insert_result = pg_query($lsf_conn, "INSERT INTO landsat_metadata(scene_id,sensor,acquisition_date,browse_url,path,row,cc_full,cc_quad_ul,cc_quad_ur,cc_quad_ll,cc_quad_lr,data_type_l1) 
					  VALUES('".$sceneIds[$i]."','".$sensor."','".$acquisitionDate."','".$response->browseUrl."','".$path."','".$row."','".$cc_full."','".$cc_quad_ul."','".$cc_quad_ur."','".$cc_quad_ll."','".$cc_quad_lr."','".$data_type_l1."');");
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