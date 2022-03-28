import logging

import pdfplumber

from aquaparser.parsers import title_parser, toc_parser
from aquaparser.schemas import Measurement, MeasurementTOC

logger = logging.getLogger(__name__)


class MeasurementParser:

    def __init__(self):
        self.title_parser = title_parser.TitleParser()
        self.toc_parser = toc_parser.TocParser()

    def parse(self, doc: pdfplumber):
        measurement = Measurement(
            title=self.title_parser.parse(doc),
            toc=self.toc_parser.parse(doc),
        )
        logger.info(measurement.title)
        self.log_toc(measurement.toc)
        return measurement

    def log_toc(self, table: list[MeasurementTOC]):
        for num, row in enumerate(table):
            smd = row.smd.replace('\n', ' ')
            row_num = num + 1
            control_string = f'{row_num}: smd = {smd}; status = {row.status}'
            logger.info(control_string)
