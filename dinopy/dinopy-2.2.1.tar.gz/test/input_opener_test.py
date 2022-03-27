import unittest
from io import BytesIO, StringIO

from dinopy.input_opener import InputOpener

reference_file_path = "files/tiny_testgenome_1chr.fasta"
expected_lines = [b'>tiny_testgenome\n', b'ACGTACGTAC\n', b'GTTTTTTTTT\n', b'TT\n']


class InputOpenerTest(unittest.TestCase):
    def test_read_file(self):
        lines = []
        with InputOpener(reference_file_path, native_io=False) as input_iterable:
            for x in input_iterable:
                lines.append(x)
        self.assertListEqual(lines, expected_lines)

    def test_read_gzip_file(self):
        lines = []
        with InputOpener(reference_file_path + ".gz") as input_iterable:
            for x in input_iterable:
                lines.append(x)
        self.assertListEqual(lines, expected_lines)

    def test_read_file_native(self):
        lines = []
        with InputOpener(reference_file_path, native_io=True) as input_iterable:
            for x in input_iterable:
                lines.append(x)
        self.assertListEqual(lines, expected_lines)

    # def test_read_stdin(self):
    #     raise NotImplementedError

    def test_read_IOBase_str(self):
        source = StringIO("This is a sample string\nfoo\n")
        lines = []
        with InputOpener(source) as reader:
            for x in reader:
                lines.append(x)
        self.assertListEqual(lines, ["This is a sample string\n", "foo\n"])

    def test_read_IOBase_bytes(self):
        source = BytesIO(b"This is a sample string\nfoo\n")
        lines = []
        with InputOpener(source) as reader:
            for x in reader:
                lines.append(x)
        self.assertListEqual(lines, [b"This is a sample string\n", b"foo\n"])

    def test_read_list(self):
        source = ["This is a sample string\n", "foo\n"]
        lines = []
        with InputOpener(source) as reader:
            for x in reader:
                lines.append(x)
        self.assertListEqual(lines, [b"This is a sample string\n", b"foo\n"])


if __name__ == "__main__":
    unittest.main()
