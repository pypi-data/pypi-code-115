def save(SlotsFolder, slotname):
    os.system(f'cp -rf ~/.config/i3 {SlotsFolder}/"{slotname}"/configs &>/dev/null')
    nitrogenSave()

def load():
        os.system('i3 reload')
        os.system(f'nitrogen --restore')
