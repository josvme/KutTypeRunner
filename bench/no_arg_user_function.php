<?php

declare(strict_types=1);

require __DIR__ . '/bootstrap.php';

function bench_no_arg_function(): int
{
    return 1;
}

benchmark('no_arg_user_function', static function (int $iterations): void {
    $sink = 0;
    for ($i = 0; $i < $iterations; $i++) {
        $sink += bench_no_arg_function();
    }

    if ($sink < 0) {
        echo "";
    }
});
