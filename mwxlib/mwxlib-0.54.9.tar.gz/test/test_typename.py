from pprint import pprint
import wx
import unittest
import mwx
from mwx import typename
from mwx.graphman import Layer

app = wx.App()
frame = mwx.Frame(None)

class TestTokenizerMethods(unittest.TestCase):

    def test_typename(self):
        values = (
            (wx, "wx"),
            (mwx, "mwx"),
            (frame, "Frame"),
            (mwx.Frame, "Frame"),
            (mwx.funcall, "funcall"),
            (mwx.typename, "typename"),
            (mwx.graphman.Layer, "mwx.graphman:Layer"),
            (mwx.graphman.Layer, "mwx.graphman:Layer"),
        )
        for text, result in values:
            self.assertEqual(mwx.typename(text), result)


if __name__ == '__main__':
    unittest.main()
