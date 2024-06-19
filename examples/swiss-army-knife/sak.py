import sqlite3
import argparse
import json
import ctypes
from collections import namedtuple


class CachedRelocInfo(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("addend", ctypes.c_size_t),
        ("st_value", ctypes.c_size_t),
        ("st_size", ctypes.c_size_t),
        ("offset", ctypes.c_size_t),
        ("symbol_dso_index", ctypes.c_size_t),
        ("dso_index", ctypes.c_size_t),
        ("symbol_dso_name", ctypes.c_char * 255),
        ("dso_name", ctypes.c_char * 255),
    ]


CachedRelocInfoTuple = namedtuple(
    "CachedRelocInfoTuple",
    [
        "type",
        "addend",
        "st_value",
        "st_size",
        "offset",
        "symbol_dso_index",
        "dso_index",
        "symbol_dso_name",
        "dso_name",
    ],
)


def write_to_sqlite(db_path: str, binary_file_path: str) -> None:
    conn = sqlite3.connect(db_path)
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
                                        symbol_dso_name, dso_name)
                       VALUES (:type, :addend, :st_value, :st_size, :offset,
                               :symbol_dso_index, :dso_index, :symbol_dso_name,
                               :dso_name)
        """,
            record._asdict(),
        )

    conn.commit()
    conn.close()


def read_from_sqlite(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT type, addend, st_value, st_size,
                   offset, symbol_dso_index, dso_index,
                   symbol_dso_name, dso_name
            FROM CachedRelocInfo
        """
    )

    while True:
        record = cursor.fetchone()
        if record is None:
            break
        yield CachedRelocInfoTuple(
            type=record[0],
            addend=record[1],
            st_value=record[2],
            st_size=record[3],
            offset=record[4],
            symbol_dso_index=record[5],
            dso_index=record[6],
            symbol_dso_name=record[7],
            dso_name=record[8],
        )

    conn.close()


def write_binary_file(file_path, records):
    with open(file_path, "wb") as f:
        for record in records:
            # Create an instance of CachedRelocInfo
            info = CachedRelocInfo(
                type=record.type,
                addend=record.addend,
                st_value=record.st_value,
                st_size=record.st_size,
                offset=record.offset,
                symbol_dso_index=record.symbol_dso_index,
                dso_index=record.dso_index,
                symbol_dso_name=record.symbol_dso_name.encode("utf-8").ljust(
                    255, b"\x00"
                ),
                dso_name=record.dso_name.encode("utf-8").ljust(255, b"\x00"),
            )
            f.write(bytearray(info))


def read_binary_file(file_path):
    struct_size = ctypes.sizeof(CachedRelocInfo)
    with open(file_path, "rb") as f:
        while True:
            data = f.read(struct_size)
            if not data:
                break
            if len(data) != struct_size:
                raise ValueError(
                    f"Expected {struct_size} bytes, got {len(data)} bytes"
                )
            record = CachedRelocInfo.from_buffer_copy(data)
            # Convert record to dictionary
            record_dict = {
                "type": record.type,
                "addend": record.addend,
                "st_value": record.st_value,
                "st_size": record.st_size,
                "offset": record.offset,
                "symbol_dso_index": record.symbol_dso_index,
                "dso_index": record.dso_index,
                "symbol_dso_name": record.symbol_dso_name.decode("utf-8"),
                "dso_name": record.dso_name.decode("utf-8"),
            }
            yield CachedRelocInfoTuple(**record_dict)


def print_file_contents(file_path):
    for record in read_binary_file(file_path):
        print(json.dumps(record._asdict()))


def diff_files(file_path1, file_path2):
    # We want a *very* stable sort
    def key(record):
        return (record.dso_index, record.offset)

    records1 = sorted(read_binary_file(file_path1), key=key)
    records2 = sorted(read_binary_file(file_path2), key=key)
    # TODO(fzakaria): use python's diff lib
    return records1 == records2


def main():
    parser = argparse.ArgumentParser(
        description="Convert binary file to SQLite database and vice versa."
    )
    parser.add_argument(
        "command",
        choices=[
            "file-to-sqlite",
            "sqlite-to-file",
            "print-file",
            "diff-files",
        ],
        help="Command to execute",
    )
    parser.add_argument(
        "file", help="Path to the binary file or first file for diff"
    )
    parser.add_argument("--db", help="Path to the SQLite database file")
    parser.add_argument("--file2", help="Path to the second file for diff")
    args = parser.parse_args()

    if args.command == "file-to-sqlite":
        if not args.db:
            parser.error("--db is required for file-to-sqlite command")
        write_to_sqlite(args.db, args.file)
    elif args.command == "sqlite-to-file":
        if not args.db:
            parser.error("--db is required for sqlite-to-file command")
        records = read_from_sqlite(args.db)
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


if __name__ == "__main__":
    main()
