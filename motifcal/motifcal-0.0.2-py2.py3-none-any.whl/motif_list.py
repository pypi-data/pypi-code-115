import random
import time
import networkx as nx
import itertools
import pandas as pd
import sys,os
from tqdm import tqdm



# naive list, ignore this method, just for contrast!!!
def motifs(k, if_direction=False) -> [nx.Graph]:
    """
    return list of motifs
    :param k:
    :param if_direction: 是否为有向图
    :return:
    """
    if k == 2:
        # 1
        if if_direction:
            G = nx.DiGraph()
            G.add_edges_from([(0, 1)])
        else:
            G = nx.Graph()
            G.add_edges_from([(0, 1)])
        return [G]
    elif k == 3:
        motifs = []
        if if_direction:
            # 1
            G = nx.DiGraph()
            G.add_edges_from([(0, 1),(0, 2)])
            motifs.append(G)
            # 2
            G = nx.DiGraph()
            G.add_edges_from([(1, 0),(2, 0)])
            motifs.append(G)
            # 3
            G = nx.DiGraph()
            G.add_edges_from([(1, 2),(2, 0)])
            motifs.append(G)
            # 4
            G = nx.DiGraph()
            G.add_edges_from([(1, 0),(0, 2),(2, 0)])
            motifs.append(G)
            # 5
            G = nx.DiGraph()
            G.add_edges_from([(0, 1),(1, 0),(0, 2)])
            motifs.append(G)
            # 6
            G = nx.DiGraph()
            G.add_edges_from([(0, 1),(0, 2),(1, 0),(2, 0)])
            motifs.append(G)
            # 7
            G = nx.DiGraph()
            G.add_edges_from([(0, 1),(0, 2),(1, 2)])
            motifs.append(G)
            # 8
            G = nx.DiGraph()
            G.add_edges_from([(1, 0),(0, 2),(2, 1)])
            motifs.append(G)
            # 9
            G = nx.DiGraph()
            G.add_edges_from([(0, 1),(0, 2),(1, 2),(2, 1)])
            motifs.append(G)
            # 10
            G = nx.DiGraph()
            G.add_edges_from([(1, 0),(2, 0),(1, 2),(2, 1)])
            motifs.append(G)
            # 11
            G = nx.DiGraph()
            G.add_edges_from([(0, 1),(1, 2),(0, 2),(2, 0)])
            motifs.append(G)
            # 12
            G = nx.DiGraph()
            G.add_edges_from([(1, 0),(0, 2),(2, 0),(1, 2),(2, 1)])
            motifs.append(G)
            # 13
            G = nx.DiGraph()
            G.add_edges_from([(0, 1),(1, 0),(0, 2),(2, 0),(1, 2),(2, 1)])
            motifs.append(G)
        else:
            # 1
            G = nx.Graph()
            G.add_edges_from([(0, 1), (1, 2)])
            motifs.append(G)
            # 2
            G = nx.Graph()
            G.add_edges_from([(0, 1), (1, 2), (0, 2)])
            motifs.append(G)
        return motifs
    elif k == 4:
        motifs = []
        if if_direction:
            raise NotImplementedError("too big")
        else:
            # 1
            G = nx.Graph()
            G.add_edges_from([(0, 1), (1, 2), (2, 3)])
            motifs.append(G)
            # 2
            G = nx.Graph()
            G.add_edges_from([(0, 1), (1, 2), (1, 3)])
            motifs.append(G)
            # 3
            G = nx.Graph()
            G.add_edges_from([(0, 1), (1, 2), (1, 3), (2, 3)])
            motifs.append(G)
            # 4
            G = nx.Graph()
            G.add_edges_from([(0, 1), (1, 2), (2, 3), (0, 3)])
            motifs.append(G)
            # 5
            G = nx.Graph()
            G.add_edges_from([(0, 1), (1, 2), (2, 3), (0, 3), (0, 2)])
            motifs.append(G)
            # 6
            G = nx.Graph()
            G.add_edges_from([(0, 1), (1, 2), (2, 3), (0, 3), (0, 2), (1, 3)])
            motifs.append(G)
        return motifs
    elif k == 5:
        motifs = []
        if if_direction:
            raise NotImplementedError("too big")
        else:
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 3), (1, 4), (2, 3)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 3), (2, 3), (3, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 2), (1, 2), (2, 3), (2, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 3), (0, 4), (2, 3), (3, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 4), (1, 2), (1, 3), (1, 4), (2, 3)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 2), (1, 2), (1, 3), (2, 4), (3, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 2), (0, 3), (0, 4), (1, 2)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 3), (1, 2), (2, 4), (3, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 3), (0, 4), (1, 3), (2, 3), (2, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 3), (0, 4), (1, 3), (1, 4), (2, 3)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 3), (1, 2), (1, 3), (1, 4), (2, 3)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 3), (1, 2), (1, 3), (1, 4), (2, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 4), (1, 2), (1, 3), (2, 4), (3, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 4), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 2), (0, 3), (0, 4), (1, 3), (2, 3), (3, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 2), (0, 4), (1, 3), (1, 4), (2, 3), (2, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 3), (1, 2), (1, 3), (1, 4), (2, 4), (3, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4)])
            motifs.append(G)
            G = nx.Graph()
            G.add_edges_from([(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)])
            motifs.append(G)
        return motifs

    else:
        raise NotImplementedError("too big")
        # 6 112
        # 7 853
        # if you want to enumerate motifs then run the following commands
        num_motifs = 112
        motifs = []
        start = time.time()
        while len(motifs) < num_motifs:
            p_min = (k - 1) / (k ** 2)
            G = nx.erdos_renyi_graph(n=k, p=random.random() * (1 - p_min) + p_min)
            if nx.is_connected(G):
                is_new = True
                for F in motifs:
                    if nx.is_isomorphic(G, F):
                        is_new = False
                        break
                if is_new:
                    motifs.append(G)
                    print('len:', len(motifs))
        print(u_time.time2str(time.time() - start))

        # sort
        motifs = sorted(motifs, key=lambda G: len(nx.edges(G)))

        for F in motifs:
            print('G = nx.Graph()')
            print('G.add_edges_from(', F.edges, ')')
            print('motifs.append(G)')

        exit()

        return motifs

# normal method fit for all k, but very slow, ignore this method!!!
def gen_motifs(k, if_direction=False) -> [nx.Graph]:

    # 计算边
    nodes = list(range(k))
    single_edges = list(itertools.permutations(nodes, 2)) if if_direction else list(itertools.combinations(nodes, 2))
    graphlist = []
    for m in range(len(single_edges)):
        for i in itertools.combinations(single_edges, m+1):
            g = nx.DiGraph() if if_direction else nx.Graph()
            g.add_nodes_from(nodes)
            g.add_edges_from(list(i))
            graphlist.append(g) if nx.is_connected(nx.to_undirected(g)) else None  # 将有向图转为无向图，查看图形的连通性

    # 删除同构图形
    remove_graphlist = []
    for item in itertools.combinations(graphlist, 2):
        if item[0] in remove_graphlist:
            continue
        remove_graphlist.append(item[0]) if nx.is_isomorphic(item[0], item[1]) else None
    motifs = list(set(graphlist).difference(set(remove_graphlist)))

    return motifs


'''
faster method fit for k<=7, use this method.
1.6h for k=5, direction=True, result has already stored in mysql.
can be modified into multi-process.
'''
def new_gen_motifs(k, if_direction=False) -> [nx.Graph]:

    if k<=7:
        if if_direction==False:
            graphlist = nx.graph_atlas_g()  #所有非同构无向图
            motifs = [i for i in graphlist if i.number_of_nodes() == k and nx.is_connected(i)]
            return motifs
        else:
            motifs = new_gen_motifs(k,if_direction=False)
            all_graphlist = []
            for motif in tqdm(motifs):
                edges = list(motif.edges())
                new_edges = [[[i],[(i[1], i[0])],[i,(i[1],i[0])]] for i in edges]
                graphlist = []
                for result in itertools.product(*new_edges):
                    g = nx.DiGraph()
                    g.add_edges_from(list(list(itertools.chain.from_iterable(result))))
                    isomorphic_list = [g1 for g1 in graphlist if nx.is_isomorphic(g,g1)]  #判断和之前是否同构
                    graphlist.append(g) if len(isomorphic_list)==0 else None
                all_graphlist.append(graphlist)
            all_graphlist = list(itertools.chain.from_iterable(all_graphlist))
            return all_graphlist
    else:
        raise NotImplementedError("too big")


if __name__ == "__main__":

    base_cwd = os.getcwd().split('Remote')[0] + 'Remote'
    sys.path.append("%s/mypackages" % base_cwd)
    from SQLProcess import SQLProcess

    TEST_MODE = False
    Polardb_zstp = SQLProcess('polardb-test-pub.mysql.polardb.rds.aliyuncs.com', '3306', 'zstp', 'thPa_2020529', 'zstp')
    Polardb_zstp.test_mode = False

    motif_frame = pd.DataFrame()
    for k in range(2, 6):
        for direction in (True, False):
            motifs = new_gen_motifs(k,if_direction=direction)
            print(len(motifs))
            add_motif_frame = pd.DataFrame({'motif':[str(i.edges()) for i in motifs],'k_id':list(range(1,len(motifs)+1))})
            add_motif_frame['motif_type'] = k
            add_motif_frame['if_direction'] = int(direction)
            motif_frame = motif_frame.append(add_motif_frame)

    Polardb_zstp.save_table(motif_frame,'graph_motif_list',exists_flag='append')

    # # 检验是否图形有同构的
    # motif_graph = motifs(3, if_direction=True)
    # for item in itertools.combinations(motif_graph, 2):
    #     print('Error: %s, %s' % (str(item[0].edges), str(item[1].edges))) if nx.is_isomorphic(item[0], item[1]) else None

