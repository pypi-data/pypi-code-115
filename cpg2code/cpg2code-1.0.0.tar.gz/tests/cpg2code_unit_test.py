import logging
import unittest
import networkx as nx
from enhanced_phpjoern_framework import Neo4jEngine
from enhanced_phpjoern_framework.graph_traversal import ControlGraphForwardTraversal
from enhanced_phpjoern_framework.const import *
from cpg2code.cpg2code_factory import Cpg2CodeFactory


class Cpg2CodeUnitTest(unittest.TestCase):
    def test_code_extract(self):
        """



        :return:
        """
        NEO4J_DEFAULT_CONFIG = {
            "NEO4J_HOST": "10.176.36.21",
            "NEO4J_USERNAME": "neo4j",
            "NEO4J_PASSWORD": "123",
            "NEO4J_PORT": "16101",
            "NEO4J_PROTOCOL": "http",
            "NEO4J_DATABASE": "neo4j",
        }
        # instance of wordpress
        # /home/lth/EnhancedPHPJoernMaster/large_scale_test/WordPress-5.7.1/wp-load.php
        neo4j_engine = Neo4jEngine.from_dict(NEO4J_DEFAULT_CONFIG)
        traversal_entity = ControlGraphForwardTraversal(neo4j_engine)
        # large_scale_test/MISP-2.4.142/app/webroot/index.php
        file = neo4j_engine.get_file_name_belong_node('wp-load.php')
        x = neo4j_engine.get_ast_child_node(neo4j_engine.get_ast_child_node(file))
        origin = neo4j_engine.get_ast_root_node(x)
        print(f"{neo4j_engine.get_node_belong_file_name(origin)} :: L{origin[NODE_LINENO]}")
        traversal_entity.origin = [origin]
        traversal_entity.run()
        rec = traversal_entity.get_record()  # type:nx.DiGraph
        rec_list = [k for k, p in rec.nodes.items()]
        result = Cpg2CodeFactory.extract_code(neo4j_engine, rec_list)
        print(result)


if __name__ == '__main__':
    unittest.main()
