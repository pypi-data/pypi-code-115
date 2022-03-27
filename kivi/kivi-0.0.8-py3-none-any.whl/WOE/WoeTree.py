# -*- coding:utf-8 -*-
# @Time : 2022/3/24 9:49
# @Author: Chensy
# @File : WoeTree.py
# @Email: chensy.cao@foxmail.com

from .WOE import WOE, pd, np

class TreeBins(WOE):
    """
    描述：决策树分箱
    """
    def __init__(self, variables, target, bins=5, fill_bin=True):
        """
        描述：决策树分箱方法，使用决策树最优 entropy 进行分箱分析。

        :param variables: 待分箱变量
        :param target: 目标标签变量
        :param bins: 决策树分箱中最大的叶子结点数量，一般对应的是最终分箱数量，默认为 5 。
        :param fill_bin: 在各分箱中偶发性会出现 good 或 bad 为 0 的情况，默认 fill_pos 为 True ，为该分箱填充 0.5。

        示例：
        >>> woe = TreeBins(variables, target, bins=5, fill_bin=True)
        >>> woe.fit()
        """
        self.bins = bins
        self.max_leaf_nodes = bins
        self.data_init(variables, target, fill_bin=fill_bin)

    def GetCutoffpoint(self, ):
        """

        :return:
        """
        from sklearn.tree import DecisionTreeClassifier

        # min_samples_leaf 叶子节点样本数量最小占比
        clf = DecisionTreeClassifier(
            criterion='entropy', max_leaf_nodes=self.max_leaf_nodes, min_samples_leaf=0.05)
        clf.fit(self.variables.to_numpy().reshape(-1, 1), self.target.to_numpy().reshape(-1, 1))

        n_nodes = clf.tree_.node_count
        left = clf.tree_.children_left
        right = clf.tree_.children_right
        threshold = clf.tree_.threshold

        self.cutoffpoint = sorted([-float('inf')] + [threshold[i] for i in range(n_nodes) if left[i] != right[i]] + [float('inf')])


    def fit(self, score=True, origin_border=False, order=None):
        """

        :param score: 是否增加 WOE score。
        :param origin_border: 是否增加 分箱中的最大值与最小值。
        :param order: 是否增加单调性判断。
        :return: DataFrame WOE result.
        """
        self.GetCutoffpoint()

        value_cut, self.fix_cutoffpoint = pd.cut(
            self.variables, self.cutoffpoint, include_lowest=True, retbins=True)

        # 分箱与原值进行合并
        Bucket = pd.DataFrame({
            'variables': self.variables,
            'target': self.target,
            'Bucket': value_cut,
        }).groupby('Bucket', as_index=True)
        # 计算 woe iv

        self.woe_iv_res(Bucket, score=score, origin_border=origin_border, order=order)
        return self.res

