import logging

import pdfplumber
import typer

from aquaparser.parsers.parser import MeasurementParser

logging.basicConfig(level=logging.INFO)

typer_app = typer.Typer(help='Aqua-Parser manager.')


@typer_app.command(help='Start parser.')
def run(filename: str):
    measurement = MeasurementParser()
    doc = pdfplumber.open(filename)
    measurement.parse(doc)


if __name__ == '__main__':
    typer_app()
