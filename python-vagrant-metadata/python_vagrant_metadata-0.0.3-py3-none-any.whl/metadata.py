"""
Class model of metadata in metadata json file
"""
from typing import Iterable, List, Optional, Union
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from packaging import version as packagingVersion

from .version_box import VersionBox


@dataclass_json
@dataclass
class Metadata:
    """
    Class model of metadata in metadata json file
    """
    name: str
    description: Optional[str] = field(compare=False, default="")
    short_description: Optional[str] = field(compare=False, default="")
    versions: List[VersionBox] = field(default_factory=list)

    def url_for(self, version: Union[str, packagingVersion.Version], provider: str) -> str:
        """
        Get the download url of box for the specific version and provider
        """
        return self[version][provider].url

    def url_for_youngest_version(self, provider: str) -> str:
        """
        Get the download url of box for the youngest version and the specific provider
        """
        return self.youngest()[provider].url

    def __getitem__(self, version: Union[str, packagingVersion.Version]) -> VersionBox:
        """
        Get the VersionBox by version
        """
        if isinstance(version, str):
            version = packagingVersion.Version(version)
        try:
            return next(self._filter_version(version))
        except StopIteration as exception:
            raise IndexError(
                f'No VersionBox with version: "{version}"') from exception

    def _filter_version(self, version: packagingVersion.Version) -> Iterable:
        return filter(lambda v: v.version == version, self.versions)

    def _filter_provider(self, provider: str) -> Iterable:
        return filter(lambda v: v.have_provider(provider), self.versions)

    def youngest(self) -> VersionBox:
        """
        Get the youngest VersionBox
        """
        return sorted(self.versions, reverse=True)[0]

    def keep_only_provider(self, provider: str):
        """
        Return Metadata instance with only version with provider
        """
        return Metadata(
            self.name,
            self.description,
            self.short_description,
            list(self._filter_provider(provider))
        )
