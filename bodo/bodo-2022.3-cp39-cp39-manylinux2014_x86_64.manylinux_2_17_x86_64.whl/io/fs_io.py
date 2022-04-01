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
            zpfmw__dmw = self.fs.open_input_file(path)
        except:
            zpfmw__dmw = self.fs.open_input_stream(path)
    elif mode == 'wb':
        zpfmw__dmw = self.fs.open_output_stream(path)
    else:
        raise ValueError(f'unsupported mode for Arrow filesystem: {mode!r}')
    return ArrowFile(self, zpfmw__dmw, path, mode, block_size, **kwargs)


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
    jim__xgd = os.environ.get('AWS_S3_ENDPOINT', None)
    if not region:
        region = os.environ.get('AWS_DEFAULT_REGION', None)
    ylr__jtaib = False
    woqtk__tuj = get_proxy_uri_from_env_vars()
    if storage_options:
        ylr__jtaib = storage_options.get('anon', False)
    return S3FileSystem(anonymous=ylr__jtaib, region=region,
        endpoint_override=jim__xgd, proxy_options=woqtk__tuj)


def get_s3_subtree_fs(bucket_name, region=None, storage_options=None):
    from pyarrow._fs import SubTreeFileSystem
    from pyarrow._s3fs import S3FileSystem
    jim__xgd = os.environ.get('AWS_S3_ENDPOINT', None)
    if not region:
        region = os.environ.get('AWS_DEFAULT_REGION', None)
    ylr__jtaib = False
    woqtk__tuj = get_proxy_uri_from_env_vars()
    if storage_options:
        ylr__jtaib = storage_options.get('anon', False)
    fs = S3FileSystem(region=region, endpoint_override=jim__xgd, anonymous=
        ylr__jtaib, proxy_options=woqtk__tuj)
    return SubTreeFileSystem(bucket_name, fs)


def get_s3_fs_from_path(path, parallel=False, storage_options=None):
    region = get_s3_bucket_region_njit(path, parallel=parallel)
    if region == '':
        region = None
    return get_s3_fs(region, storage_options)


def get_hdfs_fs(path):
    from pyarrow.fs import HadoopFileSystem as HdFS
    fnnv__dxf = urlparse(path)
    if fnnv__dxf.scheme in ('abfs', 'abfss'):
        gpt__bqn = path
        if fnnv__dxf.port is None:
            ave__yqohp = 0
        else:
            ave__yqohp = fnnv__dxf.port
        xuwc__wprd = None
    else:
        gpt__bqn = fnnv__dxf.hostname
        ave__yqohp = fnnv__dxf.port
        xuwc__wprd = fnnv__dxf.username
    try:
        fs = HdFS(host=gpt__bqn, port=ave__yqohp, user=xuwc__wprd)
    except Exception as bczn__dxb:
        raise BodoError('Hadoop file system cannot be created: {}'.format(
            bczn__dxb))
    return fs


def gcs_is_directory(path):
    import gcsfs
    fs = gcsfs.GCSFileSystem(token=None)
    try:
        bcul__xytsb = fs.isdir(path)
    except gcsfs.utils.HttpError as bczn__dxb:
        raise BodoError(
            f'{bczn__dxb}. Make sure your google cloud credentials are set!')
    return bcul__xytsb


def gcs_list_dir_fnames(path):
    import gcsfs
    fs = gcsfs.GCSFileSystem(token=None)
    return [jmv__kjfc.split('/')[-1] for jmv__kjfc in fs.ls(path)]


def s3_is_directory(fs, path):
    from pyarrow import fs as pa_fs
    try:
        fnnv__dxf = urlparse(path)
        ysqqj__cuo = (fnnv__dxf.netloc + fnnv__dxf.path).rstrip('/')
        ihp__aozf = fs.get_file_info(ysqqj__cuo)
        if ihp__aozf.type in (pa_fs.FileType.NotFound, pa_fs.FileType.Unknown):
            raise FileNotFoundError('{} is a non-existing or unreachable file'
                .format(path))
        if not ihp__aozf.size and ihp__aozf.type == pa_fs.FileType.Directory:
            return True
        return False
    except (FileNotFoundError, OSError) as bczn__dxb:
        raise
    except BodoError as vvh__kvjuu:
        raise
    except Exception as bczn__dxb:
        raise BodoError(
            f"""error from pyarrow S3FileSystem: {type(bczn__dxb).__name__}: {str(bczn__dxb)}
{bodo_error_msg}"""
            )


def s3_list_dir_fnames(fs, path):
    from pyarrow import fs as pa_fs
    jsul__ypalx = None
    try:
        if s3_is_directory(fs, path):
            fnnv__dxf = urlparse(path)
            ysqqj__cuo = (fnnv__dxf.netloc + fnnv__dxf.path).rstrip('/')
            yebd__lmyz = pa_fs.FileSelector(ysqqj__cuo, recursive=False)
            ykv__kgav = fs.get_file_info(yebd__lmyz)
            if ykv__kgav and ykv__kgav[0].path in [ysqqj__cuo, f'{ysqqj__cuo}/'
                ] and int(ykv__kgav[0].size or 0) == 0:
                ykv__kgav = ykv__kgav[1:]
            jsul__ypalx = [cgci__pax.base_name for cgci__pax in ykv__kgav]
    except BodoError as vvh__kvjuu:
        raise
    except Exception as bczn__dxb:
        raise BodoError(
            f"""error from pyarrow S3FileSystem: {type(bczn__dxb).__name__}: {str(bczn__dxb)}
{bodo_error_msg}"""
            )
    return jsul__ypalx


def hdfs_is_directory(path):
    from pyarrow.fs import FileType, HadoopFileSystem
    check_java_installation(path)
    fnnv__dxf = urlparse(path)
    evlj__kkbzn = fnnv__dxf.path
    try:
        osoak__gaddk = HadoopFileSystem.from_uri(path)
    except Exception as bczn__dxb:
        raise BodoError(' Hadoop file system cannot be created: {}'.format(
            bczn__dxb))
    rjubj__gqq = osoak__gaddk.get_file_info([evlj__kkbzn])
    if rjubj__gqq[0].type in (FileType.NotFound, FileType.Unknown):
        raise BodoError('{} is a non-existing or unreachable file'.format(path)
            )
    if not rjubj__gqq[0].size and rjubj__gqq[0].type == FileType.Directory:
        return osoak__gaddk, True
    return osoak__gaddk, False


def hdfs_list_dir_fnames(path):
    from pyarrow.fs import FileSelector
    jsul__ypalx = None
    osoak__gaddk, bcul__xytsb = hdfs_is_directory(path)
    if bcul__xytsb:
        fnnv__dxf = urlparse(path)
        evlj__kkbzn = fnnv__dxf.path
        yebd__lmyz = FileSelector(evlj__kkbzn, recursive=True)
        try:
            ykv__kgav = osoak__gaddk.get_file_info(yebd__lmyz)
        except Exception as bczn__dxb:
            raise BodoError('Exception on getting directory info of {}: {}'
                .format(evlj__kkbzn, bczn__dxb))
        jsul__ypalx = [cgci__pax.base_name for cgci__pax in ykv__kgav]
    return osoak__gaddk, jsul__ypalx


def abfs_is_directory(path):
    osoak__gaddk = get_hdfs_fs(path)
    try:
        rjubj__gqq = osoak__gaddk.info(path)
    except OSError as vvh__kvjuu:
        raise BodoError('{} is a non-existing or unreachable file'.format(path)
            )
    if rjubj__gqq['size'] == 0 and rjubj__gqq['kind'].lower() == 'directory':
        return osoak__gaddk, True
    return osoak__gaddk, False


def abfs_list_dir_fnames(path):
    jsul__ypalx = None
    osoak__gaddk, bcul__xytsb = abfs_is_directory(path)
    if bcul__xytsb:
        fnnv__dxf = urlparse(path)
        evlj__kkbzn = fnnv__dxf.path
        try:
            lfhm__rpg = osoak__gaddk.ls(evlj__kkbzn)
        except Exception as bczn__dxb:
            raise BodoError('Exception on getting directory info of {}: {}'
                .format(evlj__kkbzn, bczn__dxb))
        jsul__ypalx = [fname[fname.rindex('/') + 1:] for fname in lfhm__rpg]
    return osoak__gaddk, jsul__ypalx


def directory_of_files_common_filter(fname):
    return not (fname.endswith('.crc') or fname.endswith('_$folder$') or
        fname.startswith('.') or fname.startswith('_') and fname !=
        '_delta_log')


def find_file_name_or_handler(path, ftype):
    from urllib.parse import urlparse
    busg__nul = urlparse(path)
    fname = path
    fs = None
    ebdse__caswy = 'read_json' if ftype == 'json' else 'read_csv'
    vxl__yefm = (
        f'pd.{ebdse__caswy}(): there is no {ftype} file in directory: {fname}')
    zecf__elx = directory_of_files_common_filter
    if busg__nul.scheme == 's3':
        lro__iiafh = True
        fs = get_s3_fs_from_path(path)
        dsja__vif = s3_list_dir_fnames(fs, path)
        ysqqj__cuo = (busg__nul.netloc + busg__nul.path).rstrip('/')
        fname = ysqqj__cuo
        if dsja__vif:
            dsja__vif = [(ysqqj__cuo + '/' + jmv__kjfc) for jmv__kjfc in
                sorted(filter(zecf__elx, dsja__vif))]
            yom__ite = [jmv__kjfc for jmv__kjfc in dsja__vif if int(fs.
                get_file_info(jmv__kjfc).size or 0) > 0]
            if len(yom__ite) == 0:
                raise BodoError(vxl__yefm)
            fname = yom__ite[0]
        qcxrc__kpjq = int(fs.get_file_info(fname).size or 0)
        lezvq__rjcsq = fs.open_input_file(fname)
    elif busg__nul.scheme == 'hdfs':
        lro__iiafh = True
        fs, dsja__vif = hdfs_list_dir_fnames(path)
        qcxrc__kpjq = fs.get_file_info([busg__nul.path])[0].size
        if dsja__vif:
            path = path.rstrip('/')
            dsja__vif = [(path + '/' + jmv__kjfc) for jmv__kjfc in sorted(
                filter(zecf__elx, dsja__vif))]
            yom__ite = [jmv__kjfc for jmv__kjfc in dsja__vif if fs.
                get_file_info([urlparse(jmv__kjfc).path])[0].size > 0]
            if len(yom__ite) == 0:
                raise BodoError(vxl__yefm)
            fname = yom__ite[0]
            fname = urlparse(fname).path
            qcxrc__kpjq = fs.get_file_info([fname])[0].size
        lezvq__rjcsq = fs.open_input_file(fname)
    elif busg__nul.scheme in ('abfs', 'abfss'):
        lro__iiafh = True
        fs, dsja__vif = abfs_list_dir_fnames(path)
        qcxrc__kpjq = fs.info(fname)['size']
        if dsja__vif:
            path = path.rstrip('/')
            dsja__vif = [(path + '/' + jmv__kjfc) for jmv__kjfc in sorted(
                filter(zecf__elx, dsja__vif))]
            yom__ite = [jmv__kjfc for jmv__kjfc in dsja__vif if fs.info(
                jmv__kjfc)['size'] > 0]
            if len(yom__ite) == 0:
                raise BodoError(vxl__yefm)
            fname = yom__ite[0]
            qcxrc__kpjq = fs.info(fname)['size']
            fname = urlparse(fname).path
        lezvq__rjcsq = fs.open(fname, 'rb')
    else:
        if busg__nul.scheme != '':
            raise BodoError(
                f'Unrecognized scheme {busg__nul.scheme}. Please refer to https://docs.bodo.ai/latest/source/file_io.html'
                )
        lro__iiafh = False
        if os.path.isdir(path):
            lfhm__rpg = filter(zecf__elx, glob.glob(os.path.join(os.path.
                abspath(path), '*')))
            yom__ite = [jmv__kjfc for jmv__kjfc in sorted(lfhm__rpg) if os.
                path.getsize(jmv__kjfc) > 0]
            if len(yom__ite) == 0:
                raise BodoError(vxl__yefm)
            fname = yom__ite[0]
        qcxrc__kpjq = os.path.getsize(fname)
        lezvq__rjcsq = fname
    return lro__iiafh, lezvq__rjcsq, qcxrc__kpjq, fs


def get_s3_bucket_region(s3_filepath, parallel):
    try:
        from pyarrow import fs as pa_fs
    except:
        raise BodoError('Reading from s3 requires pyarrow currently.')
    from mpi4py import MPI
    mil__ohzp = MPI.COMM_WORLD
    bucket_loc = None
    if parallel and bodo.get_rank() == 0 or not parallel:
        try:
            wtatv__lux, gom__jmrnn = pa_fs.S3FileSystem.from_uri(s3_filepath)
            bucket_loc = wtatv__lux.region
        except Exception as bczn__dxb:
            if os.environ.get('AWS_DEFAULT_REGION', '') == '':
                warnings.warn(BodoWarning(
                    f"""Unable to get S3 Bucket Region.
{bczn__dxb}.
Value not defined in the AWS_DEFAULT_REGION environment variable either. Region defaults to us-east-1 currently."""
                    ))
            bucket_loc = ''
    if parallel:
        bucket_loc = mil__ohzp.bcast(bucket_loc)
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
        sonq__fevm = get_s3_bucket_region_njit(path_or_buf, parallel=
            is_parallel)
        fbyv__ivbj, sww__yuysu = unicode_to_utf8_and_len(D)
        qzffy__yiurv = 0
        if is_parallel:
            qzffy__yiurv = bodo.libs.distributed_api.dist_exscan(sww__yuysu,
                np.int32(Reduce_Type.Sum.value))
        _csv_write(unicode_to_utf8(path_or_buf), fbyv__ivbj, qzffy__yiurv,
            sww__yuysu, is_parallel, unicode_to_utf8(sonq__fevm))
        bodo.utils.utils.check_and_propagate_cpp_exception()
    return impl
