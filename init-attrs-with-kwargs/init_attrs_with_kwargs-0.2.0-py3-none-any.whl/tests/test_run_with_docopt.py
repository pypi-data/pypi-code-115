from typing import *

import unittest

import docopt

from init_attrs_with_kwargs import InitAttrsWKwArgs


class RunWithDocopt(unittest.TestCase):
    def test_sample2(self):
        doc = """Get total of numbers.

        Usage:
        sample2 [--maximum|--minimum|--average] <number>...

        Options:
        --maximum, -M     Get the largest number.
        --minimum, -m     Get the smallest number.
        --average, -a     Get the average of the numbers.
        """

        class MyArgs(InitAttrsWKwArgs):
            maximum: bool
            minimum: bool
            average: bool
            number: List[float]

        args = MyArgs(_cast_str_values=True, **docopt.docopt(doc, ["-m", "10.0"]))
        self.assertTrue(args.minimum)
        self.assertFalse(args.maximum)
        self.assertFalse(args.average)
        self.assertSequenceEqual(args.number, [10.0])

        args = MyArgs(_cast_str_values=True, **docopt.docopt(doc, ["-m", "10.0", "20.0"]))
        self.assertTrue(args.minimum)
        self.assertFalse(args.maximum)
        self.assertFalse(args.average)
        self.assertSequenceEqual(args.number, [10.0, 20.0])

        args = MyArgs(_cast_str_values=True, **docopt.docopt(doc, ["-M", "10.0", "20.0", "30.0"]))
        self.assertFalse(args.minimum)
        self.assertTrue(args.maximum)
        self.assertFalse(args.average)
        self.assertSequenceEqual(args.number, [10.0, 20.0, 30.0])

        args = MyArgs(_cast_str_values=True, **docopt.docopt(doc, ["10.0"]))
        self.assertFalse(args.minimum)
        self.assertFalse(args.maximum)
        self.assertFalse(args.average)
        self.assertSequenceEqual(args.number, [10.0])

        self.assertRaises(docopt.DocoptExit, lambda: MyArgs(_cast_str_values=True, **docopt.docopt(doc, ["-m", "-M", "10.0"])))
        self.assertRaises(docopt.DocoptExit, lambda: MyArgs(_cast_str_values=True, **docopt.docopt(doc, [])))

    def test_sample3(self):
        doc = """Compile and run a program.

        Usage:
        sample3 compile [options] <program>
        sample3 run [options] [<program>]

        Options:
        --verbose, -v     Verbose.
        """

        class MyArgs(InitAttrsWKwArgs):
            compile: bool
            run: bool
            program: Optional[str]
            verbose: bool

        args = MyArgs(_cast_str_values=True, **docopt.docopt(doc, ["compile", "hoge.c"]))
        self.assertTrue(args.compile)
        self.assertFalse(args.run)
        self.assertEqual(args.program, "hoge.c")
        self.assertFalse(args.verbose)

        self.assertRaises(docopt.DocoptExit, lambda: MyArgs(_cast_str_values=True, **docopt.docopt(doc, ["compile"])))

        args = MyArgs(_cast_str_values=True, **docopt.docopt(doc, ["run", "hoge.exe"]))
        self.assertFalse(args.compile)
        self.assertTrue(args.run)
        self.assertEqual(args.program, "hoge.exe")
        self.assertFalse(args.verbose)

        args = MyArgs(_cast_str_values=True, **docopt.docopt(doc, ["run"]))
        self.assertFalse(args.compile)
        self.assertTrue(args.run)
        self.assertEqual(args.program, None)
        self.assertFalse(args.verbose)

        args = MyArgs(_cast_str_values=True, **docopt.docopt(doc, ["run", "--verbose"]))
        self.assertFalse(args.compile)
        self.assertTrue(args.run)
        self.assertEqual(args.program, None)
        self.assertTrue(args.verbose)


if __name__ == "__main__":
    unittest.main()
