import os, sys, click, time
from themesaver.WindowManagers import qtile
from themesaver.Misc.slotInfo import slotInfo
from themesaver.Misc.getInfo import getGtkTheme, getIconTheme, getCursorTheme, getShell

def saveSlot(SlotsFolder, slotname, DE, WM, Configs):
    # Overwrite Check
    Overwrite = False
    if os.path.isdir(f'{SlotsFolder}/{slotname}'):
        Overwrite = click.prompt(click.style('A slot with that name already exists. Do you want to overwrite it ? [Y/n]', fg='red'), type=str)
        if Overwrite.lower() == 'y':
            click.echo(click.style('Okay overwriting', fg='green'))
            # os.system(f'rm -rf {SlotsFolder}/"{slotname}"')
        else:
            print(click.style('Not overwriting', fg='green'))
            quit()

    click.echo(click.style('======= Saving Slot =======', fg='green'))

    # Creating Slot
    if not Overwrite:
        os.system(f'mkdir -p "{SlotsFolder}/{slotname}"')

    # Taking a Screenshot  
    os.system(f'/opt/themesaver/themesaver/TakeScreenshot.sh &')
    time.sleep(0.5)
    os.system(f'rm {SlotsFolder}/"{slotname}"/Screenshot.png')
    os.system(f'scrot {SlotsFolder}/"{slotname}"/Screenshot.png')
    os.system(f'convert {SlotsFolder}/"{slotname}"/Screenshot.png -resize 470x275 {SlotsFolder}/"{slotname}"/Screenshot.png')

    # Saving All Configs
    for config in Configs:
        click.echo(click.style(f'Saving config: ', fg='green') + click.style(f'{config}', fg='blue'))
        os.system(f'cp -rf ~/.config/{config} {SlotsFolder}/"{slotname}"/configs &>/dev/null')

    if WM == 'qtile':
        qtile.save(SlotsFolder, slotname)

    slotInfo(SlotsFolder, slotname, DE, WM, getGtkTheme(), getIconTheme(), getCursorTheme(), getShell())

