from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from code_loader.contract.responsedataclasses import DatasetIntegParseResult

from leap_model_parser.contract.importmodelresponse import NodeResponse
from openapi_client.model.dataset_version import DatasetVersion


class NodeType(Enum):
    Decoder = 'Decoder'
    Encoder = 'Encoder'
    Layer = 'Layer'
    Loss = 'Loss'
    Optimizer = 'Optimizer'


@dataclass
class Node:
    name: str
    type: NodeType


@dataclass
class NodeConnection:
    node: Node
    node_inputs: Optional[Dict[str, Node]]


class LeapGraphEditor:
    def __init__(self, model_graph: Dict[str, NodeResponse]):
        self.model_graph = model_graph

        node_ids_as_int = [int(node_id) for node_id in model_graph.keys()]
        self._next_node_id_index = max(node_ids_as_int) + 1

    def add_dataset(self, dataset_name: str, dataset_version: DatasetVersion,
                    dataset_parse_result: DatasetIntegParseResult):

        dataset_version_dict = self._convert_to_node_type_dict(dataset_version)
        LeapGraphEditor._add_setup_to_metadata(dataset_version_dict['metadata'], dataset_parse_result)
        self._add_dataset_types_to_encoder_nodes(dataset_parse_result)
        dataset_version_dict['name'] = dataset_name

        dataset_node = self._get_dataset_node()
        dataset_node.data['datasetVersion'] = dataset_version_dict
        dataset_node.data['selected_dataset'] = dataset_name

    def add_connections_to_graph(self, connections: List[NodeConnection]):
        connections = self._validate_and_reorder_connections_list(connections)
        for connection in connections:
            self._add_node_connection_to_graph(connection)

    def _add_node_connection_to_graph(self, node_connection: NodeConnection):
        if node_connection.node.type == NodeType.Decoder:
            new_decoder_node_id = self._add_decoder_node(node_connection.node.name)
            for input_name, node in node_connection.node_inputs.items():
                input_node_id = self._find_or_add_input_node(node)
                self._add_connection_to_node(new_decoder_node_id, input_name, input_node_id)
        elif node_connection.node.type == NodeType.Loss:
            new_loss_node_id = self._add_loss_node(node_connection.node.name)
            for input_name, node in node_connection.node_inputs.items():
                input_node_id = self._find_or_add_input_node(node)
                self._add_connection_to_node(new_loss_node_id, input_name, input_node_id)
        elif node_connection.node.type == NodeType.Optimizer:
            new_optimizer_node_id = self._add_optimizer_node(node_connection.node.name)
            loss_node_ids = self._get_all_loss_node_ids()
            assert len(loss_node_ids) > 0
            for i, loss_node_id in enumerate(loss_node_ids):
                self._add_connection_to_node(new_optimizer_node_id, str(i), loss_node_id)
        else:
            raise Exception(f"Can't add node of type {node_connection.node.type.name}")

    def model_graph_dict(self) -> Dict[str, Any]:
        json_model_graph = {}
        for node_id, node in self.model_graph.items():
            json_model_graph[node_id] = node.__dict__

        return json_model_graph

    @staticmethod
    def _validate_and_reorder_connections_list(connections: List[NodeConnection]) -> List[NodeConnection]:
        optimizers = [connection for connection in connections if connection.node.type == NodeType.Optimizer]
        losses = [connection for connection in connections if connection.node.type == NodeType.Loss]
        decoders = [connection for connection in connections if connection.node.type == NodeType.Decoder]

        if len(optimizers) == 0:
            raise Exception('At least one optimizer needed')
        if len(losses) == 0:
            raise Exception('At least one loss needed')
        if len(optimizers) + len(losses) + len(decoders) < len(connections):
            raise Exception('Unsupported node type')

        return decoders + losses + optimizers

    def _find_encoder_node_id(self, encoder_name: str) -> Optional[str]:
        for node_id, node_response in self.model_graph.items():
            if 'type' in node_response.data and (
                    node_response.data['type'] == 'dataset' or node_response.data['type'] == 'GroundTruth'):
                if f'{node_id}-{encoder_name}' in node_response.outputs:
                    return node_id
        return None

    def _find_layer_node_id(self, layer_name: str) -> str:
        for node_id, node_response in self.model_graph.items():
            if 'type' in node_response.data and node_response.data['type'] == 'Layer':
                if node_response.data['origin_name'] == layer_name:
                    return node_id
        raise Exception(f"Couldn't find node for layer {layer_name}")

    def _generate_new_node_id(self) -> str:
        self._next_node_id_index += 1
        return str(self._next_node_id_index - 1)

    def _add_ground_truth_node(self, ground_truth_name: str) -> str:
        new_node_id = self._generate_new_node_id()
        ground_truth_node = NodeResponse(
            new_node_id,
            'GroundTruth',
            data={'name': ground_truth_name, 'output_name': ground_truth_name,
                  'type': 'GroundTruth'},
            inputs={},
            outputs={
                f'{new_node_id}-{ground_truth_name}': {'connections': []}
            }
        )
        self.model_graph[new_node_id] = ground_truth_node
        return new_node_id

    def _add_decoder_node(self, decoder_name: str) -> str:
        new_node_id = self._generate_new_node_id()

        decoder_node = NodeResponse(
            new_node_id,
            'Decoder',
            data={'decoder_name': decoder_name, 'type': 'Decoder'},
            inputs={},
            outputs={})

        self.model_graph[new_node_id] = decoder_node
        return new_node_id

    def _add_loss_node(self, loss_name: str) -> str:
        new_node_id = self._generate_new_node_id()

        loss_node = NodeResponse(
            new_node_id,
            loss_name,
            data={'type': "Loss"},
            inputs={},
            outputs={
                f'{new_node_id}-loss': {'connections': []}
            })

        self.model_graph[new_node_id] = loss_node
        return new_node_id

    def _add_optimizer_node(self, optimizer_name: str) -> str:
        new_node_id = self._generate_new_node_id()

        optimizer_node = NodeResponse(
            new_node_id,
            optimizer_name,
            data={'type': 'Optimizer'},
            inputs={},
            outputs={})

        self.model_graph[new_node_id] = optimizer_node
        return new_node_id

    def _get_output_name_from_node_id(self, input_node_id: str, input_name: Optional[str] = None) -> str:
        input_node_outputs_len = len(self.model_graph[input_node_id].outputs)
        if input_node_outputs_len == 0:
            output_name_to_add = f'{input_node_id}-feature_map'
            self.model_graph[input_node_id].outputs[output_name_to_add] = {
                'connections': []
            }
            return output_name_to_add
        if input_node_outputs_len == 1:
            return list(self.model_graph[input_node_id].outputs.keys())[0]
        if input_name is not None:
            guessed_output_name = f'{input_node_id}-{input_name}'
            if guessed_output_name in self.model_graph[input_node_id].outputs:
                return guessed_output_name

        # todo: layers with multiple outputs
        raise Exception("Can't decide on output name")

    def _add_connection_to_node(self, node_id: str, input_name: str, input_node_id: str):
        # todo: layers with multiple outputs
        output_name = self._get_output_name_from_node_id(input_node_id, input_name)
        input_name = f'{node_id}-{input_name}'
        self.model_graph[node_id].inputs[input_name] = {
            'connections': [{'data': {}, 'node': input_node_id, 'output': output_name}]
        }

        if 'connections' not in self.model_graph[input_node_id].outputs[output_name]:
            self.model_graph[input_node_id].outputs[output_name]['connections'] = []
        output_connection = {'input': input_name, 'node': node_id, 'data': {}}
        self.model_graph[input_node_id].outputs[output_name]['connections'].append(output_connection)

    def _find_or_add_input_node(self, input_node: Node) -> str:
        if input_node.type == NodeType.Encoder:
            input_node_id = self._find_encoder_node_id(input_node.name)
            if input_node_id is None:
                input_node_id = self._add_ground_truth_node(input_node.name)
        else:
            input_node_id = self._find_layer_node_id(input_node.name)

        return input_node_id

    def _get_all_loss_node_ids(self):
        loss_node_ids = []
        for node_id, node_response in self.model_graph.items():
            if 'type' in node_response.data and node_response.data['type'] == 'Loss':
                loss_node_ids.append(node_id)
        return loss_node_ids

    def _get_dataset_node(self) -> NodeResponse:
        for node_response in self.model_graph.values():
            if 'type' in node_response.data and node_response.data['type'] == 'dataset':
                return node_response

        raise Exception("Didn't find dataset node")

    @staticmethod
    def _convert_to_node_type_dict(dataset_version: DatasetVersion) -> Dict[str, Any]:
        dataset_version_dict = dataset_version.to_dict()
        for k in list(dataset_version_dict.keys()):
            new_key = dataset_version.attribute_map[k]
            dataset_version_dict[new_key] = dataset_version_dict.pop(k)

        for k in list(dataset_version_dict['metadata'].keys()):
            new_key = dataset_version.metadata.attribute_map[k]
            dataset_version_dict['metadata'][new_key] = dataset_version_dict['metadata'].pop(k)

        return dataset_version_dict

    @staticmethod
    def _add_setup_to_metadata(dataset_version_metadata: Dict[str, Any],
                               dataset_parse_result: DatasetIntegParseResult):
        setup = {}
        setup['inputs'] = [
            {
                'name': _input.name,
                'subset': _input.subset_name,
                'shape': _input.shape,
                'type': _input.type.name
            }
            for _input in dataset_parse_result.setup.inputs
        ]
        setup['outputs'] = [
            {
                'name': _output.name,
                'subset': _output.subset_name,
                'shape': _output.shape,
                'type': _output.type.name,
                'labels': _output.labels,
                'masked_input': _output.masked_input
            }
            for _output in dataset_parse_result.setup.outputs
        ]
        setup['metadata'] = [
            {
                'name': _metadata.name,
                'subset': _metadata.subset_name,
                'type': _metadata.type.name
            }
            for _metadata in dataset_parse_result.setup.metadata
        ]
        setup['subsets'] = [
            {
                'name': _subset.name,
                'ratio': 1,
                'training_length': _subset.training_length,
                'validation_length': _subset.validation_length,
                'test_length': _subset.test_length
            }
            for _subset in dataset_parse_result.setup.subsets
        ]
        dataset_version_metadata['setup'] = setup

    def _add_dataset_types_to_encoder_nodes(self, dataset_parse_result: DatasetIntegParseResult):
        for _output in dataset_parse_result.setup.outputs:
            gt_node = self._find_encoder_node_id(_output.name)
            self.model_graph[gt_node].data['output_type'] = _output.type.name
            self.model_graph[gt_node].data['labels'] = _output.labels
            self.model_graph[gt_node].data['masked_input'] = _output.masked_input
