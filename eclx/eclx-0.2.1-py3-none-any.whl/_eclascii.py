import pathlib

from lark import Lark, Token
from collections import defaultdict

with open(pathlib.Path(__file__).parent / "ecl_grammar.lark", "r") as grammar:
    LARK_GRAMMAR = grammar.read()

class EclAsciiParser:
    """A class for passing ASCII files -> generally the input files for Eclipse

    From these files it is possible to key keywords and keyword tables.
    """

    _parser = Lark(LARK_GRAMMAR)

    def __init__(self):
        self.tree = None

    def parse(self, filepath):
        """Read a file and parse it with the parser."""
        with open(filepath, "r") as f:
            txt = f.read()

        self.tree = self._parser.parse(txt)

        # get the sections node
        sections = next(self.tree.find_pred(
            lambda x: x.data.value == "sections"
        ))

        data = defaultdict(list)

        for kw_sec in sections.children:
            kw_line = next(kw_sec.find_pred(lambda x: x.data.value == "keyword_line"))
            kw_token = next(kw_line.find_data("key")).children[0]
            assert kw_token.type == "KEYWORD"
            kw = kw_token.value

            if kw_sec.data.value == "keyword_line":
                data[kw] = []
            elif kw_sec.data.value == "keyword_tab":
                tab_lines = kw_sec.find_data("tab_line")

                for tl in tab_lines:
                    table_data = list(tl.find_data("data"))[0]
                    ecl_values = [
                        token.value for token in table_data.children if isinstance(token, Token)
                    ]
                    if ecl_values: # don't add empties
                        data[kw].append(ecl_values)
            else:
                raise NotImplementedError(f"Unknown section in grammar {kw_sec.data.value}")

        self.data = dict(data)

    def __str__(self):
        return str(self.tree)

    def __repr__(self):
        return self.tree.pretty()

    def get_keywords(self):
        """Same a self.data.keys()"""
        return self.data.keys()

    def __getitem__(self, key):
        """Get a particular KW from the tree"""
        return self.data[key]


