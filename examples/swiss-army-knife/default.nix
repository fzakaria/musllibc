{ writers, python3Packages }:
writers.writePython3Bin "sak" {
  libraries = [ python3Packages.pyelftools ];
} ./sak.py
