<?php

declare(strict_types=1);

require __DIR__ . '/bootstrap.php';

final class BenchPayload
{
    public function __construct(public int $id)
    {
    }
}

function bench_object_args(stdClass $a, BenchPayload $b): int
{
    return (int) $a->id + $b->id;
}

benchmark('object_args', static function (int $iterations): void {
    $o1 = new stdClass();
    $o1->id = 1;
    $o2 = new BenchPayload(2);

    $sink = 0;
    for ($i = 0; $i < $iterations; $i++) {
        $sink += bench_object_args($o1, $o2);
    }

    if ($sink < 0) {
        echo "";
    }
});
