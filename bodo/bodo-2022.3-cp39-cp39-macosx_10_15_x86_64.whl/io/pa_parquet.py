import asyncio
import os
import threading
from collections import defaultdict
from concurrent import futures
import pyarrow.parquet as pq
from bodo.io.fs_io import get_s3_bucket_region_njit


def get_parquet_filesnames_from_deltalake(delta_lake_path):
    try:
        from deltalake import DeltaTable
    except Exception as xnpd__kguz:
        raise ImportError(
            "Bodo Error: please pip install the 'deltalake' package to read parquet from delta lake"
            )
    oter__hxati = None
    ymv__otcc = delta_lake_path.rstrip('/')
    axbm__vho = 'AWS_DEFAULT_REGION' in os.environ
    xfd__qcexa = os.environ.get('AWS_DEFAULT_REGION', '')
    hbe__xhpvq = False
    if delta_lake_path.startswith('s3://'):
        qdq__kox = get_s3_bucket_region_njit(delta_lake_path, parallel=False)
        if qdq__kox != '':
            os.environ['AWS_DEFAULT_REGION'] = qdq__kox
            hbe__xhpvq = True
    rfq__bnsjd = DeltaTable(delta_lake_path)
    oter__hxati = rfq__bnsjd.files()
    oter__hxati = [(ymv__otcc + '/' + nuet__jri) for nuet__jri in sorted(
        oter__hxati)]
    if hbe__xhpvq:
        if axbm__vho:
            os.environ['AWS_DEFAULT_REGION'] = xfd__qcexa
        else:
            del os.environ['AWS_DEFAULT_REGION']
    return oter__hxati


def get_dataset_schema(dataset):
    if dataset.metadata is None and dataset.schema is None:
        if dataset.common_metadata is not None:
            dataset.schema = dataset.common_metadata.schema
        else:
            dataset.schema = dataset.pieces[0].get_metadata().schema
    elif dataset.schema is None:
        dataset.schema = dataset.metadata.schema
    uld__fkw = dataset.schema.to_arrow_schema()
    if dataset.partitions is not None:
        for ihm__umr in dataset.partitions.partition_names:
            if uld__fkw.get_field_index(ihm__umr) != -1:
                sanw__fbyo = uld__fkw.get_field_index(ihm__umr)
                uld__fkw = uld__fkw.remove(sanw__fbyo)
    return uld__fkw


class VisitLevelThread(threading.Thread):

    def __init__(self, manifest):
        threading.Thread.__init__(self)
        self.manifest = manifest
        self.exc = None

    def run(self):
        try:
            manifest = self.manifest
            manifest.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(manifest.loop)
            manifest.loop.run_until_complete(manifest._visit_level(0,
                manifest.dirpath, []))
        except Exception as xnpd__kguz:
            self.exc = xnpd__kguz
        finally:
            if hasattr(manifest, 'loop') and not manifest.loop.is_closed():
                manifest.loop.close()

    def join(self):
        super(VisitLevelThread, self).join()
        if self.exc:
            raise self.exc


class ParquetManifest:

    def __init__(self, dirpath, open_file_func=None, filesystem=None,
        pathsep='/', partition_scheme='hive', metadata_nthreads=1):
        filesystem, dirpath = pq._get_filesystem_and_path(filesystem, dirpath)
        self.filesystem = filesystem
        self.open_file_func = open_file_func
        self.pathsep = pathsep
        self.dirpath = pq._stringify_path(dirpath)
        self.partition_scheme = partition_scheme
        self.partitions = pq.ParquetPartitions()
        self.pieces = []
        self._metadata_nthreads = metadata_nthreads
        self._thread_pool = futures.ThreadPoolExecutor(max_workers=
            metadata_nthreads)
        self.common_metadata_path = None
        self.metadata_path = None
        self.delta_lake_filter = set()
        self.partition_vals = defaultdict(set)
        vewnm__ifup = VisitLevelThread(self)
        vewnm__ifup.start()
        vewnm__ifup.join()
        for kzl__nazy in self.partition_vals.keys():
            self.partition_vals[kzl__nazy] = sorted(self.partition_vals[
                kzl__nazy])
        for vfl__lewk in self.partitions.levels:
            vfl__lewk.keys = sorted(vfl__lewk.keys)
        for jtc__kqxm in self.pieces:
            if jtc__kqxm.partition_keys is not None:
                jtc__kqxm.partition_keys = [(ozii__gilrh, self.
                    partition_vals[ozii__gilrh].index(dnpp__xul)) for 
                    ozii__gilrh, dnpp__xul in jtc__kqxm.partition_keys]
        self.pieces.sort(key=lambda piece: piece.path)
        if self.common_metadata_path is None:
            self.common_metadata_path = self.metadata_path
        self._thread_pool.shutdown()

    async def _visit_level(self, anmq__ckk, base_path, zzm__dkep):
        fs = self.filesystem
        mjqi__quakg, ung__wjz, lgta__ejoax = await self.loop.run_in_executor(
            self._thread_pool, lambda fs, base_bath: next(fs.walk(base_path
            )), fs, base_path)
        if anmq__ckk == 0 and '_delta_log' in ung__wjz:
            self.delta_lake_filter = set(get_parquet_filesnames_from_deltalake
                (base_path))
        rqkal__xuduk = []
        for ymv__otcc in lgta__ejoax:
            if ymv__otcc == '':
                continue
            rgzm__aayx = self.pathsep.join((base_path, ymv__otcc))
            if ymv__otcc.endswith('_common_metadata'):
                self.common_metadata_path = rgzm__aayx
            elif ymv__otcc.endswith('_metadata'):
                self.metadata_path = rgzm__aayx
            elif self._should_silently_exclude(ymv__otcc):
                continue
            elif self.delta_lake_filter and rgzm__aayx not in self.delta_lake_filter:
                continue
            else:
                rqkal__xuduk.append(rgzm__aayx)
        kbeyx__vpk = [self.pathsep.join((base_path, yiuo__yreb)) for
            yiuo__yreb in ung__wjz if not pq._is_private_directory(yiuo__yreb)]
        rqkal__xuduk.sort()
        kbeyx__vpk.sort()
        if len(rqkal__xuduk) > 0 and len(kbeyx__vpk) > 0:
            raise ValueError('Found files in an intermediate directory: {}'
                .format(base_path))
        elif len(kbeyx__vpk) > 0:
            await self._visit_directories(anmq__ckk, kbeyx__vpk, zzm__dkep)
        else:
            self._push_pieces(rqkal__xuduk, zzm__dkep)

    async def _visit_directories(self, anmq__ckk, ung__wjz, zzm__dkep):
        yogy__sbg = []
        for ymv__otcc in ung__wjz:
            wtvvj__qiza, zhb__yxv = pq._path_split(ymv__otcc, self.pathsep)
            ozii__gilrh, nblt__mcc = pq._parse_hive_partition(zhb__yxv)
            avgax__srjzq = self.partitions.get_index(anmq__ckk, ozii__gilrh,
                nblt__mcc)
            self.partition_vals[ozii__gilrh].add(nblt__mcc)
            asgqm__tlf = zzm__dkep + [(ozii__gilrh, nblt__mcc)]
            yogy__sbg.append(self._visit_level(anmq__ckk + 1, ymv__otcc,
                asgqm__tlf))
        await asyncio.wait(yogy__sbg)


ParquetManifest._should_silently_exclude = (pq.ParquetManifest.
    _should_silently_exclude)
ParquetManifest._parse_partition = pq.ParquetManifest._parse_partition
ParquetManifest._push_pieces = pq.ParquetManifest._push_pieces
pq.ParquetManifest = ParquetManifest


def pieces(self):
    return self._pieces


pq.ParquetDataset.pieces = property(pieces)


def partitions(self):
    return self._partitions


pq.ParquetDataset.partitions = property(partitions)
