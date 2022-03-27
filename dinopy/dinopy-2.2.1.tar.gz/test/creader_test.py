# -*- coding: utf-8 -*-
import unittest
from io import SEEK_CUR, SEEK_END

from dinopy.creader import CReader

reference_file_path = "files/tiny_testgenome_1chr.fasta"
expected_lines = [b'>tiny_testgenome\n', b'ACGTACGTAC\n', b'GTTTTTTTTT\n', b'TT\n']


class CReaderTest(unittest.TestCase):

    def test_with_statement(self):
        lines = []
        with CReader(reference_file_path) as reader:
            for line in reader:
                lines.append(line)
        self.assertListEqual(lines, expected_lines)

    def test_readable(self):
        reader = CReader(reference_file_path)
        self.assertTrue(reader.readable())
        reader.close()
        self.assertFalse(reader.readable())

    def test_seek(self):
        with CReader(reference_file_path) as reader:
            reader.seek(17)  # SEEK_SET
            line = reader.readline()
            self.assertEqual(line, expected_lines[1])

        with CReader(reference_file_path) as reader:
            reader.seek(10)  # SEEK_SET
            reader.seek(7, whence=SEEK_CUR)  # SEEK_CUR
            line = reader.readline()
            self.assertEqual(line, expected_lines[1])

        with CReader(reference_file_path) as reader:
            reader.seek(-25, whence=SEEK_END)  # SEEK_END
            line = reader.readline()
            self.assertEqual(line, expected_lines[1])

    def test_tell(self):
        with CReader(reference_file_path) as reader:
            reader.seek(17)  # SEEK_SET
            tell = reader.tell()
            self.assertEqual(tell, 17)

        with CReader(reference_file_path) as reader:
            reader.seek(10)  # SEEK_SET
            reader.seek(7, whence=SEEK_CUR)  # SEEK_CUR
            tell = reader.tell()
            self.assertEqual(tell, 17)

        with CReader(reference_file_path) as reader:
            reader.seek(-25, whence=SEEK_END)  # SEEK_END
            tell = reader.tell()
            self.assertEqual(tell, 17)

    def test_read(self):
        with CReader(reference_file_path) as reader:
            content = b''
            while True:
                b = reader.read(1)
                if b is None:
                    break
                content += b
            self.assertEqual(content, b''.join(expected_lines))

    def test_readline(self):
        with CReader(reference_file_path) as reader:
            lines = []
            while True:
                line = reader.readline()
                if line is None:
                    break
                lines.append(line)
            self.assertListEqual(lines, expected_lines)

    def test_readlines(self):
        with CReader(reference_file_path) as reader:
            lines = reader.readlines()
            self.assertListEqual(lines, expected_lines)


if __name__ == "__main__":
    unittest.main()
