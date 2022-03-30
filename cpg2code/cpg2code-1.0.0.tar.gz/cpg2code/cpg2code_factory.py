from typing import List, Set, Union
from enhanced_phpjoern_framework import Neo4jEngine
from cpg2code.symbolic_tracking import SymbolicTracking


class Cpg2CodeFactory(object):
    @staticmethod
    def extract_code(neo4j_engine: Neo4jEngine, feeder: Union[List, int]):
        """
        This an simple API for extract code from CPG

        :param neo4j_engine:
        :param feeder:
        :return:
        """
        st = SymbolicTracking(neo4j_engine)
        if isinstance(feeder, List):
            res = ""
            for node_id in feeder:
                _res = st.extract_code(neo4j_engine.get_node_itself(node_id))
                if _res != "":
                    res += _res + "\n"
            return res
        elif isinstance(feeder, int):
            return st.extract_code(neo4j_engine.get_node_itself(feeder))

    @staticmethod
    def tracking_code(neo4j_engine: Neo4jEngine, feeder: Union[List, int]):
        """
        This is an simple API for tracking code from CPG

        However, not implement yet.

        :param neo4j_engine:
        :param feeder:
        :return:
        """
        st = SymbolicTracking(neo4j_engine)
