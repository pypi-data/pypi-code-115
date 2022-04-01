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
            dixep__bkveq = self.fs.open_input_file(path)
        except:
            dixep__bkveq = self.fs.open_input_stream(path)
    elif mode == 'wb':
        dixep__bkveq = self.fs.open_output_stream(path)
    else:
        raise ValueError(f'unsupported mode for Arrow filesystem: {mode!r}')
    return ArrowFile(self, dixep__bkveq, path, mode, block_size, **kwargs)


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
    fkcbt__cwhw = os.environ.get('AWS_S3_ENDPOINT', None)
    if not region:
        region = os.environ.get('AWS_DEFAULT_REGION', None)
    qzdh__lywt = False
    lxrk__gyvz = get_proxy_uri_from_env_vars()
    if storage_options:
        qzdh__lywt = storage_options.get('anon', False)
    return S3FileSystem(anonymous=qzdh__lywt, region=region,
        endpoint_override=fkcbt__cwhw, proxy_options=lxrk__gyvz)


def get_s3_subtree_fs(bucket_name, region=None, storage_options=None):
    from pyarrow._fs import SubTreeFileSystem
    from pyarrow._s3fs import S3FileSystem
    fkcbt__cwhw = os.environ.get('AWS_S3_ENDPOINT', None)
    if not region:
        region = os.environ.get('AWS_DEFAULT_REGION', None)
    qzdh__lywt = False
    lxrk__gyvz = get_proxy_uri_from_env_vars()
    if storage_options:
        qzdh__lywt = storage_options.get('anon', False)
    fs = S3FileSystem(region=region, endpoint_override=fkcbt__cwhw,
        anonymous=qzdh__lywt, proxy_options=lxrk__gyvz)
    return SubTreeFileSystem(bucket_name, fs)


def get_s3_fs_from_path(path, parallel=False, storage_options=None):
    region = get_s3_bucket_region_njit(path, parallel=parallel)
    if region == '':
        region = None
    return get_s3_fs(region, storage_options)


def get_hdfs_fs(path):
    from pyarrow.fs import HadoopFileSystem as HdFS
    vttv__mkm = urlparse(path)
    if vttv__mkm.scheme in ('abfs', 'abfss'):
        tnj__ckc = path
        if vttv__mkm.port is None:
            gjq__kijp = 0
        else:
            gjq__kijp = vttv__mkm.port
        uqkk__dobj = None
    else:
        tnj__ckc = vttv__mkm.hostname
        gjq__kijp = vttv__mkm.port
        uqkk__dobj = vttv__mkm.username
    try:
        fs = HdFS(host=tnj__ckc, port=gjq__kijp, user=uqkk__dobj)
    except Exception as ysvso__wolpx:
        raise BodoError('Hadoop file system cannot be created: {}'.format(
            ysvso__wolpx))
    return fs


def gcs_is_directory(path):
    import gcsfs
    fs = gcsfs.GCSFileSystem(token=None)
    try:
        jdka__poav = fs.isdir(path)
    except gcsfs.utils.HttpError as ysvso__wolpx:
        raise BodoError(
            f'{ysvso__wolpx}. Make sure your google cloud credentials are set!'
            )
    return jdka__poav


def gcs_list_dir_fnames(path):
    import gcsfs
    fs = gcsfs.GCSFileSystem(token=None)
    return [ftalj__tjud.split('/')[-1] for ftalj__tjud in fs.ls(path)]


def s3_is_directory(fs, path):
    from pyarrow import fs as pa_fs
    try:
        vttv__mkm = urlparse(path)
        jgv__tbv = (vttv__mkm.netloc + vttv__mkm.path).rstrip('/')
        lmw__rfbdg = fs.get_file_info(jgv__tbv)
        if lmw__rfbdg.type in (pa_fs.FileType.NotFound, pa_fs.FileType.Unknown
            ):
            raise FileNotFoundError('{} is a non-existing or unreachable file'
                .format(path))
        if not lmw__rfbdg.size and lmw__rfbdg.type == pa_fs.FileType.Directory:
            return True
        return False
    except (FileNotFoundError, OSError) as ysvso__wolpx:
        raise
    except BodoError as jhs__lsbvh:
        raise
    except Exception as ysvso__wolpx:
        raise BodoError(
            f"""error from pyarrow S3FileSystem: {type(ysvso__wolpx).__name__}: {str(ysvso__wolpx)}
{bodo_error_msg}"""
            )


def s3_list_dir_fnames(fs, path):
    from pyarrow import fs as pa_fs
    ckuwq__zexc = None
    try:
        if s3_is_directory(fs, path):
            vttv__mkm = urlparse(path)
            jgv__tbv = (vttv__mkm.netloc + vttv__mkm.path).rstrip('/')
            mhvrb__uolz = pa_fs.FileSelector(jgv__tbv, recursive=False)
            byrjy__xdujm = fs.get_file_info(mhvrb__uolz)
            if byrjy__xdujm and byrjy__xdujm[0].path in [jgv__tbv,
                f'{jgv__tbv}/'] and int(byrjy__xdujm[0].size or 0) == 0:
                byrjy__xdujm = byrjy__xdujm[1:]
            ckuwq__zexc = [yqf__svk.base_name for yqf__svk in byrjy__xdujm]
    except BodoError as jhs__lsbvh:
        raise
    except Exception as ysvso__wolpx:
        raise BodoError(
            f"""error from pyarrow S3FileSystem: {type(ysvso__wolpx).__name__}: {str(ysvso__wolpx)}
{bodo_error_msg}"""
            )
    return ckuwq__zexc


def hdfs_is_directory(path):
    from pyarrow.fs import FileType, HadoopFileSystem
    check_java_installation(path)
    vttv__mkm = urlparse(path)
    yta__pvjsg = vttv__mkm.path
    try:
        wpwdx__kkao = HadoopFileSystem.from_uri(path)
    except Exception as ysvso__wolpx:
        raise BodoError(' Hadoop file system cannot be created: {}'.format(
            ysvso__wolpx))
    hql__otp = wpwdx__kkao.get_file_info([yta__pvjsg])
    if hql__otp[0].type in (FileType.NotFound, FileType.Unknown):
        raise BodoError('{} is a non-existing or unreachable file'.format(path)
            )
    if not hql__otp[0].size and hql__otp[0].type == FileType.Directory:
        return wpwdx__kkao, True
    return wpwdx__kkao, False


def hdfs_list_dir_fnames(path):
    from pyarrow.fs import FileSelector
    ckuwq__zexc = None
    wpwdx__kkao, jdka__poav = hdfs_is_directory(path)
    if jdka__poav:
        vttv__mkm = urlparse(path)
        yta__pvjsg = vttv__mkm.path
        mhvrb__uolz = FileSelector(yta__pvjsg, recursive=True)
        try:
            byrjy__xdujm = wpwdx__kkao.get_file_info(mhvrb__uolz)
        except Exception as ysvso__wolpx:
            raise BodoError('Exception on getting directory info of {}: {}'
                .format(yta__pvjsg, ysvso__wolpx))
        ckuwq__zexc = [yqf__svk.base_name for yqf__svk in byrjy__xdujm]
    return wpwdx__kkao, ckuwq__zexc


def abfs_is_directory(path):
    wpwdx__kkao = get_hdfs_fs(path)
    try:
        hql__otp = wpwdx__kkao.info(path)
    except OSError as jhs__lsbvh:
        raise BodoError('{} is a non-existing or unreachable file'.format(path)
            )
    if hql__otp['size'] == 0 and hql__otp['kind'].lower() == 'directory':
        return wpwdx__kkao, True
    return wpwdx__kkao, False


def abfs_list_dir_fnames(path):
    ckuwq__zexc = None
    wpwdx__kkao, jdka__poav = abfs_is_directory(path)
    if jdka__poav:
        vttv__mkm = urlparse(path)
        yta__pvjsg = vttv__mkm.path
        try:
            gvbf__qzxw = wpwdx__kkao.ls(yta__pvjsg)
        except Exception as ysvso__wolpx:
            raise BodoError('Exception on getting directory info of {}: {}'
                .format(yta__pvjsg, ysvso__wolpx))
        ckuwq__zexc = [fname[fname.rindex('/') + 1:] for fname in gvbf__qzxw]
    return wpwdx__kkao, ckuwq__zexc


def directory_of_files_common_filter(fname):
    return not (fname.endswith('.crc') or fname.endswith('_$folder$') or
        fname.startswith('.') or fname.startswith('_') and fname !=
        '_delta_log')


def find_file_name_or_handler(path, ftype):
    from urllib.parse import urlparse
    fmbia__xuge = urlparse(path)
    fname = path
    fs = None
    cts__wfw = 'read_json' if ftype == 'json' else 'read_csv'
    dyl__fxwv = (
        f'pd.{cts__wfw}(): there is no {ftype} file in directory: {fname}')
    uhbbm__ytxpb = directory_of_files_common_filter
    if fmbia__xuge.scheme == 's3':
        nsny__sfwe = True
        fs = get_s3_fs_from_path(path)
        hfnbj__fuiby = s3_list_dir_fnames(fs, path)
        jgv__tbv = (fmbia__xuge.netloc + fmbia__xuge.path).rstrip('/')
        fname = jgv__tbv
        if hfnbj__fuiby:
            hfnbj__fuiby = [(jgv__tbv + '/' + ftalj__tjud) for ftalj__tjud in
                sorted(filter(uhbbm__ytxpb, hfnbj__fuiby))]
            qjy__zzyg = [ftalj__tjud for ftalj__tjud in hfnbj__fuiby if int
                (fs.get_file_info(ftalj__tjud).size or 0) > 0]
            if len(qjy__zzyg) == 0:
                raise BodoError(dyl__fxwv)
            fname = qjy__zzyg[0]
        ozvb__eif = int(fs.get_file_info(fname).size or 0)
        tto__kfmdq = fs.open_input_file(fname)
    elif fmbia__xuge.scheme == 'hdfs':
        nsny__sfwe = True
        fs, hfnbj__fuiby = hdfs_list_dir_fnames(path)
        ozvb__eif = fs.get_file_info([fmbia__xuge.path])[0].size
        if hfnbj__fuiby:
            path = path.rstrip('/')
            hfnbj__fuiby = [(path + '/' + ftalj__tjud) for ftalj__tjud in
                sorted(filter(uhbbm__ytxpb, hfnbj__fuiby))]
            qjy__zzyg = [ftalj__tjud for ftalj__tjud in hfnbj__fuiby if fs.
                get_file_info([urlparse(ftalj__tjud).path])[0].size > 0]
            if len(qjy__zzyg) == 0:
                raise BodoError(dyl__fxwv)
            fname = qjy__zzyg[0]
            fname = urlparse(fname).path
            ozvb__eif = fs.get_file_info([fname])[0].size
        tto__kfmdq = fs.open_input_file(fname)
    elif fmbia__xuge.scheme in ('abfs', 'abfss'):
        nsny__sfwe = True
        fs, hfnbj__fuiby = abfs_list_dir_fnames(path)
        ozvb__eif = fs.info(fname)['size']
        if hfnbj__fuiby:
            path = path.rstrip('/')
            hfnbj__fuiby = [(path + '/' + ftalj__tjud) for ftalj__tjud in
                sorted(filter(uhbbm__ytxpb, hfnbj__fuiby))]
            qjy__zzyg = [ftalj__tjud for ftalj__tjud in hfnbj__fuiby if fs.
                info(ftalj__tjud)['size'] > 0]
            if len(qjy__zzyg) == 0:
                raise BodoError(dyl__fxwv)
            fname = qjy__zzyg[0]
            ozvb__eif = fs.info(fname)['size']
            fname = urlparse(fname).path
        tto__kfmdq = fs.open(fname, 'rb')
    else:
        if fmbia__xuge.scheme != '':
            raise BodoError(
                f'Unrecognized scheme {fmbia__xuge.scheme}. Please refer to https://docs.bodo.ai/latest/source/file_io.html'
                )
        nsny__sfwe = False
        if os.path.isdir(path):
            gvbf__qzxw = filter(uhbbm__ytxpb, glob.glob(os.path.join(os.
                path.abspath(path), '*')))
            qjy__zzyg = [ftalj__tjud for ftalj__tjud in sorted(gvbf__qzxw) if
                os.path.getsize(ftalj__tjud) > 0]
            if len(qjy__zzyg) == 0:
                raise BodoError(dyl__fxwv)
            fname = qjy__zzyg[0]
        ozvb__eif = os.path.getsize(fname)
        tto__kfmdq = fname
    return nsny__sfwe, tto__kfmdq, ozvb__eif, fs


def get_s3_bucket_region(s3_filepath, parallel):
    try:
        from pyarrow import fs as pa_fs
    except:
        raise BodoError('Reading from s3 requires pyarrow currently.')
    from mpi4py import MPI
    oebe__bscb = MPI.COMM_WORLD
    bucket_loc = None
    if parallel and bodo.get_rank() == 0 or not parallel:
        try:
            ghqj__lmqxw, psog__qid = pa_fs.S3FileSystem.from_uri(s3_filepath)
            bucket_loc = ghqj__lmqxw.region
        except Exception as ysvso__wolpx:
            if os.environ.get('AWS_DEFAULT_REGION', '') == '':
                warnings.warn(BodoWarning(
                    f"""Unable to get S3 Bucket Region.
{ysvso__wolpx}.
Value not defined in the AWS_DEFAULT_REGION environment variable either. Region defaults to us-east-1 currently."""
                    ))
            bucket_loc = ''
    if parallel:
        bucket_loc = oebe__bscb.bcast(bucket_loc)
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
        wsq__mhl = get_s3_bucket_region_njit(path_or_buf, parallel=is_parallel)
        zwlu__fhf, hyq__czwt = unicode_to_utf8_and_len(D)
        rpe__ddza = 0
        if is_parallel:
            rpe__ddza = bodo.libs.distributed_api.dist_exscan(hyq__czwt, np
                .int32(Reduce_Type.Sum.value))
        _csv_write(unicode_to_utf8(path_or_buf), zwlu__fhf, rpe__ddza,
            hyq__czwt, is_parallel, unicode_to_utf8(wsq__mhl))
        bodo.utils.utils.check_and_propagate_cpp_exception()
    return impl
