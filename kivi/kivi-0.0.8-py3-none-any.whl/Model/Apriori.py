# -*- coding: utf-8 -*-
# @Time    : 2020/4/8 16:23
# @Author  : Chensy Cao
# @Email   : chensy.cao@zjtlcb.com
# @FileName: Apriori.py
# @Software: PyCharm

class Apriori:
    def __init__(self, dataSet, minSupport=.5, ruleSupport=.7, is_show_rule=False):
        self.dataSet = dataSet
        self.minSupport = minSupport
        self.ruleSupport = ruleSupport
        self.is_show_rule = is_show_rule
        # 计算支持项，全部支持项与最小支持项
        self.L, self.supportData = self.apriori()

        # 计算关联规则
        self.rules = self.generateRules(self.L, self.supportData, self.ruleSupport)


    # C1 是大小为1的所有候选项集的集合
    def createC1(self, ):
        C1 = []
        for transaction in self.dataSet:
            for item in transaction:
                if not [item] in C1:
                    C1.append([item])  # store all the item unrepeatly

        C1.sort()
        # return map(frozenset, C1); frozen set, user can't change it.
        return list(map(frozenset, C1))


    def scanD(self, D, Ck):
        # 这是一个计数器，dict类型
        ssCnt = {}
        for tid in D:
            for can in Ck:
                # can 是否是 tid 的子集
                if can.issubset(tid):
                    # if not ssCnt.has_key(can):
                    if not can in ssCnt:
                        ssCnt[can] = 1
                    else:
                        ssCnt[can] += 1
        numItems = float(len(D))
        retList = []
        supportData = {}
        for key in ssCnt:
            support = ssCnt[key] / numItems  # compute support
            if support >= self.minSupport:
                retList.insert(0, key)
            supportData[key] = support
        return retList, supportData


    # apriori
    def apriori(self,):
        # 单个元素
        C1 = self.createC1()
        # 不重复的数据集
        D = list(map(set, self.dataSet))  # python3
        # 生成最小支持度的L1
        L1, supportData = self.scanD(D, C1)  # 单项最小支持度判断 0.5，生成L1
        L = [L1]
        k = 2

        while (len(L[k - 2]) > 0):  # 创建包含更大项集的更大列表,直到下一个大的项集为空
            Ck = self.aprioriGen(L[k - 2], k)  # Ck
            Lk, supK = self.scanD(D, Ck)  # get Lk
            supportData.update(supK)
            L.append(Lk)
            k += 1  # 继续向上合并 生成项集个数更多的
        return L, supportData


    # total apriori
    def aprioriGen(self, Lk, k):  # 组合，向上合并
        # creates Ck 参数：频繁项集列表 Lk 与项集元素个数 k
        retList = []
        lenLk = len(Lk)
        for i in range(lenLk):
            for j in range(i + 1, lenLk):  # 两两组合遍历
                L1 = list(Lk[i])[:k - 2]
                L2 = list(Lk[j])[:k - 2]
                L1.sort()
                L2.sort()
                if L1 == L2:  # 若两个集合的前k-2个项相同时,则将两个集合合并
                    retList.append(Lk[i] | Lk[j])  # set union
        return retList


    # 生成关联规则
    def generateRules(self, L, supportData, minConf=0.7):
        '''
        L: 频繁项集列表
        supportData: 包含那些频繁项集支持数据的字典
        minConf: 最小可信度阈值
        '''

        # 存储所有的关联规则
        bigRuleList = []

        # 只获取有两个或者更多集合的项目，从1,即第二个元素开始，L[0]是单个元素的
        for i in range(1, len(L)):
            # 两个及以上的才可能有关联一说，单个元素的项集不存在关联问题
            for freqSet in L[i]:
                H1 = [frozenset([item]) for item in freqSet]
                # 该函数遍历L中的每一个频繁项集并对每个频繁项集创建只包含单个元素集合的列表H1
                if (i > 1):
                    # 如果频繁项集元素数目超过2,那么会考虑对它做进一步的合并
                    self.rulesFromConseq(freqSet, H1, supportData, bigRuleList, minConf)
                else:  # 第一层时，后件数为1
                    self.calcConf(freqSet, H1, supportData, bigRuleList, minConf)  # 调用函数2
        return bigRuleList


    # 生成候选规则集合：计算规则的可信度以及找到满足最小可信度要求的规则
    def calcConf(self, freqSet, H, supportData, brl, minConf=0.7):
        # 针对项集中只有两个元素时，计算可信度
        prunedH = []  # 返回一个满足最小可信度要求的规则列表
        for conseq in H:  # 后件，遍历 H中的所有项集并计算它们的可信度值
            conf = supportData[freqSet] / supportData[freqSet - conseq]  # 可信度计算，结合支持度数据
            if conf >= minConf:
                if self.is_show_rule:
                    print(freqSet - conseq, '-->', conseq, 'conf:', conf)
                # 如果某条规则满足最小可信度值,那么将这些规则输出到屏幕显示
                brl.append((freqSet - conseq, conseq, conf))  # 添加到规则里，brl 是前面通过检查的 bigRuleList
                prunedH.append(conseq)  # 同样需要放入列表到后面检查
        return prunedH

    # 合并
    def rulesFromConseq(self, freqSet, H, supportData, brl, minConf=0.7):
        # 参数:一个是频繁项集,另一个是可以出现在规则右部的元素列表 H
        m = len(H[0])
        if (len(freqSet) > (m + 1)):  # 频繁项集元素数目大于单个集合的元素数
            Hmp1 = self.aprioriGen(H, m + 1)  # 存在不同顺序、元素相同的集合，合并具有相同部分的集合
            Hmp1 = self.calcConf(freqSet, Hmp1, supportData, brl, minConf)  # 计算可信度
            if (len(Hmp1) > 1):  # 满足最小可信度要求的规则列表多于1,则递归
                self.rulesFromConseq(freqSet, Hmp1, supportData, brl, minConf)
