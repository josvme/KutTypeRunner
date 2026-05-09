{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/basics/
  env.GREET = "devenv";

  # https://devenv.sh/packages/
  packages = [
    pkgs.git
    pkgs.openssl
    pkgs.pkg-config
    pkgs.php.unwrapped.dev
    pkgs.llvmPackages.clang
    pkgs.llvmPackages.libcxx
    pkgs.k6
  ];

  env.LIBCLANG_PATH = "${pkgs.llvmPackages.libclang.lib}/lib";

  # https://devenv.sh/languages/
  languages.php.enable = true;
  languages.php.package = pkgs.php;

  # https://devenv.sh/basics/
  enterShell = ''
    git --version # Use packages
  '';
}
