<?php

//* Login:
function loginLandsatFACT($client, $ini_array) {
    try {
        $loginKey = $client->login($ini_array["user_info"]["user"], $ini_array["user_info"]["pass"]);
        // echo $client->__getLastResponse() . "\n";
        return $loginKey;
    }
    catch (Exception $e) {
        $error_xml =  $client->__getLastRequest() . "\n";
        echo $error_xml;
        echo "\n\n".$e->getMessage();
    }
}

//* Get scenes for download by dataSet
//*search(string $datasetName, 
//*                  Service_Class_Coordinate $lowerLeft, 
//*                  Service_Class_Coordinate $upperRight, 
//*                  string $startDate, 
//*                  string $endDate, 
//*                  UNKNOWN $additionalCriteria, 
//*                  int $maxResults, 
//*                  int $startingNumber, 
//*                  string $sortOrder, 
//*                  string $node, 
//*                  string $apiKey)
//*Notes: result of E.G. STANDARD, which is the Level 1 Product
//*       Sort order must be ASC or DESC.
// 36.508381, -76.553009
function getDatasetsForDownload($datasetName, $client, $apiKey, $lowerLeft, $upperRight, $startDate, $endDate, $criteriaArray) {
    try {
    
        //Search for datasets
        // $lowerLeft = (object) array('latitude' => 33.93, 'longitude' => -79.40);
        // $upperRight = (object) array('latitude' => 35.27101, 'longitude' => -76.88);
        // $startDate = '2013-08-05T00:00:00Z'; //Time is ignored, but just in case it gets implemented in the future...
        // $endDate = '2013-09-05T23:59:59Z'; //Time is ignored, but just in case it gets implemented in the future...
        $node = 'EE';    
        // $additionalCritiera = null;
		$additionalCritiera = $criteriaArray; 
        $maxResults = 100;
        $sortOrder = 'ASC';
		// $sortOrder = 'DESC';
        $startingNumber = 1;
		$searchResults = $client->search($datasetName, $lowerLeft, $upperRight, $startDate, $endDate, 
												$additionalCritiera, $maxResults, $startingNumber, $sortOrder, $node, $apiKey);
        // echo $client->__getLastRequest() . "\n";
        // return $client->__getLastResponse() . "\n";
        return $searchResults;
    }
    catch (Exception $e) {
        $error_xml =  $client->__getLastRequest() . "\n";
        echo $error_xml;
        echo "\n\n".$e->getMessage();
    }
}

// /*
// ArrayOfService_Inventory_InventoryScene metadata(string $datasetName, 
                                            // string $node, 
                                            // string $entityId, 
                                            // ArrayOfString $entityIds, 
                                            // string $apiKey)
// */
function getDatasetMetadata($client, $datasetName, $node, $entityId, $apiKey) {
    try {
        $datasetMetadata = $client->metadata($datasetName, $node, $entityId, $apiKey);
        // return $client->__getLastResponse() . "\n";
		return $datasetMetadata;
    }
    catch (Exception $e) {
        $error_xml =  $client->__getLastRequest() . "\n";
        echo $error_xml;
        echo "\n\n".$e->getMessage();
    }
}

//* ArrayOfString download(string $datasetName, 
//*                            string $apiKey, 
//*                            string $node, 
//*                            ArrayOfString $entityIds, 
//*                            ArrayOfString $products)
//*Notes: 
function getDownloadUrl($datasetName, $client, $apiKey, $sceneID) {
    try {
        // $downloadUrls = $client->download($datasetName, $apiKey, 'EE', array($sceneLevel->entityId), $products);
        $downloadUrl = $client->download($datasetName,$apiKey,'EE', array($sceneID),array('STANDARD'));
		return $downloadUrl;
        // return $client->__getLastResponse() . "\n";
    }
    catch (Exception $e) {
        $error_xml =  $client->__getLastRequest() . "\n";
        echo $error_xml;
        echo "\n\n".$e->getMessage();
    }
}


// //* Get the available datasets:
// //* datasets(string $datasetName, 
// //*            Service_Class_Coordinate $lowerLeft, 
// //*            Service_Class_Coordinate $upperRight, 
// //*            string $startDate, 
// //*            string $endDate, 
// //*            string $node, 
// //*            string $apiKey)
// //*Notes: the coordinates are lat,lon format
// //*Result of ...
// function getAvailableDatasetNames($datasetName, $client, $loginKey) {
    // try {
        // $datasets = $client->datasets($datasetName, array('latitude' => '34.36','longitude' => '-79.31'), array('latitude' => '34.36','longitude' => '-79.31'),'2013-08-05','2013-09-05','EE',$loginKey);
        // // echo $client->__getLastRequest() . "\n";
        // return $client->__getLastResponse() . "\n";
    // }
    // catch (Exception $e) {
        // $error_xml =  $client->__getLastRequest() . "\n";
        // echo $error_xml;
        // echo "\n\n".$e->getMessage();
    // }
// }

//* Get download options
//*downloadOptions(string $datasetName, 
//*                  string $apiKey, 
//*                  string $node, 
//*                  string $entityId, 
//*                  ArrayOfString $entityIds)
//*Notes: result of E.G. STANDARD, which is the Level 1 Product
// try {
    // $downloadOptions = $client->downloadOptions('LANDSAT_ETM_SLC_OFF',$loginKey,'EE','LC80150362013239LGN00','');
    // echo $client->__getLastResponse() . "\n";
// }
// catch (Exception $e) {
    // $error_xml =  $client->__getLastRequest() . "\n";
    // echo $error_xml;
    // echo "\n\n".$e->getMessage();
// }



?>