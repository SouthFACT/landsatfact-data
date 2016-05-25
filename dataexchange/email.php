<?php
/* 
   Purpose: To notify the project email account when a LCV error occurs
   Create : 05/16/2016
   License: This code was developed in the public domain. This code is provided "as is", without warranty of any kind,
	express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement.
	In no event shall the authors be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise,
	arising from, out of or in connection with the software or the use or other dealings in the software. 
*/
// $argv[0] is '/path/to/path/to/script.php'
// The message is the text for the exception
$message = $argv[1];

// In case any of our lines are larger than 70 characters, we should use wordwrap()
$message = wordwrap($message, 70, "\r\n");

// Send
mail('landsatfactmsg@gmail.com', 'LCV error', $message);
?>

