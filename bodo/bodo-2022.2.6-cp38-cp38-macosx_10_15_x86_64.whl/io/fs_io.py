"""
S3 & Hadoop file system supports, and file system dependent calls
"""
import glob
import os
import warnings
from urllib.parse import urlparse
import llvmlite.binding as ll
import numba
import numpy as np
from numba.core import types
from numba.extending import overload
import bodo
from bodo.io import csv_cpp
from bodo.libs.distributed_api import Reduce_Type
from bodo.libs.str_ext import unicode_to_utf8, unicode_to_utf8_and_len
from bodo.utils.typing import BodoError, BodoWarning
from bodo.utils.utils import check_java_installation
from fsspec.implementations.arrow import ArrowFSWrapper, ArrowFile, wrap_exceptions


def fsspec_arrowfswrapper__open(self, path, mode='rb', block_size=None, **
    kwargs):
    if mode == 'rb':
        try:
            nzmvs__ikt = self.fs.open_input_file(path)
        except:
            nzmvs__ikt = self.fs.open_input_stream(path)
    elif mode == 'wb':
        nzmvs__ikt = self.fs.open_output_stream(path)
    else:
        raise ValueError(f'unsupported mode for Arrow filesystem: {mode!r}')
    return ArrowFile(self, nzmvs__ikt, path, mode, block_size, **kwargs)


ArrowFSWrapper._open = wrap_exceptions(fsspec_arrowfswrapper__open)
_csv_write = types.ExternalFunction('csv_write', types.void(types.voidptr,
    types.voidptr, types.int64, types.int64, types.bool_, types.voidptr))
ll.add_symbol('csv_write', csv_cpp.csv_write)
bodo_error_msg = """
    Some possible causes:
        (1) Incorrect path: Specified file/directory doesn't exist or is unreachable.
        (2) Missing credentials: You haven't provided S3 credentials, neither through 
            environment variables, nor through a local AWS setup 
            that makes the credentials available at ~/.aws/credentials.
        (3) Incorrect credentials: Your S3 credentials are incorrect or do not have
            the correct permissions.
    """


def get_proxy_uri_from_env_vars():
    return os.environ.get('http_proxy', None) or os.environ.get('https_proxy',
        None) or os.environ.get('HTTP_PROXY', None) or os.environ.get(
        'HTTPS_PROXY', None)


def get_s3_fs(region=None, storage_options=None):
    from pyarrow.fs import S3FileSystem
    pai__fphl = os.environ.get('AWS_S3_ENDPOINT', None)
    if not region:
        region = os.environ.get('AWS_DEFAULT_REGION', None)
    orc__fkxo = False
    ilpaj__arglc = get_proxy_uri_from_env_vars()
    if storage_options:
        orc__fkxo = storage_options.get('anon', False)
    return S3FileSystem(anonymous=orc__fkxo, region=region,
        endpoint_override=pai__fphl, proxy_options=ilpaj__arglc)


def get_s3_subtree_fs(bucket_name, region=None, storage_options=None):
    from pyarrow._fs import SubTreeFileSystem
    from pyarrow._s3fs import S3FileSystem
    pai__fphl = os.environ.get('AWS_S3_ENDPOINT', None)
    if not region:
        region = os.environ.get('AWS_DEFAULT_REGION', None)
    orc__fkxo = False
    ilpaj__arglc = get_proxy_uri_from_env_vars()
    if storage_options:
        orc__fkxo = storage_options.get('anon', False)
    fs = S3FileSystem(region=region, endpoint_override=pai__fphl, anonymous
        =orc__fkxo, proxy_options=ilpaj__arglc)
    return SubTreeFileSystem(bucket_name, fs)


def get_s3_fs_from_path(path, parallel=False, storage_options=None):
    region = get_s3_bucket_region_njit(path, parallel=parallel)
    if region == '':
        region = None
    return get_s3_fs(region, storage_options)


def get_hdfs_fs(path):
    from pyarrow.fs import HadoopFileSystem as HdFS
    pkva__utra = urlparse(path)
    if pkva__utra.scheme in ('abfs', 'abfss'):
        dvmft__iuh = path
        if pkva__utra.port is None:
            mcig__augd = 0
        else:
            mcig__augd = pkva__utra.port
        ffwys__pxpy = None
    else:
        dvmft__iuh = pkva__utra.hostname
        mcig__augd = pkva__utra.port
        ffwys__pxpy = pkva__utra.username
    try:
        fs = HdFS(host=dvmft__iuh, port=mcig__augd, user=ffwys__pxpy)
    except Exception as ooqfg__jbga:
        raise BodoError('Hadoop file system cannot be created: {}'.format(
            ooqfg__jbga))
    return fs


def gcs_is_directory(path):
    import gcsfs
    fs = gcsfs.GCSFileSystem(token=None)
    try:
        reluk__qoq = fs.isdir(path)
    except gcsfs.utils.HttpError as ooqfg__jbga:
        raise BodoError(
            f'{ooqfg__jbga}. Make sure your google cloud credentials are set!')
    return reluk__qoq


def gcs_list_dir_fnames(path):
    import gcsfs
    fs = gcsfs.GCSFileSystem(token=None)
    return [suwri__gcbs.split('/')[-1] for suwri__gcbs in fs.ls(path)]


def s3_is_directory(fs, path):
    from pyarrow import fs as pa_fs
    try:
        pkva__utra = urlparse(path)
        kuxb__don = (pkva__utra.netloc + pkva__utra.path).rstrip('/')
        xzs__rebj = fs.get_file_info(kuxb__don)
        if xzs__rebj.type in (pa_fs.FileType.NotFound, pa_fs.FileType.Unknown):
            raise FileNotFoundError('{} is a non-existing or unreachable file'
                .format(path))
        if not xzs__rebj.size and xzs__rebj.type == pa_fs.FileType.Directory:
            return True
        return False
    except (FileNotFoundError, OSError) as ooqfg__jbga:
        raise
    except BodoError as euv__piiee:
        raise
    except Exception as ooqfg__jbga:
        raise BodoError(
            f"""error from pyarrow S3FileSystem: {type(ooqfg__jbga).__name__}: {str(ooqfg__jbga)}
{bodo_error_msg}"""
            )


def s3_list_dir_fnames(fs, path):
    from pyarrow import fs as pa_fs
    ldk__ygnm = None
    try:
        if s3_is_directory(fs, path):
            pkva__utra = urlparse(path)
            kuxb__don = (pkva__utra.netloc + pkva__utra.path).rstrip('/')
            vdf__urzmc = pa_fs.FileSelector(kuxb__don, recursive=False)
            lukz__piq = fs.get_file_info(vdf__urzmc)
            if lukz__piq and lukz__piq[0].path in [kuxb__don, f'{kuxb__don}/'
                ] and int(lukz__piq[0].size or 0) == 0:
                lukz__piq = lukz__piq[1:]
            ldk__ygnm = [evbmb__peuzo.base_name for evbmb__peuzo in lukz__piq]
    except BodoError as euv__piiee:
        raise
    except Exception as ooqfg__jbga:
        raise BodoError(
            f"""error from pyarrow S3FileSystem: {type(ooqfg__jbga).__name__}: {str(ooqfg__jbga)}
{bodo_error_msg}"""
            )
    return ldk__ygnm


def hdfs_is_directory(path):
    from pyarrow.fs import FileType, HadoopFileSystem
    check_java_installation(path)
    pkva__utra = urlparse(path)
    oso__vddfj = pkva__utra.path
    try:
        hrws__qcsrl = HadoopFileSystem.from_uri(path)
    except Exception as ooqfg__jbga:
        raise BodoError(' Hadoop file system cannot be created: {}'.format(
            ooqfg__jbga))
    rupwf__gqr = hrws__qcsrl.get_file_info([oso__vddfj])
    if rupwf__gqr[0].type in (FileType.NotFound, FileType.Unknown):
        raise BodoError('{} is a non-existing or unreachable file'.format(path)
            )
    if not rupwf__gqr[0].size and rupwf__gqr[0].type == FileType.Directory:
        return hrws__qcsrl, True
    return hrws__qcsrl, False


def hdfs_list_dir_fnames(path):
    from pyarrow.fs import FileSelector
    ldk__ygnm = None
    hrws__qcsrl, reluk__qoq = hdfs_is_directory(path)
    if reluk__qoq:
        pkva__utra = urlparse(path)
        oso__vddfj = pkva__utra.path
        vdf__urzmc = FileSelector(oso__vddfj, recursive=True)
        try:
            lukz__piq = hrws__qcsrl.get_file_info(vdf__urzmc)
        except Exception as ooqfg__jbga:
            raise BodoError('Exception on getting directory info of {}: {}'
                .format(oso__vddfj, ooqfg__jbga))
        ldk__ygnm = [evbmb__peuzo.base_name for evbmb__peuzo in lukz__piq]
    return hrws__qcsrl, ldk__ygnm


def abfs_is_directory(path):
    hrws__qcsrl = get_hdfs_fs(path)
    try:
        rupwf__gqr = hrws__qcsrl.info(path)
    except OSError as euv__piiee:
        raise BodoError('{} is a non-existing or unreachable file'.format(path)
            )
    if rupwf__gqr['size'] == 0 and rupwf__gqr['kind'].lower() == 'directory':
        return hrws__qcsrl, True
    return hrws__qcsrl, False


def abfs_list_dir_fnames(path):
    ldk__ygnm = None
    hrws__qcsrl, reluk__qoq = abfs_is_directory(path)
    if reluk__qoq:
        pkva__utra = urlparse(path)
        oso__vddfj = pkva__utra.path
        try:
            jqaqi__xaw = hrws__qcsrl.ls(oso__vddfj)
        except Exception as ooqfg__jbga:
            raise BodoError('Exception on getting directory info of {}: {}'
                .format(oso__vddfj, ooqfg__jbga))
        ldk__ygnm = [fname[fname.rindex('/') + 1:] for fname in jqaqi__xaw]
    return hrws__qcsrl, ldk__ygnm


def directory_of_files_common_filter(fname):
    return not (fname.endswith('.crc') or fname.endswith('_$folder$') or
        fname.startswith('.') or fname.startswith('_') and fname !=
        '_delta_log')


def find_file_name_or_handler(path, ftype):
    from urllib.parse import urlparse
    octi__glbs = urlparse(path)
    fname = path
    fs = None
    vxmzl__qrf = 'read_json' if ftype == 'json' else 'read_csv'
    zqgy__qkm = (
        f'pd.{vxmzl__qrf}(): there is no {ftype} file in directory: {fname}')
    vhb__ngt = directory_of_files_common_filter
    if octi__glbs.scheme == 's3':
        pdjus__znqxg = True
        fs = get_s3_fs_from_path(path)
        ewn__wrs = s3_list_dir_fnames(fs, path)
        kuxb__don = (octi__glbs.netloc + octi__glbs.path).rstrip('/')
        fname = kuxb__don
        if ewn__wrs:
            ewn__wrs = [(kuxb__don + '/' + suwri__gcbs) for suwri__gcbs in
                sorted(filter(vhb__ngt, ewn__wrs))]
            qdsm__wamy = [suwri__gcbs for suwri__gcbs in ewn__wrs if int(fs
                .get_file_info(suwri__gcbs).size or 0) > 0]
            if len(qdsm__wamy) == 0:
                raise BodoError(zqgy__qkm)
            fname = qdsm__wamy[0]
        wmpm__ftwrr = int(fs.get_file_info(fname).size or 0)
        kwwdp__yrtmy = fs.open_input_file(fname)
    elif octi__glbs.scheme == 'hdfs':
        pdjus__znqxg = True
        fs, ewn__wrs = hdfs_list_dir_fnames(path)
        wmpm__ftwrr = fs.get_file_info([octi__glbs.path])[0].size
        if ewn__wrs:
            path = path.rstrip('/')
            ewn__wrs = [(path + '/' + suwri__gcbs) for suwri__gcbs in
                sorted(filter(vhb__ngt, ewn__wrs))]
            qdsm__wamy = [suwri__gcbs for suwri__gcbs in ewn__wrs if fs.
                get_file_info([urlparse(suwri__gcbs).path])[0].size > 0]
            if len(qdsm__wamy) == 0:
                raise BodoError(zqgy__qkm)
            fname = qdsm__wamy[0]
            fname = urlparse(fname).path
            wmpm__ftwrr = fs.get_file_info([fname])[0].size
        kwwdp__yrtmy = fs.open_input_file(fname)
    elif octi__glbs.scheme in ('abfs', 'abfss'):
        pdjus__znqxg = True
        fs, ewn__wrs = abfs_list_dir_fnames(path)
        wmpm__ftwrr = fs.info(fname)['size']
        if ewn__wrs:
            path = path.rstrip('/')
            ewn__wrs = [(path + '/' + suwri__gcbs) for suwri__gcbs in
                sorted(filter(vhb__ngt, ewn__wrs))]
            qdsm__wamy = [suwri__gcbs for suwri__gcbs in ewn__wrs if fs.
                info(suwri__gcbs)['size'] > 0]
            if len(qdsm__wamy) == 0:
                raise BodoError(zqgy__qkm)
            fname = qdsm__wamy[0]
            wmpm__ftwrr = fs.info(fname)['size']
            fname = urlparse(fname).path
        kwwdp__yrtmy = fs.open(fname, 'rb')
    else:
        if octi__glbs.scheme != '':
            raise BodoError(
                f'Unrecognized scheme {octi__glbs.scheme}. Please refer to https://docs.bodo.ai/latest/source/file_io.html'
                )
        pdjus__znqxg = False
        if os.path.isdir(path):
            jqaqi__xaw = filter(vhb__ngt, glob.glob(os.path.join(os.path.
                abspath(path), '*')))
            qdsm__wamy = [suwri__gcbs for suwri__gcbs in sorted(jqaqi__xaw) if
                os.path.getsize(suwri__gcbs) > 0]
            if len(qdsm__wamy) == 0:
                raise BodoError(zqgy__qkm)
            fname = qdsm__wamy[0]
        wmpm__ftwrr = os.path.getsize(fname)
        kwwdp__yrtmy = fname
    return pdjus__znqxg, kwwdp__yrtmy, wmpm__ftwrr, fs


def get_s3_bucket_region(s3_filepath, parallel):
    try:
        from pyarrow import fs as pa_fs
    except:
        raise BodoError('Reading from s3 requires pyarrow currently.')
    from mpi4py import MPI
    qlifh__ptxy = MPI.COMM_WORLD
    bucket_loc = None
    if parallel and bodo.get_rank() == 0 or not parallel:
        try:
            ekw__xismf, xqdz__vvfl = pa_fs.S3FileSystem.from_uri(s3_filepath)
            bucket_loc = ekw__xismf.region
        except Exception as ooqfg__jbga:
            if os.environ.get('AWS_DEFAULT_REGION', '') == '':
                warnings.warn(BodoWarning(
                    f"""Unable to get S3 Bucket Region.
{ooqfg__jbga}.
Value not defined in the AWS_DEFAULT_REGION environment variable either. Region defaults to us-east-1 currently."""
                    ))
            bucket_loc = ''
    if parallel:
        bucket_loc = qlifh__ptxy.bcast(bucket_loc)
    return bucket_loc


@numba.njit()
def get_s3_bucket_region_njit(s3_filepath, parallel):
    with numba.objmode(bucket_loc='unicode_type'):
        bucket_loc = ''
        if isinstance(s3_filepath, list):
            s3_filepath = s3_filepath[0]
        if s3_filepath.startswith('s3://'):
            bucket_loc = get_s3_bucket_region(s3_filepath, parallel)
    return bucket_loc


def csv_write(path_or_buf, D, is_parallel=False):
    return None


@overload(csv_write, no_unliteral=True)
def csv_write_overload(path_or_buf, D, is_parallel=False):

    def impl(path_or_buf, D, is_parallel=False):
        apb__wkem = get_s3_bucket_region_njit(path_or_buf, parallel=is_parallel
            )
        rep__vbovm, odqvg__hix = unicode_to_utf8_and_len(D)
        lna__lovu = 0
        if is_parallel:
            lna__lovu = bodo.libs.distributed_api.dist_exscan(odqvg__hix,
                np.int32(Reduce_Type.Sum.value))
        _csv_write(unicode_to_utf8(path_or_buf), rep__vbovm, lna__lovu,
            odqvg__hix, is_parallel, unicode_to_utf8(apb__wkem))
        bodo.utils.utils.check_and_propagate_cpp_exception()
    return impl
