<?php
$url = "http://www.w3schools.com/webservices/tempconvert.asmx?WSDL";
$client = new SoapClient($url);

$result = $client->CelsiusToFahrenheit(array('Celsius' => '10'));

var_dump($result);

echo $result->CelsiusToFahrenheitResult . "\n";

?>