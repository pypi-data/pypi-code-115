"""Module test_observer.

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
from unittest import TestCase

from responsive.observer import DefaultObserver, Observer, OutputObserver
from responsive.subject import Subject


class ObserverTest(TestCase):
    """Testing class Observer."""

    def test_default(self):
        """Testing observer (update should throw an exception)."""
        observer = Observer()
        self.assertRaises(NotImplementedError, observer.update, None)

    def test_output_observer(self):
        """Testing output observer."""
        messages = []

        def output(message: str) -> None:
            """Test ouput replacement instead of print."""
            messages.append(message)

        observer = OutputObserver(output_function=output)
        observer.update(self, (1, 2, 3), context="test")

        self.assertEqual(len(messages), 1)
        self.assertTrue(messages[0].find("(1, 2, 3)") >= 0)

    def test_default_observer(self):
        """Testing default observer."""
        observer = DefaultObserver()
        subject = Subject()
        subject.add_observer(observer)
        subject.notify("hello", add=" world")

        self.assertEqual(observer.get_count_updates(), 1)
        self.assertEqual(list(observer)[0][1], ("hello",))
        self.assertDictEqual(list(observer)[0][2], {"add": " world"})

        observer.clear()
        self.assertEqual(observer.get_count_updates(), 0)
