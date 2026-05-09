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
cargo build
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