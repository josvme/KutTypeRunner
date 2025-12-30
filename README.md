# README 

### What is it?
A simple Rust extension which will record the type of arguments of every user space function call.

### Setting Up Rust
Rust is set up using [rustup](https://rustup.rs/)

### Setting up PHP
To enter the nix shell, which has php with required sources, do 
```sh
nix develop
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

```
Intercepted call to Me\T::__construct: args=[]
Intercepted call to Me\T::test_function: args=["Zval { type: String, val: Some(\"hello\") }", "Zval { type: Long, val: Some(123) }"]
```