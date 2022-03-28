#!/usr/bin/python3
"""
    Same Site Scripting Testing Tool

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

__version__ = "0.0.4"

import argparse
import sys

from ptlibs import ptmisclib, ptjsonlib
from ptthreads import ptthreads

import dns.resolver
import tldextract


class ptsamesite:
    def __init__(self, args):
        self.json = args.json
        self.jsonlib = ptjsonlib.ptjsonlib(self.json)
        self.json_no = self.jsonlib.add_json("ptsamesite")

        self.data_list = []
        self.vulnerable = args.vulnerable
        self.subdomains = args.subdomains
        self.ptthreads_ = ptthreads.ptthreads()

    def run(self, args):
        try:
            domains = ptmisclib.read_file(args.file) if args.file else args.domain
        except FileNotFoundError:
            ptmisclib.end_error("File not found!", self.json_no, self.ptjsonlib, self.use_json)
        if self.vulnerable:
            ptmisclib.ptprint_(ptmisclib.out_ifnot("Vulnerable domains:", "TITLE", self.json))
        self.ptthreads_.threads(domains, self._test_domain, args.threads)
        self.jsonlib.add_data(self.json_no, {"result": self.data_list})
        ptmisclib.ptprint_(ptmisclib.out_if(self.jsonlib.get_all_json(), None, self.json))

    def _test_domain(self, domain):
        """test domains in paralell"""
        printlock = ptthreads.printlock()
        subdomains = self._prepare_subdomains_for_test(domain)
        for subdomain in subdomains:
            self.data_list.append(self._test_subdomain(subdomain, printlock))
        printlock.lock_print_output(end="")

    def _test_subdomain(self, subdomain, printlock):
        printlock.add_string_to_output( ptmisclib.out_ifnot(f"Testing {subdomain}", "TITLE", self.json), not self.vulnerable)
        data = {"domain": subdomain, "status": "null", "vulnerable": "null", "ip": "null"}
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 0.05
            ip = resolver.resolve(subdomain, "A")[0].to_text()
            # printlock.add_string_to_output( ptmisclib.out_ifnot(f"IP: {ip}", "INFO", self.json), not self.vulnerable)
            if ip == "127.0.0.1":
                printlock.add_string_to_output( ptmisclib.out_ifnot(f"Domain is vulnerable to same site scripting", "VULN", self.json), not self.vulnerable)
                printlock.add_string_to_output( ptmisclib.out_if(subdomain, "", self.vulnerable), self.vulnerable)
                self.jsonlib.set_vulnerable(self.json_no, True)
                data.update({"vulnerable": True, "ip": ip, "domain": subdomain, "status": "ok"})
            else:
                printlock.add_string_to_output( ptmisclib.out_ifnot(f"Domain not vulnerable", "NOTVULN", self.json), not self.vulnerable)
                data.update({"vulnerable": False, "ip": ip, "domain": subdomain, "status": "ok"})
            self.jsonlib.set_status(self.json_no, "ok")
        except dns.exception.DNSException as e:
            printlock.add_string_to_output( ptmisclib.out_ifnot(f"Domain not vulnerable", "NOTVULN", self.json), not self.vulnerable)
            data.update({"vulnerable": False, "domain": subdomain, "status": "ok"})
        return data

    def _prepare_subdomains_for_test(self, domain):
        ext = tldextract.extract(domain)
        subdomains = []
        while domain.startswith("."):
            domain = domain[1:]
        if self.subdomains and ext.subdomain:
            parsed_domain = ext.subdomain.split(".")
            if parsed_domain[0] == "localhost":
                parsed_domain.pop(0)
            for tested_subdomain_no in range(len(parsed_domain)):
                subdomains.append("localhost." + ".".join(parsed_domain[tested_subdomain_no:]) + "." + ext.domain + "." + ext.suffix)
            subdomains.append("localhost." + ext.domain + "." + ext.suffix)
        else:
            if not domain.startswith("localhost"):
                domain = "localhost." + domain
            subdomains.append(domain)
        return subdomains


def get_help():
    return [
        {"description": ["Same Site Scripting Testing Tool"]},
        {"usage": ["ptsamesite <options>"]},
        {"usage_example": ["ptsamesite -d example.com", "ptsamesite -d subdomain1.subdomain2.example.com -s", "ptsamesite -d example.com example2.com", "ptsamesite -f domain_list.txt"]},
        {"options": [
            ["-d",  "--domain",           "<domain>",   "Test domain"],
            ["-f",  "--file",             "<file>",     "Test domains from file"],
            ["-V", "--vulnerable",        "",           "Print only vulnerable domains"],
            ["-s", "--subdomains",        "",           "Scan all subdomains of given domain"],
            ["-t",  "--threads",          "<threads>",  "Number of threads (default 20)"],
            ["-j",  "--json",             "",           "Output in JSON format"],
            ["-v",  "--version",          "",           "Show script version and exit"],
            ["-h",  "--help",             "",           "Show this help message and exit"],
        ]}
    ]


def parse_args():
    parser = argparse.ArgumentParser(add_help=False, usage=f"{SCRIPTNAME} <options>")
    required = parser.add_argument_group("One of the following arguments is required")
    required = required.add_mutually_exclusive_group(required=True)
    required.add_argument("-d", "--domain", type=str, nargs="+")
    required.add_argument("-f", "--file", type=str)
    parser.add_argument("-s", "--subdomains", action="store_true")
    parser.add_argument("-V", "--vulnerable", action="store_true")
    parser.add_argument("-t", "--threads", default=20, type=int)
    parser.add_argument("-j", "--json", action="store_true")
    parser.add_argument("-v", "--version", action="version", version=f"{SCRIPTNAME} {__version__}")

    if len(sys.argv) == 1 or "-h" in sys.argv or "--help" in sys.argv:
        ptmisclib.help_print(get_help(), SCRIPTNAME, __version__)
        sys.exit(0)
    args = parser.parse_args()
    return args


def main():
    global SCRIPTNAME
    SCRIPTNAME = "ptsamesite"
    args = parse_args()
    script = ptsamesite(args)
    script.run(args)


if __name__ == "__main__":
    main()
