# -*- coding: utf-8 -*-
import unittest

import dinopy


class TestInit(unittest.TestCase):

    def test_qgrams_api(self):
        expected_qgrams = ["ACGT", "CGTA", "GTAC", "TACG", "ACGT"]
        for qgram in dinopy.qgrams("ACGTACGT", 4):
            self.assertEqual(qgram, expected_qgrams.pop(0))

    def test_qgrams_api_with_kwargs(self):
        expected_qgrams = [b"ACGT", b"CGTA", b"GTAC", b"TACG", b"ACGT"]
        sequence = b'ACGTACGT'
        for qgram in dinopy.qgrams(sequence, "####", dtype=bytes):
            self.assertEqual(qgram, expected_qgrams.pop(0))

        sequence = 'ACGTACGT'
        expected_qgrams = ["ACGT", "CGTA", "GTAC", "TACG", "ACGT"]
        for qgram in dinopy.qgrams(sequence, "####", dtype=str):
            self.assertEqual(qgram, expected_qgrams.pop(0))

        sequence = ['ACGTACGT', 'AC']
        expected_qgrams = ["ACGT", "CGTA", "GTAC", "TACG", "ACGT", "CGTA", "GTAC"]
        self.assertEqual(expected_qgrams, list(dinopy.qgrams(sequence, "####", dtype=str, wrap=True)))

        sequence = ['ACGTACGT', 'AC']
        expected_qgrams = ["ACGT", "CGTA", "GTAC", "TACG", "ACGT"]
        self.assertEqual(expected_qgrams, list(dinopy.qgrams(sequence, "####", dtype=str, wrap=False)))

    def test_reverse_complement_str(self):
        seq = "ACGTC"
        expected_seq = "GACGT"
        reversed_seq = dinopy.reverse_complement(seq)
        self.assertEqual(expected_seq, reversed_seq)

    def test_reverse_complement_bytes(self):
        seq = b"ACGTC"
        expected_seq = b"GACGT"
        reversed_seq = dinopy.reverse_complement(seq)
        self.assertEqual(expected_seq, reversed_seq)

    def test_reverse_complement_basenumbers(self):
        seq = b"\x00\x01\x02\x03\x01"
        expected_seq = b"\x02\x00\x01\x02\x03"
        reversed_seq = dinopy.reverse_complement(seq)
        self.assertEqual(expected_seq, reversed_seq)


if __name__ == "__main__":
    unittest.main()
