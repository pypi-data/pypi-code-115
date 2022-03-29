import os.path
__dir__ = os.path.split(os.path.abspath(os.path.realpath(__file__)))[0]
data_location = os.path.join(__dir__, "system_verilog")
src = "https://github.com/openhwgroup/cv32e40x"

# Module version
version_str = "0.3.0.post126"
version_tuple = (0, 3, 0, 126)
try:
    from packaging.version import Version as V
    pversion = V("0.3.0.post126")
except ImportError:
    pass

# Data version info
data_version_str = "0.3.0.post0"
data_version_tuple = (0, 3, 0, 0)
try:
    from packaging.version import Version as V
    pdata_version = V("0.3.0.post0")
except ImportError:
    pass
data_git_hash = "991a430a9d685fd35935c91e73ff826cdb12adf7"
data_git_describe = "0.3.0-0-g991a430"
data_git_msg = """\
commit 991a430a9d685fd35935c91e73ff826cdb12adf7
Merge: b84f137 affb070
Author: Arjan Bink <40633348+Silabs-ArjanB@users.noreply.github.com>
Date:   Tue Mar 29 08:01:47 2022 +0200

    Merge pull request #487 from silabs-halfdan/rvfi_sleep_signals_extension
    
    RVFI Sleep Signals

"""

# Tool version info
tool_version_str = "0.0.post126"
tool_version_tuple = (0, 0, 126)
try:
    from packaging.version import Version as V
    ptool_version = V("0.0.post126")
except ImportError:
    pass


def data_file(f):
    """Get absolute path for file inside pythondata_cpu_cv32e40x."""
    fn = os.path.join(data_location, f)
    fn = os.path.abspath(fn)
    if not os.path.exists(fn):
        raise IOError("File {f} doesn't exist in pythondata_cpu_cv32e40x".format(f))
    return fn
