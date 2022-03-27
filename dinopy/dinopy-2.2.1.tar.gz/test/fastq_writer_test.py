# -*- coding: utf-8 -*-
import gzip
import os
import shutil
import sys
import unittest

import dinopy
from dinopy.exceptions import InvalidDtypeError

KEEP_TMPFILES = False


class FastqWriterTest(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory for the test files.
        """
        self.tmpdir = "/tmp/FastqWriterTests"
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)

    def tearDown(self):
        if not KEEP_TMPFILES:
            try:
                shutil.rmtree(self.tmpdir)  # remove tmp dir after tests
            except OSError:
                print("Problem deleting tempfile")
                raise

    def test_creation_file(self):
        """Is a FastqWriter initialized correctly from a file object?"""
        f = open(os.path.join(self.tmpdir, "create_from_file.fastq"), 'wb')
        with dinopy.FastqWriter(f, append=False) as fqw:
            fqw.write(b'ACGTTGCA', b'a testread', b'####!!!!')
        f = open(os.path.join(self.tmpdir, "create_from_file.fastq"), 'ab')
        with dinopy.FastqWriter(f, append=True) as fqw:
            fqw.write(b'ACGTTGCA', b'a testread', b'####!!!!')

    def test_creation_stdout(self):
        """Is a FastqWriter initialized correctly on stdout?"""
        f = sys.stdout
        with dinopy.FastqWriter(f) as fqw:
            fqw.write(b'ACGTTGCA', b'a testread', b'####!!!!')
        # f = sys.stdout.buffer
        # with dinopy.FastqWriter(f) as fqw:
        #     fqw.write(b'ACGTTGCA', b'a testread', b'####!!!!')

    def test_creation_str(self):
        """Is a FastqWriter initialized correctly from a str filepath?"""
        path = os.path.join(self.tmpdir, "create_from_string.fastq")
        with dinopy.FastqWriter(path) as fqw:
            fqw.write(b'ACGTTGCA', b'a testread', b'####!!!!')
        path = os.path.join(self.tmpdir, "create_from_string.fastq")
        with dinopy.FastqWriter(path, append=True) as fqw:
            fqw.write(b'ACGTTGCA', b'a testread', b'####!!!!')

    def test_creation_bytes(self):
        """Is a FastqWriter initialized correctly from bytes filepath?"""
        path = os.path.join(self.tmpdir.encode(), b"create_from_bytes.fastq")
        with dinopy.FastqWriter(path) as fqw:
            fqw.write(b'ACGTTGCA', b'a testread', b'####!!!!')
        path = os.path.join(self.tmpdir.encode(), b"create_from_bytes.fastq")
        with dinopy.FastqWriter(path, append=True) as fqw:
            fqw.write(b'ACGTTGCA', b'a testread', b'####!!!!')

    def test_write_read_bytes(self):
        """Is a single read written correctly?"""
        seq_id = b"readname"
        sequence = b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        quality_values = b"!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
        path = os.path.join(self.tmpdir, "single_read_bytes.fastq")
        with dinopy.FastqWriter(path) as fqw:
            fqw.write(sequence, seq_id, quality_values, dtype=bytes)
        expected_result = [
            "@readname\n",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            "+\n",
            "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~\n"
        ]
        with open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)

    def test_write_read_str(self):
        """Is a single read writen correctly?"""
        seq_id = b"readname"
        sequence = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        quality_values = b"!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
        path = os.path.join(self.tmpdir, "single_read_str.fastq")
        with dinopy.FastqWriter(path) as fqw:
            fqw.write(sequence, seq_id, quality_values, dtype=str)
        expected_result = [
            "@readname\n",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            "+\n",
            "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~\n"
        ]
        with open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)

    def test_write_read_basenumbers(self):
        """Is a single read writen correctly?"""
        seq_id = b"readname"
        sequence = [0] * 94
        quality_values = b"!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
        path = os.path.join(self.tmpdir, "single_read_basenumbers.fastq")
        with dinopy.FastqWriter(path) as fqw:
            fqw.write(sequence, seq_id, quality_values, dtype=dinopy.basenumbers)
        expected_result = [
            "@readname\n",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            "+\n",
            "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~\n"
        ]
        with open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)

    def test_write_read_compressed(self):
        """Is a single read written correctly to a gzipped file?"""
        seq_id = b"readname"
        sequence = b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        quality_values = b"!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
        path = os.path.join(self.tmpdir, "single_read_bytes_compressed.fastq.gz")
        with dinopy.FastqWriter(path) as fqw:
            fqw.write(sequence, seq_id, quality_values, dtype=bytes)
        expected_result = [
            b"@readname\n",
            b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            b"+\n",
            b"!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~\n"
        ]
        with gzip.open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)

    def test_write_read_without_quality_values(self):
        """Is a single read without quality values written correctly?"""
        seq_id = b"readname"
        sequence = b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        quality_values = b"!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
        path = os.path.join(self.tmpdir, "single_read_bytes_no_quality.fastq")
        expected_result = [
            "@readname\n",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            "+\n",
            "\n"
        ]
        # write without quality values
        with dinopy.FastqWriter(path, append=False) as fqw:
            fqw.write_reads([(sequence, seq_id)], quality_values=False, dtype=bytes)
        with open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)
        # provide quality values which should not be written
        with dinopy.FastqWriter(path, force_overwrite=True, append=False) as fqw:
            fqw.write_reads([(sequence, seq_id, quality_values)], quality_values=False, dtype=bytes)
        with open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)

    def test_write_reads(self):
        """ Are multiple reads written correctly?"""
        seq_id = b"readname"
        sequence = b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        quality_values = b"!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
        path = os.path.join(self.tmpdir, "five_reads_bytes.fastq")
        with dinopy.FastqWriter(path) as fqw:
            fqw.write_reads([(sequence, seq_id, quality_values)] * 5, dtype=bytes)
        expected_result = [
                              "@readname\n",
                              "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
                              "+\n",
                              "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~\n"
                          ] * 5
        with open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)

    def test_error_handling_modes(self):
        """Are wrong modes identified and treated correctly?"""
        # mode clashes with append parameter
        with self.assertRaises(ValueError):
            f = open(os.path.join(self.tmpdir, "error.fastq"), 'wa')
            with dinopy.FastqWriter(f, append=True) as fqw:
                fqw.write(b'ACGTTGCA', b'a testread', b'####!!!!')
        # read modes
        with self.assertRaises(OSError):
            f = open(os.path.join(self.tmpdir, "error.fastq"), 'rb')
            with dinopy.FastqWriter(f) as fqw:
                fqw.write(b'ACGTTGCA', b'a testread', b'####!!!!')
        with self.assertRaises(OSError):
            f = open(os.path.join(self.tmpdir, "error.fastq"), 'r')
            with dinopy.FastqWriter(f) as fqw:
                fqw.write(b'ACGTTGCA', b'a testread', b'####!!!!')

    def test_error_handling_paths(self):
        """Are the correct errors raised by FastqWriter.__init__?"""
        # fail with empty path
        with self.assertRaises(TypeError):
            fqw = dinopy.FastqWriter()
        with self.assertRaises(TypeError):
            fqw = dinopy.FastqWriter(None)
        with self.assertRaises(ValueError):
            fqw = dinopy.FastqWriter("")
        # fail with wrong input type
        with self.assertRaises(TypeError):
            fqw = dinopy.FastqWriter(42)
        # fail when environment is not used -> no file opened
        with self.assertRaises(IOError):
            fqw = dinopy.FastqWriter(os.path.join(self.tmpdir, "path_error.fastq"))
            fqw.write(b'name', b'ACGT', b'####')
        with self.assertRaises(IOError):
            fqw = dinopy.FastqWriter(os.path.join(self.tmpdir, "path_error.fastq"))
            fqw.write_reads([b'name', b'ACGT', b'####'])

    def test_error_handling_quality_values(self):
        """Are the correct errors raised by FastqWriter.write?"""
        # fail for missing quality values
        seq_id = b"readname"
        sequence = b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        path = os.path.join(self.tmpdir, "qv_error.fastq")
        with self.assertRaises(ValueError):
            with dinopy.FastqWriter(path) as fqw:
                fqw.write_reads([(sequence, seq_id)], quality_values=True, dtype=bytes)

    def test_error_handling_dtypes(self):
        seq_id = b"readname"
        seq_bytes = b"AAA"
        seq_str = "AAA"
        seq_basenumbers = [0, 0, 0]
        path = os.path.join(self.tmpdir, "dtype_error.fastq")
        # try using bytes as basenumbers
        with self.assertRaises(InvalidDtypeError):
            with dinopy.FastqWriter(path, force_overwrite=True) as fqw:
                fqw.write(seq_bytes, seq_id, dtype=dinopy.basenumbers)
        # try using bytes as str
        with self.assertRaises(TypeError):
            with dinopy.FastqWriter(path, force_overwrite=True) as fqw:
                fqw.write(seq_bytes, seq_id, dtype=str)
        # using str as bytes
        with self.assertRaises(TypeError):
            with dinopy.FastqWriter(path, force_overwrite=True) as fqw:
                fqw.write(seq_str, seq_id, dtype=bytes)
        # try using str as basenumbers
        with self.assertRaises(InvalidDtypeError):
            with dinopy.FastqWriter(path, force_overwrite=True) as fqw:
                fqw.write(seq_str, seq_id, dtype=dinopy.basenumbers)
        # using basenumbers as bytes
        with self.assertRaises(TypeError):
            with dinopy.FastqWriter(path, force_overwrite=True) as fqw:
                fqw.write(seq_basenumbers, seq_id, dtype=bytes)
        # try using basenumbers as str
        with self.assertRaises(TypeError):
            with dinopy.FastqWriter(path, force_overwrite=True) as fqw:
                fqw.write(seq_basenumbers, seq_id, dtype=str)
        # Always fail for two_bit and four_bit (not supported)
        with self.assertRaises(InvalidDtypeError):
            with dinopy.FastqWriter(path, force_overwrite=True) as fqw:
                fqw.write(seq_bytes, seq_id, dtype=dinopy.two_bit)
        with self.assertRaises(InvalidDtypeError):
            with dinopy.FastqWriter(path, force_overwrite=True) as fqw:
                fqw.write(seq_bytes, seq_id, dtype=dinopy.four_bit)


if __name__ == "__main__":
    unittest.main()
