# Copyright 2022 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" GitLab related functions on top of git. """

import hashlib
import urllib.parse
import urllib.request
import os
import shutil
import json
import logging
import re

from . import git
from . import runner


def download_json(origin, pathname, no_cache=False):
    """ Download and parse JSON from an API, with a cache.

        :param origin: gitlab origin information, see gitlab.parse_git_origin()
        :param pathname: gitlab URL pathname (without the usual prefix)
        :param no_cache: download again, even if already cached
        :returns: parsed JSON """
    url = origin["api"] + pathname

    # Prepare cache
    cache_dir = os.getenv("HOME") + "/.cache/mrhlpr/http"
    cache_key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    cache_file = cache_dir + "/" + cache_key
    os.makedirs(cache_dir, exist_ok=True)

    # Check the cache
    if os.path.exists(cache_file) and not no_cache:
        logging.debug("Download " + url + " (cached)")
    else:
        print("Download " + url)
        # Save to temp file
        temp_file = cache_file + ".tmp"
        with urllib.request.urlopen(url) as response:
            with open(temp_file, "wb") as handle:
                shutil.copyfileobj(response, handle)

        # Pretty print JSON (easier debugging)
        with open(temp_file, "r") as handle:
            parsed = json.load(handle)
        with open(temp_file, "w") as handle:
            handle.write(json.dumps(parsed, indent=4))

        # Replace cache file
        if os.path.exists(cache_file):
            os.remove(cache_file)
        os.rename(temp_file, cache_file)

    # Parse JSON from the cache file
    logging.debug(" -> " + cache_file)
    with open(cache_file, "r") as handle:
        return json.load(handle)


def download_artifacts_zip(api, source_project_id, job, no_cache=False):
    """ Download the job artifacts zip file, with a cache.

        :param api: gitlab API url, from parse_git_origin()["api"]
        :param source_project_id: ID, from get_status()["source_project_id"]
        :param job_id: job as returned by gitlab's api, with id and runner
        :param no_cache: download again, even if already cached
        :returns: path to downloaded zip file """

    runner.verify(job["runner"])

    url = f"{api}/projects/{source_project_id}/jobs/{job['id']}/artifacts"

    # Prepare cache
    cache_dir = f"{os.getenv('HOME')}/.cache/mrhlpr/artifacts"
    cache_key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    cache_file = f"{cache_dir}/{cache_key}"
    os.makedirs(cache_dir, exist_ok=True)

    # Check the cache
    if os.path.exists(cache_file) and not no_cache:
        logging.debug(f"Download {url} (cached)")
    else:
        print(f"Download {url}")
        # Save to temp file
        temp_file = cache_file + ".tmp"
        with urllib.request.urlopen(url) as response:
            with open(temp_file, "wb") as handle:
                shutil.copyfileobj(response, handle)

        # Replace cache file
        if os.path.exists(cache_file):
            os.remove(cache_file)
        os.rename(temp_file, cache_file)

    logging.debug(f" -> {cache_file}")
    return cache_file


def parse_git_origin():
    """ Parse the origin remote's URL, so it can easily be used in API calls.
        When adjusting the output of this function, also adjust
        mrtest/origin.py.

        :returns: a dict like the following:
                  {"api": "https://gitlab.com/api/v4",
                   "api_project_id": "postmarketOS%2Fmrhlpr",
                   "full": "git@gitlab.com:postmarketOS/mrhlpr.git",
                   "project": "postmarketOS",
                   "project_id": "postmarketOS/mrhlpr",
                   "host": "gitlab.com"} """
    # Try to get the URL
    url = git.get_remote_url()
    if not url:
        print("Not inside a git repository, or no 'origin' remote configured.")
        exit(1)

    # Find the host
    domains = [
               "gitlab.alpinelinux.org",
               "gitlab.com",
               "gitlab.gnome.org",
               "invent.kde.org",
               ]
    for domain in domains:
        prefixes = [r"^git@" + domain.replace(".", "\\.") + ":",
                    r"^https:\/\/(?:[^\s\@\/]*@)?" +
                    domain.replace(".", "\\.") + "\\/"]
        host = None
        rest = None
        for prefix in prefixes:
            if re.search(prefix, url):
                host = domain
                rest = re.sub(prefix, "", url)
                break
        if host:
            break
    if not host:
        print("Failed to extract gitlab server from: " + url)
        exit(1)

    # project_id: remove ".git" suffix
    project_id = rest
    if project_id.endswith(".git"):
        project_id = project_id[:-1*len(".git")]

    # API URL parts
    api = "https://" + host + "/api/v4"
    api_project_id = urllib.parse.quote_plus(project_id)

    # Find username
    username = re.search(r"^https:\/\/([^\s\@\/]*)@gitlab\.com\/", url)

    # Return everything
    return {"api": api,
            "api_project_id": api_project_id,
            "full": url,
            "project": project_id.split("/", 1)[0],
            "project_id": project_id,
            "host": host,
            "username": username and username.group(1)}
