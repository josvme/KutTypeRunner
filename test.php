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
