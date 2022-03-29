import argparse

import src.parse_file_word.parse_word as pfw

parser = argparse.ArgumentParser(prog="cpm_file")

parser.add_argument(
    "field_path",
    help="field path of the file containing search term and source text",
)
def main():
    args = parser.parse_args()
    mat = pfw.get_match(args.field_path)
    print(mat)
