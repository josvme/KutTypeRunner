<?php

declare(strict_types=1);

function env_int(string $name, int $default): int
{
    $value = getenv($name);
    if ($value === false || $value === '') {
        return $default;
    }

    if (!is_numeric($value)) {
        throw new RuntimeException("Environment variable {$name} must be numeric.");
    }

    return max(1, (int) $value);
}

function env_string(string $name, string $default): string
{
    $value = getenv($name);
    return ($value === false || $value === '') ? $default : $value;
}

function benchmark(string $name, callable $callback, ?int $iterations = null): void
{
    $iterations = $iterations ?? env_int('BENCH_ITERATIONS', 1000000);
    $variant = env_string('BENCH_VARIANT', 'unknown');

    $start = hrtime(true);
    $callback($iterations);
    $end = hrtime(true);

    $totalNs = $end - $start;

    $record = [
        'benchmark' => $name,
        'variant' => $variant,
        'iterations' => $iterations,
        'total_ns' => $totalNs,
        'ns_per_op' => $totalNs / $iterations,
    ];

    fputcsv(
        STDOUT,
        [
            $record['benchmark'],
            $record['variant'],
            (string) $record['iterations'],
            (string) $record['total_ns'],
            (string) $record['ns_per_op'],
        ],
        ',',
        '"',
        '',
    );
}
