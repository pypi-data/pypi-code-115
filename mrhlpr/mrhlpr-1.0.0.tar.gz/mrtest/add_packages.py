# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" High level action of adding packages from MR's artifacts """

import logging
import os
import shutil
import zipfile
import subprocess

import mrhlpr.mr
import mrtest.origin
import mrtest.select_package


def extract_apks(zip_path, selection):
    """
    :param zip_path: to the downloaded artifacts zip
    :param selection: list of apks inside the zip archive
    :returns: list of full paths to extracted apk files
    """
    print("Extracting packages from artifacts archive...")
    extract_dir = f"{os.getenv('HOME')}/.cache/mrhlpr/apks"
    temp_dir = f"{extract_dir}/.temp"
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)

    ret = []
    with zipfile.ZipFile(zip_path) as zip:
        for apk in selection:
            target = f"{extract_dir}/{os.path.basename(apk)}"
            logging.debug(f"Extract {target}")

            # 'zip.extract' appends the full path inside the archive to the
            # output path. The subdirectories are not useful here, so extract
            # to a temp_dir first, then move the apk from subdirs of temp_dir
            # to the target path, then remove the temp_dir.
            zip.extract(apk, temp_dir)
            os.rename(f"{temp_dir}/{apk}", target)
            shutil.rmtree(temp_dir)

            ret += [target]

    return ret


def run_apk_add(origin, mr_id, apk_paths):
    """
    :param origin: gitlab origin information, see gitlab.parse_git_origin()
    :param mr_id: merge request ID
    :param apk_paths: list of apk file paths to be installed
    """
    cmd = [mrtest.get_sudo(),
           "apk", "add",
           "-u",
           "--virtual", mrtest.get_virtual_group(origin, mr_id),
           "--allow-untrusted"] + apk_paths

    print("Installing packages...")
    logging.debug(f"+ {cmd}")
    subprocess.run(cmd)


def confirm_mr_id(origin, mr_id):
    """
    :param origin: gitlab origin information, see gitlab.parse_git_origin()
    :param mr_id: merge request ID
    """
    link = f"https://{origin['host']}/{origin['project_id']}/-/merge_requests/{mr_id}"

    print("Welcome to mrtest, this tool allows downloading and installing")
    print("Alpine packages from merge requests.")
    print()
    print("WARNING: do not use this tool unless you understand what it does,")
    print("otherwise you can get tricked into installing malicious code!")
    print("Malicios code may make your device permanently unusable, steal")
    print("your passwords, and worse.")
    print()
    print("You are about to select and then install packages from:")
    print(link)
    print()
    print("* Did you read and understand the diff?")
    print("* If not, do you at least trust the person who submitted it?")
    print()
    print("If you don't understand the diff and don't trust the submitter,")
    print("answer with 'stop'. Otherwise, if you want to proceed, type in the")
    print("MR ID.")
    print()
    mr_id_input = input("Your answer: ")
    if mr_id_input != str(mr_id):
        print("Aborted.")
        exit(1)
    print("---")


def add_packages(origin, mr_id, no_cache):
    """
    :param origin: gitlab origin information, see gitlab.parse_git_origin()
    :param mr_id: merge request ID
    :param no_cache: instead of using a cache for api calls / downloads where
                     it makes sense, always download a fresh copy
    """
    confirm_mr_id(origin, mr_id)

    zip_path = mrhlpr.mr.get_artifacts_zip(mr_id, no_cache, origin)

    selection = mrtest.select_package.ask(zip_path)
    if selection == []:
        print("No packages selected.")
        exit(0)

    apk_paths = extract_apks(zip_path, selection)
    run_apk_add(origin, mr_id, apk_paths)

    print("All done! Use 'mrtest zap' to uninstall added packages.")
