from typing import Optional, Type, Tuple

import enum

from sirena.base import BaseEdgeRenderer, BaseDiagramRenderer, BaseDiagram, Edge, BaseNode


class NodeShapes(enum.Enum):
    ROUNDED_RECT: str = "{}({})"
    STADIUM: str = "{}([{}])"
    SUBROUTINE: str = "{}[[{}]]"
    CYLINDER: str = "{}[({})]"
    CIRCLE: str = "{}(({}))"
    ASYMMETRIC: str = "{}>{}]"
    RHOMBUS: str = "{}{{{}}}"
    HEXAGON: str = "{}{{{{{}}}}}"
    PARALLELOGRAM: str = "{}[/{}/]"
    PARALLELOGRAM_ALT: str = "{}[\{}\]"
    TRAPEZOID: str = "{}[/{}\]"
    TRAPEZOID_ALT: str = "{}[\{}/]"


class ArrowTypes(enum.Enum):
    X: Tuple[str, str] = ("x", "x")
    O: Tuple[str, str] = ("0", "0")
    ARROW: Tuple[str, str] = ("<", ">")


class Symbol(BaseNode):
    shape: NodeShapes = NodeShapes.ROUNDED_RECT

    def render(self) -> str:
        return self.shape.value.format(self.id, self.text or self.id)


class LineStyle(enum.Enum):
    NORMAL: str = "normal"
    THICK: str = "thick"
    DOTTED: str = "dotted"


class LineDirection(enum.Enum):
    NONE: str = "none"
    UNIDIRECTIONAL: str = "unidirectional"
    MULTIDIRECTIONAL: str = "multidirectional"




class FlowChartEdgeRenderer(BaseEdgeRenderer):
    _edge: 'FlowChartEdge'

    def _render_start_node(self):
        return self._edge.start.render()

    def _render_end_node(self):
        return self._edge.end.render()

    def _render_text(self) -> str:
        if self._edge.text:
            return f"|{self._edge.text}|"

        return ""

    def _render_start_arrow(self) -> str:
        if self._edge.direction == "multi":
            return f"{self._edge.arrow_type.value[0]}"

        return ""

    def _render_end_arrow(self) -> str:
        if self._edge.direction == "multi" or self._edge.direction == "uni":
            return f"{self._edge.arrow_type.value[1]}"

        return ""

    def _render_line(self):

        if self._edge.line_style == LineStyle.NORMAL:
            return f"{self._render_start_arrow()}-{(self._edge.length - 1) * '-'}->{self._render_text()}"

        if self._edge.line_style == LineStyle.DOTTED:
            return f"{self._render_start_arrow()}-{(self._edge.length) * '.'}->{self._render_text()}"

        if self._edge.line_style == LineStyle.THICK:
            return f"{self._render_start_arrow()}={(self._edge.length - 1) * '='}=>{self._render_text()}"

    def render(self):
        return self._render_start_node() + self._render_line() + self._render_end_node()


class FlowChartEdge(Edge):
    text: str = None
    line_style: LineStyle = LineStyle.NORMAL
    arrow_type: ArrowTypes = ArrowTypes.ARROW
    direction: LineDirection = LineDirection.UNIDIRECTIONAL
    length: int = 1
    edge_renderer: Type[BaseEdgeRenderer] = FlowChartEdgeRenderer

class FlowChartRenderer(BaseDiagramRenderer):
    _diagram: 'FlowChart'

    def render(self):

        items_string = "\n\t".join([item.render() for item in self._diagram.items])

        return f"flowchart {self._diagram.orientation}\n\t{items_string}"


class SubGraphRenderer:
    def __init__(self, subgraph: "SubGraph"):
        self._subgraph = subgraph

    def render(self):
        items_string = "\n\t".join([item.render() for item in self._subgraph.items])

        return f"subgraph {self._subgraph.id}\n\t{items_string}\n\tend"


class SubGraph(BaseDiagram):
    renderer: Type[SubGraphRenderer] = SubGraphRenderer
    title: Optional[str] = None
    id: str


class FlowChart(BaseDiagram):
    renderer: Type[FlowChartRenderer] = FlowChartRenderer
    orientation: str = "LR"


# a = Node(id="a", text="test")
# b = Node(id="b")
# c = Node(id="c")
#
# sg = SubGraph(id="test")
# sg + Node(id="e")
#
#
# e = FlowChartEdge(start=a, end=b, direction=LineDirection.UNIDIRECTIONAL)
# e2 = FlowChartEdge(start=a, end=c, text="blah", length=3, line_style=LineStyle.DOTTED)
#
#
# fc = (
#     FlowChart(orientation="TD")
#     + e
#     + e2
#     + FlowChartEdge(start=b, end=c, line_style=LineStyle.THICK)
#     + sg
#     + FlowChartEdge(start=b, end=Node(id="e"))
# )
#
# print(fc.render())
