# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/main/LICENSE
# Copyright (c) https://github.com/PyCQA/pylint/blob/main/CONTRIBUTORS.txt

"""Module to add McCabe checker class for pylint."""

from typing import TYPE_CHECKING

from astroid import nodes
from mccabe import PathGraph as Mccabe_PathGraph
from mccabe import PathGraphingAstVisitor as Mccabe_PathGraphingAstVisitor

from pylint import checkers
from pylint.checkers.utils import check_messages
from pylint.interfaces import HIGH, IAstroidChecker

if TYPE_CHECKING:
    from pylint.lint import PyLinter


class PathGraph(Mccabe_PathGraph):
    def __init__(self, node):
        super().__init__(name="", entity="", lineno=1)
        self.root = node


class PathGraphingAstVisitor(Mccabe_PathGraphingAstVisitor):
    def __init__(self):
        super().__init__()
        self._bottom_counter = 0

    def default(self, node, *args):
        for child in node.get_children():
            self.dispatch(child, *args)

    def dispatch(self, node, *args):
        self.node = node
        klass = node.__class__
        meth = self._cache.get(klass)
        if meth is None:
            class_name = klass.__name__
            meth = getattr(self.visitor, "visit" + class_name, self.default)
            self._cache[klass] = meth
        return meth(node, *args)

    def visitFunctionDef(self, node):
        if self.graph is not None:
            # closure
            pathnode = self._append_node(node)
            self.tail = pathnode
            self.dispatch_list(node.body)
            bottom = f"{self._bottom_counter}"
            self._bottom_counter += 1
            self.graph.connect(self.tail, bottom)
            self.graph.connect(node, bottom)
            self.tail = bottom
        else:
            self.graph = PathGraph(node)
            self.tail = node
            self.dispatch_list(node.body)
            self.graphs[f"{self.classname}{node.name}"] = self.graph
            self.reset()

    visitAsyncFunctionDef = visitFunctionDef

    def visitSimpleStatement(self, node):
        self._append_node(node)

    visitAssert = (
        visitAssign
    ) = (
        visitAugAssign
    ) = (
        visitDelete
    ) = (
        visitPrint
    ) = (
        visitRaise
    ) = (
        visitYield
    ) = (
        visitImport
    ) = (
        visitCall
    ) = (
        visitSubscript
    ) = (
        visitPass
    ) = (
        visitContinue
    ) = (
        visitBreak
    ) = visitGlobal = visitReturn = visitExpr = visitAwait = visitSimpleStatement

    def visitWith(self, node):
        self._append_node(node)
        self.dispatch_list(node.body)

    visitAsyncWith = visitWith

    def _append_node(self, node):
        if not self.tail:
            return None
        self.graph.connect(self.tail, node)
        self.tail = node
        return node

    def _subgraph(self, node, name, extra_blocks=()):
        """Create the subgraphs representing any `if` and `for` statements."""
        if self.graph is None:
            # global loop
            self.graph = PathGraph(node)
            self._subgraph_parse(node, node, extra_blocks)
            self.graphs[f"{self.classname}{name}"] = self.graph
            self.reset()
        else:
            self._append_node(node)
            self._subgraph_parse(node, node, extra_blocks)

    def _subgraph_parse(self, node, pathnode, extra_blocks):
        """Parse the body and any `else` block of `if` and `for` statements."""
        loose_ends = []
        self.tail = node
        self.dispatch_list(node.body)
        loose_ends.append(self.tail)
        for extra in extra_blocks:
            self.tail = node
            self.dispatch_list(extra.body)
            loose_ends.append(self.tail)
        if node.orelse:
            self.tail = node
            self.dispatch_list(node.orelse)
            loose_ends.append(self.tail)
        else:
            loose_ends.append(node)
        if node:
            bottom = f"{self._bottom_counter}"
            self._bottom_counter += 1
            for end in loose_ends:
                self.graph.connect(end, bottom)
            self.tail = bottom


class McCabeMethodChecker(checkers.BaseChecker):
    """Checks McCabe complexity cyclomatic threshold in methods and functions
    to validate a too complex code.
    """

    __implements__ = IAstroidChecker
    name = "design"

    msgs = {
        "R1260": (
            "%s is too complex. The McCabe rating is %d",
            "too-complex",
            "Used when a method or function is too complex based on "
            "McCabe Complexity Cyclomatic",
        )
    }
    options = (
        (
            "max-complexity",
            {
                "default": 10,
                "type": "int",
                "metavar": "<int>",
                "help": "McCabe complexity cyclomatic threshold",
            },
        ),
    )

    @check_messages("too-complex")
    def visit_module(self, node: nodes.Module) -> None:
        """Visit an astroid.Module node to check too complex rating and
        add message if is greater than max_complexity stored from options
        """
        visitor = PathGraphingAstVisitor()
        for child in node.body:
            visitor.preorder(child, visitor)
        for graph in visitor.graphs.values():
            complexity = graph.complexity()
            node = graph.root
            if hasattr(node, "name"):
                node_name = f"'{node.name}'"
            else:
                node_name = f"This '{node.__class__.__name__.lower()}'"
            if complexity <= self.config.max_complexity:
                continue
            self.add_message(
                "too-complex", node=node, confidence=HIGH, args=(node_name, complexity)
            )


def register(linter: "PyLinter") -> None:
    linter.register_checker(McCabeMethodChecker(linter))
