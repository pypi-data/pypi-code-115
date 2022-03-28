#!/usr/bin/python3
"""
    Apache Multiviews Detection & Enumeration Tool

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

__version__ = "0.0.3"

import argparse
import copy
import re
import sys
import urllib

import requests

from ptlibs import ptjsonlib, ptmisclib
from ptthreads import ptthreads


class ptmultiviews:
    def __init__(self, args):
        self.use_json = args.json
        self.ptjsonlib = ptjsonlib.ptjsonlib(self.use_json)
        self.json_no = self.ptjsonlib.add_json(SCRIPTNAME)

        self.url_domain_file_test = None
        self.domain_file_test = None
        self.url_test = None
        self.file_test = None

        self.output_file = self.get_output_file(args.output)
        self.headers = ptmisclib.get_request_headers(args)
        self.timeout = 15
        self.redirects = args.redirects
        self.proxies = {"http": args.proxy, "https": args.proxy}

        self.without_extensions = args.without_extensions
        self.without_domain = args.without_domain
        self.all = args.all
        self.data = []

    def run(self, args):
        url_list = self._process_parameters(args.url, args.domain, args.file)
        self.url_list = copy.copy(url_list)
        ptthreads_ = ptthreads.ptthreads()

        if self.url_test:
            if self._check_vulnerable(url_list[0]) and not args.check_only:
                ptthreads_.threads(url_list, self._enumerate_files, 1)
        if self.url_domain_file_test:
            if self._check_vulnerable(url_list[0]):
                ptmisclib.ptprint_(ptmisclib.out_ifnot("Enumerated:", "INFO", self.use_json))
                try:
                    ptthreads_.threads(url_list[1:], self._enumerate_files, args.threads)
                except Exception as e:
                    ptmisclib.end_error(f"Cannot connect to server", self.json_no, self.ptjsonlib, self.use_json)
            else:
                ptmisclib.end_error(f"Multiviews disabled", self.json_no, self.ptjsonlib, self.use_json)
        if self.domain_file_test:
                ptmisclib.ptprint_(ptmisclib.out_ifnot("Enumerated:", "INFO", self.use_json))
                ptthreads_.threads(url_list, self._enumerate_files, args.threads)
        if self.file_test:
            ptmisclib.ptprint_(ptmisclib.out_ifnot("Enumerated:", "INFO", self.use_json))
            ptthreads_.threads(url_list, self._enumerate_files, args.threads)
        self.ptjsonlib.add_data(self.json_no, {"enumerated_files": self.data})

        if self.output_file:
            self.output_file.write('\n'.join(self.data))
            self.output_file.close()
        self.ptjsonlib.set_status(self.json_no, "ok")
        ptmisclib.ptprint_(ptmisclib.out_if(self.ptjsonlib.get_all_json(), "", self.use_json))

    def _enumerate_files(self, url):
        """Enumerate files from URL"""
        malformed_headers = dict({"Accept": "foo/foo"}, **self.headers)
        malformed_url = self.strip_url_extension(url, self.without_extensions)
        try:
            r = requests.get(malformed_url, headers=malformed_headers, proxies=self.proxies, timeout=self.timeout, verify=False, allow_redirects=self.redirects)
        except requests.exceptions.ConnectionError:
            if self.file_test:
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Cannot connect to {url}, skipping", "ERROR", self.use_json))
                return
            else:
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Cannot connect to server - {url}", "ERROR", self.use_json))
                return
        if r.status_code == 406:
            enumerated_files = re.findall('<a href="(.*)">', r.text)
            path_list = []
            extracted_path = None
            if self.without_domain:
                extracted_path = url.split("/", 3)[-1]
            for f in enumerated_files:
                path = f"{url.rsplit('/', 1)[0]}/{f}"
                if not self.all:
                    if path in self.url_list:
                        continue
                if self.without_domain:
                    path = f"{extracted_path}/{f}"
                path_list.append(path)
                ptmisclib.ptprint_(ptmisclib.out_ifnot(path, "", self.use_json))
            self.data.extend(path_list)

    def _check_vulnerable(self, url: str):
        """Check if multiviews"""
        STATUS_CODES = [200, 301, 302]
        malformed_url = self.strip_url_extension(url, self.without_extensions)
        try:
            r = requests.get(malformed_url, headers=self.headers, proxies=self.proxies, timeout=self.timeout, verify=False, allow_redirects=self.redirects)
            ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Testing URL: {r.url}", "INFO", self.use_json))
            ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Status code: {r.status_code}", "INFO", self.use_json))
            ptmisclib.ptprint_(ptmisclib.out_ifnot(f" ", "", self.use_json))
            if r.status_code in STATUS_CODES and r.headers.get("Vary") and "negotiate" in r.headers.get("Vary"):
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Multiviews: Enabled", "VULN", self.use_json))
                self.ptjsonlib.set_vulnerable(self.json_no, "True")
                return True
            if r.status_code == 200:
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Multiviews: Disabled", "NOTVULN", self.use_json))
                self.ptjsonlib.set_vulnerable(self.json_no, "False")
                return False
            if self.domain_file_test:
                self.ptjsonlib.set_vulnerable(self.json_no, "False")
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Multiviews: Disabled / Unknown status code, setting to false & going next url", "", self.use_json))
            else:
                ptmisclib.end_error(f"Bad status code [{r.status_code}] - File not found or multiviews disabled", self.json_no, self.ptjsonlib, self.use_json)
        except Exception as e:
            ptmisclib.end_error(f"Cannot connect to website! - {e}", self.json_no, self.ptjsonlib, self.use_json)

    def _process_parameters(self, url, domain, file_urls):
        """Returns appropriate URLs"""
        if url and not file_urls and not domain:
            self.url_test = True
            return [self.parse_url(url)]
        if domain and file_urls and not url:
            self.domain_file_test = True
            domain = self._adjust_domain(domain)
            try:
                with open(file_urls, 'r') as fh:
                    return list(set([domain + line for line in self._read_file_lines(fh) if line]))
            except IOError as e:
                ptmisclib.end_error(f"Cannot read file - {e}.", self.json_no, self.ptjsonlib, self.use_json)
        if file_urls and not url and not domain:
            self.file_test = True
            ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Reading file: {file_urls}", "INFO", self.use_json))
            try:
                with open(file_urls, 'r') as fh:
                    return list(set([line for line in self._read_file_lines(fh)]))
            except IOError as e:
                ptmisclib.end_error(f"Cannot read file - {e}.", self.json_no, self.ptjsonlib, self.use_json)
        if url and domain and file_urls:
            self.url_domain_file_test = True
            url = self.parse_url(url)
            domain = self._adjust_domain(domain)
            try:
                with open(file_urls, 'r') as fh:
                    return [url] + list(set(domain+line for line in self._read_file_lines(fh)))
            except IOError as e:
                ptmisclib.end_error(f"Cannot read file - {e}.", self.json_no, self.ptjsonlib, self.use_json)
        if domain and not file_urls and not url:
            ptmisclib.end_error("To use --domain parameter you need to supply --file parameter.", self.json_no, self.ptjsonlib, self.use_json)
        ptmisclib.end_error("Bad argument combination, see --help", self.json_no, self.ptjsonlib, self.use_json)

    def _adjust_domain(self, domain):
        """Adjust domain from --domain parameter"""
        o = urllib.parse.urlparse(domain)
        if not re.match("http[s]?$", o.scheme):
            ptmisclib.end_error("Invalid scheme", self.json_no, self.ptjsonlib, self.use_json)
        if not o.path.endswith("/"):
            return domain + "/"
        else:
            return domain

    def parse_url(self, url):
        o = urllib.parse.urlparse(url)
        if not re.match("http[s]?$", o.scheme):
            ptmisclib.end_error(f"invalid scheme - '{o.scheme}'.", self.json_no, self.ptjsonlib, self.use_json)
        if not ((o.path) or len(o.path) == 1) and not self.url_domain_file_test:
            #o = o._replace(path="/favicon.ico")
            ptmisclib.end_error(f"URL with PATH to file is required.", self.json_no, self.ptjsonlib, self.use_json)
        modified_url = f"{o.scheme}://{o.netloc}{o.path}"
        return modified_url

    def _read_file_lines(self, file_handler):
        """Reads file and yields each line"""
        is_error = False
        for line in file_handler:
            l = urllib.parse.urlparse(line.split()[0])

            if self.file_test:
                if re.match("http[s]?$", l.scheme):
                    yield f"{l.scheme}://{l.netloc}{l.path}"
                else:
                    if not is_error:
                        ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Found lines containing invalid URLs - they will be skipped.", "ERROR", self.use_json))
                        is_error = True
                    continue

            if (self.domain_file_test or self.url_domain_file_test):
                line = line.strip()
                if l.scheme:
                    while l.path.startswith("/"):
                        l = l._replace(path=l.path[1:])
                    """
                    if not l.path.endswith("/"):
                        yield l.path.rsplit(".", 1)[0]
                    else:
                    """
                    yield l.path
                else:
                    while line.startswith("/"):
                        line = line[1:].strip()
                    yield line

    def strip_url_extension(self, url, strip_all_extensions=False):
        o = urllib.parse.urlparse(url)
        if strip_all_extensions:
            path = o.path.rsplit("/", 1)
            if "." in path[1]:
                new_path = f"{path[0]}/{path[1].split('.', 1)[0]}"
                o = o._replace(path=new_path)
        else:
            o = o._replace(path=o.path.rsplit(".", 1)[0])
        return urllib.parse.urlunparse(o)

    def get_output_file(self, output):
        if output:
            try:
                output_file = open(output, 'a')
                return output_file
            except Exception as e:
                ptmisclib.end_error(f"IO Error\n{e}", self.json_no, self.ptjsonlib, self.use_json)

    def _check_valid_url(self, url):
        """Connects to URL and check if response returns 200, else quit"""
        r = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=self.timeout, verify=False, allow_redirects=self.redirects)
        if r.status_code == 200:
            return True
        else:
            ptmisclib.end_error(f"Invalid status code ({r.status_code}), please specify path to existing file", self.json_no, self.ptjsonlib, self.use_json)

    def _load_urls(self, file):
        try:
            with open(file, "r") as f:
                domain_list = [line.strip("\n") for line in f]
        except IOError as e:
            ptmisclib.end_error(e, self.json_no, self.ptjsonlib, self.use_json)
        return domain_list


def get_help():
    return [
        {"description": ["Apache Multiviews Detection & Enumeration Tool"]},
        {"usage": ["ptmultiviews <options>"]},
        {"usage_example": [
            "ptmultiviews -u https://www.example.com/",
            "ptmultiviews -u https://www.example.com/ -co",
            "ptmultiviews -u https://www.example.com/ -d https://www.example.com/ -f files.txt",
            "ptmultiviews -d https://www.example.com/ -f files.txt",
            "ptmultiviews -f urlList.txt",
        ]},
        {"options": [
            ["-u",   "--url",                    "<url>",            "Connect to URL"],
            ["-d",   "--domain",                 "<domain>",         "Domain to test, (use with --file argument)"],
            ["-f",   "--file",                   "<file>",           "Load list of URLs from file"],
            ["-o",   "--output",                 "<output>",         "Save output to file"],
            ["-co",  "--check-only",             "",                 "Check for multiviews without enumerating"],
            ["-a",   "--all",                    "",                 "Return all sources, including sources specified in [--file, --url]"],
            ["-wd",  "--without-domain",         "",                 "Enumerated files will be printed without domain"],
            ["-we",  "--without-extensions",     "",                 "Removes all extensions from tested file"],
            ["-r",   "--redirects",              "",                 "Follow redirects (default False)"],
            ["-t",   "--threads",                "<threads>",        "Set number of threads (default 20)"],
            ["-p",   "--proxy",                  "<proxy>",          "Set proxy (e.g. http://127.0.0.1:8080)"],
            ["-ua",  "--user-agent",             "<ua>",             "Set User-Agent header"],
            ["-c",   "--cookie",                 "<cookie>",         "Set cookie"],
            ["-H",   "--headers",                "<header:value>",   "Set custom header(s)"],
            ["-j",   "--json",                   "",                 "Output in JSON format"],
            ["-v",   "--version",                "",                 "Show script version and exit"],
            ["-h",   "--help",                   "",                 "Show this help message and exit"]
        ]
        }]


def parse_args():
    parser = argparse.ArgumentParser(usage=f"{SCRIPTNAME} <options>")
    parser.add_argument("-u", "--url", type=str)
    parser.add_argument("-d", "--domain", type=str)
    parser.add_argument("-f", "--file", type=str)
    parser.add_argument("-o", "--output", type=str)
    parser.add_argument("-co", "--check-only", action="store_true")
    parser.add_argument("-wd", "--without-domain", action="store_true")
    parser.add_argument("-we", "--without-extensions", action="store_true")
    parser.add_argument("-a", "--all", action="store_true")
    parser.add_argument("-r", "--redirects", action="store_true")
    parser.add_argument("-t", "--threads", type=int, default=20)
    parser.add_argument("-p", "--proxy", type=str)
    parser.add_argument("-ua", "--user-agent", type=str, default="Penterep Tools")
    parser.add_argument("-H", "--headers", type=ptmisclib.pairs)
    parser.add_argument("-c", "--cookie", type=str)
    parser.add_argument("-j", "--json", action="store_true")
    parser.add_argument("-v", "--version", action="version", version=f"{SCRIPTNAME} {__version__}")

    if len(sys.argv) == 1 or "-h" in sys.argv or "--help" in sys.argv:
        ptmisclib.help_print(get_help(), SCRIPTNAME, __version__)
        sys.exit(0)
    args = parser.parse_args()
    ptmisclib.print_banner(SCRIPTNAME, __version__, args.json)
    return args


def main():
    global SCRIPTNAME
    SCRIPTNAME = "ptmultiviews"
    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
    args = parse_args()
    script = ptmultiviews(args)
    script.run(args)


if __name__ == "__main__":
    main()
