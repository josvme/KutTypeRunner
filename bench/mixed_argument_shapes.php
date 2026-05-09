<?php

declare(strict_types=1);

require __DIR__ . '/bootstrap.php';

final class MixedPayload
{
    public function __construct(public int $id)
    {
    }
}

function bench_mixed_args(mixed $a, mixed $b): int
{
    if (is_int($a) && is_int($b)) {
        return $a + $b;
    }

    if (is_string($a) && is_string($b)) {
        return strlen($a) + strlen($b);
    }

    if (is_object($a) && is_object($b) && isset($a->id, $b->id)) {
        return (int) $a->id + (int) $b->id;
    }

    return 0;
}

benchmark('mixed_argument_shapes', static function (int $iterations): void {
    $o1 = new stdClass();
    $o1->id = 3;
    $o2 = new MixedPayload(4);

    $sink = 0;
    for ($i = 0; $i < $iterations; $i++) {
        $mod = $i % 3;
        if ($mod === 0) {
            $sink += bench_mixed_args($i, $i + 1);
            continue;
        }

        if ($mod === 1) {
            $sink += bench_mixed_args('alpha', 'beta');
            continue;
        }

        $sink += bench_mixed_args($o1, $o2);
    }

    if ($sink < 0) {
        echo "";
    }
});
