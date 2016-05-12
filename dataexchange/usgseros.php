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
        $maxResults = 5000;
        $sortOrder = 'ASC';
        $months = array();
		// $sortOrder = 'DESC';
        $startingNumber = 1;
        
	$searchResults = $client->search($datasetName, $lowerLeft, $upperRight, $startDate, $endDate, $months,$additionalCritiera, $maxResults, $startingNumber, $sortOrder, $node, $apiKey);
        print_r( $lowerLeft);
        print_r($upperRight);

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
        $acct_id = array();
        $entityIds = json_encode($acct_id);
        $datasetMetadata = $client->metadata($datasetName, $node, $entityId, $entityIds, $apiKey);
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



//* ArrayOfString download(string $datasetName,
//*                            string $apiKey,
//*                            string $node,
//*                            ArrayOfString $entityIds,
//*                            ArrayOfString $products)
//*Notes:
function getOrderScene($datasetName, $client, $apiKey, $sceneID) {
    print_r(" apikey getOrderScene:" . $apiKey . ".\n");
    try {
        $productCode = $client->getOrderProducts($apiKey,$datasetName,'EE', $sceneID,array('STANDARD'));
        
        //Aggregate a list of available products
        $products = array();
        //check if orders
        $ifOrders = false;
        $downloadUrl = '';

        //Iterate over the download options
        foreach ($productCode as $sceneLevel) {
          print_r("\n Setting up Order for: " .  $sceneLevel->entityId . ".\n");

          //find available Products for each scene
          foreach ($sceneLevel->availableProducts as $product) {


            //on procede when cost is $0 and level 1
            if($product->price == 0 and substr($product->productCode, 0, 1) != 'W'){

              print_r("  Order Product Code: " .  $product->productCode . ".\n");

              //check for produc medias
              foreach ($product->outputMedias as $outputMedias) {

                //only need to order products that are marked download
                if($outputMedias === 'DWNLD'){

                  // update order basket
                   $client->updateOrderScene($apiKey,'EE',$datasetName,$sceneID,$product->productCode ,'None',$outputMedias);
                   $items = $client->itemBasket($apiKey);

                   //submit order for each item in the basket
                   foreach ($items->orderItemBasket as $orderItem) {

                     //get orders
                     $orders[] = $orderItem->orderScenes;

                     //make sure there are orders in the basket
                     if(count($orders)>0){
                       print_r("     Submitting Order.\n");

                       //order the in the baske items
                       $client->submitOrder($apiKey,'EE');
                       $ifOrders = (count($orders)>0);
                     }
                   }
                }
              }
            }
          }
          print_r("\n");
        }

        if($ifOrders){
          //see if order is ready
         $downloadUrl = $client->download($datasetName,$apiKey,'EE', array($sceneID),array('STANDARD'));

         $time = 0;

         //keep check order until the download is ready
         while (empty($downloadUrl->item)) {

           print_r("     Checking Order For Scene: $sceneID - Seconds Elapased: $time\n");

           $downloadUrl = $client->download($datasetName,$apiKey,'EE', array($sceneID),array('STANDARD'));

           //pause 20 seconds so we do not slam the server with requests seems to take a few minutes
           sleep(20);
           $time = $time+20;
           //break the loop after 3.5 hours
           if ($time > 12601){
             print_r("     Exceeded 3.5 hours. ($time seconds)\n");
             break;
           }
         }
       }
    //return the url when ready
		return $downloadUrl;
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
