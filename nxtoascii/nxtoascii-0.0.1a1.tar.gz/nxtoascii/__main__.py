import os
from nxtoascii.converter import Converter


def main():
    import argparse

    description = "Convert a Bliss Nexus file to SPEC, MULTISPEC, CSV or a generic ASCII columns file"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("filename", type=str, help="Nexus file name")
    parser.add_argument(
        "--format",
        type=str.upper,
        default="MULTISPEC",
        choices=["MULTISPEC", "SPEC", "CSV", "ASCII"],
        help="Output format (SPEC by default)",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default=os.path.join(".", "converted"),
        help="Output directory (current directory by default)",
    )
    parser.add_argument(
        "--scans",
        type=str,
        default="*",
        help='Scan title pattern (for example "dscan*")',
    )
    parser.add_argument(
        "--columns", nargs="+", default=[], help="Select columns for sorting"
    )
    parser.add_argument(
        "--only_columns", action="store_true", help="Only save the selected columns"
    )
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    # args.filename = "/data/visitor/im59/bm23/im59_bm23.h5"
    # args.outdir = "/tmp/exafs"
    # args.pattern = "*exafs*"

    converter = Converter(
        args.filename,
        args.outdir,
        title_pattern=args.scans,
        output_format=args.format,
        selected_columns=args.columns,
        only_selected_columns=args.only_columns,
        raise_on_error=args.debug,
    )
    converter.convert()


if __name__ == "__main__":
    main()
