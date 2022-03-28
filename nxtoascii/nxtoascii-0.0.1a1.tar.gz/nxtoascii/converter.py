import os
import re
import time
import logging
from fnmatch import fnmatch
from contextlib import contextmanager
import numpy
from silx.io import h5py_utils
from silx.io.utils import h5py_read_dataset


logger = logging.getLogger(__name__)


class Converter:
    def __init__(
        self,
        input_filename,
        output_directory,
        title_pattern="*",
        output_format="SPEC",
        selected_columns=tuple(),
        only_selected_columns=False,
        raise_on_error=False,
    ):
        self.input_filename = input_filename
        self.output_directory = output_directory
        self.title_pattern = title_pattern
        self.output_extension = ".dat"
        self.output_format = output_format
        self.selected_columns = selected_columns
        self.only_selected_columns = only_selected_columns
        self.raise_on_error = raise_on_error
        self._info = {}

    @property
    def output_format(self):
        return self._output_format

    @output_format.setter
    def output_format(self, value):
        self._output_format = value.upper()

    @property
    def input_filename(self):
        return self._input_filename

    @input_filename.setter
    def input_filename(self, value):
        self._input_filename = value
        self._output_basename = os.path.splitext(os.path.basename(value))[0]

    def generate_output_filename(self, basename=None):
        if not self.output_directory:
            self.output_directory = os.path.join(".", "converted")
        if basename:
            basename = re.sub("[^a-zA-Z0-9_]+", "_", basename)
        else:
            basename = self._output_basename
        return os.path.join(self.output_directory, basename + self.output_extension)

    @contextmanager
    def _convert_context(self):
        scan_names = h5py_utils.safe_top_level_names(
            self.input_filename, retry_timeout=10
        )
        try:
            scan_names = sorted(scan_names, key=float)
        except ValueError:
            pass
        self._info = {}
        os.makedirs(self.output_directory, exist_ok=True)

        output_filename = self.generate_output_filename()
        if self.output_format == "MULTISPEC":
            output_fileobj = open(output_filename, "wb")
        else:
            output_fileobj = None

        self._info = {
            "output_fileobj": output_fileobj,
            "output_filename": output_filename,
        }
        try:
            yield scan_names
        finally:
            self._info = {}
            if output_fileobj is not None:
                output_fileobj.close()

    def convert(self):
        failed = []
        try:
            with self._convert_context() as scan_names:
                for scan_name in scan_names:
                    try:
                        succes = self._convert_scan(scan_name)
                    except Exception as e:
                        logger.error(
                            "Error converting scan {}: {}".format(repr(self.uri), e)
                        )
                        if self.raise_on_error:
                            raise
                        succes = False
                    if not succes:
                        failed.append(self.uri)
        except Exception as e:
            logger.error(
                "Error converting file {}: {}".format(repr(self.input_filename), e)
            )
            if self.raise_on_error:
                raise
            failed.insert(0, self.input_filename)
        return failed

    @h5py_utils.retry(retry_timeout=10)
    def _convert_scan(self, scan_name):
        with h5py_utils.File(self.input_filename) as h5file:
            nxentry = h5file[scan_name]
            title = h5py_read_dataset(nxentry["title"])
            if not fnmatch(title, self.title_pattern):
                return True
            # We need to convert this NXentry
            self._info["scan_name"] = scan_name
            self._info["nxentry"] = nxentry
            self._info["title"] = title
            if self.output_format != "MULTISPEC":
                self._info["output_filename"] = self.generate_output_filename(
                    basename=scan_name
                )
            return self._save_nxentry()

    @property
    def output_fileobj(self):
        return self._info.get("output_fileobj")

    @property
    def appending(self):
        return self.output_fileobj is not None and self.output_fileobj.tell() > 0

    @property
    def output_filename(self):
        return self._info.get("output_filename")

    @property
    def output_obj(self):
        obj = self.output_fileobj
        if obj is None:
            return self.output_filename
        else:
            return obj

    @property
    def title(self):
        return self._info.get("title", "")

    @property
    def nxentry(self):
        return self._info.get("nxentry")

    @property
    def scan_name(self):
        return self._info.get("scan_name")

    @property
    def uri(self):
        try:
            return self.input_filename + "::" + self.scan_name
        except Exception:
            return self.input_filename + "::..."

    @property
    def columns(self):
        return self._info.get("columns", list())

    @property
    def column_names(self):
        return self._info.get("column_names", list())

    @property
    def write_args(self):
        return self._info.get("write_args", tuple())

    @property
    def write_kwargs(self):
        return self._info.get("write_kwargs", dict())

    def _save_nxentry(self):
        try:
            self.read_columns()
        except Exception as e:
            logger.error("Error reading {}: {}".format(repr(self.uri), e))
            if self.raise_on_error:
                raise
            return False

        try:
            self.create_write_options()
        except Exception as e:
            logger.error("Error parsing {}: {}".format(repr(self.uri), e))
            if self.raise_on_error:
                raise
            return False

        try:
            self.save_as_ascii()
        except Exception as e:
            logger.error("Error writing {}: {}".format(repr(self.uri), e))
            if self.raise_on_error:
                raise
            return False

        print("Converted {} -> {}".format(self.uri, self.output_filename))
        return True

    def read_columns(self):
        measurement = self.nxentry["measurement"]
        columns = []
        column_names = []
        for channel_name in measurement:
            dset = measurement[channel_name]
            if dset.ndim == 1:
                columns.append(dset[()])
                column_names.append(channel_name)

        if not column_names:
            raise RuntimeError("No data available")
        selected_columns = [
            name for name in self.selected_columns if name in column_names
        ]
        if self.only_selected_columns and not selected_columns:
            raise RuntimeError("No columns selected")
        idx = [column_names.index(name) for name in selected_columns]
        if not self.only_selected_columns:
            idx.extend(i for i in range(len(column_names)) if i not in idx)

        column_names = [column_names[i] for i in idx]
        columns = [columns[i] for i in idx]

        self._info["columns"] = columns
        self._info["column_names"] = column_names

    def save_as_ascii(self):
        numpy.savetxt(*self.write_args, **self.write_kwargs)

    def create_write_options(self):
        fmt = "%.18e"
        column_names = self.column_names
        if "SPEC" in self.output_format:
            delimiter = " "
            comments = ""
            # fmt = "%.7g"
            dateline = "#D " + str(time.ctime(time.time()))
            if self.appending:
                lines = []
            else:
                lines = ["#F " + os.path.abspath(self.output_filename), dateline]
            lines.extend(
                [
                    "\n" "#S {} {}".format(self.scan_name, self.title),
                    dateline,
                    "#N " + str(len(column_names)),
                    "#L " + "  ".join(column_names),
                ]
            )
            header = "\n".join(lines)
        elif self.output_format == "CSV":
            delimiter = ","
            comments = ""
            header = delimiter.join(column_names)
        else:
            delimiter = " "
            comments = "# "
            column_names = [name.replace(delimiter, "") for name in self.column_names]
            header = self.title + "\n" + delimiter.join(column_names)

        columns = self.columns
        n = min(col.size for col in columns)
        data = numpy.stack([col[:n] for col in columns], axis=1)
        self._info["write_args"] = self.output_obj, data
        self._info["write_kwargs"] = {
            "fmt": fmt,
            "header": header,
            "delimiter": delimiter,
            "comments": comments,
        }
