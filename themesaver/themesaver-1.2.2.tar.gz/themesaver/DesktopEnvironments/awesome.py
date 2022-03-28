def save(SlotsFolder, slotname):
    os.system(f'cp -rf ~/.config/awesome {SlotsFolder}/"{slotname}"/configs &>/dev/null')
    nitrogenSave()  

def load():
    os.system('echo "awesome.restart()" | awesome-client')
    os.system(f'nitrogen --restore')