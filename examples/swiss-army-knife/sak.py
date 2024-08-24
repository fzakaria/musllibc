import sqlite3
import argparse
import json
import ctypes
from elftools.elf.elffile import ELFFile
from typing import Iterable, Optional, Tuple
from dataclasses import dataclass, asdict
import os
import sys


@dataclass
class CachedRelocInfo:
    type: int
    addend: int
    st_value: int
    st_size: int
    offset: int
    symbol_dso_index: int
    dso_index: int
    symbol_name: str
    symbol_dso_name: str
    dso_name: str


class CachedRelocInfoStruct(ctypes.Structure):
    """A ctypes structure representing cached relocation info."""

    _fields_ = [
        ("type", ctypes.c_int),
        ("addend", ctypes.c_size_t),
        ("st_value", ctypes.c_size_t),
        ("st_size", ctypes.c_size_t),
        ("offset", ctypes.c_size_t),
        ("symbol_dso_index", ctypes.c_size_t),
        ("dso_index", ctypes.c_size_t),
        ("symbol_name", ctypes.c_char * 255),
        ("symbol_dso_name", ctypes.c_char * 255),
        ("dso_name", ctypes.c_char * 255),
    ]

    @classmethod
    def from_dataclass(
        cls, record: CachedRelocInfo
    ) -> "CachedRelocInfoStruct":
        return cls(
            type=record.type,
            addend=record.addend,
            st_value=record.st_value,
            st_size=record.st_size,
            offset=record.offset,
            symbol_dso_index=record.symbol_dso_index,
            dso_index=record.dso_index,
            symbol_name=record.symbol_name.encode("utf-8").ljust(255, b"\x00"),
            symbol_dso_name=record.symbol_dso_name.encode("utf-8").ljust(
                255, b"\x00"
            ),
            dso_name=record.dso_name.encode("utf-8").ljust(255, b"\x00"),
        )


@dataclass
class SymbolInfo:
    """A dataclass representing the st_value and st_size of a symbol."""

    st_value: int
    st_size: int


def write_to_sqlite(conn: sqlite3.Connection, binary_file_path: str) -> None:
    """
    Write binary data to a SQLite database.

    Args:
        db_path: The path to the SQLite database.
        binary_file_path: The path to the binary file.
    """

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE CachedRelocInfo (
            id INTEGER PRIMARY KEY,
            type INTEGER,
            addend INTEGER,
            st_value INTEGER,
            st_size INTEGER,
            offset INTEGER,
            symbol_dso_index INTEGER,
            dso_index INTEGER,
            symbol_name TEXT,
            symbol_dso_name TEXT,
            dso_name TEXT
        )
    """
    )

    conn.execute("BEGIN TRANSACTION")

    for record in read_binary_file(binary_file_path):
        # conversion to dictionary is necessary for the named
        # argument to work for insertion
        cursor.execute(
            """
            INSERT INTO CachedRelocInfo(type, addend, st_value, st_size,
                                        offset, symbol_dso_index, dso_index,
                                        symbol_name, symbol_dso_name, dso_name)
                       VALUES (:type, :addend, :st_value, :st_size, :offset,
                               :symbol_dso_index, :dso_index, :symbol_name,
                               :symbol_dso_name, :dso_name)
        """,
            asdict(record),
        )

    conn.commit()


def read_from_sqlite(db_path: str) -> Iterable[CachedRelocInfo]:
    """
    Read data from a SQLite database and yield it as CachedRelocInfoTuple.

    Args:
        db_path: The path to the SQLite database.

    Yields:
        CachedRelocInfoTuple: The next record from the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT type, addend, st_value, st_size,
                   offset, symbol_dso_index, dso_index,
                   symbol_name, symbol_dso_name, dso_name
            FROM CachedRelocInfo
        """
    )

    while True:
        record = cursor.fetchone()
        if record is None:
            break
        yield CachedRelocInfo(**record)

    conn.close()


def write_binary_file(
    file_path: str, records: Iterable[CachedRelocInfo]
) -> None:
    """
    Write records to a binary file.

    Args:
        file_path: The path to the binary file.
        records: The records to write.
    """
    with open(file_path, "xb") as f:
        for record in records:
            info = CachedRelocInfoStruct.from_dataclass(record)
            f.write(bytearray(info))


def read_binary_file(file_path: str) -> Iterable[CachedRelocInfo]:
    """
    Read records from a binary file and yield them as CachedRelocInfo.

    Args:
        file_path: The path to the binary file.

    Yields:
        CachedRelocInfoTuple: The next record from the binary file.
    """
    struct_size = ctypes.sizeof(CachedRelocInfoStruct)
    with open(file_path, "rb") as f:
        while True:
            data = f.read(struct_size)
            if not data:
                break
            if len(data) != struct_size:
                raise ValueError(
                    f"Expected {struct_size} bytes, got {len(data)} bytes"
                )
            record = CachedRelocInfoStruct.from_buffer_copy(data)
            # Convert record to dictionary
            record_dict = {
                "type": record.type,
                "addend": record.addend,
                "st_value": record.st_value,
                "st_size": record.st_size,
                "offset": record.offset,
                "symbol_dso_index": record.symbol_dso_index,
                "dso_index": record.dso_index,
                "symbol_name": record.symbol_name.decode("utf-8"),
                "symbol_dso_name": record.symbol_dso_name.decode("utf-8"),
                "dso_name": record.dso_name.decode("utf-8"),
            }
            yield CachedRelocInfo(**record_dict)


def write_json_file(
    json_file_path: str, records: Iterable[CachedRelocInfo]
) -> None:
    """
    Write records to a JSON file.

    Args:
        json_file_path: The path to the JSON file.
        records: The records to write.
    """
    with open(json_file_path, "w") as f:
        for record in records:
            json.dump(asdict(record), f)
            f.write("\n")


def read_json_file(json_file_path: str) -> Iterable[CachedRelocInfo]:
    """
    Read records from a JSON file and yield them as CachedRelocInfo.

    Args:
        json_file_path: The path to the JSON file.

    Yields:
        CachedRelocInfo: The next record from the JSON file.
    """
    with open(json_file_path, "r") as f:
        for line in f:
            yield CachedRelocInfo(**json.loads(line.strip()))


def print_file_contents(file_path: str) -> None:
    """
    Print the contents of a binary file.

    Args:
        file_path: The path to the binary file.
    """
    for record in read_binary_file(file_path):
        print(json.dumps(asdict(record)))


def diff_files(file_path1: str, file_path2: str) -> bool:
    """
    Compare two binary files for equality.

    Args:
        file_path1: The path to the first binary file.
        file_path2 : The path to the second binary file.

    Returns:
        True if the files are equal, False otherwise.
    """

    # We want a *very* stable sort
    def key(record: CachedRelocInfo) -> Tuple[int, int]:
        return (record.dso_index, record.offset)

    records1 = sorted(read_binary_file(file_path1), key=key)
    records2 = sorted(read_binary_file(file_path2), key=key)
    # TODO(fzakaria): use python's diff lib
    return records1 == records2


def get_symbol_info(
    elf_file_path: str, symbol_name: str
) -> Optional[SymbolInfo]:
    """
    Get the st_value and st_size of a symbol in an ELF file.

    Args:
        elf_file_path: The path to the ELF file.
        symbol_name: The name of the symbol to search for.

    Returns:
        A dictionary containing the st_value and st_size of the symbol,
        or None if the symbol was not found.
    """
    with open(elf_file_path, "rb") as f:
        elffile = ELFFile(f)
        symtab = elffile.get_section_by_name(".symtab")

        if symtab:
            for symbol in symtab.iter_symbols():
                if symbol.name == symbol_name:
                    return SymbolInfo(
                        st_value=symbol["st_value"],
                        st_size=symbol["st_size"],
                    )
    return None


def get_override_records(
    file_path: str, elf_file_path: str, symbol_name: str
) -> Iterable[CachedRelocInfo]:
    """
    Finds all records in the relocation cache file that match
    the given symbol name, and replaces it with the st_value and
    st_size of the symbol found in elf_file_path.

    Additionally, it sets the symbol_dso_index to -1 and sets
    the symbol_dso_name to the elf_file_path.

    Args:
        file_path: The path to the relocation cache file.
        elf_file_path: The path to the ELF file.
        symbol_name: The name of the symbol to search for.

    Returns:
    """
    symbol_info = get_symbol_info(elf_file_path, symbol_name)

    for record in read_binary_file(file_path):
        if record.symbol_name != symbol_name:
            continue

        record.symbol_dso_index = -1
        record.st_size = symbol_info.st_size
        record.st_value = symbol_info.st_value
        record.symbol_dso_name = os.path.realpath(elf_file_path)

        yield record


def inject_records(file_path: str) -> None:
    with open(file_path, "ab") as f:
        f.seek(0, os.SEEK_END)
        for line in sys.stdin:
            record = CachedRelocInfo(**json.loads(line.strip()))
            struct_record = CachedRelocInfoStruct.from_dataclass(record)
            f.write(bytearray(struct_record))


def main():
    parser = argparse.ArgumentParser(
        description="Convert binary file to SQLite database and vice versa."
    )
    parser.add_argument(
        "command",
        choices=[
            "file-to-sqlite",
            "sqlite-to-file",
            "file-to-json",
            "json-to-file",
            "print-file",
            "diff-files",
            "get-symbol-info",
            "get-override-records",
            "has-necessary-symbols",
            "inject-records",
        ],
        help="Command to execute",
    )
    parser.add_argument(
        "file", help="Path to the binary file or first file for diff"
    )
    parser.add_argument("--db", help="Path to the SQLite database file")
    parser.add_argument("--json", help="Path to the JSON file")
    parser.add_argument("--file2", help="Path to the second file for diff")
    parser.add_argument(
        "--symbol", help="Symbol name to search for in ELF file"
    )
    parser.add_argument(
        "--symbol-dso-name", help="DSO name that has symbols to check against"
    )
    args = parser.parse_args()

    if args.command == "file-to-sqlite":
        if not args.db:
            parser.error("--db is required for file-to-sqlite command")
        conn = sqlite3.connect(args.db)
        write_to_sqlite(conn, args.file)
        conn.close()
    elif args.command == "sqlite-to-file":
        if not args.db:
            parser.error("--db is required for sqlite-to-file command")
        records = read_from_sqlite(args.db)
        write_binary_file(args.file, records)
    elif args.command == "file-to-json":
        if not args.json:
            parser.error("--json is required for file-to-json command")
        records = read_binary_file(args.file)
        write_json_file(args.json, records)
    elif args.command == "json-to-file":
        if not args.json:
            parser.error("--json is required for json-to-file command")
        records = read_json_file(args.json)
        write_binary_file(args.file, records)
    elif args.command == "print-file":
        print_file_contents(args.file)
    elif args.command == "diff-files":
        if not args.file2:
            parser.error("--file2 is required for diff-files command")
        if diff_files(args.file, args.file2):
            print("Files are equal")
        else:
            print("Files are different")
    elif args.command == "get-symbol-info":
        if not args.symbol:
            parser.error("--symbol is required for get-symbol-info command")
        info = get_symbol_info(args.file, args.symbol)
        if info is not None:
            print(json.dumps(info))
        else:
            print(f"Symbol {args.symbol} not found in {args.file}")
    elif args.command == "get-override-records":
        if not args.symbol:
            parser.error(
                "--symbol is required for get-override-records command"
            )
        if not args.file2:
            parser.error(
                "--file2 is required for get-override-records command"
            )
        records = get_override_records(args.file, args.file2, args.symbol)
        for record in records:
            print(json.dumps(asdict(record)))
    elif args.command == "has-necessary-symbols":
        if not args.file2:
            parser.error(
                "file2 is required for has-necessary-symbols command"
            )
        if not args.symbol_dso_name:
            parser.error(
                "--symbol-dso-name is required"
            )
        conn = sqlite3.connect(":memory:")
        write_to_sqlite(conn, args.file)
        # Create the ELF file (file2) SQLite table
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ELFSymbols (
            id INTEGER PRIMARY KEY,
            symbol_name TEXT,
            dso_name TEXT
        )
        """)
        with open(args.file2, 'rb') as f:
            elffile = ELFFile(f)
            symtab = elffile.get_section_by_name('.dynsym')

            if not symtab:
                print("No dynamic symbol table found in ELF file.")
                return

            conn.execute("BEGIN TRANSACTION")
            for symbol in symtab.iter_symbols():
                cursor.execute("""
                INSERT INTO ELFSymbols (symbol_name)
                VALUES (:name)
                """, {"name": symbol.name})
        conn.commit()

        cursor.execute("""
            SELECT cri.symbol_name
            FROM CachedRelocInfo cri
            LEFT JOIN ELFSymbols es
            ON cri.symbol_name = es.symbol_name
            WHERE es.symbol_name IS NULL AND
                  cri.symbol_dso_name = :dso_name;
            """, {"dso_name": args.symbol_dso_name})

        missing_symbols = cursor.fetchall()
        if not missing_symbols:
            print("All necessary symbols are present.")
            return True
        else:
            print("The following symbols are missing:")
            for symbol in missing_symbols:
                print(symbol[0])

        conn.close()
    elif args.command == "inject-records":
        # This is the 1-line workflow to select some records
        # and override it.
        # TODO(fzakaria): Make a command to do this all
        #
        # ./result/bin/sak get-override-records \
        #           ./result-1/bin/hello_world_relo.bin \
        #               --symbol puts --file2 ./libputs.so  | \
        #           fzf -m  --preview 'echo {}' \
        #               --preview-window down:5:wrap | \
        #           ./result/bin/sak inject-records ./hello_world_relo.bin
        inject_records(args.file)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        exit(0)
