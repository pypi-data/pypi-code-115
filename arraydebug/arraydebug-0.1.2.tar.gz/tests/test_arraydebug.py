#!/usr/bin/env python

"""Tests for `arraydebug` package."""

import numpy as np
import unittest
import arraydebug


class TestArraydebug(unittest.TestCase):
    def setUp(self) -> None:
        arraydebug.enable()

    def tearDown(self) -> None:
        arraydebug.enable()

    def test(self):
        self.assertEqual(repr(1), "1")
        self.assertEqual(repr("abc"), "'abc'")
        self.assertEqual(repr([1, 2, 3, 4]), "[1, 2, 3, 4]")

    def test_enable(self):
        arr = np.arange(4)

        arraydebug.enable()
        self.assertEqual(repr(arr), "<ndarray: shape=(4,), dtype=int64>\narray([0, 1, 2, 3])")

        arraydebug.disable()
        self.assertEqual(repr(arr), "array([0, 1, 2, 3])")

    def test_register_repr(self):
        class A:
            def __init__(self, x):
                self.x = x

        info_fn = lambda a: f"<class A object with x={a.x}>"
        arraydebug.register_repr(A, info_fn)
        self.assertEqual(repr(A(5)), "<class A object with x=5>")
