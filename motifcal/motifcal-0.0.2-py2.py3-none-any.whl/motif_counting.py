""" ESU motif counting."""

import networkx as nx
from tqdm import tqdm
import pandas as pd
import time

# Download all motifs
# base_cwd = os.getcwd().split('Remote')[0]+'Remote'
# sys.path.append("%s/graph/graph_features"%base_cwd)
from motif_list import motifs, new_gen_motifs
print("\nDownloading all motifs.\n")
G_motiflist = dict()
for k in range(2,6):
    G_motiflist[k] = motifs(k)


class ESU(object):
    """
    ESU Algorithms to calculate motif counting.
    """

    def __init__(self, graph, k_count, G_motiflist, if_print=False):
        """
        :param graph: NetworkX object.
        :param k_count: Number of motif nodes.
        :param G_motif_list: Motif list, dict 形式，对应不同的k_count.
        """
        if k_count >= 6:
            self.G_motifs = new_gen_motifs(k_count)
        else:
            self.G_motifs = G_motiflist[k_count]
        self.graph = graph
        self.k_count = k_count
        self.isolates = list(nx.isolates(self.graph))
        self.if_print = if_print
        self.change_id = False

    def _extension_group(self, v_node, node=None):
        """
        计算节点集的邻居节点（大于{u}).
        :param node: Source node. 一个点
        :return nodes list
        """
        node = node if node is not None else v_node
        # nodes_set = set(nx.neighbors(self.graph, node))
        #set(chain.from_iterable([list(nx.neighbors(self.graph, node)) for node in nodes]))
        return {v for v in set(nx.neighbors(self.graph, node)) if v>v_node}


    def _new_extension(self, v_node, subgraph_set, extension_set):
        '''
        计算 extension set
        :param v_node: key node
        :param subgraph_set:
        :param extension_set:
        :return: list
        '''
        new_extension = []
        redeem_set = set()
        for element in extension_set:
            redeem_set.add(element)
            new_subgraph_set = subgraph_set.copy()
            new_subgraph_set.add(element)
            add_extension_set = self._extension_group(v_node,element)
            new_extension_set = add_extension_set | extension_set
            new_extension_set = new_extension_set - redeem_set - new_subgraph_set
            new_extension.append([v_node, new_subgraph_set, new_extension_set])
        return new_extension



    def change_nodes_id(self):

        degree = pd.DataFrame(nx.degree(self.graph), columns=['map_index', 'degree'])
        degree = degree.sort_values('degree').reset_index(drop=True)
        nodes_dict = dict(zip(degree['map_index'], range(0, degree.shape[0])))
        edges = pd.DataFrame(self.graph.edges(), columns=['start_id', 'end_id'])
        edges['start_id'] = edges['start_id'].map(nodes_dict)
        edges['end_id'] = edges['end_id'].map(nodes_dict)
        edges = [(d[0],d[1]) for v, d in edges.iterrows()]

        new_graph = nx.Graph()
        new_graph.add_nodes_from(nodes_dict.values())
        new_graph.add_edges_from(edges)

        self.graph = new_graph
        self.nodes_dict = nodes_dict
        self.change_id = True


    def _calculate_motifs(self):
        """
        Enumerating pairwise motif counts.
        """
        print("\nCalculating motifs.\n") if self.if_print else None

        self.change_nodes_id() if self.graph.number_of_nodes()>50 else None

        # 分割子图
        sub_graph = [[v,{v},self._extension_group(v)] for v in self.graph.nodes() if v not in self.isolates]
        sub_graph = [x for x in sub_graph if len(x[2])>0]   # 邻居节点为空的部分删除

        #计算每一步的extension set 和subgraph set
        while len(sub_graph[0][1])<(self.k_count-1):
            subgraph_list = []
            #sub_graph = [x for x in sub_graph if len(x[2])>0]
            if self.if_print:
                for graph in tqdm(sub_graph):
                    subgraph_list += self._new_extension(graph[0], graph[1], graph[2])
            else:
                for graph in sub_graph:
                    subgraph_list += self._new_extension(graph[0], graph[1], graph[2])
            sub_graph = [x for x in subgraph_list if len(x[2])>0]
            if len(sub_graph) == 0:
                break

        t = []
        for graph in sub_graph:
            t += [graph[1]|{element} for element in graph[2]]

        self.graph_nodeslist = t
            #[k for u,k,v in sub_graph]
        self.graphlist = [nx.subgraph(self.graph,g) for g in self.graph_nodeslist]


    def _judge_isomorphic(self):
        """
        Comparing graphs to judge whether they are isomorphic.
        """
        print("\nJudging isomorphic.\n") if self.if_print else None
        motif_statistic = dict()
        edges_dict = dict(zip(self.graphlist,[x.number_of_edges() for x in self.graphlist]))
        if len(self.graphlist)>0:
            for G_motif in self.G_motifs:
                number_of_edges = G_motif.number_of_edges()
                use_graphlist = [k for k, v in edges_dict.items() if v == number_of_edges] # 查询同构较慢，先筛选一次
                use_graphlist = [x for x in use_graphlist if nx.is_isomorphic(x, G_motif)]  #判断是否同构
                motif_statistic[str(G_motif.edges())] = len(use_graphlist)
                if self.if_print and len(use_graphlist) > 0:
                    print("cal motif count for: %s, %d" % (G_motif.edges(),len(use_graphlist)))

        self.motif_statistic = motif_statistic



    def fit(self):
        """
        Stat motifs pattern the target graph.
        """
        start_t = time.time()
        if (self.graph.number_of_nodes()-len(self.isolates))<self.k_count:
            self.motif_statistic = []
        else:
            #self.if_print = True if self.graph.number_of_nodes()>100 else self.if_print
            self._calculate_motifs()
            self._judge_isomorphic()

        end_t = time.time()
        self.take_time = (end_t - start_t)
        return self.motif_statistic

if __name__ == '__main__':
    # G=nx.Graph()
    # G.add_nodes_from([1,2,3,4,5])
    # G.add_edges_from([(1, 2), (1, 3),(2,4),(2,3),(3,5)])
    G = nx.ladder_graph(4)
    # G = nx.DiGraph([(0, 1), (1, 2), (2, 3),(3, 4),(4, 5),(1, 5),(3, 5),(5, 2)])
    cal_motifs = ESU(G, 3, G_motiflist, if_print=True)
    cal_motifs.fit()