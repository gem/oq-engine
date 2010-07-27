<?php

// The data arrives in the $_POST scope just like an old-school form post.

/*
Validate the data. Normally, these kinds of tests would be done on the client side
as well as here but for this sample code these will do to raise errors.
*/

$Err = "";

if (trim($_POST['scenario list 1'] == "")) {
	
}

if (trim($_POST['Population'] == "")) {
	
}

if ($Err == "") {
	// OK. No validation errors. Update your database table or whatever you need to do with the data here
	
	// Set the json to return "success" 
	$result = "{success: true}"; 

} else {
	// Errors. Set the json to return the fieldnames and the associated error messages
	$result = '{success: false, errors:{'.$Err.'} }'; // Return the error message(s)
}

/* Example results:
$result = '{success: false, errors:{firstname:"Must not be empty, company:"Must not be empty"} }';
$result = '{success: true}';
*/
echo $result;
?>
