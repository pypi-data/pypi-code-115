#!/usr/bin/python
# -*- coding: utf-8 -*-

from pathlib import Path
import unittest

from mixstream._MixStream import VorbisFileError
from mixstream._MixStream import VorbisFileMixStream


class VorbisFileMixStreamTest(unittest.TestCase):

    def setUp(self):
        default_filename = "guitar_drumrolls.ogg"
        self.test_directory = Path(__file__).parent
        self.filename = bytes(self.test_directory / default_filename)
        self.channel = 5
        self.length = 227.97061224489795

    def test_init_file_error(self):
        with self.assertRaises(IOError):
            VorbisFileMixStream(b"")

    def test_init_filetype_error(self):
        with self.assertRaises(VorbisFileError):
            other_filename = self.test_directory / "notes_drumrolls.mid"
            VorbisFileMixStream(bytes(other_filename))

    def test_play(self):
        mixstream = VorbisFileMixStream(self.filename)
        _play = mixstream.play(self.channel)

        self.assertEqual(_play, self.channel)

    def test_is_playing(self):
        mixstream = VorbisFileMixStream(self.filename)
        mixstream.play(self.channel)

        self.assertTrue(mixstream.is_playing())

    def test_stop(self):
        mixstream = VorbisFileMixStream(self.filename)
        mixstream.play(self.channel)
        mixstream.stop()

        self.assertFalse(mixstream.is_playing())

    def test_seek(self):
        time = 22
        mixstream = VorbisFileMixStream(self.filename)
        _seek = mixstream.seek(time)

        self.assertEqual(_seek, time)

    def test_get_position_init(self):
        mixstream = VorbisFileMixStream(self.filename)
        position = mixstream.get_position()

        self.assertEqual(position, -1)

    def test_get_position_seek(self):
        time = 22
        mixstream = VorbisFileMixStream(self.filename)
        mixstream.seek(time)
        mixstream.play(self.channel)
        position = mixstream.get_position()

        self.assertEqual(position, time)

    def test_get_length(self):
        mixstream = VorbisFileMixStream(self.filename)
        _length = mixstream.get_length()

        self.assertEqual(_length, self.length)
