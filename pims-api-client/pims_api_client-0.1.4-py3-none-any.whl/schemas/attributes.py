from typing import Optional
from pydantic import BaseModel
from .base import PerPageRequest

class AttributeFilter(PerPageRequest):
    name: Optional[str] = None
    type: Optional[str] = None
    group: Optional[str] = None


class AttributeListItem(BaseModel):
    id: str
    group: dict
    value: dict
    name: str
    type: str
    type_translation: str
    code: str
    is_required: bool
    is_editable: bool
    is_filterable: bool
    is_visible: bool
    position: int


class AttributeGroupItem(BaseModel):
    id: str
    name: str
    code: str
    position: int