#!/usr/bin/env python3
#@ ====================================================================================================== @#
#> Valheim BepInEx Patcher <#
#< Est. 10/24/21 >#
#@ ====================================================================================================== @#
#$ ====================================================================================================== $#
import logging
from os import chdir
from os.path import dirname
from shutil import copytree
from subprocess import TimeoutExpired, call
from sys import exit as ex
from time import sleep
from typing import Any, NoReturn

from PyLoadBar import load

#@ Declare variables containing patch files directory and destination:
chdir(dirname(__file__))

patch_stable: str = './patch-files/stable' #TODO: Retrieve/download build files with API rather than local storage.
patch_latest: str = './patch-files/bleeding-edge' #TODO: Retrieve/download build files with API rather than local storage.
build_Stable: str = 'v5.19.00'
build_BleedingEdge: str = 'fa9b1ab'
patchDestination: str = 'C:\Program Files (x86)\Steam\steamapps\common\Valheim'
textborder: str = "=".ljust((50),"=")
logFile: str = './logs/logfile.log'
__version__: str = '0.4.0'

#* Establish Logger:
class vbp_Logger():
    """Generater for application logging.
    - Uses built-in Python `logging` module.
    """

    def __init__(self, log_file: str, log_format: str = '[%(asctime)s - %(levelname)s] : %(message)s'):
        """Initialize logger instance

        :param log_file: file to write logs to.
        :type log_file: str
        :param log_format: formatting of log messages, defaults to '%(asctime)s - %(levelname)s - %(message)s'
        :type log_format: str, optional
        """
        self.logger = logging.getLogger(__name__)
        self.log_format = log_format
        self.formatter = logging.Formatter(log_format)
        self.log_file = log_file
        self.fhandler = logging.FileHandler(log_file)
        self.logger.addHandler(self.fhandler)
        self.fhandler.setFormatter(self.formatter)
        self.logger.setLevel(logging.DEBUG)

    def debug(self, msg):
        return self.logger.debug(msg)
    def info(self, msg):
        return self.logger.info(msg)
    def warning(self, msg):
        return self.logger.warning(msg)
    def error(self, msg):
        return self.logger.error(msg, exc_info=False)

logger = vbp_Logger(logFile)


#$ ====================================================================================================== $#


def vbp() -> None | NoReturn:
    """Patcher for BepInEx, a modding console for Valheim.

    - User may choose between several patch installion options:
        - Latest stable build.
        - Latest bleeding-edge (beta) build.
        - Latest stable build, then latest bleeding-edge build afterwards.

    :return: patch BepInEx to chosen build.
    :rtype: None | NoReturn
    """
    logger.info(f'Welcome to the Valheim Bepinex Patcher v{__version__}!\n\n')
    while True:
        logger.debug('Display user menu...')
        choosePatch: str = input(
            f"Welcome to the Valheim Bepinex Patcher!\n\nWhich patch build would you like to install?\n\n{textborder}\n[1.] Stable Release: {build_Stable}\n[2.] Bleeding-Edge Build: {build_BleedingEdge}\n[3.] Full Upgrade (apply both MAIN & BLEEDING-EDGE patches in order of release): {build_Stable} then {build_BleedingEdge}\n[4.] Open Valheim\n[5.] Exit Program\n\n> "
        )
        match choosePatch:
            case '1': stable_patch()
            case '2': BE_patch()
            case '3': full_patch()
            case '4': openValheim()
            case '5':
                logger.info('BepInEx patching process cancelled...\nPreparing to exit...\n')
                load('\nBepInEx patching process cancelled', 'Preparing to exit...', enable_display=False)
                return exitPatcher()
            case _:
                logger.warning(f'Invalid Input:\n==> "{choosePatch}"\n\n==> Must ONLY enter [1] for stable release {build_Stable}, [2] for bleeding-edge build {build_BleedingEdge}, [3] for FULL upgrade (apply both patches in order), or [4] to exit program <==\n')
                print(f'\n\t- ERROR: Invalid Input -\n\nYour Entry:  "{choosePatch}".\n\n==> Must ONLY enter [1] for stable release {build_Stable}, [2] for bleeding-edge build {build_BleedingEdge}, [3] for FULL upgrade (apply both patches in order), or [4] to exit program <==\n\n')
                sleep(1.5)
                continue

        return exitPatcher()


def stable_patch() -> None | NoReturn:
    """Install latest BepInEx stable-build patch version to local directory.

    :return: Installs BepInEx patch.
    :rtype: None
    """
    while True:
        logger.debug('Confirmation prompt for BepInEx stable-build patch...')
        confirmStable: str = input(
            f'\nReally patch BepInEx to latest stable-build v{build_Stable} in location:\n\n====> "{patchDestination}"?\n\n> Enter [y] or [n]:\n{textborder}\n> '
        )
        match confirmStable.lower():
            case 'yes'|'y':
                patch(patch_stable, patchDestination, build_Stable)
                promptStart()
            case 'n'|'no':
                logger.info('BepInEx patching process cancelled...\nPreparing to exit...\n')
                load('\nBepInEx patching process cancelled', 'Preparing to exit...', enable_display=False)
                return exitPatcher()
            case _:
                logger.warning(f'Invalid Input: "{confirmStable}"\n==> Must ONLY enter either [y] for "YES" or [n] for "NO" <==\n')
                print(f'\n\t- ERROR: Invalid Input\n\nYour Entry: "{confirmStable}".\n\n==> Must ONLY enter either [y] for "YES" or [n] for "NO" <==\n\n')
                sleep(1.250)
                continue


def BE_patch() -> None | NoReturn:
    """Install latest BepInEx bleeding-edge patch version to local directory.

    :return: Install bleeding-edge patch to BepInEx directory.
    :rtype: None
    """
    while True:
        logger.debug('Confirmation prompt for BepInEx bleeding-edge patch...')
        confirmLatest: str = input(
            f'\nReally patch BepInEx to the latest bleeding-edge beta build {build_BleedingEdge} in location:\n\n====> "{patchDestination}"?\n\n> Enter [y] or [n]:\n{textborder}\n> '
        )
        match confirmLatest.lower():
            case 'yes'|'y':
                patch(patch_stable, patchDestination, build_BleedingEdge)
                promptStart()
            case 'n'|'no':
                logger.info('BepInEx patching process cancelled...\nPreparing to exit...\n')
                load('\nBepInEx patching process cancelled', 'Preparing to exit...', enable_display=False)
                return exitPatcher()
            case _:
                logger.warning(f'Invalid Input: "{confirmLatest}"\n==> Must ONLY enter either [y] for "YES" or [n] for "NO" <==\n')
                print(f'\n\t- ERROR: Invalid Input\n\nYour Entry: "{confirmLatest}".\n\n==> Must ONLY enter either [y] for "YES" or [n] for "NO" <==\n\n')
                sleep(1.250)
                continue


def full_patch() -> None | bool:
    """Install both latest BepInEx stable build, before then installing latest bleeding-edge build.

    :return: Install both stable and bleeding edge patch builds in order of release to BepInEx directory.
    :rtype: None
    """
    while True:
        logger.debug('Confirmation prompt for BepInEx full patch (install stable then bleeding-edge build)...')
        confirmFull: str = input(
            f'\nReally install latest stable patch {build_Stable} then apply latest "bleeding-edge" build {build_BleedingEdge}?\n> Enter [y] or [n]:\n{textborder}\n> '
        )
        match confirmFull.lower():
            case 'yes'|'y':
                patch(patch_stable, patchDestination, build_Stable)
                patch(patch_stable, patchDestination, build_BleedingEdge)
                return promptStart()
            case 'n'|'no':
                logger.info('BepInEx patching process cancelled...\nPreparing to exit...\n')
                load('\nBepInEx patching process cancelled', 'Preparing to exit...', enable_display=False)
                return exitPatcher()
            case _:
                logger.warning(f'Invalid Input: "{confirmFull}"\n==> Must ONLY enter either [y] for "YES" or [n] for "NO" <==\n')
                print(f'\n\t- ERROR: Invalid Input\n\nYour Entry: "{confirmFull}".\n\n==> Must ONLY enter either [y] for "YES" or [n] for "NO" <==\n\n')
                sleep(1.250)
                continue


def promptStart() -> NoReturn | None:
    """Prompt user to choose whether or not to start the game post patching.

    :return: Exits program or starts game.
    :rtype: NoReturn | None
    """

    while True:
        logger.debug('Display user prompt to start game...\n')
        startPrompt: str = input(
            f'\nStart Game?\n\n> Enter [y] or [n]:\n{"=".ljust(16, "=")}\n> ')
        match startPrompt.lower():
            case 'y'|'yes':
                openValheim()
                return exitPatcher()
            case 'n'|'no':
                logger.info('Patching process successfully completed!\nPreparing to exit...\n')
                load('\nPatching process successfully completed',
                     '\nPreparing to exit...', enable_display=False)
                return exitPatcher()
            case _:
                logger.warning(f'Invalid Input: "{startPrompt}"\n==> Must ONLY enter either [y] for "YES" or [n] for "NO" <==\n')
                print(f'\n\t- ERROR: Invalid Input\n\nYour Entry: "{startPrompt}".\n\n==> Must ONLY enter either [y] for "YES" or [n] for "NO" <==\n\n')
                sleep(1.250)
                continue


def openValheim():
    """Calls command to open "Valheim" within Steam client.
    - Will raise `TimeoutExpired` exception if executable doesn't start within 10 seconds.
        - Prevents program from freezing.

    :return: Start game client.
    :rtype: int | None
    """
    try:
        logger.info('Starting Valheim...\n\n')
        load("\nStarting Game", "Opening Valheim...")
        return call(r"C:\Program Files (x86)\Steam\Steam.exe -applaunch 892970", timeout=10)
    except TimeoutExpired as exp:
        logger.error(f'Having trouble starting game...\n==> {exp}\n')
        print(f'Having trouble starting game...\n==> {exp}\n')


def patch(patchFile: Any, patchLocation: Any, patchTitle: Any) -> Any:
    """Patch BepInEx according to provided parameter values.

    :param patchFile: Directory containing patch files.
    :type patchFile: Any
    :param patchLocation: Location of BepInEx install directory to install files.
    :type patchLocation: Any
    :param patchTitle: Build title of patch to be installed.
    :type patchTitle: Any
    :return: Patch BepInEx with desired version build.
    :rtype: Any
    """
    try:
        logger.info(f'Patching BepInEx build {patchTitle} to location: {patchLocation}...\n\n')
        load(
            f'\nPatching BepInEx build {patchTitle} to location: {patchLocation}',
            f'\nPatch build {patchTitle} successfully installed!')
        copytree(patchFile, patchLocation, dirs_exist_ok=True)
        logger.info(f'Patch build {patchTitle} successfully installed!\n')
    except Exception as exc:
        logger.error(f'Something went wrong...\n==> {exc}\n==> Failed to successfully copy BepInEx build {patchTitle} to location: {patchLocation}...')
        print(f'Something went wrong...\n==> {exc}\n==> Failed to successfully copy BepInEx build {patchTitle} to location: {patchLocation}...')

def exitPatcher() -> None | NoReturn:
    """Exit the application and finalize log.

    :return: Exits application.
    :rtype: None | NoReturn
    """
    logger.info(f'Exiting patcher...\n\n==> End of log...\n{textborder}\n\n')
    return ex()


if __name__ == '__main__':
    vbp()
