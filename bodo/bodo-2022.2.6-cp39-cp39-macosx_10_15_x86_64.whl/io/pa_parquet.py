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
    except Exception as hhj__ijbmq:
        raise ImportError(
            "Bodo Error: please pip install the 'deltalake' package to read parquet from delta lake"
            )
    hnu__urabz = None
    nqt__dpp = delta_lake_path.rstrip('/')
    phd__rmdg = 'AWS_DEFAULT_REGION' in os.environ
    gkeyc__cjq = os.environ.get('AWS_DEFAULT_REGION', '')
    vnvlc__amcbz = False
    if delta_lake_path.startswith('s3://'):
        ytxo__luvj = get_s3_bucket_region_njit(delta_lake_path, parallel=False)
        if ytxo__luvj != '':
            os.environ['AWS_DEFAULT_REGION'] = ytxo__luvj
            vnvlc__amcbz = True
    sww__pywsl = DeltaTable(delta_lake_path)
    hnu__urabz = sww__pywsl.files()
    hnu__urabz = [(nqt__dpp + '/' + fsbf__fvsl) for fsbf__fvsl in sorted(
        hnu__urabz)]
    if vnvlc__amcbz:
        if phd__rmdg:
            os.environ['AWS_DEFAULT_REGION'] = gkeyc__cjq
        else:
            del os.environ['AWS_DEFAULT_REGION']
    return hnu__urabz


def get_dataset_schema(dataset):
    if dataset.metadata is None and dataset.schema is None:
        if dataset.common_metadata is not None:
            dataset.schema = dataset.common_metadata.schema
        else:
            dataset.schema = dataset.pieces[0].get_metadata().schema
    elif dataset.schema is None:
        dataset.schema = dataset.metadata.schema
    xelte__dvkx = dataset.schema.to_arrow_schema()
    if dataset.partitions is not None:
        for odx__nuira in dataset.partitions.partition_names:
            if xelte__dvkx.get_field_index(odx__nuira) != -1:
                sfvo__jsm = xelte__dvkx.get_field_index(odx__nuira)
                xelte__dvkx = xelte__dvkx.remove(sfvo__jsm)
    return xelte__dvkx


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
        except Exception as hhj__ijbmq:
            self.exc = hhj__ijbmq
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
        lgkby__eclb = VisitLevelThread(self)
        lgkby__eclb.start()
        lgkby__eclb.join()
        for bidp__gncnh in self.partition_vals.keys():
            self.partition_vals[bidp__gncnh] = sorted(self.partition_vals[
                bidp__gncnh])
        for ytp__zwa in self.partitions.levels:
            ytp__zwa.keys = sorted(ytp__zwa.keys)
        for pjtaj__psku in self.pieces:
            if pjtaj__psku.partition_keys is not None:
                pjtaj__psku.partition_keys = [(tpkt__spv, self.
                    partition_vals[tpkt__spv].index(gwgl__cen)) for 
                    tpkt__spv, gwgl__cen in pjtaj__psku.partition_keys]
        self.pieces.sort(key=lambda piece: piece.path)
        if self.common_metadata_path is None:
            self.common_metadata_path = self.metadata_path
        self._thread_pool.shutdown()

    async def _visit_level(self, mid__zacc, base_path, kkpas__nrc):
        fs = self.filesystem
        dqifz__hmnux, vaqzp__dfjsw, nsov__jdq = (await self.loop.
            run_in_executor(self._thread_pool, lambda fs, base_bath: next(
            fs.walk(base_path)), fs, base_path))
        if mid__zacc == 0 and '_delta_log' in vaqzp__dfjsw:
            self.delta_lake_filter = set(get_parquet_filesnames_from_deltalake
                (base_path))
        jzn__infv = []
        for nqt__dpp in nsov__jdq:
            if nqt__dpp == '':
                continue
            fxrk__ghtr = self.pathsep.join((base_path, nqt__dpp))
            if nqt__dpp.endswith('_common_metadata'):
                self.common_metadata_path = fxrk__ghtr
            elif nqt__dpp.endswith('_metadata'):
                self.metadata_path = fxrk__ghtr
            elif self._should_silently_exclude(nqt__dpp):
                continue
            elif self.delta_lake_filter and fxrk__ghtr not in self.delta_lake_filter:
                continue
            else:
                jzn__infv.append(fxrk__ghtr)
        nzkco__hze = [self.pathsep.join((base_path, vtsj__ktm)) for
            vtsj__ktm in vaqzp__dfjsw if not pq._is_private_directory(
            vtsj__ktm)]
        jzn__infv.sort()
        nzkco__hze.sort()
        if len(jzn__infv) > 0 and len(nzkco__hze) > 0:
            raise ValueError('Found files in an intermediate directory: {}'
                .format(base_path))
        elif len(nzkco__hze) > 0:
            await self._visit_directories(mid__zacc, nzkco__hze, kkpas__nrc)
        else:
            self._push_pieces(jzn__infv, kkpas__nrc)

    async def _visit_directories(self, mid__zacc, vaqzp__dfjsw, kkpas__nrc):
        hiyvl__kyhdy = []
        for nqt__dpp in vaqzp__dfjsw:
            axsjq__mzx, avj__unbhw = pq._path_split(nqt__dpp, self.pathsep)
            tpkt__spv, rlmxy__gyw = pq._parse_hive_partition(avj__unbhw)
            ocigo__yvqs = self.partitions.get_index(mid__zacc, tpkt__spv,
                rlmxy__gyw)
            self.partition_vals[tpkt__spv].add(rlmxy__gyw)
            ufxi__oivt = kkpas__nrc + [(tpkt__spv, rlmxy__gyw)]
            hiyvl__kyhdy.append(self._visit_level(mid__zacc + 1, nqt__dpp,
                ufxi__oivt))
        await asyncio.wait(hiyvl__kyhdy)


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
