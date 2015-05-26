<?php
$xmlstr = <<<XML
<?xml version='1.0' standalone='yes'?>
<additionalCriteria>
	<filterType>or</filterType>
	<childFilters>
		<item>
			<filterType>and</filterType>
			<childFilters>
				<item>
					<fieldId>10036</fieldId>
					<filterType>between</filterType>
					<firstValue>10</firstValue>
					<secondValue>50</secondValue>
				</item>
				<item>
					<fieldId>10038</fieldId>
					<filterType>between</filterType>
					<firstValue>10</firstValue>
					<secondValue>50</secondValue>
				</item>
			</childFilters>
		</item>
		<item>
			<filterType>and</filterType>
			<childFilters>
				<item>
					<fieldId>10036</fieldId>
					<filterType>between</filterType>
					<firstValue>60</firstValue>
					<secondValue>100</secondValue>
				</item>
				<item>
					<fieldId>10038</fieldId>
					<filterType>between</filterType>
					<firstValue>60</firstValue>
					<secondValue>100</secondValue>
				</item>
			</childFilters>
		</item>
	</childFilters>
</additionalCriteria>
XML;

$simpleXML = new SimpleXMLElement($xmlstr);
// echo $movies->movie[0]->plot;
// print_r($movies);
$array = (array)$simpleXML;
print_r($array);
?>