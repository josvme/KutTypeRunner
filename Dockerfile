FROM nixos/nix:2.24.14

RUN mkdir -p /etc/nix \
    && printf 'experimental-features = nix-command flakes\n' > /etc/nix/nix.conf

RUN nix profile install nixpkgs#devenv
RUN nix profile install nixpkgs#rustup && rustup default stable

ENV PATH=/root/.cargo/bin:$PATH
WORKDIR /workspace

CMD ["bash"]
