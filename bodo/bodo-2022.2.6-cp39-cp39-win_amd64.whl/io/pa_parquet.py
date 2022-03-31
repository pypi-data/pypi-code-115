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
    except Exception as gla__qqmhs:
        raise ImportError(
            "Bodo Error: please pip install the 'deltalake' package to read parquet from delta lake"
            )
    bwot__nwila = None
    jxlkn__eyd = delta_lake_path.rstrip('/')
    vmx__vlilf = 'AWS_DEFAULT_REGION' in os.environ
    art__darsp = os.environ.get('AWS_DEFAULT_REGION', '')
    aydt__vdvbr = False
    if delta_lake_path.startswith('s3://'):
        cqplm__ulf = get_s3_bucket_region_njit(delta_lake_path, parallel=False)
        if cqplm__ulf != '':
            os.environ['AWS_DEFAULT_REGION'] = cqplm__ulf
            aydt__vdvbr = True
    zwp__ynkm = DeltaTable(delta_lake_path)
    bwot__nwila = zwp__ynkm.files()
    bwot__nwila = [(jxlkn__eyd + '/' + azmyr__fhjt) for azmyr__fhjt in
        sorted(bwot__nwila)]
    if aydt__vdvbr:
        if vmx__vlilf:
            os.environ['AWS_DEFAULT_REGION'] = art__darsp
        else:
            del os.environ['AWS_DEFAULT_REGION']
    return bwot__nwila


def get_dataset_schema(dataset):
    if dataset.metadata is None and dataset.schema is None:
        if dataset.common_metadata is not None:
            dataset.schema = dataset.common_metadata.schema
        else:
            dataset.schema = dataset.pieces[0].get_metadata().schema
    elif dataset.schema is None:
        dataset.schema = dataset.metadata.schema
    rcl__gblnq = dataset.schema.to_arrow_schema()
    if dataset.partitions is not None:
        for goyrz__ugc in dataset.partitions.partition_names:
            if rcl__gblnq.get_field_index(goyrz__ugc) != -1:
                izxtg__ycvpb = rcl__gblnq.get_field_index(goyrz__ugc)
                rcl__gblnq = rcl__gblnq.remove(izxtg__ycvpb)
    return rcl__gblnq


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
        except Exception as gla__qqmhs:
            self.exc = gla__qqmhs
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
        ihwj__ohdme = VisitLevelThread(self)
        ihwj__ohdme.start()
        ihwj__ohdme.join()
        for vnp__pnpkw in self.partition_vals.keys():
            self.partition_vals[vnp__pnpkw] = sorted(self.partition_vals[
                vnp__pnpkw])
        for tbe__arred in self.partitions.levels:
            tbe__arred.keys = sorted(tbe__arred.keys)
        for bmmyw__eoks in self.pieces:
            if bmmyw__eoks.partition_keys is not None:
                bmmyw__eoks.partition_keys = [(ybqai__nxdv, self.
                    partition_vals[ybqai__nxdv].index(xlirv__wqmwp)) for 
                    ybqai__nxdv, xlirv__wqmwp in bmmyw__eoks.partition_keys]
        self.pieces.sort(key=lambda piece: piece.path)
        if self.common_metadata_path is None:
            self.common_metadata_path = self.metadata_path
        self._thread_pool.shutdown()

    async def _visit_level(self, uxil__icc, base_path, rvxgj__xxwv):
        fs = self.filesystem
        moctf__bhfc, paq__oosd, odmew__gkm = await self.loop.run_in_executor(
            self._thread_pool, lambda fs, base_bath: next(fs.walk(base_path
            )), fs, base_path)
        if uxil__icc == 0 and '_delta_log' in paq__oosd:
            self.delta_lake_filter = set(get_parquet_filesnames_from_deltalake
                (base_path))
        dnbzt__mia = []
        for jxlkn__eyd in odmew__gkm:
            if jxlkn__eyd == '':
                continue
            zgz__hajo = self.pathsep.join((base_path, jxlkn__eyd))
            if jxlkn__eyd.endswith('_common_metadata'):
                self.common_metadata_path = zgz__hajo
            elif jxlkn__eyd.endswith('_metadata'):
                self.metadata_path = zgz__hajo
            elif self._should_silently_exclude(jxlkn__eyd):
                continue
            elif self.delta_lake_filter and zgz__hajo not in self.delta_lake_filter:
                continue
            else:
                dnbzt__mia.append(zgz__hajo)
        daor__hlgv = [self.pathsep.join((base_path, zwu__rmm)) for zwu__rmm in
            paq__oosd if not pq._is_private_directory(zwu__rmm)]
        dnbzt__mia.sort()
        daor__hlgv.sort()
        if len(dnbzt__mia) > 0 and len(daor__hlgv) > 0:
            raise ValueError('Found files in an intermediate directory: {}'
                .format(base_path))
        elif len(daor__hlgv) > 0:
            await self._visit_directories(uxil__icc, daor__hlgv, rvxgj__xxwv)
        else:
            self._push_pieces(dnbzt__mia, rvxgj__xxwv)

    async def _visit_directories(self, uxil__icc, paq__oosd, rvxgj__xxwv):
        rln__lnnk = []
        for jxlkn__eyd in paq__oosd:
            jyn__hsgjo, cgev__trbfa = pq._path_split(jxlkn__eyd, self.pathsep)
            ybqai__nxdv, cmd__oop = pq._parse_hive_partition(cgev__trbfa)
            gphjq__jqw = self.partitions.get_index(uxil__icc, ybqai__nxdv,
                cmd__oop)
            self.partition_vals[ybqai__nxdv].add(cmd__oop)
            rtzj__ttoj = rvxgj__xxwv + [(ybqai__nxdv, cmd__oop)]
            rln__lnnk.append(self._visit_level(uxil__icc + 1, jxlkn__eyd,
                rtzj__ttoj))
        await asyncio.wait(rln__lnnk)


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
