from typing import List, Union, Type, Optional

import pydantic


class BaseEdgeRenderer:
    def __init__(self, edge_data: "Edge"):
        self._edge = edge_data

    def render(self):
        raise NotImplemented


class BaseDiagramRenderer:
    def __init__(self, diagram: "BaseDiagram"):
        self._diagram = diagram

    def render(self):
        raise NotImplementedError


class BaseNode(pydantic.BaseModel):
    id: str
    text: Optional[str]

    def render(self) -> str:
        return self.shape.value.format(self.id, self.text or self.id)


class Edge(pydantic.BaseModel):
    start: BaseNode
    end: BaseNode
    edge_renderer: Type[BaseEdgeRenderer]

    def render(self) -> str:
        return self.edge_renderer(self).render()


class BaseDiagram(pydantic.BaseModel):
    items: List[Union[BaseNode, Edge]] = []
    renderer: Type[BaseDiagramRenderer] = BaseDiagramRenderer

    def __add__(self, other: Union["BaseNode", "Edge"]):
        self.items.append(other)
        return self

    def render(self):
        return self.renderer(self).render()


BaseNode.update_forward_refs()
Edge.update_forward_refs()
