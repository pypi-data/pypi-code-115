#!/usr/bin/python3
"""
    Copyright (c) 2020 HACKER Consulting s.r.o.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

__version__ = "0.0.2"

import argparse
import sys
import urllib

import requests

import ptlibs.ptjsonlib as ptjsonlib
import ptlibs.ptmisclib as ptmisclib


class ptsecurixt:
    def __init__(self, args):
        self.use_json = args.json
        self.ptjsonlib = ptjsonlib.ptjsonlib(self.use_json)
        self.json_no = self.ptjsonlib.add_json("ptsecurixt")
        self.ptjsonlib.add_data(self.json_no, {"test_results": []})

        self.url = self.adjust_url(args.url)
        self.proxy = {"http": args.proxy, "https": args.proxy}
        self.headers = ptmisclib.get_request_headers(args)

    def run(self):
        self.data = []
        self.found_txt_file = False
        known_places = ["security.txt", ".well-known/security.txt"]
        for location in known_places:
            path = self.url + location
            found = self.get_security_txt(path)
        self.is_vulnerable = self.found_txt_file
        self.ptjsonlib.add_data(self.json_no, {"test_results": self.data})
        self.ptjsonlib.set_vulnerable(self.json_no, self.is_vulnerable)
        self.ptjsonlib.set_status(self.json_no, "ok")
        ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Finished", "TITLE", self.use_json))
        ptmisclib.ptprint_(ptmisclib.out_if(self.ptjsonlib.get_all_json(), "", self.use_json))

    def get_security_txt(self, path):
        ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Searching for: {path}", "INFO", self.use_json))
        try:
            response = requests.get(path, headers=self.headers, proxies=self.proxy, verify=False, allow_redirects=False)
            if response.status_code == 200 and "text/plain" in response.headers["content-type"]:
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Found security.txt file", "NOTVULN", self.use_json))
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f"File contents:", "INFO", self.use_json))
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f"{response.text}", "", self.use_json))
                self.data.append({"url": path, "file_contents": response.text})
                self.found_txt_file = True
            else:
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Not found", "VULN", self.use_json))
                self.data.append({"url": path, "file_contents": "null"})
        except Exception:
            ptmisclib.end_error("Cannot connect to website", self.json_no, self.ptjsonlib, self.use_json)

    def adjust_url(self, url):
        ext = urllib.parse.urlparse(url)
        if ext.scheme not in ["http", "https"]:
            ptmisclib.end_error("Missing or wrong scheme, only HTTP protocol is supported.", self.json_no, self.ptjsonlib, self.use_json)
        if not ext.path.endswith("/") and ext.netloc:
            return url + "/"
        else:
            return url


def get_help():
    return [
        {"description": ["Script searches for security.txt file in known locations"]},
        {"usage": ["ptsecurixt <options>"]},
        {"usage_example": [
            "ptsecurixt -u https://www.example.com",
        ]},
        {"options": [
            ["-u",  "--url",                    "<url>",            "Connect to URL"],
            ["-p",  "--proxy",                  "<proxy>",          "Set proxy (e.g. http://127.0.0.1:8080)"],
            ["-H",  "--headers",                "<header:value>",   "Set custom header(s)"],
            ["-ua",  "--user-agent",            "<ua>",             "Set User-Agent header"],
            ["-c",  "--cookie",                 "<cookie>",         "Set cookie"],
            ["-j",  "--json",                   "",                 "Output in JSON format"],
            ["-v",  "--version",                "",                 "Show script version and exit"],
            ["-h",  "--help",                   "",                 "Show this help message and exit"]
        ]
        }]


def parse_args():
    parser = argparse.ArgumentParser(add_help="False", description="ptseruxt <options>")
    parser.add_argument("-u", "--url", type=str, required=True)
    parser.add_argument("-p", "--proxy", type=str)
    parser.add_argument("-H", "--headers", type=ptmisclib.pairs, nargs="+")
    parser.add_argument("-ua", "--user-agent", type=str, default="Penterep Tools")
    parser.add_argument("-c", "--cookie", type=str)
    parser.add_argument("-j", "--json", action="store_true")
    parser.add_argument("-v", "--version", action='version', version=f'{SCRIPTNAME} {__version__}')

    if len(sys.argv) == 1 or "-h" in sys.argv or "--help" in sys.argv:
        ptmisclib.help_print(get_help(), SCRIPTNAME, __version__)
        sys.exit(0)
    args = parser.parse_args()
    ptmisclib.print_banner(SCRIPTNAME, __version__, args.json)
    return args


def main():
    global SCRIPTNAME
    SCRIPTNAME = "ptsecurixt"
    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
    args = parse_args()
    script = ptsecurixt(args)
    script.run()


if __name__ == "__main__":
    main()
