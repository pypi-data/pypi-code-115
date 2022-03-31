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
import json
import os
from unittest import TestCase

from parameterized import parameterized

from responsive.constants import Operation
from responsive.data import make_responsive
from responsive.observer import DefaultObserver


class TestResponsiveness(TestCase):
    """Testing responsiveness."""

    @parameterized.expand(
        [
            ["pure_dict_with_string.json", "other string"],
            ["pure_dict_with_int.json", 9876543210],
            ["pure_dict_with_float.json", 1234.56789],
            ["pure_dict_with_list.json", [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]],
            ["pure_dict_with_pure_dict.json", {"value": "other string"}],
        ]
    )
    def test_responsiveness_for_pure_dict(self, filename, new_value):
        """Testing responsiveness for pur dictionaries."""
        with open(os.path.join("test", "resources", filename), encoding="utf-8") as handle:
            observer = DefaultObserver()

            data = json.loads(handle.read())
            responsive_data = make_responsive(data)
            responsive_data.add_observer(observer)

            old_value = responsive_data.value
            responsive_data.value = new_value

            if filename.find("with_pure_dict") >= 0:
                self.assertEqual(responsive_data.value, new_value)
                responsive_data.value.value = "yet another string"

                self.assertEqual(observer.get_count_updates(), 2)
                self.assertEqual(responsive_data.value.value, "yet another string")
            else:
                self.assertEqual(observer.get_count_updates(), 1)
                self.assertEqual(responsive_data.value, new_value)

            if filename.find("with_list") < 0:
                self.assertEqual(list(observer)[0][2]["old"], old_value)
                self.assertEqual(list(observer)[0][2]["new"], new_value)
            else:
                self.assertEqual(list(observer)[0][2]["operation"], Operation.VALUE_CHANGED)

    @parameterized.expand(
        [
            ["pure_list_with_string.json", "other string"],
            ["pure_list_with_list.json", ["other string"]],
            ["pure_list_with_pure_dict.json", {"value": "other string"}],
        ]
    )
    def test_responsiveness_for_pure_list(self, filename, new_value):
        """Testing responsiveness for pur lists."""
        with open(os.path.join("test", "resources", filename), encoding="utf-8") as handle:
            observer = DefaultObserver()

            data = json.loads(handle.read())
            responsive_data = make_responsive(data)
            responsive_data.add_observer(observer)

            old_value = responsive_data[0]
            responsive_data[0] = new_value

            if filename.find("with_pure_dict") >= 0:
                self.assertEqual(responsive_data[0], new_value)
                responsive_data[0].value = "yet another string"

                self.assertEqual(observer.get_count_updates(), 2)
                self.assertEqual(responsive_data[0].value, "yet another string")
            else:
                self.assertEqual(observer.get_count_updates(), 1)
                self.assertEqual(responsive_data[0], new_value)

            self.assertEqual(list(observer)[0][2]["old"], old_value)
            self.assertEqual(list(observer)[0][2]["new"], new_value)
