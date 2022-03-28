#!/usr/bin/python3
"""
    ptandroid - APK / AXML Data Parser

    Copyright (c) 2020 HACKER Consulting s.r.o.

    ptandroid is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ptandroid is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with ptandroid.  If not, see <https://www.gnu.org/licenses/>.
"""

__version__ = "0.0.4"

import argparse
import os
import stat
import re
import subprocess
import sys
import tempfile

import defusedxml.ElementTree as ET

import ptlibs.ptjsonlib as ptjsonlib
import ptlibs.ptmisclib as ptmisclib


class ptandroid:
    def __init__(self, args):
        self.use_json        =    args.json
        self.ptjsonlib       =    ptjsonlib.ptjsonlib(args.json)
        self.json_no         =    self.ptjsonlib.add_json(SCRIPTNAME)

        self.path2apktool    =    os.path.join(os.path.dirname(os.path.realpath(__file__)), "utils", "apktool.jar")
        self.file_name       =    args.file
        self.file_extension  =    args.file.rsplit(".", 1)[-1].upper()
        self.file_content    =    None

        self.get_everything  =    False
        self.apk_required    =    False
        self.is_vulnerable   =    False

        self.result          =    list()

        if len(sys.argv) == 3 or (len(sys.argv) == 4 and self.use_json):
            self.get_everything = True
        if args.content_urls or args.https_urls:
            self.apk_required = True
        if self.apk_required and self.file_extension != "APK":
            ptmisclib.end_error("APK required for selected arguments", self.json_no, self.ptjsonlib, self.use_json)

    def run(self, args):
        apk_tests_results = None
        if self.file_extension == "APK" and (self.get_everything or (args.content_urls or args.https_urls)):
            self.check_dependencies()
            apk_tests_results = self.process_apk(args)

        axml_tests_results = self.process_axml(self.get_axml(), args)
        self.result.extend(axml_tests_results)
        if apk_tests_results:
            self.result.extend(apk_tests_results)

        if not self.use_json:
            self._print_result(self.result)

        if self.use_json:
            self.ptjsonlib.set_status(self.json_no, "ok")
            if self.is_vulnerable:
                self.ptjsonlib.set_vulnerable(self.json_no, True)
            ptmisclib.ptprint_(ptmisclib.out_if(self.ptjsonlib.get_all_json(), "", self.use_json))

    def get_axml(self):
        if self.file_extension == "APK":
            xml_content = self._get_axml_from_apk()
        elif self.file_extension == "XML":
            xml_content = self.validate_xml_content(self._read_file(self.file_name))
        else:
            ptmisclib.end_error("Only [APK, XML] files are supported.", self.json_no, self.ptjsonlib, self.use_json)
        return re.sub(r'([\w\d]*:)([\w\d]*=)', r"\2", xml_content)

    def validate_xml_content(self, xml_content):
        if "<manifest" in xml_content:
            if re.findall(r'targetSdkVersion="\d{1,2}"', xml_content):
                return xml_content
            else:
                ptmisclib.end_error("Unsupported axml: targetSdkVersion not found. (apktool not supported, try providing apk)", self.json_no, self.ptjsonlib, self.use_json)
        else:
            ptmisclib.end_error("This is not a valid axml file", self.json_no, self.ptjsonlib, self.use_json)

    def _get_axml_from_apk(self):
        """Retrieves axml from apk file"""
        p = subprocess.run(['androguard', '--silent', 'axml', self.file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            if p.stderr.endswith("does not exist.\n"):
                err_msg = p.stderr.split(":")[-1].lstrip()
            else:
                err_msg = p.stdout
            ptmisclib.end_error(f"There was an error parsing APK - {err_msg}", self.json_no, self.ptjsonlib, self.use_json)

        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        output_stripped = ansi_escape.sub('', p.stdout)

        return output_stripped

    def check_dependencies(self):
        """check dependencies for parsing apk files"""
        try:
            subprocess.run(["java", "-version"], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        except:
            ptmisclib.end_error("JRE not found (required for parsing apk)", self.json_no, self.ptjsonlib, self.use_json)
        try:
            subprocess.run(["androguard", "--version"], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        except:
            ptmisclib.end_error("Androguard not found (required for parsing apk), install by running: 'pip install androguard'", self.json_no, self.ptjsonlib, self.use_json)
        try:
            is_executable = os.access(self.path2apktool, os.X_OK)
            if not is_executable:
                os.chmod(self.path2apktool, os.stat(self.path2apktool).st_mode | stat.S_IEXEC)
        except:
            ptmisclib.end_error(f"Cannot execute nor set execution privileges for apktool, run script as root or manually run 'sudo chmod +x {self.path2apktool}'", self.json_no, self.ptjsonlib, self.use_json)

    def process_apk(self, args):
        """apk related tests (decompilation required)"""
        local_result = []
        with tempfile.TemporaryDirectory() as dir_path:
            self._decompile_apk(dir_path)
            if args.content_urls or self.get_everything:
                local_result.append(self._get_content_urls(dir_path))
            if args.https_urls or self.get_everything:
                local_result.append(self._get_https_urls(dir_path))
        return local_result

    def process_axml(self, xml_content, args):
        """process validated xml content"""
        if args.manifest or self.get_everything:
            self.print_axml(xml_content)

        root = self._get_tree(xml_content)
        sdk_data = self._get_sdk_data(root)

        self.targetSdkVersion = sdk_data["targetSdkVersion"]
        self.minSdkversion = sdk_data["minSdkVersion"]

        result = []
        if args.info or self.get_everything:
            package_data = self._get_package_data(root)
            user_permission_data = self._get_user_permission_data(root)
            defined_permission_data = self._get_defined_permission_data(root)
            application_data = self._get_application_data(root)
            result.extend([{"test_name": "Package_data", **package_data, **sdk_data, **application_data, **user_permission_data, **defined_permission_data}])
        if args.components or args.activities or self.get_everything:
            activity_list = self._get_activity_data(root)
            result.append({"test_name": "Activities", "activities": activity_list})
        if args.components or args.providers or self.get_everything:
            provider_data = self._get_provider_data(root)
            result.append({"test_name": "Providers", "providers": provider_data})
        if args.components or args.receivers or self.get_everything:
            receiver_data = self._get_receiver_data(root)
            result.append({"test_name": "Receivers", "receivers": receiver_data})
        if args.services or self.get_everything:
            services_data = self._get_services_data(root)
            result.append({"test_name": "Services", "services": services_data})

        return result

    def print_axml(self, axml_content):
        ptmisclib.ptprint_(ptmisclib.out_ifnot("AndroidManifest.xml", "INFO", condition=self.use_json, colortext=True))
        while axml_content.endswith("\n"):
            axml_content = axml_content[:-1]

        ptmisclib.ptprint_(ptmisclib.out_ifnot(axml_content, "", self.use_json))

    def _get_sdk_data(self, root):
        """returns minSdkVersion, targetSdkVersion"""
        sdk = root.find("uses-sdk")
        if sdk is not None:
            data = {"minSdkVersion" : sdk.get("minSdkVersion"), "targetSdkVersion": sdk.get("targetSdkVersion")}
            if not data["targetSdkVersion"]:
                ptmisclib.end_error("Invalid axml - targetSdkVersion not found", self.json_no, self.ptjsonlib, self.use_json)
            return data
        else:
            ptmisclib.end_error("Error parsing SDK data", self.json_no, self.ptjsonlib, self.use_json)

    def _get_package_data(self, root):
        """Returns versionName, versionCode, package values from MANIFEST element"""
        data = {"package": root.get("package"), "versionName": root.get("versionName"), "versionCode": root.get("versionCode")}
        self.ptjsonlib.add_data(self.json_no, data)
        return data

    def _get_application_data(self, root):
        """Returns allowBackup, debuggable, sharedUserId values from *APPLICATION* element"""
        application = root.find("application")
        data = {"allowBackup": self._str2bool(application.get("allowBackup"), True), "debuggable": self._str2bool(application.get("debuggable"), False), "sharedUserId": application.get("sharedUserId")}
        self.ptjsonlib.add_data(self.json_no, data)
        return data

    def _get_defined_permission_data(self, root):
        """Get permision names from all *PERMISSION* elements"""
        permission_list = root.findall("permission")
        names = [permission.get("name") for permission in permission_list]
        self.ptjsonlib.add_data(self.json_no, {"defined_permissions": names})
        return {"defined_permissions": names}

    def _get_user_permission_data(self, root):
        """Get permision names from all *USES-PERMISSION* elements"""
        permission_list = root.findall("uses-permission")
        names = [permission.get("name") for permission in permission_list]
        self.ptjsonlib.add_data(self.json_no, {"uses_permissions": names})
        return {"user_permissions": names}

    def _get_activity_data(self, root):
        """Returns name, exported values from all *ACTIVITY* elements"""
        result = []
        activity_list = root.find("application").findall("activity")
        for activity in activity_list:
            data = {"name": activity.get("name"), "exported": self._str2bool(activity.get("exported"), False, 16), "permission": activity.get("permission", "None")}
            if activity.find("intent-filter"):
                data["exported"] = True
            if data["exported"] and not self.is_vulnerable:
                self.is_vulnerable = True
            result.append(data)
        self.ptjsonlib.add_data(self.json_no, {"activities": result})
        return result

    def _get_provider_data(self, root):
        """Returns provider info"""
        result = []
        provider_list = root.find("application").findall("provider")
        for provider in provider_list:
            data = {"name": provider.get("name"), "exported": self._str2bool(provider.get("exported"), False, 16), "permission": provider.get("permission", "None"), "path_permissions": []}
            if data["exported"] and not self.is_vulnerable:
                self.is_vulnerable = True
            if provider.findall("path-permission"):
                for path_permission in provider.findall("path-permission"):
                    data["path_permissions"].append(path_permission.attrib)
            result.append(data)
        self.ptjsonlib.add_data(self.json_no, {"providers": result})
        return result

    def _get_receiver_data(self, root):
        """Returns receiver info"""
        result = []
        receiver_list = root.find("application").findall("receiver")
        for receiver in receiver_list:
            data = {"name": receiver.get("name"), "exported": self._str2bool(receiver.get("exported"), False, 16), "permission": receiver.get("permission", "None")}
            if data["exported"] and not self.is_vulnerable:
                self.is_vulnerable = True
            result.append(data)
        self.ptjsonlib.add_data(self.json_no, {"receivers": result})
        return result

    def _get_services_data(self, root):
        """Returns services information"""
        result = []
        services_list = root.find("application").findall("service")
        for service in services_list:
            data = {"name": service.get("name"), "exported": self._str2bool(service.get("exported"), False, 16), "permission": service.get("permission")}
            if data["exported"] and not self.is_vulnerable:
                self.is_vulnerable = True
            result.append(data)
        self.ptjsonlib.add_data(self.json_no, {"services": result})
        return result

    def _decompile_apk(self, dir_path):
        ptmisclib.ptprint_(ptmisclib.out_ifnot(" ", "", self.use_json))
        ptmisclib.ptprint_(ptmisclib.out_ifnot(f"Decompiling apk..", "INFO", self.use_json), f"\r")
        p = subprocess.run(["java", "-jar", self.path2apktool, "d", self.file_name, "-o", dir_path, "-f"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            ptmisclib.end_error("There was an error decompiling APK\n\n"+p.stderr, self.json_no, self.ptjsonlib, self.use_json)
            # FIXME - stderr2json

    def _get_content_urls(self, dir_path):
        """Returns content:// links from dir_path"""
        p = subprocess.run(["grep", "-Ehro", "content:\/\/.*[^\"]", dir_path+"/smali"], stdout=subprocess.PIPE, text=True)
        content_urls = set()
        for url in p.stdout.split():
            if url.endswith("/"):
                url = url[:-1]
            content_urls.add(url)

        self.ptjsonlib.add_data(self.json_no, {"content_urls": list(content_urls)})

        return {"test_name": "Content_URLs", "content_urls": list(content_urls)}

    def _get_https_urls(self, dir_path):
        """Returns http(s):// links from dir_path"""
        p = subprocess.run(["grep", "-Ehro", "https?:\/\/\S*[^\"]", dir_path+"/smali"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        https_urls = set()

        for url in p.stdout.split():
            https_urls.add(url)

        self.ptjsonlib.add_data(self.json_no, {"https_urls": list(https_urls)})

        return {"test_name": "HTTP(S)_URLs", "https_urls": list(https_urls)}


    def _str2bool(self, string, default=False, targetSdk=None):
        if string is None:
            string = "None"
        if string.lower() == "true":
            return True
        elif string.lower() == "false":
            return False
        else:
            if targetSdk and int(self.targetSdkVersion) <= targetSdk:
                return not default
            else:
                return default

    def _print_result(self, result_list, nested=False):
        spacing = " "*3
        for d in result_list:
            for key, value in d.items():
                if key == "test_name":
                    ptmisclib.ptprint_("\n"+ptmisclib.out_ifnot(value.replace('_', ' '), "INFO", self.use_json, colortext="INFO"))
                    continue
                if isinstance(value, (str, bool)) or value is None:
                    ptmisclib.ptprint_(ptmisclib.out_ifnot(f"{key}: {str(value)}", "", self.use_json))
                if isinstance(value, list):
                    if nested or (not nested and key.upper() != d['test_name'].upper().replace("(","").replace(")","")):
                        ptmisclib.ptprint_(ptmisclib.out_ifnot(f"{key}:" ,"", self.use_json), end="\n")
                    if not value:
                        ptmisclib.ptprint_(ptmisclib.out_ifnot(f"{spacing}None" ,"", self.use_json))
                        continue
                    elif isinstance(value[0], str):
                        ptmisclib.ptprint_(f"{spacing}"+ptmisclib.out_ifnot(f'\n{spacing}'.join(value) ,"", self.use_json))
                    elif isinstance(value[0], dict):
                        self._print_result(value, nested=True)
            if nested and d != result_list[-1]:
                ptmisclib.ptprint_(ptmisclib.out_ifnot(f" ", "", self.use_json))

    def _get_tree(self, xml_content):
        try:
            root = ET.fromstring(xml_content)
        except Exception as e:
            ptmisclib.end_error("Cannot parse xml", self.json_no, self.ptjsonlib, self.use_json)
        return root

    def _read_file(self, f):
        """return content of file"""
        try:
            with open(f, 'r') as file_:
                return file_.read()
        except:
            ptmisclib.end_error("Error reading file: File not found", self.json_no, self.ptjsonlib, self.use_json)


def get_help():
    return [
        {"description": ["Android Application Package Parser"]},
        {"usage": ["ptandroid <options>"]},
        {"usage_example": [
            "ptandroid -f app.apk",
            "ptandroid -f AndroidManifest.xml"
        ]},
        {"options": [
            ["-f",  "--file",                 "<file>",     "Load File: app.apk, AndroidManifest.xml [.apk, .xml]"],
            ["-m",  "--manifest",             "",           "Print axml content"],
            ["-i",  "--info",                 "",           "Print package data info"],
            ["-c",  "--components",           "",           "Print components info"],
            ["-a",  "--activities",           "",           "Print activities info"],
            ["-p",  "--providers",            "",           "Print providers info"],
            ["-r",  "--receivers",            "",           "Print receivers info"],
            ["-s",  "--services",             "",           "Print services info"],
            ["-cu", "--content-urls",         "",           "Print content urls [apk file required]"],
            ["-hu", "--https-urls",           "",           "Print http(s) urls [apk file required]"],
            ["-j",  "--json",                 "",           "Enable JSON output"],
            ["-v",  "--version",              "",           "Show script version and exit"],
            ["-h",  "--help",                 "",           "Show this help message and exit"]
        ]
        }]

def parse_args():
    parser = argparse.ArgumentParser(add_help=False, usage=f"{SCRIPTNAME}.py <options>")
    parser.add_argument("-f", "--file", type=str, required=True)
    parser.add_argument("-m", "--manifest", action="store_true")
    parser.add_argument("-i", "--info", action="store_true")
    parser.add_argument("-c", "--components", action="store_true")
    parser.add_argument("-a", "--activities", action="store_true")
    parser.add_argument("-p", "--providers", action="store_true")
    parser.add_argument("-r", "--receivers", action="store_true")
    parser.add_argument("-s", "--services", action="store_true")
    parser.add_argument("-cu", "--content-urls", action="store_true")
    parser.add_argument("-hu", "--https-urls", action="store_true")
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
    SCRIPTNAME = "ptandroid"
    args = parse_args()
    script = ptandroid(args)
    script.run(args)

if __name__ == "__main__":
    main()
