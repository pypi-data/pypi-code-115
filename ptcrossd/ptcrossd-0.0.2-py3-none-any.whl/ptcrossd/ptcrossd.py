#!/usr/bin/python3
"""
    Crossdomain tester

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

import defusedxml.ElementTree as ET
import requests 

import ptlibs.ptjsonlib as ptjsonlib
import ptlibs.ptmisclib as ptmisclib


class ptcrossd:
    def __init__(self, args):
        self.use_json = args.json
        self.ptjsonlib = ptjsonlib.ptjsonlib(self.use_json)
        self.json_no = self.ptjsonlib.add_json("ptcrossd")

        self.headers = ptmisclib.get_request_headers(args)
        self.proxies = {"http": args.proxy, "https": args.proxy}
        self.url = self.adjust_url(args.url)

    def run(self):
        ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Testing: {self.url}", "TITLE", self.use_json))
        response = self.get_response()
        if response:
            self.proccess_crossdomain(response)
        ptmisclib.ptprint_(ptmisclib.out_if(self.ptjsonlib.get_all_json(), condition=self.use_json))

    def get_response(self):
        try:
            response = requests.get(self.url, headers=self.headers, proxies=self.proxies, verify=False, allow_redirects=False)
            if response.status_code == 200:
                data = {"url": self.url, "crossdomain_found": "True", "status_code": response.status_code, "xml_content": response.text}
                self.ptjsonlib.set_status(self.json_no, "ok")
                self.ptjsonlib.add_data(self.json_no, data)
                return response
            else:
                ptmisclib.end_error(f"crossdomain.xml not found", self.json_no, self.ptjsonlib, self.use_json)
        except (requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema):
            ptmisclib.end_error("missing scheme", self.json_no, self.ptjsonlib, self.use_json)
        except requests.exceptions.Timeout:
            ptmisclib.end_error("timeout Error", self.json_no, self.ptjsonlib, self.use_json)
        except Exception as e:
            ptmisclib.end_error(f"server not reachable {e}", self.json_no, self.ptjsonlib, self.use_json)

    def proccess_crossdomain(self, response):
        """Parse crossdomain file, check if vulnerable and set corresponding JSON"""
        try:
            tree = ET.fromstring(response.text)
        except ET.ParseError:
            ptmisclib.end_error("error Parsing XML", self.json_no, self.ptjsonlib, self.use_json)
        except ET.EntitiesForbidden:
            ptmisclib.end_error("forbidden entities found, quitting", self.json_no, self.ptjsonlib, self.use_json)

        ptmisclib.ptprint_(ptmisclib.out_ifnot("File contents:\n", "TITLE", self.use_json))
        ptmisclib.ptprint_(ptmisclib.out_ifnot(ptmisclib.get_colored_text(response.text, "ADDITIONS"), "", self.use_json))
        vulnerable = None

        acf_elements = tree.findall("allow-access-from")
        if acf_elements:
            for acf in acf_elements:
                if acf.attrib["domain"] and acf.attrib["domain"] == "*":
                    vulnerable = True
            if vulnerable:
                ptmisclib.ptprint_(ptmisclib.out_ifnot("file is vulnerable to open policy", "VULN", self.use_json))
                self.ptjsonlib.set_vulnerable(self.json_no, "True")
            else:
                ptmisclib.ptprint_(ptmisclib.out_ifnot("no vulnerabilities found", "NOTVULN", self.use_json))
                self.ptjsonlib.set_vulnerable(self.json_no, "False")
        else:
            ptmisclib.ptprint_(ptmisclib.out_ifnot("allow-access-from element not found", "INFO", self.use_json))
            self.ptjsonlib.set_vulnerable(self.json_no, "False")

    def adjust_url(self, url):
        ext = urllib.parse.urlparse(url)
        path = ext.path
        if not ext.path.endswith("/crossdomain.xml"):
            if not ext.path.endswith("/"):
                path = path + "/"
            path = path + "crossdomain.xml"
        return ext.scheme + "://" + ext.netloc + path


def get_help():
    return [
        {"description": ["Crossdomain.xml Testing Tool"]},
        {"usage": ["ptcrossd <options>"]},
        {"usage_example": [
            "ptcrossd -u https://www.example.com/crossdomain.xml",
            "ptcrossd -u https://www.example.com/"
        ]},
        {"options": [
            ["-u",  "--url",                    "<url>",            "Connect to URL"],
            ["-p",  "--proxy",                  "<proxy>",          "Set proxy (e.g. http://127.0.0.1:8080)"],
            ["-c",  "--cookie",                 "<cookie>",         "Set cookie"],
            ["-H",  "--headers",                "<header:value>",   "Set custom header(s)"],
            ["-ua",  "--user-agent",            "<user-agent>",     "Set User-Agent header"],
            ["-j",  "--json",                   "",                 "Output in JSON format"],
            ["-v",  "--version",                "",                 "Show script version and exit"],
            ["-h",  "--help",                   "",                 "Show this help message and exit"]
        ]
        }]                                                 


def parse_args():
    parser = argparse.ArgumentParser(add_help="False")
    parser.add_argument("-u", "--url", type=str, required=True)
    parser.add_argument("-p", "--proxy", type=str)
    parser.add_argument("-c", "--cookie", type=str)
    parser.add_argument("-H", "--headers", type=ptmisclib.pairs, nargs="+")
    parser.add_argument("-ua", "--user-agent", type=str, default="Penterep Tools")
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
    SCRIPTNAME = "ptcrossd"
    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'

    args = parse_args()
    script = ptcrossd(args)
    script.run()


if __name__ == "__main__":
    main()
