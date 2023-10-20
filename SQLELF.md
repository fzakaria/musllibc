# SQLELF

This document outlines some of the manual steps you can go through to get this fork working.
The changes in this fork are mainly restricted to [dynlink.c](./ldso/dlstart.c) to support
reading a SQLite database from the '.sqlelf' section of an ELF file.

## Preparing a SQLite ELF supported file

Step 1: Compile musl and install it
```console
./configure --prefix=$(realpath build) \
            --exec-prefix=$(realpath build) \
            --syslibdir=$(realpath build/lib/) \
            --host=x86_64-linux-gnu \
            --enable-debug

make && make install
```

Step 2: Create a C-program and compile it with musl-gcc
```
$ cat hello_world.c
#include <stdio.h>

int main() {
    printf("Hello, World!\n");
    return 0;
}

$ ./build/bin/musl-gcc hello_world.c -o hello_world
``` 
Step 3: Create the SQLite backup of the ELF file
```console
sqlelf hello_world
> .backup hello_world.sqlite
```
[sqlelf](https://github.com/fzakaria/sqlelf) can be installed either with pip (venv), pipx or run from the source directory of the repository.

Step 4: Disable WAL
```console
sqlite3 hello_world.sqlite
> pragma journal_mode=DELETE;
```
Step 5: Add the SQLite database to the ELF file
```console
objcopy --add-section .sqlelf=hello_world.sqlite \
        --set-section-flags .sqlelf=noload,readonly \
        hello_world hello_world.sqlelf
``

Step 6: Run it!
```console
./hello_world.sqlelf
```