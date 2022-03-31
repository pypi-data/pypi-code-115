"""Module test_subject.

The MIT License

Copyright 2022 Thomas Lehmann.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
# pylint: disable=too-few-public-methods
from unittest import TestCase

from responsive.data import make_responsive


class SomeOtherData:
    """Some test data."""

    def __init__(self):
        """Initialize test data."""
        self.some_str_2 = ""
        self.some_int_2 = 0


class SomeData:
    """Some test data."""

    def __init__(self):
        """Initialize test data."""
        self.some_str = ""
        self.some_int = 0
        self.some_list = []
        self.some_other_data = SomeOtherData()


class DataTest(TestCase):
    """Testing data functions."""

    def test_set_and_get_string_value(self):
        """Test set and get of a string value."""
        some_data = make_responsive(SomeData())
        some_data.some_str = "hello world 1"
        some_data.some_int = 1234567890
        some_data.some_other_data.some_str_2 = "hello world 2"
        some_data.some_other_data.some_int_2 = 9876543210

        self.assertEqual(some_data.some_str, "hello world 1")
        self.assertEqual(some_data.some_int, 1234567890)
        self.assertEqual(some_data.some_other_data.some_str_2, "hello world 2")
        self.assertEqual(some_data.some_other_data.some_int_2, 9876543210)

    def test_set_and_get_list_values(self):
        """Test set and get of list values."""
        for some_data in (make_responsive(SomeData()), make_responsive({"some_list": []})):
            some_data.some_list = [1, 2, 3, 4, 5]  # skipcq: PY-W0070
            some_data.some_list.append(6)
            some_data.some_list.remove(2)
            some_data.some_list[-2] = 9

            self.assertEqual(some_data.some_list, [1, 3, 4, 9, 6])
            self.assertEqual(some_data.some_list, some_data.some_list)
            self.assertNotEqual(some_data.some_list, 1234567890)
            self.assertEqual(some_data.some_list[-1], 6)
