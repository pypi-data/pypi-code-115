3  # !/usr/bin/python3
# -*- coding: utf-8 -*-
"""This file contains all tests for methods of the FastaWriter."""
import os
import shutil
import sys
import unittest

import dinopy
from dinopy.fasta_writer import ChromosomeFormatError

KEEP_TMPFILES = False


# TODO: add creation tests to Fasta Writer


class FastaWriterTest(unittest.TestCase):
    """Test creation and initialization of FastaWriter."""

    def setUp(self):
        """Create a temporary directory for the test files.
        """
        self.tmpdir = "/tmp/FastaWriterTests_Creation"
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
        """Is a FastaWriter initialized correctly from a file object?"""
        f = open(os.path.join(self.tmpdir, "create_from_file.fasta"), 'wb')
        with dinopy.FastaWriter(f, append=False) as fqw:
            fqw.write_entry((b'ACGTTGCA', b'a testread'))
        f = open(os.path.join(self.tmpdir, "create_from_file.fasta"), 'ab')
        with dinopy.FastaWriter(f, append=True) as fqw:
            fqw.write_entry((b'ACGTTGCA', b'a testread'))

    def test_creation_stdout(self):
        """Is a FastaWriter initialized correctly on stdout?"""
        f = sys.stdout
        with dinopy.FastaWriter(f) as fqw:
            fqw.write_entry((b'ACGTTGCA', b'a testread'))
        # f = sys.stdout.buffer
        # with dinopy.FastaWriter(f) as fqw:
        #     fqw.write_entry((b'ACGTTGCA', b'a testread'))

    def test_creation_str(self):
        """Is a FastaWriter initialized correctly from a str filepath?"""
        path = os.path.join(self.tmpdir, "create_from_string.fasta")
        with dinopy.FastaWriter(path) as fqw:
            fqw.write_entry((b'ACGTTGCA', b'a testread'))
        path = os.path.join(self.tmpdir, "create_from_string.fasta")
        with dinopy.FastaWriter(path, append=True) as fqw:
            fqw.write_entry((b'ACGTTGCA', b'a testread'))

    def test_creation_bytes(self):
        """Is a FastaWriter initialized correctly from bytes filepath?"""
        path = os.path.join(self.tmpdir.encode(), b"create_from_bytes.fasta")
        with dinopy.FastaWriter(path) as fqw:
            fqw.write_entry((b'ACGTTGCA', b'a testread'))
        path = os.path.join(self.tmpdir.encode(), b"create_from_bytes.fasta")
        with dinopy.FastaWriter(path, append=True) as fqw:
            fqw.write_entry((b'ACGTTGCA', b'a testread'))

    def test_open_various_sources(self):
        cases = [
            "/tmp/somefile.txt",
            b"/tmp/otherfile.txt",
            open("/tmp/3.txt", 'w'),  # TODO think of a solution. expects str, not bytes, because it's a TextIOWrapper
            open("/tmp/3.txt", 'wb'),
            open("/tmp/3.txt.gz", 'w'),
            # TODO think of a solution. expects str, not bytes, because it's a TextIOWrapper
            open("/tmp/3.txt.gz", 'wb'),
            sys.stdout,
        ]
        for case in cases:
            with dinopy.FastaWriter(case, force_overwrite=True) as faw:
                print(case)
                faw.write_entry((b'ACGTTGCA', b'a testread'))


class WriteGenomeTest(unittest.TestCase):
    """Check all methods dealing with writing from a whole genome."""

    test_sequence_str = "ACGTACGTACGTTTTTTTTTTT"
    test_sequence_basenumbers = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
    test_sequence_bytes = bytes(test_sequence_str, "utf-8")
    test_seqeunce_length = 22
    test_name = b"tiny_testgenome"
    test_width = 10
    test_chr_info = [(b"tiny_testgenome chr1", 15, (0, 15)), (b"tiny_testgenome chr2", 7, (15, 22)), ]

    def setUp(self):
        """Create a temporary directory for the test files.
        """
        self.tmpdir = "/tmp/FastaWriterTests_WriteGenome"
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)

    def tearDown(self):
        if not KEEP_TMPFILES:
            try:
                shutil.rmtree(self.tmpdir)  # remove tmp dir after tests
            except OSError:
                print("Problem deleting tempfile")
                raise

    def test_name_str(self):
        """Does writing a single chromosome with name work?"""
        path = os.path.join(self.tmpdir, "single_chr_with_name.fasta")
        expected_result = [
            ">tiny_testgenome\n",
            "ACGTACGTAC\n",
            "GTTTTTTTTT\n",
            "TT\n",
        ]
        # write sequence
        with dinopy.FastaWriter(path, force_overwrite=True, line_width=self.test_width) as writer:
            writer.write_genome(
                self.test_sequence_str,
                self.test_name,
                dtype=str,
            )
        # check if file is empty
        if os.stat(path).st_size == 0:
            raise ValueError("File is empty")
        # check if all lines are written correctly
        with open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)

    def test_chr_info_str(self):
        """Does writing several chromosomes with chr_info work?"""
        path = os.path.join(self.tmpdir, "two_chr_with_chrinfo.fasta")
        expected_result = [
            ">tiny_testgenome chr1\n",
            "ACGTACGTAC\n",
            "GTTTT\n",
            ">tiny_testgenome chr2\n",
            "TTTTTTT\n",
        ]
        # write sequence
        with dinopy.FastaWriter(path, force_overwrite=True, line_width=self.test_width) as writer:
            writer.write_genome(
                self.test_sequence_str,
                self.test_chr_info,
                dtype=str,
            )
        # check if file is empty
        if os.stat(path).st_size == 0:
            raise ValueError("File is empty")
        # check if all lines are written correctly
        with open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)

    def test_name_basenumbers(self):
        """Does writing a single chromosomes with name from basenumbers work?"""
        path = os.path.join(self.tmpdir, "single_chr_basenumbers.fasta")
        expected_result = [
            ">tiny_testgenome\n",
            "ACGTACGTAC\n",
            "GTTTTTTTTT\n",
            "TT\n",
        ]
        # write sequence
        with dinopy.FastaWriter(path, force_overwrite=True, line_width=self.test_width) as writer:
            writer.write_genome(
                self.test_sequence_basenumbers,
                self.test_name,
                dtype=dinopy.basenumbers,
            )
        #  check if file is empty
        if os.stat(path).st_size == 0:
            raise ValueError("File is empty")
        #  check if all lines are written correctly
        with open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)

    def test_chr_info_basenumbers(self):
        """Does writing several chromosomes with chr_info from basenumberswork?"""
        path = os.path.join(self.tmpdir, "two_chr_basenumbers.fasta")
        expected_result = [
            ">tiny_testgenome chr1\n",
            "ACGTACGTAC\n",
            "GTTTT\n",
            ">tiny_testgenome chr2\n",
            "TTTTTTT\n",
        ]
        # write sequence
        with dinopy.FastaWriter(path, force_overwrite=True, line_width=self.test_width) as writer:
            writer.write_genome(
                self.test_sequence_basenumbers,
                self.test_chr_info,
                dtype=dinopy.basenumbers,
            )
        # check if file is empty
        if os.stat(path).st_size == 0:
            raise ValueError("File is empty")
        # check if all lines are written correctly
        with open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)

    def test_write_genome_name_bytes(self):
        """Does writing a genome with one chromosome from bytes work?"""
        path = os.path.join(self.tmpdir, "write_genome_1chr_bytes.fasta")
        expected_result = [
            ">tiny_testgenome\n",
            "ACGTACGTAC\n",
            "GTTTTTTTTT\n",
            "TT\n",
        ]
        # write sequence
        with dinopy.FastaWriter(path, force_overwrite=True, line_width=self.test_width) as writer:
            writer.write_genome(
                self.test_sequence_bytes,
                self.test_name,
                dtype=bytes,
            )
        #  check if file is empty
        if os.stat(path).st_size == 0:
            raise ValueError("File is empty")
        #  check if all lines are written correctly
        with open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)

    def test_write_genome_chr_info_bytes(self):
        """Does writing a genome with two chromosomes from bytes work?"""
        path = os.path.join(self.tmpdir, "write_genome_2chr_bytes.fasta")
        expected_result = [
            ">tiny_testgenome chr1\n",
            "ACGTACGTAC\n",
            "GTTTT\n",
            ">tiny_testgenome chr2\n",
            "TTTTTTT\n",
        ]
        # write sequence
        with dinopy.FastaWriter(path, force_overwrite=True, line_width=self.test_width) as writer:
            writer.write_genome(
                self.test_sequence_bytes,
                self.test_chr_info,
                dtype=bytes,
            )
        # check if file is empty
        if os.stat(path).st_size == 0:
            raise ValueError("File is empty")
        # check if all lines are written correctly
        with open(path, 'r') as written_file:
            for line, expected_line in zip(written_file, expected_result):
                self.assertEqual(line, expected_line)

    def test_error_handling(self):
        """Do invalid inputs result in reasonable errors?"""
        valid_path = os.path.join(self.tmpdir, "errors.fasta")

        #  check if write raises ValueError for invalid types of chromosome_info
        with self.assertRaises(ChromosomeFormatError):
            with dinopy.FastaWriter(valid_path, force_overwrite=True) as writer:
                writer.write_genome("ACGT", 42)
        #  check if write raises ValueError for invalid types of chromosome_info
        with self.assertRaises(ChromosomeFormatError):
            with dinopy.FastaWriter(valid_path, force_overwrite=True) as writer:
                writer.write_genome("ACGT", (42, 23, 0, 8, 15, 47, 11))
        #  check if error is raised for already existing file
        with self.assertRaises(FileExistsError):
            # make sure the file exists
            with open(valid_path, "wb") as test_file:
                test_file.write(b"spam, bacon and eggs.")
            with dinopy.FastaWriter(valid_path, write_fai=False, force_overwrite=False, append=False) as writer:
                writer.write_genome("ACGT", b"foo")
        #  check if genome boundaries are respected
        with self.assertRaises(IndexError):
            with dinopy.FastaWriter(valid_path, force_overwrite=True) as writer:
                writer.write_genome(
                    "ACGT",
                    [(b"foo", 4, (0, 5))],
                )
        with self.assertRaises(IndexError):
            with dinopy.FastaWriter(valid_path, force_overwrite=True) as writer:
                writer.write_genome(
                    "ACGT",
                    [(b"foo", 4, (-1, 3))],
                )
        with self.assertRaises(IndexError):
            with dinopy.FastaWriter(valid_path, force_overwrite=True) as writer:
                writer.write_genome(
                    "ACGT",
                    [(b"foo", 4, (3, 1))],
                )


class WriteChromosomesTest(unittest.TestCase):
    """Check all methods dealing with the writing of single chromosomes."""

    def setUp(self):
        """Create a temporary directory for the test files.
        """
        self.tmpdir = "/tmp/FastaWriterTests_WriteChromosomes"
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)

    def tearDown(self):
        if not KEEP_TMPFILES:
            try:
                shutil.rmtree(self.tmpdir)  # remove tmp dir after tests
            except OSError:
                print("Problem deleting tempfile")
                raise

    def test_write_chromosomes_str(self):
        """Does write_chromosomes work with str input?"""
        chromosomes = [
            ("ACGTACGT", b"chr1"),
            ("TTTTTTTT", b"chr2"),
            ("ACGTACGT", b"chr3"),
            ("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
             b"chr4"),
        ]
        filepath = os.path.join(self.tmpdir, "write_4chr_str.fasta")
        expected_file_content = [
            ">chr1\n",
            "ACGTACGT\n",
            ">chr2\n",
            "TTTTTTTT\n",
            ">chr3\n",
            "ACGTACGT\n",
            ">chr4\n",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            "AAAAAAAAAAAAAAAAAAAA\n"
        ]
        with dinopy.FastaWriter(filepath, force_overwrite=True, line_width=80) as writer:
            writer.write_chromosomes(
                chromosomes,
                dtype=str,
            )
        with open(filepath, 'r') as testfile:
            for line, expected_line in zip(testfile, expected_file_content):
                self.assertEqual(line, expected_line)

    def test_write_chromosomes_basenumbers(self):
        """Does write_chromosomes work with basenumbers input?"""
        chromosomes = [
            ([0, 1, 2, 3, 0, 1, 2, 3], b"chr1"),
            ([3, 3, 3, 3, 3, 3, 3, 3], b"chr2"),
            ([0, 1, 2, 3, 0, 1, 2, 3], b"chr3"),
            (
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], b"chr4"),
        ]
        filepath = os.path.join(self.tmpdir, "write_4chr_basenumbers.fasta")
        expected_file_content = [
            ">chr1\n",
            "ACGTACGT\n",
            ">chr2\n",
            "TTTTTTTT\n",
            ">chr3\n",
            "ACGTACGT\n",
            ">chr4\n",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            "AAAAAAAAAAAAAAAAAAAA\n"
        ]
        with dinopy.FastaWriter(filepath, force_overwrite=True, line_width=80) as writer:
            writer.write_chromosomes(
                chromosomes,
                dtype=dinopy.basenumbers,
            )
        with open(filepath, 'r') as testfile:
            for line, expected_line in zip(testfile, expected_file_content):
                self.assertEqual(line, expected_line)

    def test_write_chromosomes_bytes(self):
        """Does write_chromosomes work with bytes input?"""
        chromosomes = [
            (b"ACGTACGT", b"chr1"),
            (b"TTTTTTTT", b"chr2"),
            (b"ACGTACGT", b"chr3"),
            (b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
             b"chr4"),
        ]
        filepath = os.path.join(self.tmpdir, "write_4chr_byte.fasta")
        expected_file_content = [
            ">chr1\n",
            "ACGTACGT\n",
            ">chr2\n",
            "TTTTTTTT\n",
            ">chr3\n",
            "ACGTACGT\n",
            ">chr4\n",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            "AAAAAAAAAAAAAAAAAAAA\n"
        ]
        with dinopy.FastaWriter(filepath, force_overwrite=True, line_width=80) as writer:
            writer.write_chromosomes(
                chromosomes,
                dtype=bytes,
            )
        with open(filepath, 'r') as testfile:
            for line, expected_line in zip(testfile, expected_file_content):
                self.assertEqual(line, expected_line)


class WriteChromosomeTest(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory for the test files.
        """
        self.tmpdir = "/tmp/FastaWriterTests_AppendChromosomes"
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)

    def tearDown(self):
        if not KEEP_TMPFILES:
            try:
                shutil.rmtree(self.tmpdir)  # remove tmp dir after tests
            except OSError:
                print("Problem deleting tempfile")
                raise

    def test_write_entry(self):
        """Are single entries written correctly?"""
        base_file_content = [
            ">chr1\n",
            "ACGTACGT\n",
        ]
        expected_file_content = [
            ">chr1\n",
            "ACGTACGT\n",
            ">chr2\n",
            "TTTTTTTT\n",
            ">chr3\n",
            "ACGTACGT\n",
            ">chr4\n",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            "AAAAAAAAAAAAAAAAAAAA\n"
        ]
        chromosome_a = ("TTTTTTTT", b"chr2")
        chromosome_b = ([0, 1, 2, 3, 0, 1, 2, 3], b"chr3")
        chromosome_c = (
        b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        b"chr4")
        filepath = os.path.join(self.tmpdir, "test_append_chr.fasta")
        # write test file
        with open(filepath, 'w') as testfile:
            for line in base_file_content:
                testfile.write(line)
        with dinopy.FastaWriter(filepath, append=True, line_width=80) as writer:
            writer.write_entry(
                chromosome_a,
                dtype=str,
            )
            writer.write_entry(
                chromosome_b,
                dtype=dinopy.basenumbers,
            )
            writer.write_entry(
                chromosome_c,
                dtype=bytes,
            )
        with open(filepath, 'r') as testfile:
            for line, expected_line in zip(testfile, expected_file_content):
                self.assertEqual(line, expected_line)

    def test_write_chromosome(self):
        """Same as test_write_entry"""
        """Are single entries written correctly?"""
        base_file_content = [
            ">chr1\n",
            "ACGTACGT\n",
        ]
        expected_file_content = [
            ">chr1\n",
            "ACGTACGT\n",
            ">chr2\n",
            "TTTTTTTT\n",
            ">chr3\n",
            "ACGTACGT\n",
            ">chr4\n",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            "AAAAAAAAAAAAAAAAAAAA\n"
        ]
        chromosome_a = ("TTTTTTTT", b"chr2")
        chromosome_b = ([0, 1, 2, 3, 0, 1, 2, 3], b"chr3")
        chromosome_c = (
        b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        b"chr4")
        filepath = os.path.join(self.tmpdir, "test_append_chr.fasta")
        # write test file
        with open(filepath, 'w') as testfile:
            for line in base_file_content:
                testfile.write(line)
        with dinopy.FastaWriter(filepath, append=True, line_width=80) as writer:
            writer.write_chromosome(
                chromosome_a,
                dtype=str,
            )
            writer.write_chromosome(
                chromosome_b,
                dtype=dinopy.basenumbers,
            )
            writer.write_chromosome(
                chromosome_c,
                dtype=bytes,
            )
        with open(filepath, 'r') as testfile:
            for line, expected_line in zip(testfile, expected_file_content):
                self.assertEqual(line, expected_line)


class ValidateChrInfoTest(unittest.TestCase):
    """Check if the validation of chromosome info works"""

    def test_normalize_chr_info(self):
        """Are chromosome info normalized correctly?"""
        chr_info = [
            (b"chr1", 12, (0, 12)),
            (b"chr2", 13, (12, 25)),
            (b"chr3", 17, (25, 42)),
        ]
        genome_length = 42
        with dinopy.FastaWriter(sys.stdout, write_fai=False) as writer:  # create a dummy fasta writer
            self.assertEqual(
                chr_info,
                writer._normalize_chromosome_info(chr_info, genome_length)
            )

    def test_normalize_chr_info_name(self):
        """Are chromosome info normalized correctly?"""
        genome_name = "spam genome"
        genome_length = 42
        faw = dinopy.FastaWriter(sys.stdout, write_fai=False)  # create a dummy fasta writer
        self.assertEqual(
            [(b"spam genome", 42, (0, genome_length))],
            faw._normalize_chromosome_info(genome_name, genome_length)
        )

    def test_error_handling(self):
        """Are chromosome info normalized correctly?"""
        index_error_cases = [
            [(b"name", 12, (12, 0))],  # wrong order
            [(b"name", 12, (0, 10))],  # interval size != length
            [(b"name", 55, (0, 55))],  # interval stop > genome length
            [(b"name", 1, (55, 56))],  # interval start > genome length
        ]
        chromosome_format_error_cases = [
            [b"foo"],  # wrong tuple format
            (b"name", 1, (55, 56)),  # single tuple (not list)
        ]
        genome_length = 42
        with dinopy.FastaWriter(sys.stdout, write_fai=False) as writer:  # create a dummy fasta writer
            for chr_info in index_error_cases:
                with self.assertRaises(IndexError):
                    writer._normalize_chromosome_info(chr_info, genome_length)
            for chr_info in chromosome_format_error_cases:
                with self.assertRaises(ChromosomeFormatError):
                    writer._normalize_chromosome_info(chr_info, genome_length)


class WriteEntriesTest(unittest.TestCase):
    """Check all methods dealing with the writing of single chromosomes."""

    def setUp(self):
        """Create a temporary directory for the test files.
        """
        self.tmpdir = "/tmp/FastaWriterTests_WriteChromosomes"
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)

    def tearDown(self):
        if not KEEP_TMPFILES:
            try:
                shutil.rmtree(self.tmpdir)  # remove tmp dir after tests
            except OSError:
                print("Problem deleting tempfile")
                raise

    def test_write_entries_str(self):
        """Does write_entries work with str input?"""
        chromosomes = [
            ("ACGTACGT", b"chr1"),
            ("TTTTTTTT", b"chr2"),
            ("ACGTACGT", b"chr3"),
            ("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
             b"chr4"),
        ]
        filepath = os.path.join(self.tmpdir, "write_4chr_str.fasta")
        expected_file_content = [
            ">chr1\n",
            "ACGTACGT\n",
            ">chr2\n",
            "TTTTTTTT\n",
            ">chr3\n",
            "ACGTACGT\n",
            ">chr4\n",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            "AAAAAAAAAAAAAAAAAAAA\n"
        ]
        with dinopy.FastaWriter(filepath, force_overwrite=True, line_width=80) as writer:
            writer.write_entries(
                chromosomes,
                dtype=str,
            )
        with open(filepath, 'r') as testfile:
            for line, expected_line in zip(testfile, expected_file_content):
                self.assertEqual(line, expected_line)

    def test_write_entries_basenumbers(self):
        """Does write_entries work with basenumbers input?"""
        chromosomes = [
            ([0, 1, 2, 3, 0, 1, 2, 3], b"chr1"),
            ([3, 3, 3, 3, 3, 3, 3, 3], b"chr2"),
            ([0, 1, 2, 3, 0, 1, 2, 3], b"chr3"),
            (
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], b"chr4"),
        ]
        filepath = os.path.join(self.tmpdir, "write_4chr_basenumbers.fasta")
        expected_file_content = [
            ">chr1\n",
            "ACGTACGT\n",
            ">chr2\n",
            "TTTTTTTT\n",
            ">chr3\n",
            "ACGTACGT\n",
            ">chr4\n",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            "AAAAAAAAAAAAAAAAAAAA\n"
        ]
        with dinopy.FastaWriter(filepath, force_overwrite=True, line_width=80) as writer:
            writer.write_entries(
                chromosomes,
                dtype=dinopy.basenumbers,
            )
        with open(filepath, 'r') as testfile:
            for line, expected_line in zip(testfile, expected_file_content):
                self.assertEqual(line, expected_line)

    def test_write_entries_bytes(self):
        """Does write_entries work with bytes input?"""
        chromosomes = [
            (b"ACGTACGT", b"chr1"),
            (b"TTTTTTTT", b"chr2"),
            (b"ACGTACGT", b"chr3"),
            (b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
             b"chr4"),
        ]
        filepath = os.path.join(self.tmpdir, "write_4chr_byte.fasta")
        expected_file_content = [
            ">chr1\n",
            "ACGTACGT\n",
            ">chr2\n",
            "TTTTTTTT\n",
            ">chr3\n",
            "ACGTACGT\n",
            ">chr4\n",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
            "AAAAAAAAAAAAAAAAAAAA\n"
        ]
        with dinopy.FastaWriter(filepath, force_overwrite=True, line_width=80) as writer:
            writer.write_entries(
                chromosomes,
                dtype=bytes,
            )
        with open(filepath, 'r') as testfile:
            for line, expected_line in zip(testfile, expected_file_content):
                self.assertEqual(line, expected_line)

    def test_write_entry_list(self):
        # writer._write_entry_list()
        # raise NotImplementedError("Test method stub.")
        pass


if __name__ == "__main__":
    unittest.main()
