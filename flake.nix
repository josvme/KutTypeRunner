{
  description = "Type Runner PHP Rust Extension";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, flake-utils, nixpkgs, ... }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = (import nixpkgs) {
          inherit system;
        };
      in {
        devShells = {
          default = pkgs.mkShell {
            name = "type runner";

            nativeBuildInputs = [
              pkgs.openssl
              pkgs.pkg-config
              pkgs.php.unwrapped.dev
              pkgs.llvmPackages.clang
              pkgs.llvmPackages.libcxx
            ];

            LIBCLANG_PATH = "${pkgs.llvmPackages.libclang.lib}/lib";
          };
        };
      }
    );
}
