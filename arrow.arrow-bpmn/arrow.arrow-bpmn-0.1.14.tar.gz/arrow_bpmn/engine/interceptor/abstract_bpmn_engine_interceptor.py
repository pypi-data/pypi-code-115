from abc import ABC
from typing import Tuple

from arrow_bpmn.__spi__ import State, Environment
from arrow_bpmn.__spi__.action import Action
from arrow_bpmn.__spi__.bpmn_node import BpmnNode


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class BpmnEngineInterceptor(ABC):

    def intercept_node(self, node: BpmnNode) -> BpmnNode:
        return node

    def __call__(self, action: Action, state: State, env: Environment) -> Tuple[Action, State, Environment]:
        return action, state, env
