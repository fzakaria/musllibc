{
  pkgs ?
    import (builtins.fetchTarball {
      name = "nixos-24.05";
      url = https://github.com/NixOS/nixpkgs/archive/24.05.tar.gz;
    }) {
      overlays = [
        (self: super: {
          pythonBindNow = super.python3.overrideAttrs (_: {
            # name = "python-now";
            NIX_CFLAGS_COMPILE = "-Wl,-z,now";
            doCheck = false;
          });
        })
      ];
    },
}:
pkgs.pythonBindNow
