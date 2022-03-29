"""
Class model of version box in metadata json file
We have two classes in this file:
- VersionBox
- VersionBoxList
"""
from dataclasses import dataclass, field
from typing import Iterable, List, Optional
from dataclasses_json import dataclass_json
from packaging import version as packagingVersion

from .provider import Provider


@dataclass_json
@dataclass(eq=True, order=True)
class VersionBox:
    """
    Class model of version box in metadata json file
    """
    version: str = field(compare=True)
    status: Optional[str] = field(compare=False, default="active")
    description_html: Optional[str] = field(compare=False, default="")
    description_markdown: Optional[str] = field(compare=False, default="")
    providers: List[Provider] = field(default_factory=list)
    _version: Optional[str] = field(init=False, default='', compare=False)

    def have_provider(self, provider: str) -> bool:
        """
        Test if the provider is in provider list
        """
        return any(self._filter_provider(provider))

    def provider(self, provider: str) -> Provider:
        """
        Get the provider by this name
        """
        try:
            return self.__getitem__(provider)
        except IndexError:
            return None

    def _filter_provider(self, provider: str) -> Iterable:
        return filter(lambda p: p.name == provider, self.providers)

    @property
    def version(self) -> packagingVersion.Version:
        """
        Get the version with type packaging.version.Version
        """
        return self._version

    @version.setter
    def version(self, version: str) -> None:
        """
        Set the version into type packaging.version.Version
        """
        self._version = packagingVersion.Version(version)

    def __getitem__(self, provider: str) -> Provider:
        try:
            return next(self._filter_provider(provider))
        except StopIteration as exception:
            raise IndexError(
                f'No ProviderList with name: "{provider}"') from exception

    def _filter_provider(self, provider: str) -> Iterable:
        return filter(lambda p: p.name == provider, self.providers)
