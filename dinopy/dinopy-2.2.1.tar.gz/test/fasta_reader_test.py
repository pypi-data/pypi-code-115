# -*- coding: utf-8 -*-
import unittest

import numpy as np

import dinopy
from dinopy import basenumbers
from dinopy import conversion as cnv
from dinopy.definitions import FastaEntryC, FastaChromosomeInfoC, FastaReadC, FastaChromosomeC
from dinopy.exceptions import MalformedFASTAError

REFERENCE_PATH = "files/testgenome.fasta"
REFERENCE_PATH_ZIPPED = "files/testgenome.fasta.gz"
REFERENCE_PATH_IUPAC = "files/testgenome_IUPAC.fasta"
REFERENCE_PATH_EMPTY = "files/empty.fasta"
REFERENCE_PATH_MALFORMED = "files/broken.fasta"


class TestFastaParserReading(unittest.TestCase):
    """Test the functionality of the FastaReader.
    Including whole-genome and iterator version.

    Here the user-methods versions of the parser are tested.
    """

    def test_parse_entries(self):
        """"""
        expected_entries = [
            FastaEntryC(b'ACGTTGCATCTACGTTGCATCTACGTTGCATC' * 3,
                        b'chromosome_I',
                        96,
                        (0, 96)),
            FastaEntryC(b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' * 5,
                        b'chromosome_II',
                        160,
                        (96, 256)),
            FastaEntryC(b'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT' * 3 + b'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
                        b'chromosome_III',
                        126,
                        (256, 382))
        ]
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        for a, b in zip(fasta_parser.entries(), expected_entries):
            self.assertEqual(a, b)

    def test_parse_genome(self):
        expected_sequence = b"ACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAATTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"
        expected_info = [
            FastaChromosomeInfoC(b'chromosome_I', 96, (0, 96)),
            FastaChromosomeInfoC(b'chromosome_II', 160, (96, 256)),
            FastaChromosomeInfoC(b'chromosome_III', 126, (256, 382))
        ]
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        g = fasta_parser.genome()
        seq = g.sequence
        info = g.info

        self.assertEqual(seq, expected_sequence)
        for a, b in zip(info, expected_info):
            self.assertEqual(a, b)

    def test_parse_reads_with_names(self):
        """"""
        expected_reads = [FastaReadC(b'ACGTTGCATCTACGTTGCATCTACGTTGCATC' * 3, b'chromosome_I'),
                          FastaReadC(b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' * 5, b'chromosome_II'),
                          FastaReadC(b'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT' * 3 + b'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
                                     b'chromosome_III')
                          ]
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        for a, b in zip(fasta_parser.reads(read_names=True), expected_reads):
            self.assertEqual(a, b)

    def test_parse_reads_without_names(self):
        """"""
        expected_reads = [b'ACGTTGCATCTACGTTGCATCTACGTTGCATC' * 3,
                          b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' * 5,
                          b'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT' * 3 + b'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT'
                          ]
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        for a, b in zip(fasta_parser.reads(read_names=False), expected_reads):
            self.assertEqual(a, b)

    def test_random_access_by_name(self):
        """With a fai file available, can we do random access by name?"""
        # 2345678901234567890123456789012345
        expected_sequence = b"GTTGCATCTACGTTGCATCTACGTTGCATCACGT"
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH, write_fai=True)
        sequence = fasta_parser.random_access("chromosome_I", 2, 36)
        self.assertEqual(expected_sequence, sequence)

    def test_random_access_by_index(self):
        """With a fai file available, can we do random access by index?"""
        expected_sequences = [
            b"GTTGCATCTACGTTGCATCTACGTTGCATCACGT",
            b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            b"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
        ]
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH, write_fai=True)
        for chr_nr, expected_sequence in enumerate(expected_sequences):
            sequence = fasta_parser.random_access(chr_nr, 2, 36)
            self.assertEqual(expected_sequence, sequence)

    def test_whole_genome_reading_bytes(self):
        """Is the whole genome returned correctly as bytes?"""
        expected_genome_length = 382
        expected_sequence = b"ACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAATTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)

        g = fasta_parser.genome(dtype=bytes)
        genome = g.sequence
        info = g.info
        computed_genome_length = len(genome)
        self.assertEqual(computed_genome_length, expected_genome_length)
        self.assertEqual(expected_sequence, genome)

    def test_whole_genome_reading_str(self):
        """Is the whole genome returned correctly as string?"""
        expected_genome_length = 382
        expected_sequence = "ACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAATTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)

        g = fasta_parser.genome(dtype=str)
        genome = g.sequence
        info = g.info
        computed_genome_length = len(genome)
        self.assertEqual(computed_genome_length, expected_genome_length)
        self.assertEqual(expected_sequence, genome)

    def test_whole_genome_reading_basenumbers(self):
        """Is the whole genome returned correctly as basenumbers?"""
        expected_genome_length = 382
        expected_sequence = bytes(
            [0, 1, 2, 3, 3, 2, 1, 0, 3, 1, 3, 0, 1, 2, 3, 3, 2, 1, 0, 3, 1, 3, 0, 1, 2, 3, 3, 2, 1, 0, 3, 1, 0, 1, 2, 3,
             3, 2, 1, 0, 3, 1, 3, 0, 1, 2, 3, 3, 2, 1, 0, 3, 1, 3, 0, 1, 2, 3, 3, 2, 1, 0, 3, 1, 0, 1, 2, 3, 3, 2, 1, 0,
             3, 1, 3, 0, 1, 2, 3, 3, 2, 1, 0, 3, 1, 3, 0, 1, 2, 3, 3, 2, 1, 0, 3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
             3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
             3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
             3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, ])
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)

        g = fasta_parser.genome(dtype=basenumbers)
        genome = g.sequence
        info = g.info
        computed_genome_length = len(genome)
        self.assertEqual(computed_genome_length, expected_genome_length)
        self.assertEqual(expected_sequence, genome)

    def test_chromosome_reading_bytes(self):
        """Are the selected chromosomes returned correctly as bytes?"""
        # set up expected results
        expected_length_chr1 = 96
        expected_length_chr1and3 = 222
        expected_sequence_chr1 = b"ACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATC"
        expected_sequence_chr1and3 = b"ACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"
        test_chromosome_selection_1 = 0
        test_chromosome_selection_1and3 = [0, 2]
        test_chromosome_selection_1and3_name = [b"chromosome_I", "chromosome_III"]

        # compute actual results for chr 1
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        entry = list(fasta_parser.chromosomes(selected_chromosomes=test_chromosome_selection_1, dtype=bytes))[0]
        computed_length_chr1 = entry.length
        # check them
        self.assertEqual(computed_length_chr1, expected_length_chr1)
        self.assertEqual(expected_sequence_chr1, entry.sequence)

        # compute actual results for chr 1 and 3
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        entries = list(fasta_parser.chromosomes(selected_chromosomes=test_chromosome_selection_1and3, dtype=bytes))
        computed_length_chr1and3 = entries[0].length + entries[1].length
        # check them
        self.assertEqual(computed_length_chr1and3, expected_length_chr1and3)
        self.assertEqual(expected_sequence_chr1and3, entries[0].sequence + entries[1].sequence)

        # compute actual results for chr 1 and 3 using names
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        entries = list(fasta_parser.chromosomes(selected_chromosomes=test_chromosome_selection_1and3_name, dtype=bytes))
        computed_length_chr1and3 = entries[0].length + entries[1].length
        # check them
        self.assertEqual(computed_length_chr1and3, expected_length_chr1and3)
        self.assertEqual(expected_sequence_chr1and3, entries[0].sequence + entries[1].sequence)

    def test_chromosome_reading_str(self):
        """Are the selected chromosomes returned correctly as string?"""
        # set up expected results
        expected_length_chr1 = 96
        expected_length_chr1and3 = 222
        expected_sequence_chr1 = "ACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATC"
        expected_sequence_chr1and3 = "ACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"
        test_chromosome_selection_1 = 0
        test_chromosome_selection_1and3 = [0, 2]
        test_chromosome_selection_1and3_name = [b"chromosome_I", "chromosome_III"]

        # compute actual results for chr 1
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        entry = list(fasta_parser.chromosomes(selected_chromosomes=test_chromosome_selection_1, dtype=str))[0]
        computed_length_chr1 = entry.length
        # check them
        self.assertEqual(computed_length_chr1, expected_length_chr1)
        self.assertEqual(expected_sequence_chr1, entry.sequence)

        # compute actual results for chr 1 and 3 using indices
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        entries = list(fasta_parser.chromosomes(selected_chromosomes=test_chromosome_selection_1and3, dtype=str))
        computed_length_chr1and3 = entries[0].length + entries[1].length
        # check them
        self.assertEqual(computed_length_chr1and3, expected_length_chr1and3)
        self.assertEqual(expected_sequence_chr1and3, entries[0].sequence + entries[1].sequence)

        # compute actual results for chr 1 and 3 using names
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        entries = list(fasta_parser.chromosomes(selected_chromosomes=test_chromosome_selection_1and3_name, dtype=str))
        computed_length_chr1and3 = entries[0].length + entries[1].length
        # check them
        self.assertEqual(computed_length_chr1and3, expected_length_chr1and3)
        self.assertEqual(expected_sequence_chr1and3, entries[0].sequence + entries[1].sequence)

    def test_chromosome_reading_basenumbers(self):
        """Are the selected chromosomes returned correctly as basenumbers?"""
        # set up expected results
        expected_length_chr1 = 96
        expected_length_chr1and3 = 222
        expected_sequence_chr1 = cnv.string_to_basenumbers(
            "ACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATC")
        expected_sequence_chr1and3 = cnv.string_to_basenumbers(
            "ACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCACGTTGCATCTACGTTGCATCTACGTTGCATCTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT")
        test_chromosome_selection_1 = 0
        test_chromosome_selection_1and3 = [0, 2]
        test_chromosome_selection_1and3_name = [b"chromosome_I", "chromosome_III"]

        # compute actual results for chr 1
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        entry = list(fasta_parser.chromosomes(selected_chromosomes=test_chromosome_selection_1, dtype=basenumbers))[0]
        computed_length_chr1 = entry.length
        # check them
        self.assertEqual(computed_length_chr1, expected_length_chr1)
        self.assertEqual(expected_sequence_chr1, entry.sequence)

        # compute actual results for chr 1 and 3
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        entries = list(
            fasta_parser.chromosomes(selected_chromosomes=test_chromosome_selection_1and3, dtype=basenumbers))
        computed_length_chr1and3 = entries[0].length + entries[1].length
        # check them
        self.assertEqual(computed_length_chr1and3, expected_length_chr1and3)
        self.assertEqual(expected_sequence_chr1and3, entries[0].sequence + entries[1].sequence)

        # compute actual results for chr 1 and 3 using names
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH)
        entries = list(
            fasta_parser.chromosomes(selected_chromosomes=test_chromosome_selection_1and3_name, dtype=basenumbers))
        computed_length_chr1and3 = entries[0].length + entries[1].length
        # check them
        self.assertEqual(computed_length_chr1and3, expected_length_chr1and3)
        self.assertEqual(expected_sequence_chr1and3, entries[0].sequence + entries[1].sequence)

    def test_chromosome_selection_errors(self):
        """Are the correct errors generated for invalid chromosome selection input?"""
        # obsolete. If a single negative or out of bounds value is given, result will simply be empty.
        pass

    def test_lines_bytes(self):
        """Are the lines of the fasta_file returned correctly? (seq as bytes)"""
        expected_lines = [
            b">chromosome_I",
            b"ACGTTGCATCTACGTTGCATCTACGTTGCATC",
            b"ACGTTGCATCTACGTTGCATCTACGTTGCATC",
            b"ACGTTGCATCTACGTTGCATCTACGTTGCATC",
            b">chromosome_II",
            b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            b">chromosome_III",
            b"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            b"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            b"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            b"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
        ]
        fparser = dinopy.FastaReader(REFERENCE_PATH)
        lines = fparser.lines(dtype=bytes)
        for line, expected_line in zip(list(lines), expected_lines):
            if isinstance(expected_line, str) and expected_line[0] == ">":
                self.assertEqual(line, expected_line)
            else:
                np.testing.assert_array_equal(line, expected_line)

        expected_lines_wo_names = [
            b"ACGTTGCATCTACGTTGCATCTACGTTGCATC",
            b"ACGTTGCATCTACGTTGCATCTACGTTGCATC",
            b"ACGTTGCATCTACGTTGCATCTACGTTGCATC",
            b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            b"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            b"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            b"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            b"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
        ]
        fparser = dinopy.FastaReader(REFERENCE_PATH)
        lines = fparser.lines(skip_name_lines=True, dtype=bytes)
        for line, expected_line in zip(list(lines), expected_lines_wo_names):
            if isinstance(expected_line, str) and expected_line[0] == ">":
                self.assertEqual(line, expected_line)
            else:
                np.testing.assert_array_equal(line, expected_line)

    def test_lines_str(self):
        """Are the lines of the fasta_file returned correctly? (seq as string)"""
        expected_lines = [
            b">chromosome_I",
            "ACGTTGCATCTACGTTGCATCTACGTTGCATC",
            "ACGTTGCATCTACGTTGCATCTACGTTGCATC",
            "ACGTTGCATCTACGTTGCATCTACGTTGCATC",
            b">chromosome_II",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            b">chromosome_III",
            "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
        ]
        fparser = dinopy.FastaReader(REFERENCE_PATH)
        lines = fparser.lines(dtype=str)
        self.assertEqual(list(lines), expected_lines)

        expected_lines_wo_names = [
            "ACGTTGCATCTACGTTGCATCTACGTTGCATC",
            "ACGTTGCATCTACGTTGCATCTACGTTGCATC",
            "ACGTTGCATCTACGTTGCATCTACGTTGCATC",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
            "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
        ]
        fparser = dinopy.FastaReader(REFERENCE_PATH)
        lines = fparser.lines(skip_name_lines=True, dtype=str)
        self.assertEqual(list(lines), expected_lines_wo_names)

    def test_lines_basenumbers(self):
        """Are the lines of the fasta_file returned correctly? (seq as basenumbers)"""
        expected_lines = [
            b">chromosome_I",
            cnv.string_to_basenumbers("ACGTTGCATCTACGTTGCATCTACGTTGCATC"),
            cnv.string_to_basenumbers("ACGTTGCATCTACGTTGCATCTACGTTGCATC"),
            cnv.string_to_basenumbers("ACGTTGCATCTACGTTGCATCTACGTTGCATC"),
            b">chromosome_II",
            cnv.string_to_basenumbers("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
            cnv.string_to_basenumbers("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
            cnv.string_to_basenumbers("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
            cnv.string_to_basenumbers("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
            cnv.string_to_basenumbers("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
            b">chromosome_III",
            cnv.string_to_basenumbers("TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"),
            cnv.string_to_basenumbers("TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"),
            cnv.string_to_basenumbers("TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"),
            cnv.string_to_basenumbers("TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"),
        ]
        fparser = dinopy.FastaReader(REFERENCE_PATH)
        lines = fparser.lines(dtype=basenumbers)
        for line, expected_line in zip(list(lines), expected_lines):
            if isinstance(expected_line, str):
                self.assertEqual(line, expected_line)
            else:
                np.testing.assert_array_equal(line, expected_line)

        expected_lines_wo_names = [
            cnv.string_to_basenumbers("ACGTTGCATCTACGTTGCATCTACGTTGCATC"),
            cnv.string_to_basenumbers("ACGTTGCATCTACGTTGCATCTACGTTGCATC"),
            cnv.string_to_basenumbers("ACGTTGCATCTACGTTGCATCTACGTTGCATC"),
            cnv.string_to_basenumbers("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
            cnv.string_to_basenumbers("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
            cnv.string_to_basenumbers("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
            cnv.string_to_basenumbers("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
            cnv.string_to_basenumbers("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"),
            cnv.string_to_basenumbers("TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"),
            cnv.string_to_basenumbers("TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"),
            cnv.string_to_basenumbers("TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"),
            cnv.string_to_basenumbers("TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"),
        ]
        fparser = dinopy.FastaReader(REFERENCE_PATH)
        lines = fparser.lines(skip_name_lines=True, dtype=basenumbers)
        for line, expected_line in zip(list(lines), expected_lines_wo_names):
            self.assertEqual(line, expected_line)

    def test_fai_access(self):
        """Does random whole-chromosome access work getitem-style?"""
        fparser = dinopy.FastaReader(REFERENCE_PATH, write_fai=True)
        expected1 = FastaChromosomeC(b'ACGTTGCATCTACGTTGCATCTACGTTGCATC' * 3,
                                     b'chromosome_I',
                                     96)
        expected2 = FastaChromosomeC(b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' * 5,
                                     b'chromosome_II',
                                     160)
        expected3 = FastaChromosomeC(b'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT' * 3 + b'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
                                     b'chromosome_III',
                                     126, )

        self.assertEqual(list(fparser[b'chromosome_II'])[0], expected2)
        self.assertEqual(list(fparser[1])[0], expected2)
        self.assertEqual(list(fparser['chromosome_II'])[0], expected2)

        chromosomes1_and_3 = list(map(list, fparser[[0, 2]]))
        self.assertEqual(chromosomes1_and_3[0][0], expected1)
        self.assertEqual(chromosomes1_and_3[1][0], expected3)

        chromosomes1_and_3 = list(map(list, fparser[['chromosome_I', 'chromosome_III']]))
        self.assertEqual(chromosomes1_and_3[0][0], expected1)
        self.assertEqual(chromosomes1_and_3[1][0], expected3)

        chromosomes1_and_3 = list(map(list, fparser[[0, 'chromosome_III']]))
        self.assertEqual(chromosomes1_and_3[0][0], expected1)
        self.assertEqual(chromosomes1_and_3[1][0], expected3)

    def test_random_access_getitem_style(self):
        """Does getitem style random access work? i.e. far[(chromosome_name_or_number, start, end)]"""
        expected_sequence = b"GTTGCATCTACGTTGCATCTACGTTGCATCACGT"
        fparser = dinopy.FastaReader(REFERENCE_PATH, write_fai=True)
        sequence = fparser[('chromosome_I', 2, 36)]
        self.assertEqual(expected_sequence, sequence)

        sequences = fparser[[('chromosome_I', 2, 36), ('chromosome_II', 23, 25)]]
        expected_sequences = [b"GTTGCATCTACGTTGCATCTACGTTGCATCACGT", b"AA"]
        self.assertListEqual(expected_sequences, sequences)

    def test_read_empty_fasta_with_read_names(self):
        """Does iterating over reads+names of an empty FASTA file do nothing?"""
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH_EMPTY)
        for _read, _name in fasta_parser.reads(read_names=True):
            self.assertTrue(False, "Reading from an empty iterator should not return any reads.")

    def test_read_empty_fasta(self):
        """Does iterating over reads of an empty FASTA file do nothing?"""
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH_EMPTY)
        for _read in fasta_parser.reads(read_names=False):
            self.assertTrue(False, "Reading from an empty iterator should not return any reads.")

    def test_error_for_malformed_fasta(self):
        """Is the correct error raised for a FASTA file missing a '>' in the first name line?"""
        fasta_parser = dinopy.FastaReader(REFERENCE_PATH_MALFORMED)
        with self.assertRaises(MalformedFASTAError):
            for _read in fasta_parser.reads(read_names=True):
                ...

if __name__ == "__main__":
    unittest.main()
