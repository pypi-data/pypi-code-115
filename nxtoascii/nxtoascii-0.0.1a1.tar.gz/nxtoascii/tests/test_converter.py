import os
import re
import numpy
import h5py
import pytest
from nxtoascii import Converter


def get_column_names(filename, comment="#"):
    with open(filename, "r") as f:
        line = names = f.readline().strip()
        while line.startswith(comment) or not line:
            names = line
            line = f.readline().strip()
        names = re.split("[ ,;]", names)
        return [s for s in names if s and not s.startswith(comment)]


def read_ascii(files, output_format, blocks=None):
    if output_format == "CSV":
        delimiter = ","
        skip_header = 1
    elif output_format in ["SPEC", "MULTISPEC"]:
        delimiter = None
        skip_header = 3
    else:
        delimiter = None
        skip_header = 0
    for filename in files:
        names = get_column_names(filename)
        data = numpy.genfromtxt(filename, skip_header=skip_header, delimiter=delimiter)
        if blocks:
            nrows_total = sum(tuple(zip(*blocks))[1])
            assert data.shape[0] == nrows_total
            row0 = 0
            for scan_name, nrows in blocks:
                row1 = row0 + nrows
                datai = data[row0:row1]
                row0 = row1
                datai = {name: vec for name, vec in zip(names, datai.T)}
                yield scan_name, datai
        else:
            data = {name: vec for name, vec in zip(names, data.T)}
            scan_name = os.path.basename(filename)
            scan_name = os.path.splitext(scan_name)[0]
            scan_name = scan_name.replace("_", ".")
            yield scan_name, data


def read_hdf5(filename):
    with h5py.File(filename, mode="r") as h5file:
        for scan_name in h5file:
            grp = h5file[scan_name]["measurement"]
            data = {k: grp[k][()] for k in grp}
            yield scan_name, data


def assert_data_equal(data1, data2):
    assert set(data1.keys()) == set(data2.keys())
    for scan_name, scandata1 in data1.items():
        scandata2 = data2[scan_name]
        assert set(scandata1.keys()) == set(scandata2.keys())
        for k, v in scandata1.items():
            err_msg = "scan {}, channel {}".format(scan_name, k)
            numpy.testing.assert_allclose(v, scandata2[k], err_msg=err_msg)


@pytest.mark.parametrize("output_format", ["MULTISPEC", "SPEC", "CSV", "ASCII"])
def test_converter(tmpdir, blisshdf5file, output_format):
    outdir = tmpdir / "converted"

    converter = Converter(
        blisshdf5file, str(outdir), output_format=output_format, raise_on_error=True
    )
    converter.convert()

    if output_format == "MULTISPEC":
        nexpected = 1
    else:
        nexpected = 10
    files = outdir.listdir()
    assert len(files) == nexpected

    data1 = dict(read_hdf5(blisshdf5file))
    if output_format == "MULTISPEC":
        blocks = [
            (name, len(next(iter(datai.values()))))
            for name, datai in sorted(data1.items(), key=lambda tpl: float(tpl[0]))
        ]
    else:
        blocks = None

    data2 = dict(read_ascii(files, output_format, blocks=blocks))
    assert_data_equal(data1, data2)
