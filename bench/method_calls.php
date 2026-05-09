<?php

declare(strict_types=1);

require __DIR__ . '/bootstrap.php';

final class BenchMethods
{
    public function instanceCall(int $value): int
    {
        return $value + 1;
    }

    public static function staticCall(int $value): int
    {
        return $value + 1;
    }
}

benchmark('method_instance', static function (int $iterations): void {
    $receiver = new BenchMethods();
    $sink = 0;

    for ($i = 0; $i < $iterations; $i++) {
        $sink += $receiver->instanceCall($i);
    }

    if ($sink < 0) {
        echo "";
    }
});

benchmark('method_static', static function (int $iterations): void {
    $sink = 0;

    for ($i = 0; $i < $iterations; $i++) {
        $sink += BenchMethods::staticCall($i);
    }

    if ($sink < 0) {
        echo "";
    }
});
