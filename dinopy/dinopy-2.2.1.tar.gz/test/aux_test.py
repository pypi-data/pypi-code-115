# -*- coding: utf-8 -*-
"""Tests for all auxiliary function."""
import unittest

from dinopy import auxiliary as aux
from dinopy.definitions import basenumbers


class QGramGeneratorTest(unittest.TestCase):
    """Test the generation of qgrams with the qgram generator."""

    def test_qgram_generator(self):
        """ Does the qgram generator generate all possible 2-qgrams? """
        expected_qgrams = ["AA", "AC", "AG", "AT",
                           "CA", "CC", "CG", "CT",
                           "GA", "GC", "GG", "GT",
                           "TA", "TC", "TG", "TT"]
        two_gram_generator = aux.qgram_generator(2, dtype=str)
        for qgram in two_gram_generator:
            self.assertEqual("".join(qgram), expected_qgrams.pop(0))

    def test_qgram_generator_seq_types(self):
        """Does the qgram generator respect seq_type?"""
        str_generator = aux.qgram_generator(3, dtype=str)
        str_expected = "AAA"
        self.assertEqual(str_expected, str_generator.__next__())
        basenumbers_generator = aux.qgram_generator(3, dtype=basenumbers)
        basenumbers_expected = b"\x00\x00\x00"
        self.assertEqual(basenumbers_expected, basenumbers_generator.__next__())
        bytes_generator = aux.qgram_generator(3, dtype=bytes)
        bytes_expected = b"AAA"
        self.assertEqual(bytes_expected, bytes_generator.__next__())
        bytearray_generator = aux.qgram_generator(3, dtype=bytearray)
        bytearray_expected = bytearray(b"AAA")
        self.assertEqual(bytearray_expected, bytearray_generator.__next__())


if __name__ == "__main__":
    unittest.main()
