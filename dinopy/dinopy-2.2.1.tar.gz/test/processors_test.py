# -*- coding: utf-8 -*-
"""Tests for processor functions."""
import copy
import random
import unittest
from array import array
from random import choice, seed

import numpy as np

import dinopy
from dinopy import *
from dinopy.definitions import basenumbers
from dinopy.processors import qgrams, reverse_complement, complement, suffix_array


class QGramProcessorTest(unittest.TestCase):

    def test_qgrams_dtype_encoding_combinations(self):
        """Make sure every combination of dtype and encoding is valid, i.e. does not raise an exception
        """
        fp = dinopy.FastaReader("files/testgenome_IUPAC.fasta")
        shp = dinopy.shape.Shape("#######")
        for wrap in (True, False):
            for encoding in [None, dinopy.two_bit, dinopy.four_bit]:
                for dt in [str, bytes, basenumbers, bytearray]:
                    for qgram in qgrams(fp.reads(dtype=dt), shp, dtype=dt, encoding=encoding, wrap=wrap):
                        pass

    def test_qgrams_str_default(self):
        """Does the qgram processor correctly generate str qgrams without changing type?"""
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = ['ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTT', 'CGTTT',
                           'GTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT']
        for qgram1, qgram2 in zip(expected_qgrams, qgrams(fp.reads(dtype=str), shp, dtype=str, encoding=None)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_str_default_wrap(self):
        """Does the qgram processor correctly wrap on two consecutive items?"""
        source = ['ACCCA', 'GTTTG']
        shp = dinopy.shape.Shape("####")
        expected_qgrams = ['ACCC', 'CCCA', 'CCAG', 'CAGT', 'AGTT', 'GTTT', 'TTTG']
        for qgram1, qgram2 in zip(expected_qgrams, qgrams(source, shp, dtype=str, encoding=None, wrap=True)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_str_default_wrap2(self):
        """Does the qgram processor correctly wrap on two consecutive items if the shape is longer than a single item?"""
        source = ['ACCCA', 'GTTTG']
        shp = dinopy.shape.Shape("######")
        expected_qgrams = ['ACCCAG', 'CCCAGT', 'CCAGTT', 'CAGTTT', 'AGTTTG']
        for qgram1, qgram2 in zip(expected_qgrams, qgrams(source, shp, dtype=str, encoding=None, wrap=True)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_bytes_default(self):
        """Does the qgram processor correctly generate bytes qgrams without changing type?"""
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = [b'ACGTA', b'CGTAC', b'GTACG', b'TACGT', b'ACGTA', b'CGTAC', b'GTACG', b'TACGT', b'ACGTT',
                           b'CGTTT', b'GTTTT', b'TTTTT', b'TTTTT', b'TTTTT', b'TTTTT', b'TTTTT', b'TTTTT', b'TTTTT']
        for qgram1, qgram2 in zip(expected_qgrams, qgrams(fp.reads(dtype=bytes), shp, dtype=bytes, encoding=None)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_bytearray_default(self):
        """Does the qgram processor correctly generate bytes qgrams without changing type?"""
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = list(map(bytearray,
                                   [b'ACGTA', b'CGTAC', b'GTACG', b'TACGT', b'ACGTA', b'CGTAC', b'GTACG', b'TACGT',
                                    b'ACGTT', b'CGTTT', b'GTTTT', b'TTTTT', b'TTTTT', b'TTTTT', b'TTTTT', b'TTTTT',
                                    b'TTTTT', b'TTTTT']))
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(fp.reads(dtype=bytearray), shp, dtype=bytearray, encoding=None)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_basenumbers_default(self):
        """Does the qgram processor correctly generate basenumber qgrams without changing type?"""
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = [b'\x00\x01\x02\x03\x00', b'\x01\x02\x03\x00\x01', b'\x02\x03\x00\x01\x02',
                           b'\x03\x00\x01\x02\x03', b'\x00\x01\x02\x03\x00', b'\x01\x02\x03\x00\x01',
                           b'\x02\x03\x00\x01\x02', b'\x03\x00\x01\x02\x03', b'\x00\x01\x02\x03\x03',
                           b'\x01\x02\x03\x03\x03', b'\x02\x03\x03\x03\x03', b'\x03\x03\x03\x03\x03',
                           b'\x03\x03\x03\x03\x03', b'\x03\x03\x03\x03\x03', b'\x03\x03\x03\x03\x03',
                           b'\x03\x03\x03\x03\x03', b'\x03\x03\x03\x03\x03', b'\x03\x03\x03\x03\x03']
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(fp.reads(dtype=basenumbers), shp, dtype=basenumbers, encoding=None)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_auto_default(self):
        """Does the qgram processor correctly generate str qgrams without explicitly specifying str type
        (i.e. by auto detecting the correct type)?
        """
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = ['ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTT', 'CGTTT',
                           'GTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT']
        for qgram1, qgram2 in zip(expected_qgrams, qgrams(fp.reads(dtype=str), shp, dtype=None, encoding=None)):
            self.assertEqual(qgram1, qgram2)

    # Tests for two-bit encoding #
    def test_qgrams_str_twobit(self):
        """Does the qgram processor correctly generate two-bit qgrams from a str-source?"""
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = list(map(dinopy.conversion.encode_twobit,
                                   ['ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTT',
                                    'CGTTT', 'GTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT']))
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(fp.reads(dtype=str), shp, dtype=str, encoding=dinopy.two_bit)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_bytes_twobit(self):
        """Does the qgram processor correctly generate two-bit qgrams from a bytes-source?"""
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = list(map(dinopy.conversion.encode_twobit,
                                   ['ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTT',
                                    'CGTTT', 'GTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT']))
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(fp.reads(dtype=bytes), shp, dtype=bytes, encoding=dinopy.two_bit)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_basenumbers_twobit(self):
        """Does the qgram processor correctly generate two-bit qgrams from a basenumber-source?"""
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = list(map(dinopy.conversion.encode_twobit,
                                   ['ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTT',
                                    'CGTTT', 'GTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT']))
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(fp.reads(dtype=basenumbers), shp, dtype=basenumbers, encoding=dinopy.two_bit)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_auto_twobit(self):
        """Does the qgram processor correctly generate two-bit qgrams from a source with auto detecting the source's type?"""
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = list(map(dinopy.conversion.encode_twobit,
                                   ['ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTT',
                                    'CGTTT', 'GTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT']))
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(fp.reads(dtype=str), shp, dtype=None, encoding=dinopy.two_bit)):
            self.assertEqual(qgram1, qgram2)

    # Tests for four-bit encoding #
    def test_qgrams_str_fourbit(self):
        """Does the qgram processor correctly generate two-bit qgrams from a str-source?"""
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = list(map(dinopy.conversion.encode_fourbit,
                                   ['ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTT',
                                    'CGTTT', 'GTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT']))
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(fp.reads(dtype=str), shp, dtype=str, encoding=dinopy.four_bit)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_bytes_fourbit(self):
        """Does the qgram processor correctly generate two-bit qgrams from a bytes-source?"""
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = list(map(dinopy.conversion.encode_fourbit,
                                   ['ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTT',
                                    'CGTTT', 'GTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT']))
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(fp.reads(dtype=bytes), shp, dtype=bytes, encoding=dinopy.four_bit)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_basenumbers_fourbit(self):
        """Does the qgram processor correctly generate two-bit qgrams from a basenumber-source?"""
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = list(map(dinopy.conversion.encode_fourbit,
                                   ['ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTT',
                                    'CGTTT', 'GTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT']))
        for qgram1, qgram2 in zip(expected_qgrams, qgrams(fp.reads(dtype=basenumbers), shp, dtype=basenumbers,
                                                          encoding=dinopy.four_bit)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_auto_fourbit(self):
        """Does the qgram processor correctly generate two-bit qgrams from a source with auto detecting the source's type?"""
        fp = dinopy.FastaReader("files/tiny_testgenome_1chr.fasta")
        shp = dinopy.shape.Shape("#####")
        expected_qgrams = list(map(dinopy.conversion.encode_fourbit,
                                   ['ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTA', 'CGTAC', 'GTACG', 'TACGT', 'ACGTT',
                                    'CGTTT', 'GTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT', 'TTTTT']))
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(fp.reads(dtype=str), shp, dtype=None, encoding=dinopy.four_bit)):
            self.assertEqual(qgram1, qgram2)

    # Tests for two-bit encoding + wrapping #
    def test_qgrams_str_twobit_wrap(self):
        """Does the qgram processor correctly wrap str items when using two_bit encoding?"""
        source = ['ACCCA', 'GTTTG']
        shp = dinopy.shape.Shape("####")
        expected_qgrams = list(
            map(dinopy.conversion.encode_twobit, ['ACCC', 'CCCA', 'CCAG', 'CAGT', 'AGTT', 'GTTT', 'TTTG']))
        for qgram1, qgram2 in zip(expected_qgrams, qgrams(source, shp, dtype=str, encoding=dinopy.two_bit, wrap=True)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_bytes_twobit_wrap(self):
        """Does the qgram processor correctly wrap bytes items when using two_bit encoding?"""
        source = [b'ACCCA', b'GTTTG']
        shp = dinopy.shape.Shape("####")
        expected_qgrams = list(
            map(dinopy.conversion.encode_twobit, [b'ACCC', b'CCCA', b'CCAG', b'CAGT', b'AGTT', b'GTTT', b'TTTG']))
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(source, shp, dtype=bytes, encoding=dinopy.two_bit, wrap=True)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_basenumbers_twobit_wrap(self):
        """Does the qgram processor correctly wrap basenumber items when using two_bit encoding?"""
        source = [b'\x00\x01\x01\x01\x00', b'\x02\x03\x03\x03\x02']
        shp = dinopy.shape.Shape("####")
        expected_qgrams = list(
            map(dinopy.conversion.encode_twobit, [b'ACCC', b'CCCA', b'CCAG', b'CAGT', b'AGTT', b'GTTT', b'TTTG']))
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(source, shp, dtype=basenumbers, encoding=dinopy.two_bit, wrap=True)):
            self.assertEqual(qgram1, qgram2)

    # Tests for four-bit encoding + wrapping #
    def test_qgrams_str_fourbit_wrap(self):
        """Does the qgram processor correctly wrap str items when using four_bit encoding?"""
        source = ['ACCCA', 'GTTTG']
        shp = dinopy.shape.Shape("####")
        expected_qgrams = list(
            map(dinopy.conversion.encode_fourbit, ['ACCC', 'CCCA', 'CCAG', 'CAGT', 'AGTT', 'GTTT', 'TTTG']))
        for qgram1, qgram2 in zip(expected_qgrams, qgrams(source, shp, dtype=str, encoding=dinopy.four_bit, wrap=True)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_bytes_fourbit_wrap(self):
        """Does the qgram processor correctly wrap bytes items when using four_bit encoding?"""
        source = [b'ACCCA', b'GTTTG']
        shp = dinopy.shape.Shape("####")
        expected_qgrams = list(
            map(dinopy.conversion.encode_fourbit, [b'ACCC', b'CCCA', b'CCAG', b'CAGT', b'AGTT', b'GTTT', b'TTTG']))
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(source, shp, dtype=bytes, encoding=dinopy.four_bit, wrap=True)):
            self.assertEqual(qgram1, qgram2)

    def test_qgrams_basenumbers_fourbit_wrap(self):
        """Does the qgram processor correctly wrap basenumber items when using four_bit encoding?"""
        source = [b'\x00\x01\x01\x01\x00', b'\x02\x03\x03\x03\x02']
        shp = dinopy.shape.Shape("####")
        expected_qgrams = list(
            map(dinopy.conversion.encode_fourbit, [b'ACCC', b'CCCA', b'CCAG', b'CAGT', b'AGTT', b'GTTT', b'TTTG']))
        for qgram1, qgram2 in zip(expected_qgrams,
                                  qgrams(source, shp, dtype=basenumbers, encoding=dinopy.four_bit, wrap=True)):
            self.assertEqual(qgram1, qgram2)

        # Test wrapping

    def test_general_wrap(self):
        source = ['AAAA', 'CCCC', 'GG', 'TTTTTTTTT', 'AAA']
        expected_wraps = ['AAAA', 'AACC', 'CCCC', 'CCGG', 'GG', 'GGTT', 'TTTTTTTTT', 'TTAA', 'AAA']
        for a, b in zip(dinopy.processors._general_wrap(source, 3), expected_wraps):
            self.assertEqual(a, b)

    def test_wrap_bytes(self):
        source = [b'AAAA', b'CCCC', b'GG', b'TTTTTTTTT', b'AAA']
        expected_wraps = [b'AAAA', b'AACC', b'CCCC', b'CCGG', b'GG', b'GGTT', b'TTTTTTTTT', b'TTAA', b'AAA']
        for a, b in zip(dinopy.processors._general_wrap(source, 3), expected_wraps):
            self.assertEqual(a, b)

    def test_wrap_str(self):
        source = ['AAAA', 'CCCC', 'GG', 'TTTTTTTTT', 'AAA']
        expected_wraps = ['AAAA', 'AACC', 'CCCC', 'CCGG', 'GG', 'GGTT', 'TTTTTTTTT', 'TTAA', 'AAA']
        for a, b in zip(dinopy.processors._general_wrap(source, 3), expected_wraps):
            self.assertEqual(a, b)

    def test_wrap_bytearray(self):
        source = list(map(bytearray, [b'AAAA', b'CCCC', b'GG', b'TTTTTTTTT', b'AAA']))
        expected_wraps = list(
            map(bytearray, [b'AAAA', b'AACC', b'CCCC', b'CCGG', b'GG', b'GGTT', b'TTTTTTTTT', b'TTAA', b'AAA']))
        for a, b in zip(dinopy.processors._general_wrap(source, 3), expected_wraps):
            self.assertEqual(a, b)

    # def test_qgrams_wrap_bytes(self):
    #     raise NotImplementedError("Test method stub.")
    #
    # def test_qgrams_wrap_str(self):
    #     raise NotImplementedError("Test method stub.")
    #
    # def test_qgrams_wrap_bytearray(self):
    #     raise NotImplementedError("Test method stub.")

    def test_first_qgram_2bit(self):
        source = "ACG"
        expected_qgram = 0b000110
        self.assertEqual(dinopy.processors._first_qgram_2bit(source), expected_qgram)

    def test_first_qgram_4bit(self):
        source = "ACGN"
        expected_qgram = 0b0001001001001111
        self.assertEqual(dinopy.processors._first_qgram_4bit(source), expected_qgram)

    def test_4bit_qgrams_with_shape(self):
        source = "ACGNA"
        shape = dinopy.shape.Shape("#_##")
        expected_qgrams = [0b000101001111, 0b001011110001]
        self.assertListEqual(list(dinopy.processors._4bit_qgrams_with_shape(source, shape)), expected_qgrams)

    # def test_bisulfite(self):
    #     raise NotImplementedError("Test method stub.")
    #
    # def test_replace_bytearray(self):
    #     source = bytearray(b'ACGT')
    #     expected = bytearray(b'ATGT')
    #     replacement = {b'C': b'T'}
    #     result = processors.replace_bytearray(source, replacement)
    #     self.assertEqual(expected, result)
    #
    # def test_validate_bytearray_dict(self):
    #     raise NotImplementedError("Test method stub.")


class ComplementTest(unittest.TestCase):

    def test_reverse_complement_str(self):
        """Is the reverse complement of strings computed correctly?"""
        seq = "ACGTC"
        expected_seq = "GACGT"
        reversed_seq = reverse_complement(seq)
        self.assertEqual(expected_seq, reversed_seq)

    def test_reverse_complement_bytes(self):
        """Is the reverse complement of bytes computed correctly?"""
        seq = b"ACGTC"
        expected_seq = b"GACGT"
        reversed_seq = reverse_complement(seq)
        self.assertEqual(expected_seq, reversed_seq)

    def test_reverse_complement_basenumbers(self):
        """Is the reverse complement of basenumbers computed correctly?"""
        # encoded as bytes
        seq = b"\x00\x01\x02\x03\x01"
        expected_seq = b"\x02\x00\x01\x02\x03"
        reversed_seq = reverse_complement(seq)
        self.assertEqual(expected_seq, reversed_seq)
        # encoded as list of integer
        seq = [0, 1, 2, 3, 1]
        expected_seq = [2, 0, 1, 2, 3]
        reversed_seq = list(reverse_complement(seq))
        self.assertEqual(expected_seq, reversed_seq)
        # encoded as array of integer
        seq = array("b", [0, 1, 2, 3, 1])
        expected_seq = [2, 0, 1, 2, 3]
        reversed_seq = list(reverse_complement(seq))
        self.assertEqual(expected_seq, reversed_seq)

    def test_reverse_complement_2bit(self):
        """Is the reverse complement of 2bit encoded sequences computed correctly?"""
        seq = 0b0001101101
        expected_seq = 0b1000011011
        reversed_seq = processors.reverse_complement_2bit(seq, seq_length=5)
        self.assertEqual(expected_seq, reversed_seq)

    def test_reverse_complement_2bit_sentinel(self):
        """Is the reverse complement of 2bit encoded sequences computed correctly?"""
        seq = 0b110001101101
        expected_seq = 0b111000011011
        reversed_seq = processors.reverse_complement_2bit(seq, sentinel=True)
        self.assertEqual(expected_seq, reversed_seq)

    def test_reverse_complement_4bit(self):
        """Is the reverse complement of 4bit encoded sequences (with IUPAC) computed correctly?"""
        seq = 0b001001100101  # CSR ←→ YSG
        expected_seq = 0b101001100100
        reversed_seq = processors.reverse_complement_4bit(seq, seq_length=3)
        self.assertEqual(expected_seq, reversed_seq)

    def test_reverse_complement_4bit_sentinel(self):
        """Is the reverse complement of 4bit encoded sequences (with IUPAC) computed correctly?"""
        seq = 0b1111001001100101  # CSR ←→ YSG
        expected_seq = 0b1111101001100100
        reversed_seq = processors.reverse_complement_4bit(seq, sentinel=True)
        self.assertEqual(expected_seq, reversed_seq)

    def test_complement_str(self):
        """Is the complement of strings computed correctly?"""
        seq = "ACGTC"
        expected_seq = "TGCAG"
        reversed_seq = complement(seq)
        self.assertEqual(expected_seq, reversed_seq)

    def test_complement_bytes(self):
        """Is the complement of bytes computed correctly?"""
        seq = b"ACGTC"
        expected_seq = b"TGCAG"
        reversed_seq = complement(seq)
        self.assertEqual(expected_seq, reversed_seq)

    def test_complement_basenumbers(self):
        """Is the complement of basenumbers computed correctly?"""
        # encoded as bytes
        seq = b"\x00\x01\x02\x03\x01"
        expected_seq = b"\x03\x02\x01\x00\x02"
        reversed_seq = complement(seq)
        self.assertEqual(expected_seq, reversed_seq)
        # encoded as list of integer
        seq = [0, 1, 2, 3, 1]
        expected_seq = [3, 2, 1, 0, 2]
        reversed_seq = list(complement(seq))
        self.assertEqual(expected_seq, reversed_seq)
        # encoded as array of integer
        seq = array("b", [0, 1, 2, 3, 1])
        expected_seq = [3, 2, 1, 0, 2]
        reversed_seq = list(complement(seq))
        self.assertEqual(expected_seq, reversed_seq)

    def test_complement_2bit(self):
        """Is the complement of 2bit encoded sequences computed correctly?"""
        seq = 0b110001101101
        expected_seq = 0b001110010010
        reversed_seq = processors.complement_2bit(seq, seq_length=6)
        self.assertEqual(expected_seq, reversed_seq)

    def test_complement_2bit_sentinel(self):
        """Is the complement of 2bit with sentinel encoded sequences computed correctly?"""
        seq = 0b110001101101
        expected_seq = 0b111110010010
        reversed_seq = processors.complement_2bit(seq, sentinel=True)
        self.assertEqual(expected_seq, reversed_seq)

    def test_complement_4bit(self):
        """Is the complement of 4bit encoded sequences (with IUPAC) computed correctly?"""
        seq = 0b000110110110  # CSR ←→ YSG
        expected_seq = 0b111001001001
        reversed_seq = processors.complement_4bit(seq, seq_length=3)
        self.assertEqual(expected_seq, reversed_seq)

    def test_complement_4bit_sentinel(self):
        """Is the complement of 4bit with sentinel encoded sequences (with IUPAC) computed correctly?"""
        seq = 0b1111000110110110  # CSR ←→ YSG
        expected_seq = 0b1111111001001001
        reversed_seq = processors.complement_4bit(seq, sentinel=True)
        self.assertEqual(expected_seq, reversed_seq)

    def test_incorrect_bases(self):
        """Are the right errors generated for non-ACGT characters?"""
        sequence_with_forbidden_characters = "ACGT!"
        self.assertRaises(
            KeyError,
            reverse_complement,
            sequence_with_forbidden_characters,
        )  # this should not work, due to the !


class EncodingTest(unittest.TestCase):

    def test_2bit_qgrams(self):
        seq = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        expected_1_grams = [0] * 33
        expected_10_grams = [0] * 24
        expected_15_grams = [0] * 19
        expected_29_grams = [0] * 5
        expected_30_grams = [0] * 4
        expected_31_grams = [0] * 3

        np.testing.assert_array_equal(list(processors._2bit_qgrams(seq, 1)), expected_1_grams)
        np.testing.assert_array_equal(list(processors._2bit_qgrams(seq, 10)), expected_10_grams)
        np.testing.assert_array_equal(list(processors._2bit_qgrams(seq, 15)), expected_15_grams)
        np.testing.assert_array_equal(list(processors._2bit_qgrams(seq, 29)), expected_29_grams)
        np.testing.assert_array_equal(list(processors._2bit_qgrams(seq, 30)), expected_30_grams)
        np.testing.assert_array_equal(list(processors._2bit_qgrams(seq, 31)), expected_31_grams)

    #        random.seed(42)
    #        seq = "ACGTNURYMKWSBDHV"
    #        expected_16_grams = [3221225472] # including

    def test_2bit_qgrams_with_shape(self):
        seq = "ACGTNURYMKWSBDHV"
        shp = shape.Shape("#_#")
        expected_shp_grams = list(map(dinopy.conversion.encode_twobit,
                                      [b'AG', b'CT', b'GA', b'TT', b'AG', b'TC', b'GA', b'CG', b'AA', b'GC', b'AT',
                                       b'CG', b'TA', b'GA']))
        random.seed(42)
        np.testing.assert_array_equal(list(processors._2bit_qgrams_with_shape(seq, shp)), expected_shp_grams)

    def test_4bit_qgrams(self):
        seq = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        expected_1_grams = [1] * 33
        expected_10_grams = [0b0001000100010001000100010001000100010001] * 24
        expected_14_grams = [0b00010001000100010001000100010001000100010001000100010001] * 20

        np.testing.assert_array_equal(list(processors._4bit_qgrams(seq, 1)), expected_1_grams)
        np.testing.assert_array_equal(list(processors._4bit_qgrams(seq, 10)), expected_10_grams)
        np.testing.assert_array_equal(list(processors._4bit_qgrams(seq, 14)), expected_14_grams)

        seq = "ACGTNURYMKWSBDHV"
        expected_11_grams = [
            0b00010010010010001111100001011010001111001001,  # 'ACGTNURYMKW',
            0b00100100100011111000010110100011110010010110,  # 'CGTNURYMKWS',
            0b01001000111110000101101000111100100101101110,  # 'GTNURYMKWSB',
            0b10001111100001011010001111001001011011101101,  # 'TNURYMKWSBD',
            0b11111000010110100011110010010110111011011011,  # 'NURYMKWSBDH',
            0b10000101101000111100100101101110110110110111,  # 'URYMKWSBDHV',
        ]
        np.testing.assert_array_equal(list(processors._4bit_qgrams(seq, 11)), expected_11_grams)

    def test_encoding_errors(self):
        """Does the encoding fail for q >= 32? Is the correct error raised?"""
        # seq = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        # expected_32_grams = [55340232221128654848]*2
        # np.testing.assert_array_equal(list(processors._2bit_qgrams(seq, 32)), expected_32_grams)
        pass


class SuffixArrayProcessorTest(unittest.TestCase):

    def test_suffix_array(self):
        seq = "immissiissippi$"
        expected_suffix_array = [14, 13, 6, 0, 10, 3, 7, 2, 1, 12, 11, 5, 9, 4, 8]
        sa = suffix_array(seq)
        self.assertListEqual(list(sa)[1:], expected_suffix_array)

    def test_suffix_array_bytearray(self):
        seq = bytearray(b"immissiissippi$")
        expected_suffix_array = [14, 13, 6, 0, 10, 3, 7, 2, 1, 12, 11, 5, 9, 4, 8]
        sa = suffix_array(seq)
        self.assertListEqual(list(sa)[1:], expected_suffix_array)

    def test_suffix_array3(self):
        seq = "cabacbbabacbbc$"

        suffixes = [seq[i:] for i in range(len(seq))]
        sorted_suffixes = sorted(zip(suffixes, range(len(seq))))
        expected_suffix_array = [i for _, i in sorted_suffixes]
        sa = suffix_array(seq)
        self.assertListEqual(list(sa)[1:], expected_suffix_array)

    def test_suffix_array2(self):
        for s in [42, 1337, 0, 7474, 123456789]:
            seed(s)
            seq = bytes("".join([choice(['A', 'C', 'G', 'T']) for _ in range(10000)] + ['\x00']), encoding="ASCII")

            # cpp implementation (dinopy/cpp/sais.cpp)
            sa = suffix_array(seq)

            # naive implementation for comparison
            suffixes = [seq[i:] for i in range(len(seq))]
            sorted_suffixes = sorted(zip(suffixes, range(len(seq))))
            expected_suffix_array = [i for _, i in sorted_suffixes]

            self.assertListEqual(list(sa), expected_suffix_array)


class IUPACAmbiguityTest(unittest.TestCase):
    iupac_mapping = dict({
        65: [65],
        67: [67],
        71: [71],
        84: [84],
        78: [65, 67, 71, 84],
        85: [84],
        82: [65, 71],
        89: [67, 84],
        77: [65, 67],
        75: [71, 84],
        87: [65, 84],
        83: [67, 71],
        66: [67, 71, 84],
        68: [65, 71, 84],
        72: [65, 67, 84],
        86: [65, 67, 71],
        97: [97],
        99: [99],
        103: [103],
        116: [116],
        110: [97, 99, 103, 116],
        117: [116],
        114: [97, 103],
        121: [99, 116],
        109: [97, 99],
        107: [103, 116],
        119: [97, 116],
        115: [99, 103],
        98: [99, 103, 116],
        100: [97, 103, 116],
        104: [97, 99, 116],
        118: [97, 99, 103],
        'A': ['A'],
        'C': ['C'],
        'G': ['G'],
        'T': ['T'],
        'N': ['A', 'C', 'G', 'T'],
        'U': ['T'],
        'R': ['A', 'G'],
        'Y': ['C', 'T'],
        'M': ['A', 'C'],
        'K': ['G', 'T'],
        'W': ['A', 'T'],
        'S': ['C', 'G'],
        'B': ['C', 'G', 'T'],
        'D': ['A', 'G', 'T'],
        'H': ['A', 'C', 'T'],
        'V': ['A', 'C', 'G'],
        'n': ['a', 'c', 'g', 't'],
        'u': ['t'],
        'r': ['a', 'g'],
        'y': ['c', 't'],
        'm': ['a', 'c'],
        'k': ['g', 't'],
        'w': ['a', 't'],
        's': ['c', 'g'],
        'b': ['c', 'g', 't'],
        'd': ['a', 'g', 't'],
        'h': ['a', 'c', 't'],
        'v': ['a', 'c', 'g'],
        0: [0],
        1: [1],
        2: [2],
        3: [3],
        4: [0, 1, 2, 3],
        5: [3],
        6: [0, 2],
        7: [1, 3],
        8: [0, 1],
        9: [2, 3],
        10: [0, 3],
        11: [1, 2],
        12: [1, 2, 3],
        13: [0, 2, 3],
        14: [0, 1, 3],
        15: [0, 1, 2],
    })

    def test_str_no_IUPAC(self):
        """Are strings without IUPAC Amb. Codes kept as are?"""
        seq = "ACGT"
        replaced_seq = dinopy.processors.replace_ambiguities(seq)
        self.assertEqual(seq, replaced_seq)

    def test_bytes_no_IUPAC(self):
        """Are bytes without IUPAC Amb. Codes kept as are?"""
        seq = b"ACGT"
        replaced_seq = dinopy.processors.replace_ambiguities(seq)
        self.assertEqual(seq, replaced_seq)

    def test_bytearray_no_IUPAC(self):
        """Are bytearrays without IUPAC Amb. Codes kept as are?"""
        seq = bytearray(b"ACGT")
        replaced_seq = dinopy.processors.replace_ambiguities(copy.deepcopy(seq))
        self.assertEqual(seq, replaced_seq)

    def test_basenumbers_no_IUPAC(self):
        """Are basenumbers without IUPAC Amb. Codes kept as are?"""
        seq = dinopy.conversion.bytes_to_basenumbers(b"ACGT")
        replaced_seq = dinopy.processors.replace_ambiguities(copy.deepcopy(seq))
        self.assertEqual(seq, replaced_seq)

    # no way to discern between 2 and 4bit
    # def test_bit_encoding_no_IUPAC(self):
    #     """Are bitencoded seqs without IUPAC Amb. Codes kept as are?"""
    #     raise NotImplementedError

    def test_str_with_IUPAC(self):
        """Are IUPAC Amb. Codes in strings replaced correctly?"""
        seq = "ACGTMRWSYKVHDBN"
        replaced_seq = dinopy.processors.replace_ambiguities(seq)
        for base, code in zip(replaced_seq, seq):
            self.assertIn(base, self.iupac_mapping[code])

    def test_bytes_with_IUPAC(self):
        """Are IUPAC Amb. Codes in bytes replaced correctly?"""
        seq = b"ACGTMRWSYKVHDBN"
        replaced_seq = dinopy.processors.replace_ambiguities(seq)
        for base, code in zip(replaced_seq, seq):
            self.assertIn(base, self.iupac_mapping[code])

    def test_bytearray_with_IUPAC(self):
        """Are IUPAC Amb. Codes in bytearrays replaced correctly?"""
        seq = bytearray(b"ACGTMRWSYKVHDBN")
        replaced_seq = dinopy.processors.replace_ambiguities(copy.deepcopy(seq))
        for base, code in zip(replaced_seq, seq):
            self.assertIn(base, self.iupac_mapping[code])

    def test_basenumbers_with_IUPAC(self):
        """Are IUPAC Amb. Codes in basenumbers replaced correctly?"""
        seq = dinopy.conversion.bytes_to_basenumbers(b"ACGTMRWSYKVHDBN")
        replaced_seq = dinopy.processors.replace_ambiguities(copy.deepcopy(seq))
        for base, code in zip(replaced_seq, seq):
            self.assertIn(base, self.iupac_mapping[code])

    # no way to discern between 2 and 4bit
    # def test_bit_encoding_with_IUPAC(self):
    #     """Are IUPAC Amb. Codes in bit encoded seqs replaced correctly?"""
    #     raise NotImplementedError


if __name__ == "__main__":
    unittest.main()
