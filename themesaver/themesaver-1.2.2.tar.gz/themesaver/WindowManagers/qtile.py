import os, sys
# sys.path.insert(0, '/opt/themesaver/themesaver/Misc')
# import saveWallpaper

from Misc import saveWallpaper


def save(SlotsFolder, slotname):
    os.system(f'cp -rf ~/.config/qtile {SlotsFolder}/"{slotname}"/configs &>/dev/null')
    saveWallpaper.nitrogen(SlotsFolder, slotname)

def load():
        os.system('qtile cmd-obj -o cmd -f restart')
        os.system(f'nitrogen --restore')