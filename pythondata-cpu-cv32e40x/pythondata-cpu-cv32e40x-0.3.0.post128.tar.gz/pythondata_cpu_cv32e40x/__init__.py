import os.path
__dir__ = os.path.split(os.path.abspath(os.path.realpath(__file__)))[0]
data_location = os.path.join(__dir__, "system_verilog")
src = "https://github.com/openhwgroup/cv32e40x"

# Module version
version_str = "0.3.0.post128"
version_tuple = (0, 3, 0, 128)
try:
    from packaging.version import Version as V
    pversion = V("0.3.0.post128")
except ImportError:
    pass

# Data version info
data_version_str = "0.3.0.post2"
data_version_tuple = (0, 3, 0, 2)
try:
    from packaging.version import Version as V
    pdata_version = V("0.3.0.post2")
except ImportError:
    pass
data_git_hash = "db3746634940d7db77720e58d4df32fc1060f695"
data_git_describe = "0.3.0-2-gdb37466"
data_git_msg = """\
commit db3746634940d7db77720e58d4df32fc1060f695
Merge: 991a430 fd755de
Author: silabs-oysteink <66771756+silabs-oysteink@users.noreply.github.com>
Date:   Thu Mar 31 10:40:11 2022 +0200

    Merge pull request #493 from silabs-halfdan/rvfi_csr_sleep_assertions
    
    Added RVFI assertions

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
