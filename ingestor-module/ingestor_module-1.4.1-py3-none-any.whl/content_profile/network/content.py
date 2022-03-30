from typing import ClassVar

from graphdb import GraphDb, GraphDbConnection
from graphdb.schema import Node, Relationship
from pandas import DataFrame

# LABEL NODE NAME & VARIABLE NAME
from ingestor.common.constants import LABEL, CONTENT, PROPERTIES, RELATIONSHIP, CATEGORY, SUBCATEGORY, COUNTRY, \
    CONTENT_ID, HOMEPAGE, ACTORS, TAGS, PACKAGES, PRODUCTS, ACTOR, PRODUCT, PACKAGE, CONTENT_CORE, CONTENT_CORE_ID, \
    CONTENT_CORE_TITLE, CONTENT_CORE_EPISODE, CONTENT_CORE_SYNOPSIS, CONTENT_CORE_SYNOPSIS_EN, SEASON_ID, SEASON, \
    SEASON_NAME, HOMEPAGE_ID, CC_SIMILARITY_SCORE, ALL_SIMILARITY_SCORE, IS_CONNECTED, PAY_TV_CONTENT, \
    NO_PAY_TV_CONTENT, YES, NO
# RELATIONSHIP NAME
from ingestor.content_profile.config import content_node_properties, HAS_CATEGORY, HAS_SUBCATEGORY, HAS_COUNTRY, \
    HAS_ACTOR, HAS_TAG, HAS_PRODUCT, HAS_PACKAGE, HAS_HOMEPAGE, HAS_CONTENT_CORE
from ingestor.content_profile.content_similarity import cluster_data_to_df, generate_new_features, \
    generate_tfidf_matrix, calculate_cosine_similarity, cluster_data_to_single_df, combine_features, create_tfidf_df, \
    calculate_single_cosine_similarity
from ingestor.content_profile.network.content_utils import ContentUtils


class ContentNetworkGenerator:

    def __init__(
            self,
            connection_class: GraphDbConnection
    ):
        self.graph = GraphDb.from_connection(connection_class)

    @classmethod
    def from_connection_uri(
            cls,
            connection_uri: str
    ) -> ClassVar:
        """Create new object based on connection uri
        :param connection_uri: string connection uri
        :return: object class
        """
        return cls(GraphDbConnection.from_uri(connection_uri))

    @classmethod
    def from_connection_class(
            cls,
            connection_class: GraphDbConnection
    ) -> ClassVar:
        """Define new class based on object connection
        :param connection_class: object connection class
        :return: object class
        """
        return cls(connection_class)

    def create_content_homepage_network(self, payload: DataFrame):
        content_nodes = []
        if HOMEPAGE in payload.columns:
            for props in payload[HOMEPAGE].loc[0]:
                static_node = Node(**{LABEL: HOMEPAGE, PROPERTIES: props})
                home_page = self.graph.find_node(static_node)

                if home_page[0].properties[IS_CONNECTED].lower() == YES:
                    content_label = PAY_TV_CONTENT

                else:
                    content_label = NO_PAY_TV_CONTENT
                print("Generating content to homepage network for content label {0}".format(content_label))
                for property_num, property_val in payload.iterrows():
                    content_node_dict = {}
                    if property_val[CONTENT_ID] and property_val[CONTENT_ID] is not None and property_val[
                        CONTENT_ID] != '':
                        content_node_property = content_node_properties(property_val)
                        content_node = Node(**{LABEL: content_label, PROPERTIES: content_node_property})
                        content_node = self.graph.create_node(content_node)
                        if len(home_page) == 0:
                            print("Record not available in static network for node {0}".format(static_node))
                        else:
                            self.graph.create_relationship_without_upsert(content_node, home_page[0], Relationship(
                                **{RELATIONSHIP: HAS_HOMEPAGE}))
                        content_node_dict[LABEL] = content_label
                        content_node_dict[HOMEPAGE_ID] = home_page[0].properties[HOMEPAGE_ID]
                        content_node_dict[CONTENT] = content_node
                        content_nodes.append(content_node_dict)

        else:
            print("Homepage feature is not available")
        return content_nodes

    def child_network_generator(self, content_node, feature, label, relationship, payload: DataFrame):
        if feature in payload.columns:
            for props in payload[feature].loc[0]:
                static_node = Node(**{LABEL: label, PROPERTIES: props})
                node_in_graph = self.graph.find_node(static_node)
                if len(node_in_graph) == 0:
                    print("Record not available in static network for node {0}".format(static_node))
                else:
                    self.graph.create_relationship_without_upsert(content_node, node_in_graph[0],
                                                                  Relationship(**{RELATIONSHIP: relationship}))
        else:
            print("Feature not available")
        return content_node

    def child_network_generator_2(self, content_node, feature, label, relationship, payload: DataFrame):
        if feature in payload.columns:
            for props in payload[feature].loc[0]:
                final_content_core_props = ContentUtils.prepare_content_core_properties(props, self.graph)
                final_content_core_node = Node(**{LABEL: label, PROPERTIES: final_content_core_props})

                final_content_core_node = self.graph.create_node(final_content_core_node)

                self.graph.create_relationship_without_upsert(content_node, final_content_core_node,
                                                              Relationship(**{RELATIONSHIP: relationship}))
        else:
            print("Feature not available")

        return content_node



    def content_creator_updater_network(self, payload: DataFrame) -> bool:
        print("Generating content node")
        content_nodes = self.create_content_homepage_network(payload=payload)
        if len(content_nodes) > 0:
            for record in content_nodes:
                content_label = record["label"]
                content_node = record["content"]
                content_homepage_id = record["homepage_id"]
                print("Generating content to category network")
                content_node = self.child_network_generator(content_node, CATEGORY, CATEGORY, HAS_CATEGORY,
                                                            payload=payload)
                print("Generating content to subcategory network")
                content_node = self.child_network_generator(content_node, SUBCATEGORY, SUBCATEGORY, HAS_SUBCATEGORY,
                                                            payload=payload)
                print("Generating content to country network")
                content_node = self.child_network_generator(content_node, COUNTRY, COUNTRY, HAS_COUNTRY,
                                                            payload=payload)
                print("Generating content to actor network")
                content_node = self.child_network_generator(content_node, ACTORS, ACTOR, HAS_ACTOR, payload=payload)
                print("Generating content to tag network")
                content_node = self.child_network_generator(content_node, TAGS, TAGS, HAS_TAG, payload=payload)
                print("Generating content to product network")
                content_node = self.child_network_generator(content_node, PRODUCTS, PRODUCT, HAS_PRODUCT,
                                                            payload=payload)
                print("Generating content to package network")
                content_node = self.child_network_generator(content_node, PACKAGES, PACKAGE, HAS_PACKAGE,
                                                            payload=payload)
                print("Generating content to content core network")
                content_node = self.child_network_generator_2(content_node, CONTENT_CORE, CONTENT_CORE,
                                                              HAS_CONTENT_CORE,
                                                              payload=payload)
                # print("Updating similarity property in content nodes")
                # content_node = self.add_content_similarity_property(content_node, content_label, content_homepage_id, payload=payload)
        else:
            print("No content node is available")
        return True

    def specified_homepage_network_data(self, connected_flag, content_homepage_id):
        homepage_network = []
        list_homepage_ids = []
        query_network = self.graph.custom_query(f'''
                    g.V().has('{HOMEPAGE_ID}',{content_homepage_id}).has('{IS_CONNECTED}',
                                '{connected_flag}').in('{HAS_HOMEPAGE}').valueMap().by(unfold()).toList()
                    ''', payload={
            HOMEPAGE_ID: content_homepage_id,
            IS_CONNECTED: connected_flag,
            HAS_HOMEPAGE: HAS_HOMEPAGE
        })
        homepage_network.append(query_network)
        list_homepage_ids.append(content_homepage_id)
        return homepage_network, list_homepage_ids

    def add_similarity_property(self, content_node, list_dict_content_similarities, list_homepage_id, content_label):
        content_similarity_property = {}
        for (homepage_id, dict_content_similarities) in zip(list_homepage_id, list_dict_content_similarities):
            for key, value in dict_content_similarities.items():
                output_type = {homepage_id: value}
                content_similarity_property.setdefault(key, [])
                content_similarity_property[key].append(output_type)

        for content_id, sim_property in content_similarity_property.items():
            node_to_update = Node(**{LABEL: content_label, PROPERTIES: {CONTENT_ID: content_id}})
            query_content_node = self.graph.find_node(node_to_update)
            dict_similarity_score = dict(sum(map(list, map(dict.items, sim_property)), []))
            self.graph.update_node_property(query_content_node[0], {CC_SIMILARITY_SCORE: dict_similarity_score})
        return content_node

    def get_all_content(self, content_label):
        query = self.graph.custom_query(f'''
        g.V().hasLabel('{content_label}').valueMap().by(unfold()).toList()
        ''', payload={
            content_label: content_label
        })
        return query

    def add_all_content_similarity_property(self, content_node, all_content_dict_cos_sim, content_label):
        for key, value in all_content_dict_cos_sim.items():
            node_to_update = Node(**{LABEL: content_label, PROPERTIES: {CONTENT_ID: key}})
            query_content_node = self.graph.find_node(node_to_update)
            self.graph.update_node_property(query_content_node[0], {ALL_SIMILARITY_SCORE: value})
        return content_node

    def add_content_similarity_all_content(self, content_node, content_label):
        all_content_cluster = self.get_all_content(content_label)
        all_content_df = cluster_data_to_single_df(all_content_cluster)
        all_content_new_df = combine_features(all_content_df)
        all_content_tfidf = create_tfidf_df(all_content_new_df)
        all_content_dict_cos_sim = calculate_single_cosine_similarity(all_content_tfidf)
        output_all_content_similarity = self.add_all_content_similarity_property(content_node, all_content_dict_cos_sim,
                                                                                 content_label)
        return output_all_content_similarity

    def add_content_similarity_property(self, content_node, content_label, content_homepage_id, payload):
        # Calculate Content-Similarity in Homepage_id Wise
        if content_label == PAY_TV_CONTENT:
            connected_flag = YES
        else:
            connected_flag = NO

        list_homepage_network, list_homepage_ids = self.specified_homepage_network_data(connected_flag, content_homepage_id)
        list_dataframe_homepage = cluster_data_to_df(list_homepage_network)
        list_new_df_homepage = generate_new_features(list_dataframe_homepage)
        list_tfidf_df = generate_tfidf_matrix(list_new_df_homepage)
        list_dict_content_similarities = calculate_cosine_similarity(list_tfidf_df)
        self.add_similarity_property(content_node, list_dict_content_similarities, list_homepage_ids, content_label)
        self.add_content_similarity_all_content(content_node, content_label)
        return content_node
