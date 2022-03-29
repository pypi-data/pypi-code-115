import argparse
import csv
import re

from openpyxl import Workbook

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('csvfile', help='The .csv file to be converted')
parser.add_argument('-o,--output', dest='output', help='Name of the output file')


def main():
    args = parser.parse_args()

    with open(args.csvfile) as input_file:
        reader = csv.reader(input_file)

        wb = Workbook()
        ws1 = wb.active
        ws1.title = 'Course'
        for row in reader:
            ws1.append(row)

    if args.output:
        output_filename = args.output
    else:
        output_filename = re.sub(r'\.csv$', '.xlsx', args.csvfile)
    with open(output_filename, 'wb') as output_file:
        wb.save(output_file)
