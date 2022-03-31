"""Module test_listwrapper.

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
from responsive.wrapper import ListWrapper


class ListWrapperTest(TestCase):
    """Testing class ListWrapper."""

    def test_len(self):
        """Testing length of list."""
        wrapper = ListWrapper([1, 2, 3, 4], make_responsive)
        self.assertEqual(len(wrapper), 4)

    def test_set_and_get_by_index(self):
        """Testing __setitem__ and __getitem__."""
        data = [1, 2, 3, 4]
        wrapper = ListWrapper([1, 2, 3, 4], make_responsive)
        wrapper[2] = 9
        self.assertEqual(wrapper[2], 9)
        self.assertEqual(data, [1, 2, 3, 4])

    def test_eq(self):
        """Testing __eq__."""
        data = [1, 2, 3, 4]
        wrapper = ListWrapper(data, make_responsive)
        self.assertEqual(wrapper, data)
        self.assertNotEqual(wrapper, 1234)

    def test_iter(self):
        """Testing in and not in."""
        data = [1, 2, 3, 4]
        wrapper = ListWrapper(data, make_responsive)
        self.assertTrue(2 in wrapper)
        self.assertTrue(5 not in wrapper)
        self.assertEqual(list(wrapper), data)
