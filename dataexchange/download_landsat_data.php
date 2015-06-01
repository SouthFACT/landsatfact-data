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
	
	//Initialize the database connection
	lsf_db_init();
	$datasetName = "LANDSAT_8";
	$lsf_conn = pg_connect($lsf_database);
	if (!$lsf_conn) {
	  echo "An error occurred on lsf_conn.\n";
	}
	$select_result=pg_query($lsf_conn, "SELECT * FROM vw_last_days_scenes;");
	if  (!$select_result) {
		print_r("query did not execute\n");
	}
	if (pg_num_rows($select_result) > 0) {
		print_r("Matching records found : ".pg_num_rows($select_result)."\n");
		while ($row = pg_fetch_array($select_result)) {
			if (substr($row[0], 0, 3)=="LE7") {
			  $datasetName = "LANDSAT_ETM_SLC_OFF";
			}
			print_r("Downloading " . $row[0]);
			$downloadUrl = getDownloadUrl($datasetName, $client, $apiKey, $row[0]);
			custom_put_contents($downloadUrl->item,'/fsdata1/lsfdata/tarFiles/'.$row[0].'.tar.gz');
			print_r("\n");		  
		}		
	}
	pg_close($lsf_conn);

} catch (Exception $e) {
	die("Error: {$e->getMessage()}\n\n");
}
?>