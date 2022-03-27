import _io
import sys

cases = [
    ("/tmp/somefile.txt", "str path"),
    (b"/tmp/otherfile.txt", "bytes path"),
    (open("/tmp/3.txt", 'w'), "file in w"),
    (open("/tmp/3.txt", 'a'), "file in a"),
    (open("/tmp/3.txt", 'wb'), "file in wb"),
    (open("/tmp/3.txt", 'ab'), "file in ab"),
    (open("/tmp/3.txt.gz", 'w'), "gzipped file in w"),
    (open("/tmp/3.txt.gz", 'a'), "gzipped file in a"),
    (open("/tmp/3.txt.gz", 'wb'), "gzipped file in wb"),
    (open("/tmp/3.txt.gz", 'ab'), "gzipped file in ab"),
    (sys.stdout, "stdout"),
    (sys.stdout.buffer, "stdout.buffer"),
]

for target, name in cases:

    if isinstance(target, bytes):
        found = "bytes filepath"

    elif target is sys.stdout:
        # set sys.stdout.buffer
        # This fails for you, right?
        found = "sys.stdout"
    elif isinstance(target, str):
        # open file, get it's buffer
        found = "str filepath"
    elif isinstance(target, _io.TextIOWrapper):
        # get targets buffer
        found = "TextIOWrapper"
    elif isinstance(target, _io.BufferedWriter):
        # everything ok
        found = "BufferedWriter"

    print("Expected: {:>20}     found {:>20} ".format(name, found))
