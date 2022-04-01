from pathlib import Path
from typing import (
    Optional,
    Tuple,
)


from dataladmetadatamodel.uuidset import UUIDSet
from dataladmetadatamodel.versionlist import TreeVersionList


class MetadataCache:
    def __init__(self):
        self.tvl_us_cache = dict()

    def get_tree_version_list_uiid_set(
            self,
            metadata_store: Path
    ) -> Tuple[Optional[TreeVersionList], Optional[UUIDSet]]:
        return self.tvl_us_cache.get(metadata_store, (None, None))

    def add_tree_version_list_uuid_set(self,
                                       metadata_store: Path,
                                       tree_version_list: TreeVersionList,
                                       uuid_set: UUIDSet):

        self.tvl_us_cache[metadata_store] = (tree_version_list, uuid_set)

    def get