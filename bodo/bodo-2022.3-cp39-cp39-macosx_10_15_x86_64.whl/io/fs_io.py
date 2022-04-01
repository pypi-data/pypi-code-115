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
            eoog__hsmn = self.fs.open_input_file(path)
        except:
            eoog__hsmn = self.fs.open_input_stream(path)
    elif mode == 'wb':
        eoog__hsmn = self.fs.open_output_stream(path)
    else:
        raise ValueError(f'unsupported mode for Arrow filesystem: {mode!r}')
    return ArrowFile(self, eoog__hsmn, path, mode, block_size, **kwargs)


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
    xkm__cwcp = os.environ.get('AWS_S3_ENDPOINT', None)
    if not region:
        region = os.environ.get('AWS_DEFAULT_REGION', None)
    kua__zklr = False
    oqi__goxy = get_proxy_uri_from_env_vars()
    if storage_options:
        kua__zklr = storage_options.get('anon', False)
    return S3FileSystem(anonymous=kua__zklr, region=region,
        endpoint_override=xkm__cwcp, proxy_options=oqi__goxy)


def get_s3_subtree_fs(bucket_name, region=None, storage_options=None):
    from pyarrow._fs import SubTreeFileSystem
    from pyarrow._s3fs import S3FileSystem
    xkm__cwcp = os.environ.get('AWS_S3_ENDPOINT', None)
    if not region:
        region = os.environ.get('AWS_DEFAULT_REGION', None)
    kua__zklr = False
    oqi__goxy = get_proxy_uri_from_env_vars()
    if storage_options:
        kua__zklr = storage_options.get('anon', False)
    fs = S3FileSystem(region=region, endpoint_override=xkm__cwcp, anonymous
        =kua__zklr, proxy_options=oqi__goxy)
    return SubTreeFileSystem(bucket_name, fs)


def get_s3_fs_from_path(path, parallel=False, storage_options=None):
    region = get_s3_bucket_region_njit(path, parallel=parallel)
    if region == '':
        region = None
    return get_s3_fs(region, storage_options)


def get_hdfs_fs(path):
    from pyarrow.fs import HadoopFileSystem as HdFS
    lhcmf__dlquk = urlparse(path)
    if lhcmf__dlquk.scheme in ('abfs', 'abfss'):
        ejpv__bkl = path
        if lhcmf__dlquk.port is None:
            blpq__ckb = 0
        else:
            blpq__ckb = lhcmf__dlquk.port
        pwlgm__phou = None
    else:
        ejpv__bkl = lhcmf__dlquk.hostname
        blpq__ckb = lhcmf__dlquk.port
        pwlgm__phou = lhcmf__dlquk.username
    try:
        fs = HdFS(host=ejpv__bkl, port=blpq__ckb, user=pwlgm__phou)
    except Exception as uwt__ile:
        raise BodoError('Hadoop file system cannot be created: {}'.format(
            uwt__ile))
    return fs


def gcs_is_directory(path):
    import gcsfs
    fs = gcsfs.GCSFileSystem(token=None)
    try:
        gdc__vco = fs.isdir(path)
    except gcsfs.utils.HttpError as uwt__ile:
        raise BodoError(
            f'{uwt__ile}. Make sure your google cloud credentials are set!')
    return gdc__vco


def gcs_list_dir_fnames(path):
    import gcsfs
    fs = gcsfs.GCSFileSystem(token=None)
    return [ffh__noj.split('/')[-1] for ffh__noj in fs.ls(path)]


def s3_is_directory(fs, path):
    from pyarrow import fs as pa_fs
    try:
        lhcmf__dlquk = urlparse(path)
        avsv__pomkt = (lhcmf__dlquk.netloc + lhcmf__dlquk.path).rstrip('/')
        piwtr__doz = fs.get_file_info(avsv__pomkt)
        if piwtr__doz.type in (pa_fs.FileType.NotFound, pa_fs.FileType.Unknown
            ):
            raise FileNotFoundError('{} is a non-existing or unreachable file'
                .format(path))
        if not piwtr__doz.size and piwtr__doz.type == pa_fs.FileType.Directory:
            return True
        return False
    except (FileNotFoundError, OSError) as uwt__ile:
        raise
    except BodoError as byh__cnxm:
        raise
    except Exception as uwt__ile:
        raise BodoError(
            f"""error from pyarrow S3FileSystem: {type(uwt__ile).__name__}: {str(uwt__ile)}
{bodo_error_msg}"""
            )


def s3_list_dir_fnames(fs, path):
    from pyarrow import fs as pa_fs
    okmx__fhz = None
    try:
        if s3_is_directory(fs, path):
            lhcmf__dlquk = urlparse(path)
            avsv__pomkt = (lhcmf__dlquk.netloc + lhcmf__dlquk.path).rstrip('/')
            wxlku__lzll = pa_fs.FileSelector(avsv__pomkt, recursive=False)
            bauw__zrsb = fs.get_file_info(wxlku__lzll)
            if bauw__zrsb and bauw__zrsb[0].path in [avsv__pomkt,
                f'{avsv__pomkt}/'] and int(bauw__zrsb[0].size or 0) == 0:
                bauw__zrsb = bauw__zrsb[1:]
            okmx__fhz = [wcfsy__teual.base_name for wcfsy__teual in bauw__zrsb]
    except BodoError as byh__cnxm:
        raise
    except Exception as uwt__ile:
        raise BodoError(
            f"""error from pyarrow S3FileSystem: {type(uwt__ile).__name__}: {str(uwt__ile)}
{bodo_error_msg}"""
            )
    return okmx__fhz


def hdfs_is_directory(path):
    from pyarrow.fs import FileType, HadoopFileSystem
    check_java_installation(path)
    lhcmf__dlquk = urlparse(path)
    aypl__yjobt = lhcmf__dlquk.path
    try:
        bxg__woam = HadoopFileSystem.from_uri(path)
    except Exception as uwt__ile:
        raise BodoError(' Hadoop file system cannot be created: {}'.format(
            uwt__ile))
    givzf__vzjdk = bxg__woam.get_file_info([aypl__yjobt])
    if givzf__vzjdk[0].type in (FileType.NotFound, FileType.Unknown):
        raise BodoError('{} is a non-existing or unreachable file'.format(path)
            )
    if not givzf__vzjdk[0].size and givzf__vzjdk[0].type == FileType.Directory:
        return bxg__woam, True
    return bxg__woam, False


def hdfs_list_dir_fnames(path):
    from pyarrow.fs import FileSelector
    okmx__fhz = None
    bxg__woam, gdc__vco = hdfs_is_directory(path)
    if gdc__vco:
        lhcmf__dlquk = urlparse(path)
        aypl__yjobt = lhcmf__dlquk.path
        wxlku__lzll = FileSelector(aypl__yjobt, recursive=True)
        try:
            bauw__zrsb = bxg__woam.get_file_info(wxlku__lzll)
        except Exception as uwt__ile:
            raise BodoError('Exception on getting directory info of {}: {}'
                .format(aypl__yjobt, uwt__ile))
        okmx__fhz = [wcfsy__teual.base_name for wcfsy__teual in bauw__zrsb]
    return bxg__woam, okmx__fhz


def abfs_is_directory(path):
    bxg__woam = get_hdfs_fs(path)
    try:
        givzf__vzjdk = bxg__woam.info(path)
    except OSError as byh__cnxm:
        raise BodoError('{} is a non-existing or unreachable file'.format(path)
            )
    if givzf__vzjdk['size'] == 0 and givzf__vzjdk['kind'].lower(
        ) == 'directory':
        return bxg__woam, True
    return bxg__woam, False


def abfs_list_dir_fnames(path):
    okmx__fhz = None
    bxg__woam, gdc__vco = abfs_is_directory(path)
    if gdc__vco:
        lhcmf__dlquk = urlparse(path)
        aypl__yjobt = lhcmf__dlquk.path
        try:
            riywp__ikx = bxg__woam.ls(aypl__yjobt)
        except Exception as uwt__ile:
            raise BodoError('Exception on getting directory info of {}: {}'
                .format(aypl__yjobt, uwt__ile))
        okmx__fhz = [fname[fname.rindex('/') + 1:] for fname in riywp__ikx]
    return bxg__woam, okmx__fhz


def directory_of_files_common_filter(fname):
    return not (fname.endswith('.crc') or fname.endswith('_$folder$') or
        fname.startswith('.') or fname.startswith('_') and fname !=
        '_delta_log')


def find_file_name_or_handler(path, ftype):
    from urllib.parse import urlparse
    minli__ahoz = urlparse(path)
    fname = path
    fs = None
    ces__rygg = 'read_json' if ftype == 'json' else 'read_csv'
    akyv__rqz = (
        f'pd.{ces__rygg}(): there is no {ftype} file in directory: {fname}')
    djbur__npyq = directory_of_files_common_filter
    if minli__ahoz.scheme == 's3':
        orf__lxoju = True
        fs = get_s3_fs_from_path(path)
        kxpvt__thuq = s3_list_dir_fnames(fs, path)
        avsv__pomkt = (minli__ahoz.netloc + minli__ahoz.path).rstrip('/')
        fname = avsv__pomkt
        if kxpvt__thuq:
            kxpvt__thuq = [(avsv__pomkt + '/' + ffh__noj) for ffh__noj in
                sorted(filter(djbur__npyq, kxpvt__thuq))]
            oyg__tgtq = [ffh__noj for ffh__noj in kxpvt__thuq if int(fs.
                get_file_info(ffh__noj).size or 0) > 0]
            if len(oyg__tgtq) == 0:
                raise BodoError(akyv__rqz)
            fname = oyg__tgtq[0]
        ajk__czx = int(fs.get_file_info(fname).size or 0)
        nzv__acnyt = fs.open_input_file(fname)
    elif minli__ahoz.scheme == 'hdfs':
        orf__lxoju = True
        fs, kxpvt__thuq = hdfs_list_dir_fnames(path)
        ajk__czx = fs.get_file_info([minli__ahoz.path])[0].size
        if kxpvt__thuq:
            path = path.rstrip('/')
            kxpvt__thuq = [(path + '/' + ffh__noj) for ffh__noj in sorted(
                filter(djbur__npyq, kxpvt__thuq))]
            oyg__tgtq = [ffh__noj for ffh__noj in kxpvt__thuq if fs.
                get_file_info([urlparse(ffh__noj).path])[0].size > 0]
            if len(oyg__tgtq) == 0:
                raise BodoError(akyv__rqz)
            fname = oyg__tgtq[0]
            fname = urlparse(fname).path
            ajk__czx = fs.get_file_info([fname])[0].size
        nzv__acnyt = fs.open_input_file(fname)
    elif minli__ahoz.scheme in ('abfs', 'abfss'):
        orf__lxoju = True
        fs, kxpvt__thuq = abfs_list_dir_fnames(path)
        ajk__czx = fs.info(fname)['size']
        if kxpvt__thuq:
            path = path.rstrip('/')
            kxpvt__thuq = [(path + '/' + ffh__noj) for ffh__noj in sorted(
                filter(djbur__npyq, kxpvt__thuq))]
            oyg__tgtq = [ffh__noj for ffh__noj in kxpvt__thuq if fs.info(
                ffh__noj)['size'] > 0]
            if len(oyg__tgtq) == 0:
                raise BodoError(akyv__rqz)
            fname = oyg__tgtq[0]
            ajk__czx = fs.info(fname)['size']
            fname = urlparse(fname).path
        nzv__acnyt = fs.open(fname, 'rb')
    else:
        if minli__ahoz.scheme != '':
            raise BodoError(
                f'Unrecognized scheme {minli__ahoz.scheme}. Please refer to https://docs.bodo.ai/latest/source/file_io.html'
                )
        orf__lxoju = False
        if os.path.isdir(path):
            riywp__ikx = filter(djbur__npyq, glob.glob(os.path.join(os.path
                .abspath(path), '*')))
            oyg__tgtq = [ffh__noj for ffh__noj in sorted(riywp__ikx) if os.
                path.getsize(ffh__noj) > 0]
            if len(oyg__tgtq) == 0:
                raise BodoError(akyv__rqz)
            fname = oyg__tgtq[0]
        ajk__czx = os.path.getsize(fname)
        nzv__acnyt = fname
    return orf__lxoju, nzv__acnyt, ajk__czx, fs


def get_s3_bucket_region(s3_filepath, parallel):
    try:
        from pyarrow import fs as pa_fs
    except:
        raise BodoError('Reading from s3 requires pyarrow currently.')
    from mpi4py import MPI
    wle__wvi = MPI.COMM_WORLD
    bucket_loc = None
    if parallel and bodo.get_rank() == 0 or not parallel:
        try:
            mppl__aolzs, qvrjf__tzawk = pa_fs.S3FileSystem.from_uri(s3_filepath
                )
            bucket_loc = mppl__aolzs.region
        except Exception as uwt__ile:
            if os.environ.get('AWS_DEFAULT_REGION', '') == '':
                warnings.warn(BodoWarning(
                    f"""Unable to get S3 Bucket Region.
{uwt__ile}.
Value not defined in the AWS_DEFAULT_REGION environment variable either. Region defaults to us-east-1 currently."""
                    ))
            bucket_loc = ''
    if parallel:
        bucket_loc = wle__wvi.bcast(bucket_loc)
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
        emlsm__uekzr = get_s3_bucket_region_njit(path_or_buf, parallel=
            is_parallel)
        aow__dtnuw, jwrtz__dxpoe = unicode_to_utf8_and_len(D)
        vmvd__zfeeg = 0
        if is_parallel:
            vmvd__zfeeg = bodo.libs.distributed_api.dist_exscan(jwrtz__dxpoe,
                np.int32(Reduce_Type.Sum.value))
        _csv_write(unicode_to_utf8(path_or_buf), aow__dtnuw, vmvd__zfeeg,
            jwrtz__dxpoe, is_parallel, unicode_to_utf8(emlsm__uekzr))
        bodo.utils.utils.check_and_propagate_cpp_exception()
    return impl
