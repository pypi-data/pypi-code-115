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
    except Exception as ozr__bkrb:
        raise ImportError(
            "Bodo Error: please pip install the 'deltalake' package to read parquet from delta lake"
            )
    oyivh__qiusr = None
    ysui__xkf = delta_lake_path.rstrip('/')
    rtnp__hysgb = 'AWS_DEFAULT_REGION' in os.environ
    nrq__fznf = os.environ.get('AWS_DEFAULT_REGION', '')
    bph__rxhq = False
    if delta_lake_path.startswith('s3://'):
        xet__hvm = get_s3_bucket_region_njit(delta_lake_path, parallel=False)
        if xet__hvm != '':
            os.environ['AWS_DEFAULT_REGION'] = xet__hvm
            bph__rxhq = True
    czg__xpboj = DeltaTable(delta_lake_path)
    oyivh__qiusr = czg__xpboj.files()
    oyivh__qiusr = [(ysui__xkf + '/' + glxh__qdlf) for glxh__qdlf in sorted
        (oyivh__qiusr)]
    if bph__rxhq:
        if rtnp__hysgb:
            os.environ['AWS_DEFAULT_REGION'] = nrq__fznf
        else:
            del os.environ['AWS_DEFAULT_REGION']
    return oyivh__qiusr


def get_dataset_schema(dataset):
    if dataset.metadata is None and dataset.schema is None:
        if dataset.common_metadata is not None:
            dataset.schema = dataset.common_metadata.schema
        else:
            dataset.schema = dataset.pieces[0].get_metadata().schema
    elif dataset.schema is None:
        dataset.schema = dataset.metadata.schema
    oxeay__lzxg = dataset.schema.to_arrow_schema()
    if dataset.partitions is not None:
        for htrr__jaw in dataset.partitions.partition_names:
            if oxeay__lzxg.get_field_index(htrr__jaw) != -1:
                kugjy__fyn = oxeay__lzxg.get_field_index(htrr__jaw)
                oxeay__lzxg = oxeay__lzxg.remove(kugjy__fyn)
    return oxeay__lzxg


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
        except Exception as ozr__bkrb:
            self.exc = ozr__bkrb
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
        owsr__sbkq = VisitLevelThread(self)
        owsr__sbkq.start()
        owsr__sbkq.join()
        for wbaks__ixwt in self.partition_vals.keys():
            self.partition_vals[wbaks__ixwt] = sorted(self.partition_vals[
                wbaks__ixwt])
        for ylhq__klcn in self.partitions.levels:
            ylhq__klcn.keys = sorted(ylhq__klcn.keys)
        for bauwv__rgk in self.pieces:
            if bauwv__rgk.partition_keys is not None:
                bauwv__rgk.partition_keys = [(xtst__ghqw, self.
                    partition_vals[xtst__ghqw].index(yxsl__vbo)) for 
                    xtst__ghqw, yxsl__vbo in bauwv__rgk.partition_keys]
        self.pieces.sort(key=lambda piece: piece.path)
        if self.common_metadata_path is None:
            self.common_metadata_path = self.metadata_path
        self._thread_pool.shutdown()

    async def _visit_level(self, ctcff__kkkz, base_path, zmdv__fhi):
        fs = self.filesystem
        zvw__oxjb, ajj__kkiq, uvll__bzuxj = await self.loop.run_in_executor(
            self._thread_pool, lambda fs, base_bath: next(fs.walk(base_path
            )), fs, base_path)
        if ctcff__kkkz == 0 and '_delta_log' in ajj__kkiq:
            self.delta_lake_filter = set(get_parquet_filesnames_from_deltalake
                (base_path))
        hnib__xsj = []
        for ysui__xkf in uvll__bzuxj:
            if ysui__xkf == '':
                continue
            muru__eodjk = self.pathsep.join((base_path, ysui__xkf))
            if ysui__xkf.endswith('_common_metadata'):
                self.common_metadata_path = muru__eodjk
            elif ysui__xkf.endswith('_metadata'):
                self.metadata_path = muru__eodjk
            elif self._should_silently_exclude(ysui__xkf):
                continue
            elif self.delta_lake_filter and muru__eodjk not in self.delta_lake_filter:
                continue
            else:
                hnib__xsj.append(muru__eodjk)
        oqlqx__dkej = [self.pathsep.join((base_path, etvz__vmro)) for
            etvz__vmro in ajj__kkiq if not pq._is_private_directory(etvz__vmro)
            ]
        hnib__xsj.sort()
        oqlqx__dkej.sort()
        if len(hnib__xsj) > 0 and len(oqlqx__dkej) > 0:
            raise ValueError('Found files in an intermediate directory: {}'
                .format(base_path))
        elif len(oqlqx__dkej) > 0:
            await self._visit_directories(ctcff__kkkz, oqlqx__dkej, zmdv__fhi)
        else:
            self._push_pieces(hnib__xsj, zmdv__fhi)

    async def _visit_directories(self, ctcff__kkkz, ajj__kkiq, zmdv__fhi):
        hedfx__udrsi = []
        for ysui__xkf in ajj__kkiq:
            ywnvp__rky, szqv__pqc = pq._path_split(ysui__xkf, self.pathsep)
            xtst__ghqw, clla__quxbu = pq._parse_hive_partition(szqv__pqc)
            ubsw__swlfw = self.partitions.get_index(ctcff__kkkz, xtst__ghqw,
                clla__quxbu)
            self.partition_vals[xtst__ghqw].add(clla__quxbu)
            chwt__dlesc = zmdv__fhi + [(xtst__ghqw, clla__quxbu)]
            hedfx__udrsi.append(self._visit_level(ctcff__kkkz + 1,
                ysui__xkf, chwt__dlesc))
        await asyncio.wait(hedfx__udrsi)


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
