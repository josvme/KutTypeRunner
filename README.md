# README 

### What is it?
A simple Rust extension which will record the type of arguments of every user space function call.

### Setting Up Rust
Rust is set up using [rustup](https://rustup.rs/)

### Setting up PHP
To enter the nix shell, which has php with required sources, do 
```sh
devenv shell
```

### Docker dev shell (devenv alternative)
If you are not using `devenv`, use the containerized shell:

```sh
docker compose up -d --build
docker compose exec devenv bash
devenv shell
```

This uses a Nix-based container with `devenv` installed, so the environment is sourced from `devenv.nix` directly for feature parity.
Nix/devenv caches are persisted via Docker named volumes, so repeated runs avoid re-downloading most artifacts.

When done:

```sh
docker compose down
```

To also clear caches:

```sh
docker compose down -v
```

### Building the extension
Now we can build our extension
```sh
cargo build --releas
```

### Testing the extension
Now we can test our extension using our test.php file.
```sh
php -c php.ini test.php
```

Output
```
Intercepted call to Me\T::__construct: args=[]
Intercepted call to Me\T::test_function: args=["string", "long"]
Intercepted call to Me\T::test_function: args=["Me\\T", "stdClass"]
```

### Testing with real apps
```sh
composer create-project symfony/symfony-demo demo
php -c php.ini -S localhost:8000 -t demo/public/
curl http://localhost:8000/
```

Output 
```
Intercepted call to ComposerAutoloaderInit053d3b4bab2213aebd2d000bac677a7c::getLoader: args=[]
Intercepted call to ComposerAutoloaderInit053d3b4bab2213aebd2d000bac677a7c::loadClassLoader: args=["string"]
Intercepted call to Composer\Autoload\ClassLoader::__construct: args=["string"]
Intercepted call to Composer\Autoload\ClassLoader::initializeIncludeClosure: args=[]
....
```

# Benchmark Summary

## Micro-Benchmarks

| Benchmark | Baseline median (ns/op) | With ext median (ns/op) | Slowdown % | Delta (ns/op) |
|---|---:|---:|---:|---:|
| control_loop | 6.97 | 7.04 | 0.95 | 0.07 |
| method_instance | 53.20 | 461.54 | 767.58 | 408.34 |
| method_static | 48.48 | 406.44 | 738.43 | 357.96 |
| mixed_argument_shapes | 124.24 | 657.06 | 428.87 | 532.83 |
| no_arg_user_function | 28.01 | 244.54 | 772.95 | 216.52 |
| object_args | 63.56 | 715.06 | 1025.06 | 651.50 |
| scalar_args | 134.70 | 457.14 | 239.37 | 322.44 |

## Symfony Benchmark

| Scenario | Baseline rps | With ext rps | Throughput drop % | Baseline p95 (ms) | With ext p95 (ms) | Latency slowdown % |
|---|---:|---:|---:|---:|---:|---:|
| / @c1 | 68.45 | 62.79 | 8.27 | 16.69 | 18.01 | 7.96 |
| / @c20 | 70.89 | 64.55 | 8.95 | 283.57 | 314.76 | 11.00 |

## Notes
- Slowdown formula: `(with_ext / baseline) - 1`
- Throughput drop formula: `1 - (with_ext_rps / baseline_rps)`
