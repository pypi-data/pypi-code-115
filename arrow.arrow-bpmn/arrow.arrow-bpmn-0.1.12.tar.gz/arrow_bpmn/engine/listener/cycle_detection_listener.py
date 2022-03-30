from arrow_bpmn.__spi__ import BpmnNode, State
from arrow_bpmn.engine.listener.abstract_bpmn_engine_listener import BpmnEngineListener


class CycleDetectionListener(BpmnEngineListener):

    def before_node_execution(self, node: BpmnNode, state: State):
        super().before_node_execution(node, state)

    def after_node_execution(self, node: BpmnNode, state: State):
        super().after_node_execution(node, state)