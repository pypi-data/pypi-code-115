import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from os import path
from pygame import mixer
from twodx import Twodx
import sys, traceback
from datetime import timedelta
import signal


def sigint_handler(sig, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, sigint_handler)


if len(sys.argv) <= 1:
    print("Usage: 2dxplay infile.2dx")
    sys.exit(1)

infile = sys.argv[1]

mixer.init()

try:
    twodx_file = Twodx(path.abspath(infile))
    wav = twodx_file.load(0)
    sound = mixer.Sound(wav)
except:
    traceback.print_exc()
    sys.exit(1)

channel = sound.play()
print(f"Playing: {infile}")
length = timedelta(seconds=int(sound.get_length()))
print(f"Length: {length}")

while channel.get_busy():
    pass