def save(RequiredChannelsXfce, SlotsFolder, slotname):
    for channel in RequiredChannelsXfce:
        os.system(f'xfconf-query -c {channel.strip()} -l > {SlotsFolder}/{channel.strip()}')
        PropertiesFile = open(f'{SlotsFolder}/{channel.strip()}', 'r').readlines()
        os.mkdir(SlotsFolder / slotname / channel.strip())
        os.system(f'mkdir "{SlotsFolder}/{slotname}/{channel.strip())}"')
        for Property in Properties:
            os.system(f'xfconf-query -c {channel.strip()} -p {Property.strip()} > {SlotsFolder}/"{slotname}"/{channel.strip()}/{Property.replace("/","+")}')

        os.system(f'rm {SlotsFolder}/{channel.strip()}')
    os.system(f'xfce4-panel-profiles save {SlotsFolder}/"{slotname}"/"{slotname}"')

    WallpaperPath = os.popen('''xfconf-query -c xfce4-desktop -p /backdrop/screen0/$(xrandr|awk '/\<connected/{print "monitor"$1}')/workspace0/last-image''').read().strip()


def load(RequiredChannelsXfce, SlotsFolder, slotname):
    for PropertyFolders in RequiredChannelsXfce:
        for PropertyFiles in os.listdir(f'{SlotsFolder}/{slotname}/{PropertyFolders}'):
            PropertyFile = open(
                f'{SlotsFolder}/{slotname}/{PropertyFolders}/{PropertyFiles}')
            PropertyFileValue = PropertyFile.read()
            PropertyFilePath = PropertyFiles.replace('+', '/').strip()
            os.popen(
                f'xfconf-query -c "{PropertyFolders.strip()}" -p "{PropertyFilePath}" -s "{PropertyFileValue.strip()}" ')

    os.system(f'xfce4-panel-profiles load {SlotsFolder}/"{slotname}"/"{slotname}"')
    subprocess.Popen(['setsid', 'xfce4-panel', '&>/dev/null'],stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    # Setting Wallpaper
    os.system('xfconf-query -c xfce4-desktop -p /backdrop/screen0/$(xrandr|awk \'/\<connected/{print "monitor"$1}\')/workspace0/last-image -s ' + f'"{SlotsFolder}/{slotname}/Wallpaper.png"')
