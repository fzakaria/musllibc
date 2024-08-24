{
  symlinkJoin,
  stdenv,
  python3,
  lib,
}: let
  fs = lib.fileset;
  # Define the possible values for total_functions and num_shared_objects
  num_functions = [1 10 100 1000 10000 100000 1000000];
  num_shared_objects = [1 10 100 1000 10000]; #100000 1000000];
  combinations =
    builtins.filter (combination: (combination.functions * combination.shared_objects) <= 1000000)
    (lib.crossLists (functions: shared_objects: {
      functions = functions;
      shared_objects = shared_objects;
    }) [num_functions num_shared_objects]);
  buildBinary = combination: let
    functions = toString combination.functions;
    shared_objects = toString combination.shared_objects;
  in
    stdenv.mkDerivation {
      name = "${functions}_${shared_objects}_raw_functions_and_libraries";
      nativeBuildInputs = [python3];
      src = fs.toSource {
        root = ./.;
        fileset = fs.unions [./Makefile ./generate_sources.py];
      };
      dontStrip = true;
      NIX_CFLAGS_COMPILE = "-g -O0";
      buildPhase = ''
        python3 $src/generate_sources.py ${functions} ${shared_objects}
        echo "Building with ''${NIX_BUILD_CORES} cores"
        make -f $src/Makefile -j''${NIX_BUILD_CORES}
        mv benchmark benchmark_${functions}_${shared_objects}
      '';

      installPhase = ''
        mkdir -p $out/bin
        mkdir -p $out/lib

        mv *.so $out/lib
        mv benchmark_*_* $out/bin
      '';
    };
  # Create a list of derivations for the filtered combinations
  binaries = map (combination: buildBinary combination) combinations;
in
  symlinkJoin {
    name = "raw_functions_and_libraries";
    # only join the bin directory
    paths = builtins.map (binary: "${binary}/bin") binaries;
    postBuild = ''
      mkdir $out/bin
      mv $out/benchmark_* $out/bin
    '';
  }
