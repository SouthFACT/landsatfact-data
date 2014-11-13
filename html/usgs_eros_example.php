<?php
/**
 * USGS/EROS Inventory Service Example
 * PHP - SOAP API
 * 
 * Script Last Modified: 10/29/2014
 * 
 * Note: PHP SOAP Extension is required
 * Note: This example does not include any error handling!
 *  	 Any request can throw a SoapFault and will include a faultcode and message.
 * 		 These types of checks could be done by writing a wrapper class for SoapClient
 * Usage: php download_data.php --username foo --password bar
 */

//NOTE :: Passing credentials over a command line arguement is not considered secure
//			and is used only for the purpose of being example - credential parameters
//			should be gathered in a more secure way for production usage
//Define the command line arguements
$options = getopt('', array('username:', 'password:'));

//Make sure the input is there
$username = '';
if (isset($options['username'])) {
	$username = $options['username'];
} else {
	die("Username is Required.\n\n");
}

$password = '';
if (isset($options['password'])) {
	$password = $options['password'];
} else {
	die("Password is Required.\n\n");
}

try{
	echo "\nRunning Script...\n\n";
	
	$serviceUrl = 'earthexplorer.usgs.gov/inventory/soap?wsdl';
	$options = array(
	    'trace' => true,
	    'encoding' => 'utf-8',
	);
	
	//Create an SSL version for authentication
	$sslClient = new SoapClient("https://{$serviceUrl}", $options);

	//Create a non-SSL version for non-authentication requests
	$client = new SoapClient("http://{$serviceUrl}", $options);
	
	//Login and store the API Key
	$apiKey = $sslClient->login($username, $password);
	
	echo "API Key: {$apiKey}\n";

	//Search for datasets
	$lowerLeft = (object) array('latitude' => 15.4060, 'longitude' => 79.0082);
	$upperRight = (object) array('latitude' => 17.9578, 'longitude' => 80.6781);
	$startDate = '2013-12-02T00:00:00Z'; //Time is ignored, but just in case it gets implemented in the future...
	$endDate = '2013-12-02T23:59:59Z'; //Time is ignored, but just in case it gets implemented in the future...
	$node = 'EE';
	
	echo "Searching datasets...\n";
	$datasets = $client->datasets('L8', $lowerLeft, $upperRight, $startDate, $endDate, $node, $apiKey);
	echo 'Found ' . count($datasets) . " datasets\n";
	
	foreach ($datasets as $dataset) {
		
		if ($dataset->supportDownload === true) {
			//Because I've ran this before I know that I want LANDSAT_8, I don't want to download anything I don't
			//want so we will skip any other datasets that might be found, logging it incase I want to look into
			//downloading that data in the future.
			if ($dataset->datasetName != 'LANDSAT_8') {
				echo "Found dataset {$dataset->datasetName}, but skipping it.\n";
				continue;
			}
			
			//I don't want to limit my results, but using the datasetfields request, you can
			//find additional fields to filter on
			$additionalCritiera = null;
			$maxResults = 2;
			$sortOrder = 'ASC';
			$startingNumber = 1;
			
			//Now I need to run a search to find data to download
			echo "Searching...\n\n";
			$searchResults = $client->search($dataset->datasetName, $lowerLeft, $upperRight, $startDate, $endDate, 
												$additionalCritiera, $maxResults, $startingNumber, $sortOrder, $node, $apiKey);
			
			//Did we find anything?
			if ($searchResults->numberReturned > 0) {
				//Aggregate a list of scene ids
				$sceneIds = array();									
				foreach ($searchResults->results as $result) {
					//Add this scene to the list I would like to download
					$sceneIds[] = $result->entityId;
				}
				
				//Find the download options for these scenes
				//NOTE :: Remember the scene list cannot exceed 50,000 items!
				$downloadOptions = $client->downloadOptions($dataset->datasetName, $apiKey, $node, null, $sceneIds);
				
				//Iterate over the download options
				foreach ($downloadOptions as $sceneLevel) {
					//Aggregate a list of available products
					$products = array();
					foreach ($sceneLevel->downloadOptions as $product) {
						//Make sure the product is available for this scene
						if ($product->available === true) {
							$products[] = $product->downloadCode;
						}
					}
					
					//Did we find products?
					if (count($products) > 0) {
						//Call the download to get the direct download urls
						$downloadUrls = $client->download($dataset->datasetName, $apiKey, $node, array($sceneLevel->entityId), $products);

						//Loop through and download the data
						foreach ($downloadUrls->item as $url) {
							//TODO :: Implement a downloading routine
							echo "DOWNLOAD: {$url}\n";
						}
					}
				}
			} else {
				echo "Search found no results.\n";
			}
		} else {
			echo "{$dataset->datasetName} does not support downloading.\n";
		}
	}

	//Logout so the API Key cannot be used anymore
	if ($sslClient->logout($apiKey)) {
		echo "Logged Out\n\n";
	} else {
		echo "Logout Failed\n\n";
	}
} catch (Exception $e) {
	die("Error: {$e->getMessage()}\n\n");
}
?>