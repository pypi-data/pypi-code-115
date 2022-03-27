# -*- coding: utf-8 -*-
import gzip
import os
import unittest

from dinopy import OutputOpener

CONTENT = {'t': ["this is a test 1\n", "this is a test 2\n"],
           'b': [b"this is a test 1\n", b"this is a test 2\n"],
           'ta': ["this is a test 3\n"],
           'ba': [b"this is a test 3\n"],
           }


class TestOutputOpener(unittest.TestCase):

    def test_filepath_writing(self):
        path = "filepath"
        modes = ['t', 'b', 'ta', 'ba']
        try:
            os.remove('t' + '_' + path)
            os.remove('b' + '_' + path)
        except:
            pass

        for mode in modes:
            npath = mode.replace('a', '') + '_' + path
            with OutputOpener(npath, mode) as writer:
                for line in CONTENT[mode]:
                    writer.write(line)

        for mode in ['b', 't']:
            with open(mode + '_' + path, 'r' + mode) as reader:
                lines = reader.readlines()
                self.assertListEqual(lines, CONTENT[mode] + CONTENT[mode + 'a'])

    def test_filepath_gz_writing(self):
        path = "filepath.gz"
        modes = ['b', 'ba']
        try:
            os.remove('b' + '_' + path)
        except:
            pass

        for mode in modes:
            npath = mode.replace('a', '') + '_' + path
            with OutputOpener(npath, mode) as writer:
                for line in CONTENT[mode]:
                    writer.write(line)

        for mode in ['b']:
            with gzip.open(mode + '_' + path, 'r' + mode) as reader:
                lines = reader.readlines()
                self.assertListEqual(lines, CONTENT[mode] + CONTENT[mode + 'a'])

    def test_filehandle_writing(self):
        path = "filepath"
        modes = ['t', 'b', 'ta', 'ba']
        try:
            os.remove('t' + '_' + path)
            os.remove('b' + '_' + path)
        except:
            pass

        for mode in modes:
            npath = mode.replace('a', '') + '_' + path
            file_handle = open(npath, mode + 'w' if 'a' not in mode else mode)
            with OutputOpener(file_handle, mode) as writer:
                for line in CONTENT[mode]:
                    writer.write(line)

        for mode in ['b', 't']:
            with open(mode + '_' + path, 'r' + mode) as reader:
                lines = reader.readlines()
                self.assertListEqual(lines, CONTENT[mode] + CONTENT[mode + 'a'])

    def test_filehandle_gz_writing(self):
        path = "filepath.gz"
        modes = ['b', 'ba']
        try:
            os.remove('b' + '_' + path)
        except:
            pass

        for mode in modes:
            npath = mode.replace('a', '') + '_' + path
            file_handle = gzip.open(npath, 'w' if 'a' not in mode else 'a')
            with OutputOpener(file_handle, mode) as writer:
                for line in CONTENT[mode]:
                    writer.write(line)

        for mode in ['b']:
            with gzip.open(mode + '_' + path, 'r') as reader:
                lines = reader.readlines()
                self.assertListEqual(lines, CONTENT[mode] + CONTENT[mode + 'a'])


#    def test_sysout_writing(self):
#        path = sys.stdout
#        mode = 'b'
#        with OutputOpener(path, mode) as writer:
#            for line in CONTENT[mode]:
#                writer.write(line)

if __name__ == "__main__":
    unittest.main()
