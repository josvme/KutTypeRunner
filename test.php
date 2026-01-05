<?php

namespace Me;

class T {
    function __construct() {
    }

    function test_function($arg1, $arg2) {
        return "Inside test_function";
    }
}

$t = new T();
$t->test_function("hello", 123);
$t->test_function($t, new \stdClass());

// This shouldn't be captured
$n = ltrim(" hello");
var_dump($n);

// Function we defined
var_dump(type_runner("hello"));