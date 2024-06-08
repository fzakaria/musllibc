self: super: {
  # create a super basic openmpi
  # that doesn't have a lot of the stuff needed so we can build
  # with musl
  openmpi = (super.openmpi.override {
    fabricSupport = false;
    fortranSupport = false;
    cudaSupport = false;
    enableSGE = false;
  }).overrideAttrs (finalAttrs: previousAttrs: {
    enableParallelBuilding = true;
    buildInputs = with super.pkgs; [ zlib libevent hwloc ];
    configureFlags = [
      "--disable-mpi-fortran"
      "--disable-static"
      "--enable-mpi1-compatibility"
    ];
  });

  mpi = self.openmpi;

  # Unstable has some Musl fixes we want to pull in 
  CoinMP = super.unstable.CoinMP;

  umockdev = super.umockdev.overrideAttrs
    (finalAttrs: previousAttrs: { checkPhase = ""; });

  libgudev = super.libgudev.overrideAttrs
    (finalAttrs: previousAttrs: { checkPhase = ""; });

  pipewire = super.unstable.pipewire;

  dbus_cplusplus = super.dbus_cplusplus.overrideAttrs
    (finalAttrs: previousAttrs: {
      patches = previousAttrs.patches ++ [
        (super.fetchpatch {
          name =
            "0001-src-eventloop.cpp-use-portable-method-for-initializi.patch";
          url =
            "https://github.com/openembedded/meta-openembedded/raw/119e75e48dbf0539b4e440417901458ffff79b38/meta-oe/recipes-core/dbus/libdbus-c++-0.9.0/0001-src-eventloop.cpp-use-portable-method-for-initializi.patch";
          hash = "sha256-GJWvp5F26c88OCGLrFcXaqUl2FMSDCluppMrRQO3rzc=";
        })
        (super.fetchpatch {
          name =
            "0002-tools-generate_proxy.cpp-avoid-possibly-undefined-ui.patch";
          url =
            "https://github.com/openembedded/meta-openembedded/raw/119e75e48dbf0539b4e440417901458ffff79b38/meta-oe/recipes-core/dbus/libdbus-c++-0.9.0/0002-tools-generate_proxy.cpp-avoid-possibly-undefined-ui.patch";
          hash = "sha256-P9JuG/6k5L6NTiAGH9JRfNcwpNVOV29RQC6fTj0fKZE=";
        })
        (super.fetchpatch {
          name =
            "0003-Fixed-undefined-ssize_t-for-clang-3.8.0-on-FreeBSD.patch";
          url =
            "https://github.com/openembedded/meta-openembedded/raw/119e75e48dbf0539b4e440417901458ffff79b38/meta-oe/recipes-core/dbus/libdbus-c++-0.9.0/0003-Fixed-undefined-ssize_t-for-clang-3.8.0-on-FreeBSD.patch";
          hash = "sha256-/RCpDvaLIw0kmuBvUGbfnVEvgTKjIQWcSKWheCfgSmM=";
        })
      ];
    });

  libreoffice-unwrapped = (super.unstable.pkgsMusl.libreoffice.unwrapped.override {
    withHelp = false;
  }).overrideAttrs (finalAttrs: previousAttrs: {
    doCheck = false;
    configureFlags =
      super.lib.remove "--enable-dbus" previousAttrs.configureFlags;
    # NIX_DEBUG = 7;
    buildInputs = super.lib.lists.subtractLists ([
      super.dbus-glib
      super.gst_all_1.gst-plugins-bad
    ]) previousAttrs.buildInputs;
  });
  libreoffice-still = super.libreoffice-still.override ({
    unwrapped = self.libreoffice-unwrapped;
  });
  libreoffice = self.libreoffice-still;
}
