import enum
from typing import Dict, Optional, List, Set, Tuple, Type, Union

import pydantic

from sirena.base import BaseDiagram, BaseNode, Edge


class BaseEntity(BaseNode):
    attributes: Optional[Dict[str, str]] = pydantic.Field(default={})

    def __hash__(self):
        return hash(self.id)

    def render(self) -> str:
        return self.id


class EntityFactory:
    def __init__(self):
        self._registry: Dict[str, BaseEntity] = {}

    def __call__(self, id, attributes=None, *args, **kwargs):
        if id in self._registry:
            return self._registry[id]
        else:
            return BaseEntity(id=id, attributes=attributes or {}, *args, **kwargs)


class Cardinality(enum.Enum):
    ZERO_OR_ONE: Tuple[str, str] = ("|o ", "o|")
    EXACTLY_ONE: Tuple[str, str] = ("||", "||")
    ZERO_OR_MORE: Tuple[str, str] = ("}o", "o{")
    ONE_OR_MORE: Tuple[str, str] = ("}|", "|{")


class BaseRelationship(pydantic.BaseModel):
    left: BaseEntity
    right: BaseEntity
    left_cardinality: Cardinality
    right_cardinality: Cardinality

    def __hash__(self):
        return (
            hash(self.left)
            + hash(self.right)
            + hash(self.left_cardinality)
            + hash(self.right_cardinality)
        )

    def _render_line(self):
        return f"{self.left_cardinality.value[0]}--{self.right_cardinality.value[1]}"

    def render(self):
        return f"{self.left.render()} {self._render_line()} {self.right.render()}"


class ERDRenderer:
    def __init__(self, erd: "ERD"):
        self.erd: "ERD" = erd

    def render(self):
        section_string = "erDiagram"

        entities = []
        for entity in self.erd.entities:
            entities.append(entity.render())

        relationships = []
        for relationship in self.erd.relationships:
            relationships.append(relationship.render())

        joined_renders = "\n\t".join([x for x in entities])
        joined_renders = (
            joined_renders + "\n\t" + "\n\t".join([x for x in relationships])
        )

        return f"{section_string}\n\t{joined_renders}"


class ERD(BaseDiagram):
    renderer: Type[ERDRenderer] = ERDRenderer
    items: Set[Union[BaseRelationship, BaseEntity]] = {}

    @property
    def entities(self) -> Set[BaseEntity]:
        return {i for i in self.items if isinstance(i, BaseEntity)}

    @property
    def relationships(self) -> Set[BaseRelationship]:
        return {i for i in self.items if isinstance(i, BaseRelationship)}

    def __add__(self, other):
        if isinstance(other, BaseRelationship) or isinstance(other, BaseEntity):
            self.items.add(other)
        else:
            raise ValueError(f"Can only accept BaseRelationships & BaseEntities")
        return self

    def render(self):
        return self.renderer(self).render()


Entity = EntityFactory()

ERD.update_forward_refs(**locals())


erd = ERD()

f = []
for field in ERD.__fields__.values():
    f.append(field)
