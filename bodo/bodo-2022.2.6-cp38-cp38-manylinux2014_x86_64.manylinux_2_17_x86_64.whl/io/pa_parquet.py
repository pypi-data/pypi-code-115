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
    except Exception as nmv__wxki:
        raise ImportError(
            "Bodo Error: please pip install the 'deltalake' package to read parquet from delta lake"
            )
    jqg__jklh = None
    zcl__eryf = delta_lake_path.rstrip('/')
    xsb__amyfd = 'AWS_DEFAULT_REGION' in os.environ
    tkxl__omc = os.environ.get('AWS_DEFAULT_REGION', '')
    wvle__debdc = False
    if delta_lake_path.startswith('s3://'):
        pag__gehin = get_s3_bucket_region_njit(delta_lake_path, parallel=False)
        if pag__gehin != '':
            os.environ['AWS_DEFAULT_REGION'] = pag__gehin
            wvle__debdc = True
    icbog__vmdn = DeltaTable(delta_lake_path)
    jqg__jklh = icbog__vmdn.files()
    jqg__jklh = [(zcl__eryf + '/' + jdrwh__aoyxh) for jdrwh__aoyxh in
        sorted(jqg__jklh)]
    if wvle__debdc:
        if xsb__amyfd:
            os.environ['AWS_DEFAULT_REGION'] = tkxl__omc
        else:
            del os.environ['AWS_DEFAULT_REGION']
    return jqg__jklh


def get_dataset_schema(dataset):
    if dataset.metadata is None and dataset.schema is None:
        if dataset.common_metadata is not None:
            dataset.schema = dataset.common_metadata.schema
        else:
            dataset.schema = dataset.pieces[0].get_metadata().schema
    elif dataset.schema is None:
        dataset.schema = dataset.metadata.schema
    cfmxr__ogwdc = dataset.schema.to_arrow_schema()
    if dataset.partitions is not None:
        for vvm__clfv in dataset.partitions.partition_names:
            if cfmxr__ogwdc.get_field_index(vvm__clfv) != -1:
                wvhw__afglf = cfmxr__ogwdc.get_field_index(vvm__clfv)
                cfmxr__ogwdc = cfmxr__ogwdc.remove(wvhw__afglf)
    return cfmxr__ogwdc


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
        except Exception as nmv__wxki:
            self.exc = nmv__wxki
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
        ikhxa__ceqew = VisitLevelThread(self)
        ikhxa__ceqew.start()
        ikhxa__ceqew.join()
        for tnyi__cybyh in self.partition_vals.keys():
            self.partition_vals[tnyi__cybyh] = sorted(self.partition_vals[
                tnyi__cybyh])
        for nfwi__kig in self.partitions.levels:
            nfwi__kig.keys = sorted(nfwi__kig.keys)
        for cbw__xah in self.pieces:
            if cbw__xah.partition_keys is not None:
                cbw__xah.partition_keys = [(xbv__owhci, self.partition_vals
                    [xbv__owhci].index(rnvz__nzqfv)) for xbv__owhci,
                    rnvz__nzqfv in cbw__xah.partition_keys]
        self.pieces.sort(key=lambda piece: piece.path)
        if self.common_metadata_path is None:
            self.common_metadata_path = self.metadata_path
        self._thread_pool.shutdown()

    async def _visit_level(self, asnao__brx, base_path, azk__vtfb):
        fs = self.filesystem
        nvs__kun, vfv__zomdp, wlbc__uqz = await self.loop.run_in_executor(self
            ._thread_pool, lambda fs, base_bath: next(fs.walk(base_path)),
            fs, base_path)
        if asnao__brx == 0 and '_delta_log' in vfv__zomdp:
            self.delta_lake_filter = set(get_parquet_filesnames_from_deltalake
                (base_path))
        mup__bzpyr = []
        for zcl__eryf in wlbc__uqz:
            if zcl__eryf == '':
                continue
            fxa__pxqpv = self.pathsep.join((base_path, zcl__eryf))
            if zcl__eryf.endswith('_common_metadata'):
                self.common_metadata_path = fxa__pxqpv
            elif zcl__eryf.endswith('_metadata'):
                self.metadata_path = fxa__pxqpv
            elif self._should_silently_exclude(zcl__eryf):
                continue
            elif self.delta_lake_filter and fxa__pxqpv not in self.delta_lake_filter:
                continue
            else:
                mup__bzpyr.append(fxa__pxqpv)
        idk__tvbap = [self.pathsep.join((base_path, lqr__nwx)) for lqr__nwx in
            vfv__zomdp if not pq._is_private_directory(lqr__nwx)]
        mup__bzpyr.sort()
        idk__tvbap.sort()
        if len(mup__bzpyr) > 0 and len(idk__tvbap) > 0:
            raise ValueError('Found files in an intermediate directory: {}'
                .format(base_path))
        elif len(idk__tvbap) > 0:
            await self._visit_directories(asnao__brx, idk__tvbap, azk__vtfb)
        else:
            self._push_pieces(mup__bzpyr, azk__vtfb)

    async def _visit_directories(self, asnao__brx, vfv__zomdp, azk__vtfb):
        ymvp__srvf = []
        for zcl__eryf in vfv__zomdp:
            fbbe__bpy, fwcrc__trl = pq._path_split(zcl__eryf, self.pathsep)
            xbv__owhci, aclte__pfqef = pq._parse_hive_partition(fwcrc__trl)
            zngya__vjq = self.partitions.get_index(asnao__brx, xbv__owhci,
                aclte__pfqef)
            self.partition_vals[xbv__owhci].add(aclte__pfqef)
            yul__obqk = azk__vtfb + [(xbv__owhci, aclte__pfqef)]
            ymvp__srvf.append(self._visit_level(asnao__brx + 1, zcl__eryf,
                yul__obqk))
        await asyncio.wait(ymvp__srvf)


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
