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
	// Set umask so that whoever is running the script 
	// downloads the files with the correct permissions
	$oldUMASK = umask(0002);	
	
	$in_scene_id = $argv[1];
    print_r("downloading...");
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

	//Initialize the database connection
	lsf_db_init();
	$lsf_conn = pg_connect($lsf_database);
	if (!$lsf_conn) {
	  echo "An error occurred on lsf_conn.\n";
	}

	$datasetName = "LANDSAT_8";
	if (substr($in_scene_id, 0, 3)=="LE7") {
	  $datasetName = "LANDSAT_ETM_SLC_OFF";
	}
	print_r("Downloading " . $in_scene_id);
	print_r(" with dataset " . $datasetName);
	if (file_exists('/fsdata1/lsfdata/tarFiles/'.$in_scene_id.'.tar.gz')) {
		echo "\n The file already exists";
	} else {
		$downloadUrl = getDownloadUrl($datasetName, $client, $apiKey, $in_scene_id);
		print_r("\n downloadUrl->item :".$downloadUrl->item);
		custom_put_contents($downloadUrl->item,'/fsdata1/lsfdata/tarFiles/'.$in_scene_id.'.tar.gz');
	}						
	print_r("\n");		  
	pg_close($lsf_conn);
	// add back original umask
	umask($oldUMASK);	
} catch (Exception $e) {
	die("Error: {$e->getMessage()}\n\n");
}
?>