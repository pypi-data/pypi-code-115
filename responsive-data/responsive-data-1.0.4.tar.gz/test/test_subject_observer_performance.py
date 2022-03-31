"""Module test_subject_observer_performance.

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
from responsive.observer import DefaultObserver, DoNothingObserver
from responsive.subject import Subject


def test_subject_observer_with_default_observer_performance(benchmark):
    """Testing simple notification process."""
    observer = DefaultObserver()
    subject = Subject()
    subject.add_observer(observer)
    benchmark(subject.notify)


def test_subject_with_one_observer_with_special_interest_performance(benchmark):
    """Testing advanced notification mechanism."""
    observer = DefaultObserver()
    observer.set_interests(
        {"value": lambda value: value % 2 == 0}  # pylint: disable=compare-to-zero
    )
    subject = Subject()
    subject.add_observer(observer)

    def func():
        """Function for benchmarking."""
        subject.notify(value=2)

    benchmark(func)


def test_subject_with_do_nothing_observer_performance(benchmark):
    """Testing simple notification process with many observers."""
    observer = DoNothingObserver()
    subject = Subject()
    subject.add_observer(observer)
    benchmark(subject.notify)
