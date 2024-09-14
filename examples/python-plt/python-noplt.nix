# python-with-fno-plt.nix
{
  pkgs ?
  import (builtins.fetchTarball {
    name = "nixos-24.05";
    url = https://github.com/NixOS/nixpkgs/archive/24.05.tar.gz;
  }) {
      overlays = [
        (self: super: {
          stdenv = super.withCFlags ["-fno-plt"] super.stdenv;
        })
      ];
    },
}:
pkgs.python3

