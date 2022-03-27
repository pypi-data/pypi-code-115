__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "MPL 2.0"

from citelang.logger import logger
import citelang.utils as utils
from operator import itemgetter

import re
import os

table_template = """|Manager|Name|Credit|
|-------|----|------|
"""

template_suffix = "\n> Note that credit values are rounded and expanded (so shared dependencies are represented as one record) and may not add to 1.0. Rounded values that hit zero are removed.\n"

citation_regex = "\@([a-zA-Z0-9]+)\{(.*?)\}"
empty_content = """# Software Credit

<!--citelang start-->
<!--citelang end-->

- Generated by [CiteLang](https://github.com/vsoch/citelang)
"""


class Parser:
    """
    A parser reads in a markdown file, finds software references, and generates
    a software graph per the user preferences.
    """

    def __init__(self, filename: str = None):
        self.data = {}
        self.libs = []
        self.round_by = 3
        self.filename = None
        if filename:
            self.filename = os.path.abspath(filename)
            if not os.path.exists(self.filename):
                logger.exit(f"{filename} does not exist")

            self.content = utils.read_file(self.filename)
        else:
            self.content = empty_content

    @property
    def start_block(self):
        return "<!--citelang start-->"

    @property
    def end_block(self):
        return "<!--citelang end-->"

    def check(self):
        """
        Checks for citelang.
        """
        if self.start_block not in self.content:
            logger.exit(
                "Cannot find %s, ensure it is present where you want the citelang table."
                % self.start_block
            )
        if self.end_block not in self.content:
            logger.exit(
                "Cannot find %s, ensure it is present where you want the citelang table."
                % self.end_block
            )

    def parse(self):
        """
        Given a markdown file, return a list of parse packages and versions.
        """
        self.check()
        for match in re.findall(citation_regex, self.content):
            if len(match) != 2:
                logger.warning(
                    "found malformed citation reference %s, skipping." % match
                )
                continue
            args = {
                y[0]: y[1]
                for y in [x.strip().split("=") for x in match[-1].split(",")]
                if len(y) == 2
            }
            self.libs.append({"manager": match[0], **args})

    def prepare_table(self, roots):
        """
        Given a set of roots, prepare table data.
        """
        # Generate the table with multiple roots - flatten out credit
        table = {}

        # Multiplier for credit depending on total packages
        splitby = 1 / len(roots)
        for lib, root in roots.items():
            manager = lib.split(":")[0]
            for node in root.iternodes():
                if manager not in table:
                    table[manager] = {}
                if node.name not in table[manager]:
                    table[manager][node.name] = {
                        "credit": 0,
                        "url": node.obj.homepage,
                    }
                table[manager][node.name]["credit"] += node.credit * splitby

        # Add listing of packages and dependencies to parser
        self.data = table
        self.round_by = root.round_by
        return table

    def add_lib(self, manager, name, **args):
        """
        Manually add a library (e.g., not reading from a pre-existing file)
        """
        self.libs.append({"manager": manager, "name": name, **args})

    def render(self):
        """
        Render final file!
        """
        markdown = table_template

        # Sort from least to greatest
        listing = []
        for manager, packages in self.data.items():
            for package, meta in packages.items():
                listing.append((manager, package, meta["credit"], meta["url"]))

        listing = sorted(listing, key=itemgetter(2), reverse=True)
        for (manager, package, credit, url) in listing:
            credit = round(credit, self.round_by)
            if credit == 0:
                logger.warning("Rounded credit for %s is 0, skipping." % package)
                continue
            if url:
                package = "[%s](%s)" % (package, url)
            markdown += "|%s|%s|%s|\n" % (
                manager,
                package,
                credit,
            )

        render = []
        lines = self.content.split("\n")
        while lines:
            line = lines.pop(0)
            if self.start_block in line:
                while self.end_block not in line:
                    line = lines.pop(0)
                # When we get here we have the end block
                render += (
                    [self.start_block]
                    + markdown.split("\n")
                    + [template_suffix, self.end_block]
                )
            else:
                render.append(line)
        return "\n".join(render)
