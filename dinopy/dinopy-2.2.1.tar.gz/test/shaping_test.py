# -*- coding: utf-8 -*-
"""Tests for everything that has to do with shaping.
This includes the shape class as well as the windows and apply_shape functions.
"""
import unittest

import numpy as np

from dinopy import shaping as shp
from dinopy.shape import Shape


class WindowsTest(unittest.TestCase):
    """TestCase for all variants of the windows method"""
    test_sequence = "ACGTCCCGTAG"
    test_shape_full = "######"
    test_shape_dont_care_1 = "##__##"
    test_shape_dont_care_2 = "#_#__#"
    test_shape_error_1 = "_#####"
    test_shape_error_2 = "dsjgnlks"
    expected_result_full = [
        "ACGTCC",
        "CGTCCC",
        "GTCCCG",
        "TCCCGT",
        "CCCGTA",
        "CCGTAG",
    ]
    expected_result_dont_care_1 = [
        "ACCC",
        "CGCC",
        "GTCG",
        "TCGT",
        "CCTA",
        "CCAG",
    ]
    expected_result_dont_care_2 = [
        "AGC",
        "CTC",
        "GCG",
        "TCT",
        "CCA",
        "CGG",
    ]

    def test_windows_cython(self):
        """Does the heavily typed cython version of windows return the correct values and raises the right errors?"""
        result_full = list(map("".join, shp.windows(self.test_sequence, self.test_shape_full)))
        result_dont_care_1 = list(map("".join, shp.windows(self.test_sequence, self.test_shape_dont_care_1)))
        result_dont_care_2 = list(map("".join, shp.windows(self.test_sequence, self.test_shape_dont_care_2)))

        self.assertEqual(result_full, self.expected_result_full)
        self.assertEqual(result_dont_care_1, self.expected_result_dont_care_1)
        self.assertEqual(result_dont_care_2, self.expected_result_dont_care_2)

        # CAVE!
        # The creation of a windows-generator (with faulty parameters) does
        # NOT raise an exception. It has to be evaluated for that
        with self.assertRaises(ValueError):
            list(shp.windows(self.test_sequence, self.test_shape_error_1))
        with self.assertRaises(ValueError):
            list(shp.windows(self.test_sequence, self.test_shape_error_2))

    def test_windows_iter(self):
        """Does the heavily typed cython iterator version of windows return the correct values und raises the right errors?"""
        result_full = list(map("".join, shp.windows(self.test_sequence, self.test_shape_full)))
        result_dont_care_1 = list(map("".join, shp.windows(self.test_sequence, self.test_shape_dont_care_1)))
        result_dont_care_2 = list(map("".join, shp.windows(self.test_sequence, self.test_shape_dont_care_2)))

        self.assertEqual(result_full, self.expected_result_full)
        self.assertEqual(result_dont_care_1, self.expected_result_dont_care_1)
        self.assertEqual(result_dont_care_2, self.expected_result_dont_care_2)
        # CAVE!
        # The creation of a windows-generator (with faulty parameters) does
        # NOT raise an exception. It has to be evaluated for that
        with self.assertRaises(ValueError):
            list(shp.windows(self.test_sequence, self.test_shape_error_1))
        with self.assertRaises(ValueError):
            list(shp.windows(self.test_sequence, self.test_shape_error_2))


class ApplyShapeTest(unittest.TestCase):
    """Test the apply shape function"""

    #    def test_apply_shape_2bit(self):
    #        """Do shapes get applied correctly to 2bit encoded qgrams?"""
    #        d = {'A': 0b00, 'C': 0b01, 'G': 0b10, 'T': 0b11}
    #        shape = "##__#_##"
    #        sequence = "ACGTACGT"
    #        expected_sequence = "ACAGT"
    #        twobit_expected_qg = encode(expected_sequence, d)

    #        twobit_qg = encode(sequence, d)
    #        twobit_qg = shp.apply_shape(twobit_qg, shape)
    #        self.assertEqual(twobit_expected_qg, twobit_qg)

    def test_apply_shape(self):
        """Do shapes get applied correctly?"""
        qgrams = [
            bytes([0, 1, 2, 3, 4, 7]),
            bytes([0, 1, 2, 3, 4]),
            "ACGT",
            np.array([0, 1, 2, 3, 4, 7], dtype=int),
        ]
        shapes = [
            "##_###",
            "#####",
            "#__#",
            "##_###",
        ]
        expected_reduced_qgrams = [
            bytes([0, 1, 3, 4, 7]),
            bytes([0, 1, 2, 3, 4]),
            "AT",
            np.array([0, 1, 3, 4, 7], dtype=int),
        ]
        for qgram, shape, exp_qgram in zip(qgrams, shapes, expected_reduced_qgrams):
            computed_reduced_qgram = shp.apply_shape(qgram, shape)
            if isinstance(computed_reduced_qgram, str):
                self.assertEqual(computed_reduced_qgram, exp_qgram)
            else:
                np.testing.assert_array_equal(computed_reduced_qgram, exp_qgram)

    def test_apply_shape_errors(self):
        with self.assertRaises(ValueError):
            qgram = "ACGTA"
            shape = "##"
            shp.apply_shape(qgram, shape)

        with self.assertRaises(ValueError):
            qgram = bytes([0, 1, 2, 3, 0])
            shape = "##########"
            shp.apply_shape(qgram, shape)


class TestShape(unittest.TestCase):
    """Test the creation of shape objects."""

    def test_parse_shape_bshape(self):
        """Do binary numpy arrays get parsed correctly?"""
        shape = np.array([1, 1, 0, 0, 0, 1], dtype=np.uint8)
        expected_bshape = np.array([1, 1, 0, 0, 0, 1], dtype=np.uint8)
        s = Shape(shape)
        np.testing.assert_array_equal(s.bool_shape, expected_bshape)

    def test_parse_shape_str(self):
        """Do string shapes consisting of '#' and '_' get parsed correctly?"""
        shape = "##___#"
        expected_bshape = np.array([1, 1, 0, 0, 0, 1], dtype=np.uint8)
        s = Shape(shape)
        np.testing.assert_array_equal(s.bool_shape, expected_bshape)

    def test_parse_arbitrary_iterable(self):
        """Do arbitrary iterables consisting of exactly two different items get parsed correctly?"""
        shape = [(1, 1), (0, 1), (1, 1), (1, 1)]  # (1, 1) ~ care, (0, 1) ~ don't care
        expected_bshape = np.array([1, 0, 1, 1], dtype=np.uint8)
        s = Shape(shape)
        np.testing.assert_array_equal(s.bool_shape, expected_bshape)

        shape = "^.^"  # ^ ~ care, . ~ don't care
        expected_bshape = np.array([1, 0, 1], dtype=np.uint8)
        s = Shape(shape)
        np.testing.assert_array_equal(s.bool_shape, expected_bshape)

    def test_parse_solid_iterable(self):
        """Do iterables containing only a single element get parsed correctly?"""
        for length in range(1, 101):
            # Test several different lengths to catch uninitialized memory errors. See ticket #4
            shape = [1] * length
            expected_bshape = np.array([1] * length, dtype=np.uint8)
            s = Shape(shape)
            np.testing.assert_array_equal(s.bool_shape, expected_bshape)

    def test_parse_shape_incorrect_str1(self):
        """Do strings starting with '_' get detected?"""
        shape = "_##___#"
        with self.assertRaises(ValueError):
            _ = Shape(shape)

    def test_parse_shape_incorrect_str2(self):
        """Do strings ending with '_' get detected?"""
        shape = "##___#_"
        with self.assertRaises(ValueError):
            _ = Shape(shape)

    def test_parse_shape_incorrect_str3(self):
        """Do strings starting and ending with '_' get detected?"""
        shape = "_##___#_"
        with self.assertRaises(ValueError):
            _ = Shape(shape)

    def test_parse_shape_incorrect_str4(self):
        """Do strings that do not solely consist of '#' and '_' get detected?"""
        shape = "##__!_#"
        with self.assertRaises(ValueError):
            _ = Shape(shape)

    def test_parse_arbitrary_incorrect_iterable(self):
        """Do arbitrary iterables consisting of more than 2 items get detected?"""
        shape = [(1, 1), (0, 1), (1, 1), (1, 1), "cheese"]  # (1, 1) ~ care, (0, 1) ~ don't care
        with self.assertRaises(ValueError):
            _ = Shape(shape)

    def test_is_solid(self):
        shape = Shape("####")
        self.assertTrue(shape.is_solid())

        shape = Shape("##_#")
        self.assertFalse(shape.is_solid())

        shape = Shape("#---#")
        self.assertFalse(shape.is_solid())

        shape = Shape(23)
        self.assertTrue(shape.is_solid())

        shape = Shape("1001")
        self.assertFalse(shape.is_solid())

        shape = Shape(['what'] * 4)
        self.assertTrue(shape.is_solid())

        shape = Shape(['care', 'dont care', 'care', 'dont care', 'care'])
        self.assertFalse(shape.is_solid())


if __name__ == "__main__":
    unittest.main()
