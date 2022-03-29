"""
Class model of proviser in metadata json file
We have two classes in this file:
- Provider
- ProviderList
"""
from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Provider:
    """
    Class model of proviser in metadata json file
    """
    name: str
    url: str
    checksum_type: Optional[str] = field(default="")
    checksum: Optional[str] = field(default="")
