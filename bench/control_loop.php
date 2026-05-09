<?php

declare(strict_types=1);

require __DIR__ . '/bootstrap.php';

benchmark('control_loop', static function (int $iterations): void {
    $sink = 0;

    for ($i = 0; $i < $iterations; $i++) {
        $sink += ($i & 1);
    }

    if ($sink < 0) {
        echo "";
    }
});
