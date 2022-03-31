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
            etlg__gggd = self.fs.open_input_file(path)
        except:
            etlg__gggd = self.fs.open_input_stream(path)
    elif mode == 'wb':
        etlg__gggd = self.fs.open_output_stream(path)
    else:
        raise ValueError(f'unsupported mode for Arrow filesystem: {mode!r}')
    return ArrowFile(self, etlg__gggd, path, mode, block_size, **kwargs)


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
    dsbwk__zei = os.environ.get('AWS_S3_ENDPOINT', None)
    if not region:
        region = os.environ.get('AWS_DEFAULT_REGION', None)
    vmdyb__pgqi = False
    sqfy__drs = get_proxy_uri_from_env_vars()
    if storage_options:
        vmdyb__pgqi = storage_options.get('anon', False)
    return S3FileSystem(anonymous=vmdyb__pgqi, region=region,
        endpoint_override=dsbwk__zei, proxy_options=sqfy__drs)


def get_s3_subtree_fs(bucket_name, region=None, storage_options=None):
    from pyarrow._fs import SubTreeFileSystem
    from pyarrow._s3fs import S3FileSystem
    dsbwk__zei = os.environ.get('AWS_S3_ENDPOINT', None)
    if not region:
        region = os.environ.get('AWS_DEFAULT_REGION', None)
    vmdyb__pgqi = False
    sqfy__drs = get_proxy_uri_from_env_vars()
    if storage_options:
        vmdyb__pgqi = storage_options.get('anon', False)
    fs = S3FileSystem(region=region, endpoint_override=dsbwk__zei,
        anonymous=vmdyb__pgqi, proxy_options=sqfy__drs)
    return SubTreeFileSystem(bucket_name, fs)


def get_s3_fs_from_path(path, parallel=False, storage_options=None):
    region = get_s3_bucket_region_njit(path, parallel=parallel)
    if region == '':
        region = None
    return get_s3_fs(region, storage_options)


def get_hdfs_fs(path):
    from pyarrow.fs import HadoopFileSystem as HdFS
    iwf__mpii = urlparse(path)
    if iwf__mpii.scheme in ('abfs', 'abfss'):
        kvn__xbt = path
        if iwf__mpii.port is None:
            ugw__zusf = 0
        else:
            ugw__zusf = iwf__mpii.port
        cbkoi__dpixo = None
    else:
        kvn__xbt = iwf__mpii.hostname
        ugw__zusf = iwf__mpii.port
        cbkoi__dpixo = iwf__mpii.username
    try:
        fs = HdFS(host=kvn__xbt, port=ugw__zusf, user=cbkoi__dpixo)
    except Exception as oxfse__idt:
        raise BodoError('Hadoop file system cannot be created: {}'.format(
            oxfse__idt))
    return fs


def gcs_is_directory(path):
    import gcsfs
    fs = gcsfs.GCSFileSystem(token=None)
    try:
        tchij__hyxya = fs.isdir(path)
    except gcsfs.utils.HttpError as oxfse__idt:
        raise BodoError(
            f'{oxfse__idt}. Make sure your google cloud credentials are set!')
    return tchij__hyxya


def gcs_list_dir_fnames(path):
    import gcsfs
    fs = gcsfs.GCSFileSystem(token=None)
    return [guz__oey.split('/')[-1] for guz__oey in fs.ls(path)]


def s3_is_directory(fs, path):
    from pyarrow import fs as pa_fs
    try:
        iwf__mpii = urlparse(path)
        ordp__lko = (iwf__mpii.netloc + iwf__mpii.path).rstrip('/')
        afksz__bdrcn = fs.get_file_info(ordp__lko)
        if afksz__bdrcn.type in (pa_fs.FileType.NotFound, pa_fs.FileType.
            Unknown):
            raise FileNotFoundError('{} is a non-existing or unreachable file'
                .format(path))
        if (not afksz__bdrcn.size and afksz__bdrcn.type == pa_fs.FileType.
            Directory):
            return True
        return False
    except (FileNotFoundError, OSError) as oxfse__idt:
        raise
    except BodoError as wtpth__rej:
        raise
    except Exception as oxfse__idt:
        raise BodoError(
            f"""error from pyarrow S3FileSystem: {type(oxfse__idt).__name__}: {str(oxfse__idt)}
{bodo_error_msg}"""
            )


def s3_list_dir_fnames(fs, path):
    from pyarrow import fs as pa_fs
    ptz__jjjca = None
    try:
        if s3_is_directory(fs, path):
            iwf__mpii = urlparse(path)
            ordp__lko = (iwf__mpii.netloc + iwf__mpii.path).rstrip('/')
            lyfvs__rmz = pa_fs.FileSelector(ordp__lko, recursive=False)
            bwlq__eaie = fs.get_file_info(lyfvs__rmz)
            if bwlq__eaie and bwlq__eaie[0].path in [ordp__lko, f'{ordp__lko}/'
                ] and int(bwlq__eaie[0].size or 0) == 0:
                bwlq__eaie = bwlq__eaie[1:]
            ptz__jjjca = [qktg__vtjxl.base_name for qktg__vtjxl in bwlq__eaie]
    except BodoError as wtpth__rej:
        raise
    except Exception as oxfse__idt:
        raise BodoError(
            f"""error from pyarrow S3FileSystem: {type(oxfse__idt).__name__}: {str(oxfse__idt)}
{bodo_error_msg}"""
            )
    return ptz__jjjca


def hdfs_is_directory(path):
    from pyarrow.fs import FileType, HadoopFileSystem
    check_java_installation(path)
    iwf__mpii = urlparse(path)
    ggdv__pnnxy = iwf__mpii.path
    try:
        msxi__mwib = HadoopFileSystem.from_uri(path)
    except Exception as oxfse__idt:
        raise BodoError(' Hadoop file system cannot be created: {}'.format(
            oxfse__idt))
    iias__rvf = msxi__mwib.get_file_info([ggdv__pnnxy])
    if iias__rvf[0].type in (FileType.NotFound, FileType.Unknown):
        raise BodoError('{} is a non-existing or unreachable file'.format(path)
            )
    if not iias__rvf[0].size and iias__rvf[0].type == FileType.Directory:
        return msxi__mwib, True
    return msxi__mwib, False


def hdfs_list_dir_fnames(path):
    from pyarrow.fs import FileSelector
    ptz__jjjca = None
    msxi__mwib, tchij__hyxya = hdfs_is_directory(path)
    if tchij__hyxya:
        iwf__mpii = urlparse(path)
        ggdv__pnnxy = iwf__mpii.path
        lyfvs__rmz = FileSelector(ggdv__pnnxy, recursive=True)
        try:
            bwlq__eaie = msxi__mwib.get_file_info(lyfvs__rmz)
        except Exception as oxfse__idt:
            raise BodoError('Exception on getting directory info of {}: {}'
                .format(ggdv__pnnxy, oxfse__idt))
        ptz__jjjca = [qktg__vtjxl.base_name for qktg__vtjxl in bwlq__eaie]
    return msxi__mwib, ptz__jjjca


def abfs_is_directory(path):
    msxi__mwib = get_hdfs_fs(path)
    try:
        iias__rvf = msxi__mwib.info(path)
    except OSError as wtpth__rej:
        raise BodoError('{} is a non-existing or unreachable file'.format(path)
            )
    if iias__rvf['size'] == 0 and iias__rvf['kind'].lower() == 'directory':
        return msxi__mwib, True
    return msxi__mwib, False


def abfs_list_dir_fnames(path):
    ptz__jjjca = None
    msxi__mwib, tchij__hyxya = abfs_is_directory(path)
    if tchij__hyxya:
        iwf__mpii = urlparse(path)
        ggdv__pnnxy = iwf__mpii.path
        try:
            ghczk__qociw = msxi__mwib.ls(ggdv__pnnxy)
        except Exception as oxfse__idt:
            raise BodoError('Exception on getting directory info of {}: {}'
                .format(ggdv__pnnxy, oxfse__idt))
        ptz__jjjca = [fname[fname.rindex('/') + 1:] for fname in ghczk__qociw]
    return msxi__mwib, ptz__jjjca


def directory_of_files_common_filter(fname):
    return not (fname.endswith('.crc') or fname.endswith('_$folder$') or
        fname.startswith('.') or fname.startswith('_') and fname !=
        '_delta_log')


def find_file_name_or_handler(path, ftype):
    from urllib.parse import urlparse
    mhxoe__peo = urlparse(path)
    fname = path
    fs = None
    gsb__vsg = 'read_json' if ftype == 'json' else 'read_csv'
    qhwp__fvd = (
        f'pd.{gsb__vsg}(): there is no {ftype} file in directory: {fname}')
    rzwc__wbri = directory_of_files_common_filter
    if mhxoe__peo.scheme == 's3':
        xmvq__sqiyp = True
        fs = get_s3_fs_from_path(path)
        qvwn__vvn = s3_list_dir_fnames(fs, path)
        ordp__lko = (mhxoe__peo.netloc + mhxoe__peo.path).rstrip('/')
        fname = ordp__lko
        if qvwn__vvn:
            qvwn__vvn = [(ordp__lko + '/' + guz__oey) for guz__oey in
                sorted(filter(rzwc__wbri, qvwn__vvn))]
            exl__jgq = [guz__oey for guz__oey in qvwn__vvn if int(fs.
                get_file_info(guz__oey).size or 0) > 0]
            if len(exl__jgq) == 0:
                raise BodoError(qhwp__fvd)
            fname = exl__jgq[0]
        ypwuz__zlyy = int(fs.get_file_info(fname).size or 0)
        ivbc__neivn = fs.open_input_file(fname)
    elif mhxoe__peo.scheme == 'hdfs':
        xmvq__sqiyp = True
        fs, qvwn__vvn = hdfs_list_dir_fnames(path)
        ypwuz__zlyy = fs.get_file_info([mhxoe__peo.path])[0].size
        if qvwn__vvn:
            path = path.rstrip('/')
            qvwn__vvn = [(path + '/' + guz__oey) for guz__oey in sorted(
                filter(rzwc__wbri, qvwn__vvn))]
            exl__jgq = [guz__oey for guz__oey in qvwn__vvn if fs.
                get_file_info([urlparse(guz__oey).path])[0].size > 0]
            if len(exl__jgq) == 0:
                raise BodoError(qhwp__fvd)
            fname = exl__jgq[0]
            fname = urlparse(fname).path
            ypwuz__zlyy = fs.get_file_info([fname])[0].size
        ivbc__neivn = fs.open_input_file(fname)
    elif mhxoe__peo.scheme in ('abfs', 'abfss'):
        xmvq__sqiyp = True
        fs, qvwn__vvn = abfs_list_dir_fnames(path)
        ypwuz__zlyy = fs.info(fname)['size']
        if qvwn__vvn:
            path = path.rstrip('/')
            qvwn__vvn = [(path + '/' + guz__oey) for guz__oey in sorted(
                filter(rzwc__wbri, qvwn__vvn))]
            exl__jgq = [guz__oey for guz__oey in qvwn__vvn if fs.info(
                guz__oey)['size'] > 0]
            if len(exl__jgq) == 0:
                raise BodoError(qhwp__fvd)
            fname = exl__jgq[0]
            ypwuz__zlyy = fs.info(fname)['size']
            fname = urlparse(fname).path
        ivbc__neivn = fs.open(fname, 'rb')
    else:
        if mhxoe__peo.scheme != '':
            raise BodoError(
                f'Unrecognized scheme {mhxoe__peo.scheme}. Please refer to https://docs.bodo.ai/latest/source/file_io.html'
                )
        xmvq__sqiyp = False
        if os.path.isdir(path):
            ghczk__qociw = filter(rzwc__wbri, glob.glob(os.path.join(os.
                path.abspath(path), '*')))
            exl__jgq = [guz__oey for guz__oey in sorted(ghczk__qociw) if os
                .path.getsize(guz__oey) > 0]
            if len(exl__jgq) == 0:
                raise BodoError(qhwp__fvd)
            fname = exl__jgq[0]
        ypwuz__zlyy = os.path.getsize(fname)
        ivbc__neivn = fname
    return xmvq__sqiyp, ivbc__neivn, ypwuz__zlyy, fs


def get_s3_bucket_region(s3_filepath, parallel):
    try:
        from pyarrow import fs as pa_fs
    except:
        raise BodoError('Reading from s3 requires pyarrow currently.')
    from mpi4py import MPI
    jvlhj__oxf = MPI.COMM_WORLD
    bucket_loc = None
    if parallel and bodo.get_rank() == 0 or not parallel:
        try:
            wcg__nekf, qscem__igi = pa_fs.S3FileSystem.from_uri(s3_filepath)
            bucket_loc = wcg__nekf.region
        except Exception as oxfse__idt:
            if os.environ.get('AWS_DEFAULT_REGION', '') == '':
                warnings.warn(BodoWarning(
                    f"""Unable to get S3 Bucket Region.
{oxfse__idt}.
Value not defined in the AWS_DEFAULT_REGION environment variable either. Region defaults to us-east-1 currently."""
                    ))
            bucket_loc = ''
    if parallel:
        bucket_loc = jvlhj__oxf.bcast(bucket_loc)
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
        vpri__gwuxr = get_s3_bucket_region_njit(path_or_buf, parallel=
            is_parallel)
        dbj__klj, orhwq__jxi = unicode_to_utf8_and_len(D)
        jsp__tthxi = 0
        if is_parallel:
            jsp__tthxi = bodo.libs.distributed_api.dist_exscan(orhwq__jxi,
                np.int32(Reduce_Type.Sum.value))
        _csv_write(unicode_to_utf8(path_or_buf), dbj__klj, jsp__tthxi,
            orhwq__jxi, is_parallel, unicode_to_utf8(vpri__gwuxr))
        bodo.utils.utils.check_and_propagate_cpp_exception()
    return impl
