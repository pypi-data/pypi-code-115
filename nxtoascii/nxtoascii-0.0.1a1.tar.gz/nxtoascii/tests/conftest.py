import datetime
import numpy
import h5py
import pytest
from silx.io.dictdump import dicttonx


def timestamp():
    dt = datetime.datetime.now()
    return numpy.array(dt.isoformat(), dtype=h5py.special_dtype(vlen=str))


def add_detector_data(scandict, detectors, npoints, scannr):
    for detnr, name in enumerate(detectors, 1):
        data = numpy.arange(npoints) * scannr + detnr * 10
        scandict["instrument"][name] = {"@NX_class": "NXdetector", "data": data}
        scandict["measurement"][">" + name] = "../instrument/" + name + "/data"


def add_positioner_data(scandict, positioners, npoints, scannr):
    for psnr, name in enumerate(positioners, 1):
        data = numpy.arange(npoints) * scannr + psnr * 10
        scandict["instrument"][name] = {"@NX_class": "NXpositioner", "data": data}
        scandict["instrument"]["positioners"][">" + name] = "../" + name + "/data"
        scandict["measurement"][">" + name] = "../instrument/" + name + "/data"


@pytest.fixture()
def blisshdf5file(tmpdir):
    filename = str(tmpdir / "dataset.h5")
    adict = dict()
    positioners = ["energy"]
    detectors = ["I0", "It"]
    for scannr in range(1, 11):
        npoints = 100 + scannr
        scandict = {
            "instrument": {"@NX_class": "@NXinstrument", "positioners": {}},
            "measurement": {},
            "title": "testscan",
            "start_time": timestamp(),
        }
        adict[str(scannr) + ".1"] = scandict
        add_detector_data(scandict, detectors, npoints, scannr)
        add_positioner_data(scandict, positioners, npoints, scannr)
        scandict["end_time"] = timestamp()
    dicttonx(adict, filename)
    yield filename
