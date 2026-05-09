FROM nixos/nix:2.24.14

RUN mkdir -p /etc/nix \
    && printf 'experimental-features = nix-command flakes\n' > /etc/nix/nix.conf

RUN nix profile install nixpkgs#devenv

WORKDIR /workspace

CMD ["bash"]
