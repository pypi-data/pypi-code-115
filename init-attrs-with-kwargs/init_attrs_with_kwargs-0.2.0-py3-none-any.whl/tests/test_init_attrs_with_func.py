from typing import *

from enum import Enum

import unittest

from init_attrs_with_kwargs import cast_set_attrs, set_attrs


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class InitAttrsWKwArgsTest(unittest.TestCase):
    def test_simple(self):
        class BFISE:
            b: bool
            f: float
            i: int
            s: str
            e: Color

        BFISE()

        v1 = set_attrs(BFISE(), b=True)
        self.assertEqual(v1.b, True)

        v2 = set_attrs(BFISE(), b=False)
        self.assertEqual(v2.b, False)

        v3 = set_attrs(BFISE(), b=True, f=2.0, i=3, s="four", e=Color.RED)
        self.assertEqual(v3.b, True)
        self.assertEqual(v3.f, 2.0)
        self.assertEqual(v3.i, 3)
        self.assertEqual(v3.s, "four")
        self.assertEqual(v3.e, Color.RED)

    def test_cast_str_values(self):
        class BFISE:
            b: bool
            f: float
            i: int
            s: str
            e: Color

        v = set_attrs(BFISE(), cast_str_values=False)
        v = set_attrs(BFISE(), cast_str_values=True)

        v = set_attrs(BFISE(), cast_str_values=True, b="", f="2.0", i="3", s="four", e="RED")
        self.assertEqual(v.b, False)
        self.assertEqual(v.f, 2.0)
        self.assertEqual(v.i, 3)
        self.assertEqual(v.s, "four")
        self.assertEqual(v.e, Color.RED)

        v2 = cast_set_attrs(BFISE(), b="", f="2.0", i="3", s="four", e="RED")
        self.assertEqual(v2.b, v.b)
        self.assertEqual(v2.f, v.f)
        self.assertEqual(v2.i, v.i)
        self.assertEqual(v2.s, v.s)
        self.assertEqual(v2.e, v.e)

    def test_cast_str_values_without_need_for_casting(self):
        class BFISE:
            b: bool
            f: float
            i: int
            s: str
            e: Color

        v = cast_set_attrs(BFISE(), b=True, f=2.0, i=3, s="four", e=Color.RED)
        self.assertEqual(v.b, True)
        self.assertEqual(v.f, 2.0)
        self.assertEqual(v.i, 3)
        self.assertEqual(v.s, "four")
        self.assertEqual(v.e, Color.RED)

    def test_cast_str_values_wrong_type(self):
        class BFISE:
            b: bool
            f: float
            i: int
            s: str
            e: Color

        self.assertRaises(ValueError, lambda: set_attrs(BFISE(), cast_str_values=True, f=""))
        self.assertRaises(ValueError, lambda: set_attrs(BFISE(), cast_str_values=True, f="x"))
        self.assertRaises(ValueError, lambda: set_attrs(BFISE(), cast_str_values=True, i=""))
        self.assertRaises(ValueError, lambda: set_attrs(BFISE(), cast_str_values=True, i="x"))
        self.assertRaises(ValueError, lambda: set_attrs(BFISE(), cast_str_values=True, e=""))
        self.assertRaises(ValueError, lambda: set_attrs(BFISE(), cast_str_values=True, e="WHITE"))

    def test_cast_str_values_wrong_syntax(self):
        class FI:
            f: float
            i: int

        self.assertRaises(NameError, lambda: set_attrs(FI(), **{"---f": 1.0}))
        self.assertRaises(NameError, lambda: set_attrs(FI(), **{"-0": 1.0}))

    def test_cast_str_values_wrong_attr_names(self):
        class BFISE:
            b: bool
            f: float
            i: int
            s: str
            e: Color

        self.assertRaises(KeyError, lambda: set_attrs(BFISE(), x=""))

    def test_cast_str_values_optional(self):
        class BFISE_O:
            b: Optional[bool]
            f: Optional[float]
            i: Optional[int]
            s: Optional[str]
            e: Optional[Color]

        v = set_attrs(BFISE_O(), cast_str_values=True, b="", f="2.0", i="3", s="four", e="RED")
        self.assertEqual(v.b, False)
        self.assertEqual(v.f, 2.0)
        self.assertEqual(v.i, 3)
        self.assertEqual(v.s, "four")
        self.assertEqual(v.e, Color.RED)

    def test_cast_str_values_optional_twisted(self):
        class FI_O:
            f: Optional[float]
            i: Optional[int]

        v = set_attrs(FI_O(), cast_str_values=True, f="2.0", i="3")
        self.assertEqual(v.f, 2.0)
        self.assertEqual(v.i, 3)

    def test_cast_str_values_list(self):
        class FI_L:
            fl: List[float]
            il: List[int]

        v = set_attrs(FI_L(), cast_str_values=True, fl=["1.0", "2.0"], il=["3", "4"])
        self.assertEqual(v.fl, [1.0, 2.0])
        self.assertEqual(v.il, [3, 4])


if __name__ == "__main__":
    unittest.main()
