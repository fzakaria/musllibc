{ openssh, musl, patchelf, libffi, ruby, patchExecutable, wrapCC, llvmPackages
, enableDebugging, python3, stdenv, fetchFromGitHub, openmpi, makeWrapper, lib
, libreoffice, libreoffice-unwrapped, symlinkJoin, binutils }:
lib.recurseIntoAttrs rec {
  patched_ruby = let
    # for some reason on pkgMusl this is hanging?...
    # just disable it for now
    modified_libffi = libffi.overrideAttrs (oldAttrs: {
      doCheck = false; # Disable the check phase
    });
    modified_ruby = enableDebugging (ruby.override { libffi = libffi; });
  in patchExecutable.individual { executable = modified_ruby; };

  libreoffice_musl = libreoffice-unwrapped;

  patched_libreoffice = symlinkJoin {
    name = "patched_libreoffice";
    paths = [ libreoffice_musl ];
    buildInputs = [ binutils patchelf musl makeWrapper ];
    postBuild = ''
      patchelf --set-interpreter ${musl}/lib/libc.so $out/lib/libreoffice/program/soffice.bin --output $out/lib/libreoffice/program/soffice.bin-patched
      mv $out/lib/libreoffice/program/soffice.bin-patched $out/lib/libreoffice/program/soffice.bin

      RELOC_WRITE=soffice_relo.bin $out/lib/libreoffice/program/soffice.bin --help &> /dev/null
      cp soffice_relo.bin $out/lib/libreoffice/program/soffice_relo.bin
      makeWrapper $out/lib/libreoffice/program/soffice.bin $out/lib/libreoffice/program/soffice.bin-optimized \
                --set RELOC_READ "$out/lib/libreoffice/program/soffice_relo.bin"
    '';
  };

  patched_clang =
    patchExecutable.individual { executable = llvmPackages.clang.cc; };
  # compilers in Nixpkgs are not usable in Nix by themselves because
  # they do not know how to find header files and libc
  # wrapCC creates a wrapper file with all the necessary info included
  patched_clang_wrapped = wrapCC patched_clang;

  patched_python =
    patchExecutable.individual { executable = enableDebugging python3; };

  pynamic = stdenv.mkDerivation rec {
    name = "pynamic";
    src = fetchFromGitHub {
      owner = "LLNL";
      repo = "pynamic";
      rev = "4b17259e5171628b0f08e7cd7ddf72bcd5e19d9f";
      hash = "sha256-5npWRktvH4luT4qw6z0BJr/twQLu+2HvJ4g8cai11LA=";
    };
    sourceRoot = "${src.name}/pynamic-pyMPI-2.6a1";
    buildInputs =
      [ (python3.withPackages (ps: [ ps.mpi4py ])) openmpi makeWrapper ];
    propagatedBuildInputs = [ openssh ];

    configurePhase = ''
      # do nothing
    '';

    patches = [ ../nix/patches/0001-fix-python-path.patch ];

    postPatch = ''
      substituteInPlace Makefile.mpi4py \
        --replace '@python_path@' "''${out}/lib"
    '';

    buildPhase = ''
      # https://asc.llnl.gov/sites/asc/files/2020-09/pynamic-coral-2-benchmark-summary-v1-2.pdf
      # 900 : num_files
      # 1250 : avg_num_functions
      # -e : enables external functions to call across modules
      # -u <num_utility_mods> <avg_num_u_functions>
      # -n: add N characters to the function name
      # -b : generate the pynamic-bigexe-pyMPI
      python config_pynamic.py 900 1250 -e -u 350 1250 \
                            -n 150 -j $NIX_BUILD_CORES --with-mpi4py
      # This is used for testing
      # python3 config_pynamic.py 4 4 -e -u 2 2 -n 3 -j $NIX_BUILD_CORES --with-mpi4py
    '';

    installPhase = ''
      mkdir -p $out/bin
      mkdir -p $out/lib

      mv pynamic-mpi4py $out/bin
      mv pynamic_driver_mpi4py.py $out/lib
      mv *.so $out/lib
    '';

  };

  patched_pynamic = patchExecutable.individual {
    name = "pynamic-mpi4py";
    executable = pynamic;
  };
}
