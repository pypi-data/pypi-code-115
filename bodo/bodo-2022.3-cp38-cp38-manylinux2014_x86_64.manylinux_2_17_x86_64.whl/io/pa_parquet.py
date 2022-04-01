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
    except Exception as ugi__bhbp:
        raise ImportError(
            "Bodo Error: please pip install the 'deltalake' package to read parquet from delta lake"
            )
    usvze__chrdw = None
    rzr__tnpis = delta_lake_path.rstrip('/')
    lzv__bnu = 'AWS_DEFAULT_REGION' in os.environ
    ccgp__smaj = os.environ.get('AWS_DEFAULT_REGION', '')
    wtkyz__xug = False
    if delta_lake_path.startswith('s3://'):
        jrlxr__bjuy = get_s3_bucket_region_njit(delta_lake_path, parallel=False
            )
        if jrlxr__bjuy != '':
            os.environ['AWS_DEFAULT_REGION'] = jrlxr__bjuy
            wtkyz__xug = True
    jjno__kfwje = DeltaTable(delta_lake_path)
    usvze__chrdw = jjno__kfwje.files()
    usvze__chrdw = [(rzr__tnpis + '/' + vbwc__cnsic) for vbwc__cnsic in
        sorted(usvze__chrdw)]
    if wtkyz__xug:
        if lzv__bnu:
            os.environ['AWS_DEFAULT_REGION'] = ccgp__smaj
        else:
            del os.environ['AWS_DEFAULT_REGION']
    return usvze__chrdw


def get_dataset_schema(dataset):
    if dataset.metadata is None and dataset.schema is None:
        if dataset.common_metadata is not None:
            dataset.schema = dataset.common_metadata.schema
        else:
            dataset.schema = dataset.pieces[0].get_metadata().schema
    elif dataset.schema is None:
        dataset.schema = dataset.metadata.schema
    ootj__eey = dataset.schema.to_arrow_schema()
    if dataset.partitions is not None:
        for ljj__xxuyb in dataset.partitions.partition_names:
            if ootj__eey.get_field_index(ljj__xxuyb) != -1:
                jamcg__joni = ootj__eey.get_field_index(ljj__xxuyb)
                ootj__eey = ootj__eey.remove(jamcg__joni)
    return ootj__eey


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
        except Exception as ugi__bhbp:
            self.exc = ugi__bhbp
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
        awa__lby = VisitLevelThread(self)
        awa__lby.start()
        awa__lby.join()
        for bjr__pxe in self.partition_vals.keys():
            self.partition_vals[bjr__pxe] = sorted(self.partition_vals[
                bjr__pxe])
        for wsqge__ybl in self.partitions.levels:
            wsqge__ybl.keys = sorted(wsqge__ybl.keys)
        for crn__txrp in self.pieces:
            if crn__txrp.partition_keys is not None:
                crn__txrp.partition_keys = [(nlrx__cddme, self.
                    partition_vals[nlrx__cddme].index(fmwee__pqb)) for 
                    nlrx__cddme, fmwee__pqb in crn__txrp.partition_keys]
        self.pieces.sort(key=lambda piece: piece.path)
        if self.common_metadata_path is None:
            self.common_metadata_path = self.metadata_path
        self._thread_pool.shutdown()

    async def _visit_level(self, rnb__jdhz, base_path, vny__opnr):
        fs = self.filesystem
        xncy__oocet, trxv__tfwsx, msoa__vcxm = await self.loop.run_in_executor(
            self._thread_pool, lambda fs, base_bath: next(fs.walk(base_path
            )), fs, base_path)
        if rnb__jdhz == 0 and '_delta_log' in trxv__tfwsx:
            self.delta_lake_filter = set(get_parquet_filesnames_from_deltalake
                (base_path))
        mhgj__xmn = []
        for rzr__tnpis in msoa__vcxm:
            if rzr__tnpis == '':
                continue
            uufg__gesqa = self.pathsep.join((base_path, rzr__tnpis))
            if rzr__tnpis.endswith('_common_metadata'):
                self.common_metadata_path = uufg__gesqa
            elif rzr__tnpis.endswith('_metadata'):
                self.metadata_path = uufg__gesqa
            elif self._should_silently_exclude(rzr__tnpis):
                continue
            elif self.delta_lake_filter and uufg__gesqa not in self.delta_lake_filter:
                continue
            else:
                mhgj__xmn.append(uufg__gesqa)
        bdn__yfdf = [self.pathsep.join((base_path, mkk__wccba)) for
            mkk__wccba in trxv__tfwsx if not pq._is_private_directory(
            mkk__wccba)]
        mhgj__xmn.sort()
        bdn__yfdf.sort()
        if len(mhgj__xmn) > 0 and len(bdn__yfdf) > 0:
            raise ValueError('Found files in an intermediate directory: {}'
                .format(base_path))
        elif len(bdn__yfdf) > 0:
            await self._visit_directories(rnb__jdhz, bdn__yfdf, vny__opnr)
        else:
            self._push_pieces(mhgj__xmn, vny__opnr)

    async def _visit_directories(self, rnb__jdhz, trxv__tfwsx, vny__opnr):
        lwoi__qaukm = []
        for rzr__tnpis in trxv__tfwsx:
            hww__has, akmbn__ybgnl = pq._path_split(rzr__tnpis, self.pathsep)
            nlrx__cddme, fjpnq__ygx = pq._parse_hive_partition(akmbn__ybgnl)
            hathk__mtxo = self.partitions.get_index(rnb__jdhz, nlrx__cddme,
                fjpnq__ygx)
            self.partition_vals[nlrx__cddme].add(fjpnq__ygx)
            hnb__cihc = vny__opnr + [(nlrx__cddme, fjpnq__ygx)]
            lwoi__qaukm.append(self._visit_level(rnb__jdhz + 1, rzr__tnpis,
                hnb__cihc))
        await asyncio.wait(lwoi__qaukm)


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
