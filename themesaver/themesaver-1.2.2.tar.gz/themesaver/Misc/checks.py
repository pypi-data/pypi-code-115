import os, sys, click
sys.path.insert(0, '/opt/themesaver/themesaver/')
from Misc import getDE

def installDependencies():
    if os.path.isfile("/usr/bin/pacman"):
        Dependencies = ['xdotool', 'ttf-ubuntu-font-family', 'imagemagick', 'scrot', 'python-pip', 'wmctrl']
        toinstall = []

        for d in Dependencies:
            installCheck = os.popen(f'pacman -Qs --color always {d} | grep "local" | grep {d}').read()
            if installCheck.strip() == "":
                toinstall.append(d)

        if not len(toinstall) == 0:
            os.system(f'pkexec pacman -S {" ".join(toinstall)}')          
        
    if os.path.isfile("/usr/bin/apt"):
        Dependencies = ['xdotool', 'fonts-ubuntu', 'imagemagick', 'scrot', 'python3-pyqt5', 'python3-pip', 'gnome-shell-extensions', 'gnome-tweaks']
        toinstall = []


def checkCompatibility(DE, WM):
    SupportedDE_WM = ['xfce', 'xfwm4', 'plasma', 'kde','kwin','qtile', 'lg3d', 'gnome', 'gnome shell', 'awesome', 'i3']
    if DE not in SupportedDE_WM and WM not in SupportedDE_WM:
        click.echo(click.style(f'The Desktop Environment {DE} and Window Manager {WM} Is Not Supported', fg='red')) 
        quit()

def generatingRequiredFiles(SlotsFolder):
    def createDir(path):
        if not os.path.isdir(os.path.expanduser(path)):
            os.system(f'mkdir {path}')

    createDir(SlotsFolder)
    createDir('~/.local/share/icons')
    createDir('~/.local/share/applications')
    createDir('~/.config/themesaver')

    if not os.path.isfile(os.path.expanduser('~/.local/share/icons/ThemeSaver.png')):
        os.system('cp /opt/themesaver/GUI/Icons/OG/ThemeSaver.png ~/.local/share/icons')

    if not os.path.isfile(os.path.expanduser('~/.config/themesaver/config.env')):
        os.system('cp /opt/themesaver/config.env ~/.config/themesaver')

    if not os.path.isfile(os.path.expanduser('~/.local/share/applications/ThemeSaver.desktop')):
        os.system('touch ~/.local/share/applications/ThemeSaver.desktop')
        with open(f"{os.environ['HOME']}/.local/share/applications/ThemeSaver.desktop", "w") as DesktopFile:
            DesktopFile.write(
            '''[Desktop Entry]
            Type=Application
            Terminal=false
            Exec=themesaver gui
            Name=ThemeSaver
            Icon=ThemeSaver
            Categories=Utility;
            '''
            )

    noBin = False
    for path in os.environ['PATH'].split(':'):
        if path.endswith('/.local/bin'):
            noBin = True
            break

    shell = os.environ['SHELL'].strip().replace('/', '').replace('usr', '').replace('bin', '')
    if noBin == False:
        click.echo(click.style('Adding local bin to path', fg='blue'))
        if shell == 'bash':
            os.system("echo 'export PATH=~/.local/bin/:$PATH' >> ~/.bashrc")
        elif shell == 'zsh':
            os.system("echo 'export PATH=~/.local/bin/:$PATH' >> ~/.zshrc")

def preChecks():
    checkCompatibility(getDE.getDE(), getDE.getWM())
    installDependencies()
    generatingRequiredFiles(SlotsFolder)