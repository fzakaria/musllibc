{ stdenv, patchelf, musl, lib, makeWrapper }: {
  all = { name ? lib.strings.getName executable, executable
    , command ? "--version" }:
    stdenv.mkDerivation {
      name = "patched_${name}";

      buildInputs = [ patchelf musl executable makeWrapper ];

      phases = "installPhase";

      installPhase = ''
        mkdir -p $out/bin
        # Apply patchelf to all binaries in the bin directory to set the new interpreter.
        for bin in ${executable}/bin/*; do
            # Check if the file is executable
            if [[ ! -x "$bin" ]]; then
                continue
            fi

            # Check if the file is an ELF binary
            if ! file "$bin" | grep -q "ELF"; then
                continue
            fi
            patchelf --set-interpreter ${musl}/lib/libc.so $bin --output $out/bin/$(basename $bin)
        done
        # Add the custom relocation section
        for bin in $out/bin/*; do
            local bin_reloname=$(basename $bin)_relo.bin
            RELOC_WRITE=$bin_reloname $bin ${command}
            cp $bin_reloname $out/bin/$bin_reloname
            makeWrapper $bin $out/bin/$(basename $bin)-optimized \
                --set RELOC_READ "$out/bin/$bin_reloname"
        done
      '';
    };

  individual = { name ? lib.strings.getName executable, executable
    , command ? "--version" }:
    stdenv.mkDerivation {
      name = "patched_${name}";

      buildInputs = [ patchelf musl executable makeWrapper];

      phases = "installPhase";

      installPhase = ''
        mkdir -p $out/bin
        patchelf --set-interpreter ${musl}/lib/libc.so ${executable}/bin/${name} --output $out/bin/${name}
        RELOC_WRITE=${name}_relo.bin $out/bin/${name} ${command}
        cp ${name}_relo.bin $out/bin/${name}_relo.bin
        makeWrapper $out/bin/${name} $out/bin/${name}-optimized \
                --set RELOC_READ "$out/bin/${name}_relo.bin"
      '';
    };

}
