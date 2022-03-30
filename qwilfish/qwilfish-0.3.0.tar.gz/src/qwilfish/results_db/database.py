# Standard lib imports
import os
import sqlite3
import logging
import datetime

# Local imports
from qwilfish.results_db.dataclasses import ResultsDbTableDefinition
from qwilfish.results_db.dataclasses import ResultsDbReport

log = logging.getLogger(__name__)

class ResultsDb():

    def __init__(self, outfile=None, dummy=True):
        self.dummy = dummy
        self.con = None
        self.cur = None
        self.date = None

        if outfile:
            self.outfile = outfile
        else:
            unique_extension = 0
            fname = "qwilfish_results.db"

            while os.path.exists(fname):
                unique_extension += 1
                fname = f"qwilfish_results_{unique_extension}.db"

            self.outfile = fname

    def write(self, report: ResultsDbReport) -> None:
        if self.dummy:
            return None

        if not report.columns:
            log.warning("Prevented writing an empty report to DB")
            return
        column_names = ", ".join(list(report.columns.keys()))
        values = ", ".join(map(str, list(report.columns.values())))
        cmd = f"INSERT INTO {report.name}_{self.date}({column_names}) \
                VALUES ({values})"
        self.issue_command(cmd)

    def open(self) -> None:
        if self.dummy:
            return
        if self.con:
            log.warning("Database connection already open, returning...")
            return
        else:
            self.con = sqlite3.connect(self.outfile)
            self.cur = self.con.cursor()
            self.date = datetime.datetime.now().strftime("%y%m%d_%H%M%S")

    def close(self) -> None:
        if self.dummy:
            return
        if not self.con:
            log.warning("Database connection already closed, returning...")
            return

        self.con.close()
        self.con = None
        self.cur = None

    def create_table(self, table_def: ResultsDbTableDefinition) -> None:
        if self.dummy:
            return
        if not table_def.columns:
            log.warning("Prevented creating an empty table in DB")
            return
        columns = ", ".join([f"{k} {v.name}"
            for k,v in table_def.columns.items()])
        cmd = f"CREATE TABLE {table_def.name}_{self.date} ({columns})"
        self.issue_command(cmd)

    def issue_command(self, cmd):
        log.debug("Attempting to issue SQLite command: %s", cmd)
        self.cur.execute(cmd)
        self.con.commit()
        log.debug("Command success!")
