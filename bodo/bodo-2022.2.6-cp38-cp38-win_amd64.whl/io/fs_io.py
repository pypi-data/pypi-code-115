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
            upppi__fkfwe = self.fs.open_input_file(path)
        except:
            upppi__fkfwe = self.fs.open_input_stream(path)
    elif mode == 'wb':
        upppi__fkfwe = self.fs.open_output_stream(path)
    else:
        raise ValueError(f'unsupported mode for Arrow filesystem: {mode!r}')
    return ArrowFile(self, upppi__fkfwe, path, mode, block_size, **kwargs)


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
    vho__paukn = os.environ.get('AWS_S3_ENDPOINT', None)
    if not region:
        region = os.environ.get('AWS_DEFAULT_REGION', None)
    usv__lfoi = False
    wgrpi__wahj = get_proxy_uri_from_env_vars()
    if storage_options:
        usv__lfoi = storage_options.get('anon', False)
    return S3FileSystem(anonymous=usv__lfoi, region=region,
        endpoint_override=vho__paukn, proxy_options=wgrpi__wahj)


def get_s3_subtree_fs(bucket_name, region=None, storage_options=None):
    from pyarrow._fs import SubTreeFileSystem
    from pyarrow._s3fs import S3FileSystem
    vho__paukn = os.environ.get('AWS_S3_ENDPOINT', None)
    if not region:
        region = os.environ.get('AWS_DEFAULT_REGION', None)
    usv__lfoi = False
    wgrpi__wahj = get_proxy_uri_from_env_vars()
    if storage_options:
        usv__lfoi = storage_options.get('anon', False)
    fs = S3FileSystem(region=region, endpoint_override=vho__paukn,
        anonymous=usv__lfoi, proxy_options=wgrpi__wahj)
    return SubTreeFileSystem(bucket_name, fs)


def get_s3_fs_from_path(path, parallel=False, storage_options=None):
    region = get_s3_bucket_region_njit(path, parallel=parallel)
    if region == '':
        region = None
    return get_s3_fs(region, storage_options)


def get_hdfs_fs(path):
    from pyarrow.fs import HadoopFileSystem as HdFS
    cpf__gvd = urlparse(path)
    if cpf__gvd.scheme in ('abfs', 'abfss'):
        yeqp__xfbi = path
        if cpf__gvd.port is None:
            lih__bfrz = 0
        else:
            lih__bfrz = cpf__gvd.port
        gubs__uqqua = None
    else:
        yeqp__xfbi = cpf__gvd.hostname
        lih__bfrz = cpf__gvd.port
        gubs__uqqua = cpf__gvd.username
    try:
        fs = HdFS(host=yeqp__xfbi, port=lih__bfrz, user=gubs__uqqua)
    except Exception as bmwwz__fbp:
        raise BodoError('Hadoop file system cannot be created: {}'.format(
            bmwwz__fbp))
    return fs


def gcs_is_directory(path):
    import gcsfs
    fs = gcsfs.GCSFileSystem(token=None)
    try:
        suobb__axj = fs.isdir(path)
    except gcsfs.utils.HttpError as bmwwz__fbp:
        raise BodoError(
            f'{bmwwz__fbp}. Make sure your google cloud credentials are set!')
    return suobb__axj


def gcs_list_dir_fnames(path):
    import gcsfs
    fs = gcsfs.GCSFileSystem(token=None)
    return [hqmg__vllxc.split('/')[-1] for hqmg__vllxc in fs.ls(path)]


def s3_is_directory(fs, path):
    from pyarrow import fs as pa_fs
    try:
        cpf__gvd = urlparse(path)
        uxoby__ene = (cpf__gvd.netloc + cpf__gvd.path).rstrip('/')
        pui__byw = fs.get_file_info(uxoby__ene)
        if pui__byw.type in (pa_fs.FileType.NotFound, pa_fs.FileType.Unknown):
            raise FileNotFoundError('{} is a non-existing or unreachable file'
                .format(path))
        if not pui__byw.size and pui__byw.type == pa_fs.FileType.Directory:
            return True
        return False
    except (FileNotFoundError, OSError) as bmwwz__fbp:
        raise
    except BodoError as mhhnu__uin:
        raise
    except Exception as bmwwz__fbp:
        raise BodoError(
            f"""error from pyarrow S3FileSystem: {type(bmwwz__fbp).__name__}: {str(bmwwz__fbp)}
{bodo_error_msg}"""
            )


def s3_list_dir_fnames(fs, path):
    from pyarrow import fs as pa_fs
    clmya__dihc = None
    try:
        if s3_is_directory(fs, path):
            cpf__gvd = urlparse(path)
            uxoby__ene = (cpf__gvd.netloc + cpf__gvd.path).rstrip('/')
            brg__evcvs = pa_fs.FileSelector(uxoby__ene, recursive=False)
            bfj__ayrqw = fs.get_file_info(brg__evcvs)
            if bfj__ayrqw and bfj__ayrqw[0].path in [uxoby__ene,
                f'{uxoby__ene}/'] and int(bfj__ayrqw[0].size or 0) == 0:
                bfj__ayrqw = bfj__ayrqw[1:]
            clmya__dihc = [cgi__fgt.base_name for cgi__fgt in bfj__ayrqw]
    except BodoError as mhhnu__uin:
        raise
    except Exception as bmwwz__fbp:
        raise BodoError(
            f"""error from pyarrow S3FileSystem: {type(bmwwz__fbp).__name__}: {str(bmwwz__fbp)}
{bodo_error_msg}"""
            )
    return clmya__dihc


def hdfs_is_directory(path):
    from pyarrow.fs import FileType, HadoopFileSystem
    check_java_installation(path)
    cpf__gvd = urlparse(path)
    yxzcc__kgsv = cpf__gvd.path
    try:
        gjd__ddd = HadoopFileSystem.from_uri(path)
    except Exception as bmwwz__fbp:
        raise BodoError(' Hadoop file system cannot be created: {}'.format(
            bmwwz__fbp))
    zqnje__bpuh = gjd__ddd.get_file_info([yxzcc__kgsv])
    if zqnje__bpuh[0].type in (FileType.NotFound, FileType.Unknown):
        raise BodoError('{} is a non-existing or unreachable file'.format(path)
            )
    if not zqnje__bpuh[0].size and zqnje__bpuh[0].type == FileType.Directory:
        return gjd__ddd, True
    return gjd__ddd, False


def hdfs_list_dir_fnames(path):
    from pyarrow.fs import FileSelector
    clmya__dihc = None
    gjd__ddd, suobb__axj = hdfs_is_directory(path)
    if suobb__axj:
        cpf__gvd = urlparse(path)
        yxzcc__kgsv = cpf__gvd.path
        brg__evcvs = FileSelector(yxzcc__kgsv, recursive=True)
        try:
            bfj__ayrqw = gjd__ddd.get_file_info(brg__evcvs)
        except Exception as bmwwz__fbp:
            raise BodoError('Exception on getting directory info of {}: {}'
                .format(yxzcc__kgsv, bmwwz__fbp))
        clmya__dihc = [cgi__fgt.base_name for cgi__fgt in bfj__ayrqw]
    return gjd__ddd, clmya__dihc


def abfs_is_directory(path):
    gjd__ddd = get_hdfs_fs(path)
    try:
        zqnje__bpuh = gjd__ddd.info(path)
    except OSError as mhhnu__uin:
        raise BodoError('{} is a non-existing or unreachable file'.format(path)
            )
    if zqnje__bpuh['size'] == 0 and zqnje__bpuh['kind'].lower() == 'directory':
        return gjd__ddd, True
    return gjd__ddd, False


def abfs_list_dir_fnames(path):
    clmya__dihc = None
    gjd__ddd, suobb__axj = abfs_is_directory(path)
    if suobb__axj:
        cpf__gvd = urlparse(path)
        yxzcc__kgsv = cpf__gvd.path
        try:
            hrob__oqi = gjd__ddd.ls(yxzcc__kgsv)
        except Exception as bmwwz__fbp:
            raise BodoError('Exception on getting directory info of {}: {}'
                .format(yxzcc__kgsv, bmwwz__fbp))
        clmya__dihc = [fname[fname.rindex('/') + 1:] for fname in hrob__oqi]
    return gjd__ddd, clmya__dihc


def directory_of_files_common_filter(fname):
    return not (fname.endswith('.crc') or fname.endswith('_$folder$') or
        fname.startswith('.') or fname.startswith('_') and fname !=
        '_delta_log')


def find_file_name_or_handler(path, ftype):
    from urllib.parse import urlparse
    snihb__tyyun = urlparse(path)
    fname = path
    fs = None
    jhkv__sbspd = 'read_json' if ftype == 'json' else 'read_csv'
    vpjy__ncfpf = (
        f'pd.{jhkv__sbspd}(): there is no {ftype} file in directory: {fname}')
    lje__mpwez = directory_of_files_common_filter
    if snihb__tyyun.scheme == 's3':
        lcq__httqc = True
        fs = get_s3_fs_from_path(path)
        nvhss__uamp = s3_list_dir_fnames(fs, path)
        uxoby__ene = (snihb__tyyun.netloc + snihb__tyyun.path).rstrip('/')
        fname = uxoby__ene
        if nvhss__uamp:
            nvhss__uamp = [(uxoby__ene + '/' + hqmg__vllxc) for hqmg__vllxc in
                sorted(filter(lje__mpwez, nvhss__uamp))]
            ibu__tmaxn = [hqmg__vllxc for hqmg__vllxc in nvhss__uamp if int
                (fs.get_file_info(hqmg__vllxc).size or 0) > 0]
            if len(ibu__tmaxn) == 0:
                raise BodoError(vpjy__ncfpf)
            fname = ibu__tmaxn[0]
        bfu__dexvj = int(fs.get_file_info(fname).size or 0)
        jijga__gulk = fs.open_input_file(fname)
    elif snihb__tyyun.scheme == 'hdfs':
        lcq__httqc = True
        fs, nvhss__uamp = hdfs_list_dir_fnames(path)
        bfu__dexvj = fs.get_file_info([snihb__tyyun.path])[0].size
        if nvhss__uamp:
            path = path.rstrip('/')
            nvhss__uamp = [(path + '/' + hqmg__vllxc) for hqmg__vllxc in
                sorted(filter(lje__mpwez, nvhss__uamp))]
            ibu__tmaxn = [hqmg__vllxc for hqmg__vllxc in nvhss__uamp if fs.
                get_file_info([urlparse(hqmg__vllxc).path])[0].size > 0]
            if len(ibu__tmaxn) == 0:
                raise BodoError(vpjy__ncfpf)
            fname = ibu__tmaxn[0]
            fname = urlparse(fname).path
            bfu__dexvj = fs.get_file_info([fname])[0].size
        jijga__gulk = fs.open_input_file(fname)
    elif snihb__tyyun.scheme in ('abfs', 'abfss'):
        lcq__httqc = True
        fs, nvhss__uamp = abfs_list_dir_fnames(path)
        bfu__dexvj = fs.info(fname)['size']
        if nvhss__uamp:
            path = path.rstrip('/')
            nvhss__uamp = [(path + '/' + hqmg__vllxc) for hqmg__vllxc in
                sorted(filter(lje__mpwez, nvhss__uamp))]
            ibu__tmaxn = [hqmg__vllxc for hqmg__vllxc in nvhss__uamp if fs.
                info(hqmg__vllxc)['size'] > 0]
            if len(ibu__tmaxn) == 0:
                raise BodoError(vpjy__ncfpf)
            fname = ibu__tmaxn[0]
            bfu__dexvj = fs.info(fname)['size']
            fname = urlparse(fname).path
        jijga__gulk = fs.open(fname, 'rb')
    else:
        if snihb__tyyun.scheme != '':
            raise BodoError(
                f'Unrecognized scheme {snihb__tyyun.scheme}. Please refer to https://docs.bodo.ai/latest/source/file_io.html'
                )
        lcq__httqc = False
        if os.path.isdir(path):
            hrob__oqi = filter(lje__mpwez, glob.glob(os.path.join(os.path.
                abspath(path), '*')))
            ibu__tmaxn = [hqmg__vllxc for hqmg__vllxc in sorted(hrob__oqi) if
                os.path.getsize(hqmg__vllxc) > 0]
            if len(ibu__tmaxn) == 0:
                raise BodoError(vpjy__ncfpf)
            fname = ibu__tmaxn[0]
        bfu__dexvj = os.path.getsize(fname)
        jijga__gulk = fname
    return lcq__httqc, jijga__gulk, bfu__dexvj, fs


def get_s3_bucket_region(s3_filepath, parallel):
    try:
        from pyarrow import fs as pa_fs
    except:
        raise BodoError('Reading from s3 requires pyarrow currently.')
    from mpi4py import MPI
    rslv__dyxf = MPI.COMM_WORLD
    bucket_loc = None
    if parallel and bodo.get_rank() == 0 or not parallel:
        try:
            ozm__wwing, qofax__wqyp = pa_fs.S3FileSystem.from_uri(s3_filepath)
            bucket_loc = ozm__wwing.region
        except Exception as bmwwz__fbp:
            if os.environ.get('AWS_DEFAULT_REGION', '') == '':
                warnings.warn(BodoWarning(
                    f"""Unable to get S3 Bucket Region.
{bmwwz__fbp}.
Value not defined in the AWS_DEFAULT_REGION environment variable either. Region defaults to us-east-1 currently."""
                    ))
            bucket_loc = ''
    if parallel:
        bucket_loc = rslv__dyxf.bcast(bucket_loc)
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
        uaphg__xrdx = get_s3_bucket_region_njit(path_or_buf, parallel=
            is_parallel)
        olu__hur, jcj__dtxv = unicode_to_utf8_and_len(D)
        ypr__fdy = 0
        if is_parallel:
            ypr__fdy = bodo.libs.distributed_api.dist_exscan(jcj__dtxv, np.
                int32(Reduce_Type.Sum.value))
        _csv_write(unicode_to_utf8(path_or_buf), olu__hur, ypr__fdy,
            jcj__dtxv, is_parallel, unicode_to_utf8(uaphg__xrdx))
        bodo.utils.utils.check_and_propagate_cpp_exception()
    return impl
