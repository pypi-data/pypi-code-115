from runp import runp

import io
import sys
import unittest
from pathlib import Path


class RunPTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.test_path = Path(__file__).parent
        self.runfile = self.test_path.joinpath("testfile.py")
        self.imported_vars = runp.load_runfile(self.runfile)
        self.functions = runp.filter_vars(self.imported_vars)
        self.org_stdout, sys.stdout = sys.stdout, io.StringIO()
        self.org_stderr, sys.stderr = sys.stderr, io.StringIO()

    def tearDown(self) -> None:
        sys.stdout = self.org_stdout
        sys.stderr = self.org_stderr

    def test_load_runfile(self) -> None:
        self.assertTrue(len(self.imported_vars) >= len(self.functions))

    def test_filter_vars(self) -> None:
        self.assertEquals(len(self.functions), 4)

    def test_print_functions(self) -> None:
        out = """Available functions:
Wip.print_it\t
wet\t
wat\tWEEE
wut\tSuper docstring test"""
        runp.print_functions(self.functions)
        output = sys.stdout.getvalue().strip()  # type: ignore
        self.assertEquals(str(output), out)

    def test_print_function_no_docstring(self) -> None:
        out = """Displaying docstring for function wet in module testfile

wet() -> None"""
        runp.print_function(self.functions, "wet")
        output = sys.stdout.getvalue().strip()  # type: ignore
        self.assertEquals(str(output), out)

    def test_print_function_multi_docstring(self) -> None:
        out = """Displaying docstring for function wut in module testfile

wut(text: str, woop: bool = False) -> None
    Super docstring test
    
    Args:
        text (str): The text to print
        woop (boolean, optional): Default false"""
        runp.print_function(self.functions, "wut")
        output = sys.stdout.getvalue().strip()  # type: ignore
        self.assertEquals(str(output), out)

    def test_run_function_noargs(self) -> None:
        out = "testing, 1, 2, 3"
        runp.run_function(self.functions, "wat")
        output = sys.stdout.getvalue().strip()  # type: ignore
        self.assertEquals(str(output), out)

    def test_run_function_args(self) -> None:
        out = "mytext\ndoobey"
        runp.run_function(self.functions, "wut:mytext,doobey")
        output = sys.stdout.getvalue().strip()  # type: ignore
        self.assertEquals(str(output), out)

    def test_run_function_named_args(self) -> None:
        out = "mytext\nTrue"
        runp.run_function(self.functions, "wut:mytext,woop=True")
        output = sys.stdout.getvalue().strip()  # type: ignore
        self.assertEquals(str(output), out)

    def test_run_function_reverse_args(self) -> None:
        out = "mytext\nTrue"
        runp.run_function(self.functions, "wut:woop=True,mytext")
        output = sys.stdout.getvalue().strip()  # type: ignore
        self.assertEquals(str(output), out)

    def test_run_function_wrong_args(self) -> None:
        out = "wut() missing 1 required positional argument: 'text'"
        runp.run_function(self.functions, "wut")
        output = sys.stdout.getvalue().strip()  # type: ignore
        self.assertEquals(str(output), out)

    def test_get_function_nonexistant(self) -> None:
        nofunc = "wutwut"
        out = "No function named '{}' found!".format(nofunc)
        runp.get_function(self.functions, nofunc)
        output = sys.stdout.getvalue().strip()  # type: ignore
        self.assertEquals(str(output), out)

    def test_parse_args_noargs(self) -> None:
        inputstr = "wut"
        cmd, args, kwargs = runp.parse_args(inputstr)
        tup = (cmd, args, kwargs)
        self.assertEquals(tup, ("wut", [], {}))

    def test_parse_args_nokwargs(self) -> None:
        inputstr = "wut:wow,such,good"
        cmd, args, kwargs = runp.parse_args(inputstr)
        tup = (cmd, args, kwargs)
        self.assertEquals(tup, ("wut", ["wow", "such", "good"], {}))

    def test_parse_args(self) -> None:
        inputstr = "wut:arg=wow,'such spaces',arg2=good"
        cmd, args, kwargs = runp.parse_args(inputstr)
        tup = (cmd, args, kwargs)
        self.assertEquals(
            tup,
            ("wut", ["'such spaces'"], {"arg": "wow", "arg2": "good"})
        )

    def test_escape_split_comma(self) -> None:
        inputstr = "wut:arg=wow,'such spaces',arg2=good"
        splitted = ['wut:arg=wow', "'such spaces'", 'arg2=good']
        self.assertEquals(runp._escape_split(',', inputstr), splitted)

    def test_escape_split_equals(self) -> None:
        inputstrs = ['wut:arg=wow', "'such spaces'", 'arg2=good']
        results = [['wut:arg', 'wow'], ["'such spaces'"], ['arg2', 'good']]
        for i, inputstr in enumerate(inputstrs):
            self.assertEquals(runp._escape_split('=', inputstr), results[i])

    def test_escape_split_escape_comma(self) -> None:
        inputstr = "wut:arg=wow\\,,'such spaces',arg2=good"
        splitted = ['wut:arg=wow,', "'such spaces'", 'arg2=good']
        self.assertEquals(runp._escape_split(',', inputstr), splitted)

    def test_escape_split_escape_equals(self) -> None:
        inputstrs = ['wut:arg=wow\\=', "'such spaces'", 'arg2=good']
        results = [['wut:arg', 'wow='], ["'such spaces'"], ['arg2', 'good']]
        for i, inputstr in enumerate(inputstrs):
            self.assertEquals(runp._escape_split('=', inputstr), results[i])
            
    def test_args_empty(self) -> None:
        
        with self.assertRaises(SystemExit):
            runp.main(list())
            
        output: str = sys.stdout.getvalue().strip()  # type: ignore
        error: str = sys.stderr.getvalue().strip()  # type: ignore
        self.assertEqual(output, "")
        self.assertTrue(error.startswith("usage: runp"))
        
    def test_args_is_not_file(self) -> None:
        
        with self.assertRaises(SystemExit):
            runp.main([".\\tests"])
            
        output: str = sys.stdout.getvalue().strip()  # type: ignore
        error: str = sys.stderr.getvalue().strip()  # type: ignore
        self.assertEqual(output, "No such file '.\\tests'")
        self.assertEqual(error, "")
        
    def test_args_is_invalid(self) -> None:
        
        with self.assertRaises(SystemExit):
            runp.main([".\\invalid"])
            
        output: str = sys.stdout.getvalue().strip()  # type: ignore
        error: str = sys.stderr.getvalue().strip()  # type: ignore
        self.assertEqual(output, "No such file '.\\invalid'")
        self.assertEqual(error, "")
    
    def test_args_file_only(self) -> None:
        
        with self.assertRaises(SystemExit):
            runp.main(["./tests/testfile.py"])
            
        output: str = sys.stdout.getvalue().strip()  # type: ignore
        error: str = sys.stderr.getvalue().strip()  # type: ignore
        self.assertEqual(output, "No function was selected!")
        self.assertEqual(error, "")
        
    def test_args_list_short(self) -> None:
        
        out = """Available functions:
Wip.print_it\t
wet\t
wat\tWEEE
wut\tSuper docstring test"""

        with self.assertRaises(SystemExit):
            runp.main(["./tests/testfile.py", "-l"])
            
        output: str = sys.stdout.getvalue().strip()  # type: ignore
        error: str = sys.stderr.getvalue().strip()  # type: ignore
        self.assertEqual(output, out)
        self.assertEqual(error, "")

    def test_args_list_long(self) -> None:
        
        out = """Available functions:
Wip.print_it\t
wet\t
wat\tWEEE
wut\tSuper docstring test"""

        with self.assertRaises(SystemExit):
            runp.main(["./tests/testfile.py", "--list"])
            
        output: str = sys.stdout.getvalue().strip()  # type: ignore
        error: str = sys.stderr.getvalue().strip()  # type: ignore
        self.assertEqual(output, out)
        self.assertEqual(error, "")

    def test_args_details_short(self) -> None:
        
        out = """Displaying docstring for function wut in module testfile

wut(text: str, woop: bool = False) -> None
    Super docstring test
    
    Args:
        text (str): The text to print
        woop (boolean, optional): Default false"""

        with self.assertRaises(SystemExit):
            runp.main(["./tests/testfile.py", "-d", "wut"])
            
        output: str = sys.stdout.getvalue().strip()  # type: ignore
        error: str = sys.stderr.getvalue().strip()  # type: ignore
        self.assertEqual(output, out)
        self.assertEqual(error, "")
        
    def test_args_details_long(self) -> None:
        
        out = """Displaying docstring for function wut in module testfile

wut(text: str, woop: bool = False) -> None
    Super docstring test
    
    Args:
        text (str): The text to print
        woop (boolean, optional): Default false"""

        with self.assertRaises(SystemExit):
            runp.main(["./tests/testfile.py", "--detail", "wut"])
            
        output: str = sys.stdout.getvalue().strip()  # type: ignore
        error: str = sys.stderr.getvalue().strip()  # type: ignore
        self.assertEqual(output, out)
        self.assertEqual(error, "")
        
    def test_args_list(self) -> None:
        
        out = """testing, 1, 2, 3"""

        runp.main(["./tests/testfile.py", "wat"])
            
        output: str = sys.stdout.getvalue().strip()  # type: ignore
        error: str = sys.stderr.getvalue().strip()  # type: ignore
        self.assertEqual(output, out)
        self.assertEqual(error, "")


if __name__ == '__main__':
    unittest.main()
