"""Module test_dictwrapper.

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
# pylint: disable=compare-to-zero,no-self-use
from unittest import TestCase

from responsive.data import make_responsive
from responsive.wrapper import DictWrapper


class DictWrapperTest(TestCase):
    """Testing class DictWrapper."""

    def test_len(self):
        """Testing length of dicitionary."""
        wrapper = DictWrapper({"a": "value a", "b": "value b"}, make_responsive)
        self.assertEqual(len(wrapper), 2)

    def test_eq(self):
        """Testing __eq__."""
        data = {"a": "value a", "b": "value b"}
        wrapper = DictWrapper(data, make_responsive)
        self.assertEqual(wrapper, data)
        self.assertNotEqual(wrapper, 1234)

    def test_hash(self):
        """Testing __hash__."""
        data1 = {"a": "value a", "b": "value b"}
        data2 = {"c": "value c", "d": "value d"}
        wrapper1 = DictWrapper(data1, make_responsive)
        wrapper2 = DictWrapper(data2, make_responsive)
        self.assertEqual(hash(wrapper1), hash(tuple(sorted(data1.items()))))
        self.assertEqual(hash(wrapper2), hash(tuple(sorted(data2.items()))))
