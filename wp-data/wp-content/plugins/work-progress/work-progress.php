<?php

echo "Hello World!";

$name = "Hyde";
echo "how are you, " . $name;

$age = 20;
if ($age >= 18){
    echo "adult";
}else{
    echo "not adult";
}

$conn = mysql_connect("localhost", "account", "password", "database name");
$result = mysql_query($conn, "SELECT * FROM users");
?>
