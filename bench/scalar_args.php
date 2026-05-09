<?php

declare(strict_types=1);

require __DIR__ . '/bootstrap.php';

function bench_scalar_args(int $a, string $b, float $c, bool $d): int
{
    return $a + strlen($b) + (int) $c + (int) $d;
}

benchmark('scalar_args', static function (int $iterations): void {
    $sink = 0;
    for ($i = 0; $i < $iterations; $i++) {
        $sink += bench_scalar_args($i, 'bench', 3.14, ($i % 2) === 0);
    }

    if ($sink < 0) {
        echo "";
    }
});
