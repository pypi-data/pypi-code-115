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
# pylint: disable=compare-to-zero,no-self-use
from unittest import TestCase

from responsive.observer import DefaultObserver
from responsive.subject import Subject


class SubjectTest(TestCase):
    """Testing class subject."""

    def test_notify_single_observer(self):
        """Testing a single observer registration."""
        observer = DefaultObserver()
        subject = Subject()
        subject.add_observer(observer)
        subject.notify()
        self.assertEqual(observer.get_count_updates(), 1)

    def test_notify_multiple_observer(self):
        """Testing a multiple observer registration"""
        observers = [DefaultObserver() for _ in range(1000)]
        subject = Subject()

        for observer in observers:
            subject.add_observer(observer)

        subject.notify()

        for observer in observers:
            self.assertEqual(observer.get_count_updates(), 1)

    def test_adding_same_observer_once_only(self):
        """Ensure the same observer is added once only."""
        observer = DefaultObserver()
        subject = Subject()
        subject.add_observer(observer)
        subject.add_observer(observer)
        subject.notify()
        self.assertEqual(observer.get_count_updates(), 1)

    def test_observer_with_special_interest(self):
        """Testing filter mechanism."""
        observer = DefaultObserver()
        observer.set_interests({"value": lambda value: value % 2 == 0})
        subject = Subject()
        subject.add_observer(observer)
        subject.notify(value=2, message="hello world 1")
        subject.notify(value=3, message="hello world 2")
        self.assertEqual(observer.get_count_updates(), 1)

    def test_remove_observer(self):
        """Testing remove of observer."""
        observer = DefaultObserver()
        subject = Subject()
        subject.add_observer(observer)
        subject.remove_observer(observer)
        subject.notify()
        self.assertEqual(observer.get_count_updates(), 0)
