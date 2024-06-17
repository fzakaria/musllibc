{ writeShellScriptBin, flamegraph, examples, lib, symlinkJoin }:
lib.recurseIntoAttrs rec {

  flamegraph-script = { binary, command ? "" }:

    let
      script = b:
        (let
          svgName =
            if lib.hasSuffix "-optimized" b then "modified" else "baseline";
        in writeShellScriptBin "create-flamegraph-${svgName}" ''
          perf record -F 1000 -g -a --user-callchains -- ${b} ${command} > /dev/null
          perf script > out.perf
          ${flamegraph}/bin/stackcollapse-perf.pl out.perf > out.perf-folded
          grep _dlstart_c out.perf-folded > _dlstart_c-out.perf-folded
          ${flamegraph}/bin/flamegraph.pl --title ' ' _dlstart_c-out.perf-folded > ${svgName}.svg
          echo $(realpath ${svgName}.svg)
        '');
    in symlinkJoin {
      name = "flamegraph-script";
      paths = [ (script binary) (script (binary + "-optimized")) ];
    };

  million_functions = flamegraph-script {
    binary = "${examples.patched_functions}/bin/1000000_functions";
  };

  pynamic = flamegraph-script {
    binary = "${examples.patched_pynamic}/bin/pynamic-mpi4py";
  };

  libreoffice = flamegraph-script {
    binary =
      "${examples.patched_libreoffice}/lib/libreoffice/program/soffice.bin";
    command = "--help";
  };
}
