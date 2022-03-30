class Object:
    def __init__(self,I):
        self.I=I
        self.Start=[]
        self.End=[]
        self.T=[]
        self.assign_for=[]

    def _add(self,S,E,obs,t):
        #obs:安排的对象
        self.Start.append(S)
        self.End.append(E)
        self.Start.sort()
        self.End.sort()
        self.T.append(t)
        self.assign_for.insert(self.End.index(E),obs)

    def idle_time(self):
        Idle=[]
        try:
            if self.Start[0]!=0:
                Idle.append([0,self.Start[0]])
            K=[[self.End[i],self.Start[i+1]] for i in range(len(self.End)) if self.Start[i+1]-self.End[i]>0]
            Idle.extend(K)
        except:
            pass
        return  Idle
import random
import numpy as np

# Total_Machine=[10,20,30,40,50]  #全部机器
# Initial_Job_num=5              #初始工件个数
# Job_insert=[50,100,200]         #工件新到达个数
# DDT=[0.5,1.0,1.5]               #工件紧急程度
# E_ave=[50,100,200]              #指数分布

#随机初始化
'''
# def Init_Job(M_num,Initial_Job_num):
#     """
#             :param M_num: Machine Number
#             :param E_ave: exponetional distribution
#             :param New_insert: New Job insert
#             :param DDT:DDT
#             :return: Processing time,A:New Job arrive time,
#                                         D:Deliver time,
#                                         M_num: Machine Number,
#                                         Op_num: Operation Number,
#                                         J_num:Job NUMBER
#     """
#     Op_num = [random.randint(3, 8) for i in range(Initial_Job_num)]
#     # 生成工序数
#     Processing_time = []
#     for i in range(Initial_Job_num):
#         Job_i = []
#         for j in range(Op_num[i]):
#             k = random.randint(1, M_num - 2)
#             T = list(range(M_num))
#             random.shuffle(T)
#             T = T[0:k + 1]
#             O_i = list(np.ones(M_num) * (-1))
#             for M_i in range(len(O_i)):
#                 if M_i in T:
#                     O_i[M_i] = random.randint(5, 15)
#             Job_i.append(O_i)
#         Processing_time.append(Job_i)
#     O_num = sum(Op_num)
#     J = dict(enumerate(Op_num))
#     J_num = Initial_Job_num
#
#     return Processing_time, M_num, Op_num, J, O_num, J_num

# Processing_time,M_num,Op_num,J,O_num,J_num=Init_Job(5,10)
'''


# MK01
'''
Processing_time = [
    [[5, -1, 4, -1, -1, -1], [-1, 1, 5, -1, 3, -1], [-1, -1, 4, -1, -1, 2], [1, 6, -1, -1, -1, 5], [-1, -1, 1, -1, -1, -1], [-1, -1, 6, 3, -1, 6]],
    [[-1, 6, -1, -1, -1, -1], [-1, -1, 1, -1, -1, -1], [2, -1, -1, -1, -1, -1], [-1, 6, -1, 6, -1, -1], [1, 6, -1, -1, -1, 5],],
    [[-1, 6, -1, -1, -1, -1], [-1, -1, 4, -1, -1, 2], [1, 6, -1, -1, -1, 5], [-1, 6, 4, -1, -1, 6], [1, -1, -1, -1, 5, -1], ],
    [[1, 6, -1, -1, -1, 5], [-1, 6, -1, -1, -1, -1], [-1, -1, 1, -1, -1, -1], [-1, 1, 5, -1, 3, -1], [-1, -1, 4, -1, -1, 2], ],
    [[-1, 1, 5, -1, 3, -1], [1, 6, -1, -1, -1, 5], [-1, 6, -1, -1, -1, -1], [5, -1, 4, -1, -1, -1], [-1, 6, -1, 6, -1, -1], [-1, 6, 4, -1, -1, 6]],
    [[-1, -1, 4, -1, -1, 2], [2, -1, -1, -1, -1, -1], [-1, 6, 4, -1, -1, 6], [-1, 6, -1, -1, -1, -1], [1, 6, -1, -1, -1, 5], [3, -1, -1, 2, -1, -1]],
    [[-1, -1, -1, -1, -1, 1], [3, -1, -1, 2, -1, -1], [-1, 6, 4, -1, -1, 6], [6, 6, -1, -1, 1, -1], [-1, -1, 1, -1, -1, -1], ],
    [[-1, -1, 4, -1, -1, 2], [-1, 6, 4, -1, -1, 6], [1, 6, -1, -1, -1, 5], [-1, 6, -1, -1, -1, -1], [-1, 6, -1, 6, -1, -1], ],
    [[-1, -1, -1, -1, -1, 1], [1, -1, -1, -1, 5, -1], [-1, -1, 6, 3, -1, 6], [2, -1, -1, -1, -1, -1], [-1, 6, 4, -1, -1, 6], [-1, 6, -1, 6, -1, -1]],
    [[-1, -1, 4, -1, -1, 2], [-1, 6, 4, -1, -1, 6], [-1, 1, 5, -1, 3, -1], [-1, -1, -1, -1, -1, 1], [-1, 6, -1, 6, -1, -1], [3, -1, -1, 2, -1, -1]]
                   ]
M_num = 6
Op_num = [6,5,5,5,6,6,5,5,6,6]
J = {0:6,1:5,2:5,3:5,4:6,5:6,6:5,7:5,8:6,9:6}
O_num = 55
J_num = 10
'''


#MK02

Processing_time =[
    [[3, 2, 3, 5, 3, 6], [-1, -1, 4, -1, -1, 5], [1, 6, 3, 3, 6, 5], [-1, 6, -1, -1, -1, -1], [-1, -1, -1, -1, 6, 3], [-1, 1, 2, -1, 4, -1]],
    [[3, 4, -1, 2, 6, 1], [-1, -1, -1, -1, 6, 3], [-1, -1, -1, -1, 2, -1], [-1, 4, 3, -1, -1, -1], [-1, 1, 2, -1, 4, -1], [3, 2, 3, 5, 3, 6]],
    [[1, 6, 3, 3, 6, 5], [2, 4, 6, 6, 3, 6], [-1, 1, 2, -1, 4, -1], [4, 3, 5, -1, 2, 3], [5, 4, 3, 1, 5, 3], [4, -1, 6, 6, 3, 3]],
    [[4, 3, 5, -1, 2, 3], [3, 4, -1, 2, 6, 1], [-1, 6, -1, -1, -1, -1], [1, 6, 3, 3, 6, 5], [4, 3, -1, 5, 4, 3], [5, 4, 3, 1, 5, 3]],
    [[2, 4, 6, 6, 3, 6], [4, 3, -1, 5, 4, 3], [-1, -1, -1, 3, -1, -1], [4, -1, 6, 6, 3, 3], [3, 4, -1, 2, 6, 1], [-1, 4, 3, -1, -1, -1]],
    [[4, -1, 6, 6, 3, 3], [-1, -1, 4, -1, -1, 5], [4, 3, 5, -1, 2, 3], [2, 4, 6, 6, 3, 6], [-1, 6, -1, -1, -1, -1], [3, 4, -1, 2, 6, 1]],
    [[5, 4, 3, 1, 5, 3], [-1, -1, -1, -1, 2, -1], [2, 4, 6, 6, 3, 6], [3, 2, 3, 5, 3, 6], [4, -1, 6, 6, 3, 3]],
    [[-1, 4, 3, -1, -1, -1], [4, 3, 5, -1, 2, 3], [2, 4, 6, 6, 3, 6], [4, -1, 6, 6, 3, 3], [4, 3, -1, 5, 4, 3], [3, 4, -1, 2, 6, 1]],
    [[-1, 6, -1, -1, -1, -1], [-1, -1, 4, -1, -1, 5], [3, 4, -1, 2, 6, 1], [4, 3, -1, 5, 4, 3], [-1, 4, 3, -1, -1, -1]],
    [[-1, -1, -1, 3, -1, -1], [2, 4, 6, 6, 3, 6], [4, -1, 6, 6, 3, 3], [5, 4, 3, 1, 5, 3], [-1, -1, -1, -1, 6, 3], [3, 4, -1, 2, 6, 1]]
]
M_num = 6
Op_num = [6,6,6,6,6,6,5,6,5,6]
J = {0:6,1:6,2:6,3:6,4:6,5:6,6:5,7:6,8:5,9:6}
O_num = 58
J_num = 10
Idling_energy = [0.2, 0.28, 0.28, 0.36, 0.32, 0.32]
Processing_energy = [0.88, 0.64, 0.6, 0.6, 0.68, 0.64]


# MK03
'''
Processing_time =[
    [[-1, -1, -1, 5, 19, -1, 15, 11], [-1, -1, 18, 5, -1, -1, -1, -1], [-1, -1, 16, -1, -1, 11, 3, 18], [-1, 1, 19, -1, 7, -1, 2, -1], [-1, -1, -1, -1, 6, 3, -1, -1], [-1, -1, -1, 5, 2, -1, -1, 18], [-1, -1, -1, -1, 2, -1, -1, -1], [17, -1, -1, -1, -1, -1, -1, -1], [12, 10, 14, -1, 10, -1, -1, 5], [-1, -1, -1, -1, -1, 2, 15, 19]],
    [[-1, -1, 16, -1, -1, 11, 3, 18], [17, -1, -1, -1, -1, -1, -1, -1], [-1, 1, -1, 13, -1, -1, -1, -1], [12, 10, 14, -1, 10, -1, -1, 5], [9, 18, 13, 11, -1, 18, -1, -1], [-1, -1, -1, -1, -1, 15, 13, -1], [-1, -1, -1, 5, 19, -1, 15, 11], [-1, 1, 19, -1, 7, -1, 2, -1], [7, -1, -1, 11, -1, 13, -1, 3], [-1, -1, -1, -1, -1, 2, 15, 19]],
    [[-1, -1, 3, -1, 5, -1, -1, -1], [-1, 1, 19, -1, 7, -1, 2, -1], [-1, -1, 18, 5, -1, -1, -1, -1], [-1, -1, -1, -1, 6, 3, -1, -1], [7, -1, -1, 11, -1, 13, -1, 3], [-1, -1, -1, -1, -1, 2, 15, 19], [9, 18, 13, 11, -1, 18, -1, -1], [-1, -1, -1, 5, 2, -1, -1, 18], [17, -1, -1, -1, -1, -1, -1, -1], [-1, 1, -1, 13, -1, -1, -1, -1]],
    [[-1, -1, 18, 5, -1, -1, -1, -1], [-1, -1, 3, -1, 5, -1, -1, -1], [9, 18, 13, 11, -1, 18, -1, -1], [7, -1, -1, 11, -1, 13, -1, 3], [-1, -1, -1, -1, -1, 15, 13, -1], [-1, 1, 19, -1, 7, -1, 2, -1], [-1, -1, -1, -1, 2, -1, -1, -1], [-1, -1, 16, -1, -1, 11, 3, 18], [17, -1, -1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, 6, 3, -1, -1]],
    [[-1, -1, -1, -1, -1, 15, 13, -1], [-1, -1, -1, -1, -1, 2, 15, 19], [-1, -1, -1, -1, 2, -1, -1, -1], [-1, -1, -1, 5, 19, -1, 15, 11], [9, 18, 13, 11, -1, 18, -1, -1], [-1, 1, 19, -1, 7, -1, 2, -1], [-1, -1, -1, 5, 2, -1, -1, 18], [-1, -1, -1, -1, 6, 3, -1, -1], [-1, -1, 3, -1, 5, -1, -1, -1], [12, 10, 14, -1, 10, -1, -1, 5]],
    [[-1, 1, -1, 13, -1, -1, -1, -1], [-1, -1, -1, -1, -1, 15, 13, -1], [-1, -1, 18, 5, -1, -1, -1, -1], [-1, -1, 16, -1, -1, 11, 3, 18], [9, 18, 13, 11, -1, 18, -1, -1], [12, 10, 14, -1, 10, -1, -1, 5], [7, -1, -1, 11, -1, 13, -1, 3], [-1, -1, -1, 5, 19, -1, 15, 11], [-1, -1, -1, -1, 6, 3, -1, -1], [-1, -1, 3, -1, 5, -1, -1, -1]],
    [[12, 10, 14, -1, 10, -1, -1, 5], [7, -1, -1, 11, -1, 13, -1, 3], [-1, 1, -1, 13, -1, -1, -1, -1], [17, -1, -1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, -1, 15, 13, -1], [-1, 1, 19, -1, 7, -1, 2, -1], [-1, -1, -1, -1, 2, -1, -1, -1], [9, 18, 13, 11, -1, 18, -1, -1], [-1, -1, 18, 5, -1, -1, -1, -1], [-1, -1, -1, -1, -1, 2, 15, 19]],
    [[-1, -1, -1, -1, -1, 2, 15, 19], [17, -1, -1, -1, -1, -1, -1, -1], [-1, -1, -1, 5, 19, -1, 15, 11], [-1, -1, -1, -1, -1, 15, 13, -1], [12, 10, 14, -1, 10, -1, -1, 5], [7, -1, -1, 11, -1, 13, -1, 3], [9, 18, 13, 11, -1, 18, -1, -1], [-1, 1, -1, 13, -1, -1, -1, -1], [-1, -1, 18, 5, -1, -1, -1, -1], [-1, -1, 3, -1, 5, -1, -1, -1]],
    [[17, -1, -1, -1, -1, -1, -1, -1], [12, 10, 14, -1, 10, -1, -1, 5], [-1, -1, 16, -1, -1, 11, 3, 18], [-1, -1, -1, -1, -1, 2, 15, 19], [-1, -1, -1, -1, -1, 15, 13, -1], [7, -1, -1, 11, -1, 13, -1, 3], [-1, -1, -1, -1, 2, -1, -1, -1], [-1, 1, -1, 13, -1, -1, -1, -1], [9, 18, 13, 11, -1, 18, -1, -1], [-1, -1, -1, 5, 19, -1, 15, 11]],
    [[17, -1, -1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, -1, 15, 13, -1], [-1, -1, -1, 5, 2, -1, -1, 18], [9, 18, 13, 11, -1, 18, -1, -1], [7, -1, -1, 11, -1, 13, -1, 3], [-1, -1, 18, 5, -1, -1, -1, -1], [-1, -1, -1, -1, 6, 3, -1, -1], [-1, -1, -1, -1, -1, 2, 15, 19], [-1, -1, 16, -1, -1, 11, 3, 18], [12, 10, 14, -1, 10, -1, -1, 5]],
    [[-1, 1, -1, 13, -1, -1, -1, -1], [-1, -1, -1, -1, -1, 2, 15, 19], [-1, -1, 16, -1, -1, 11, 3, 18], [-1, -1, 18, 5, -1, -1, -1, -1], [-1, -1, -1, -1, 6, 3, -1, -1], [17, -1, -1, -1, -1, -1, -1, -1], [-1, -1, 3, -1, 5, -1, -1, -1], [-1, -1, -1, 5, 2, -1, -1, 18], [12, 10, 14, -1, 10, -1, -1, 5], [9, 18, 13, 11, -1, 18, -1, -1]],
    [[7, -1, -1, 11, -1, 13, -1, 3], [-1, -1, -1, 5, 2, -1, -1, 18], [-1, -1, 16, -1, -1, 11, 3, 18], [17, -1, -1, -1, -1, -1, -1, -1], [9, 18, 13, 11, -1, 18, -1, -1], [-1, -1, -1, -1, -1, 2, 15, 19], [-1, -1, -1, -1, 2, -1, -1, -1], [-1, -1, 3, -1, 5, -1, -1, -1], [-1, -1, -1, 5, 19, -1, 15, 11], [-1, 1, -1, 13, -1, -1, -1, -1]],
    [[12, 10, 14, -1, 10, -1, -1, 5], [-1, -1, -1, -1, 2, -1, -1, -1], [-1, -1, 18, 5, -1, -1, -1, -1], [-1, 1, 19, -1, 7, -1, 2, -1], [-1, -1, -1, -1, -1, 15, 13, -1], [-1, -1, 16, -1, -1, 11, 3, 18], [-1, -1, -1, 5, 19, -1, 15, 11], [9, 18, 13, 11, -1, 18, -1, -1], [-1, -1, -1, -1, 6, 3, -1, -1], [7, -1, -1, 11, -1, 13, -1, 3]],
    [[-1, -1, 16, -1, -1, 11, 3, 18], [-1, -1, -1, 5, 2, -1, -1, 18], [-1, 1, -1, 13, -1, -1, -1, -1], [-1, 1, 19, -1, 7, -1, 2, -1], [-1, -1, -1, -1, 6, 3, -1, -1], [-1, -1, 18, 5, -1, -1, -1, -1], [-1, -1, -1, -1, -1, 15, 13, -1], [-1, -1, -1, -1, 2, -1, -1, -1], [9, 18, 13, 11, -1, 18, -1, -1], [17, -1, -1, -1, -1, -1, -1, -1]],
    [[12, 10, 14, -1, 10, -1, -1, 5], [-1, -1, -1, -1, 6, 3, -1, -1], [-1, -1, -1, -1, -1, 15, 13, -1], [-1, -1, -1, 5, 19, -1, 15, 11], [-1, -1, 16, -1, -1, 11, 3, 18], [17, -1, -1, -1, -1, -1, -1, -1], [9, 18, 13, 11, -1, 18, -1, -1], [-1, -1, -1, 5, 2, -1, -1, 18], [-1, -1, 18, 5, -1, -1, -1, -1], [-1, 1, 19, -1, 7, -1, 2, -1]]
]
M_num = 8
Op_num = [10,10,10,10,10,10,10,10,10,10,10,10,10,10,10]
J = {0:10,1:10,2:10,3:10,4:10,5:10,6:10,7:10,8:10,9:10,10:10,11:10,12:10,13:10,14:10}
O_num = 150
J_num = 15
'''



print(Processing_time,M_num,Op_num,J,O_num,J_num,Idling_energy,Processing_energy)




'''  如果第i个的结束和第i+1个开始之间有空隙，那么就加入idle
if self.Start[i+1]-self.End[i]>0:
    for i in range(len(self.End)):
        k = [self.End[i],self.Start[i+1]]
'''

import math
import gym
from gym import spaces, logger
from gym.utils import seeding
import numpy as np
import random
# from Object_Fjsp import Object
# from init_Job import Init_Job,Processing_time,M_num,Op_num,J,O_num,J_num


class DymEnv(gym.Env):
    def __init__(self):
        self.O_num = O_num          # 工序总数
        self.M_num = M_num          # 机器数
        self.J_num = J_num          # 工件数
        self.J = J                  # 工件对应的工序数
        self.Processing_time = Processing_time     # 加工时间
        self.UProcessing_time = np.zeros([self.J_num,max(self.J.values())])  # 工件的各个工序的平均处理时间
        self.CTK = [0 for i in range(M_num)]  # 各机器上最后一道工序的完工时间列表
        self.OP = [0 for i in range(J_num)]  # 各工件的已加工工序数列表
        self.UK = [0 for i in range(M_num)]  # 各机器的实际使用率
        self.CRJ = [0 for i in range(J_num)]  # 工件完工率
        self.Iunt = [0 for i in range(M_num)]  # 单机不可用时间
        self.Idling_energy = Idling_energy
        self.Processing_energy = Processing_energy


        self.Fle_Cap_Machine = [0 for i in range(M_num)]  # 机器剩余柔性程度
        self.Fle_Cap_Job = [0 for i in range(J_num)]      # 工件剩余柔性程度
        self.Fle_Cap_Job_num = [0 for i in range(J_num)]    # 工件剩余可加工工序可选择机器数量
        self.Fle_Cap_Machine_num = [0 for i in range(M_num)]    # 机器剩余可加工工序数量

        for i in range(len(self.Processing_time)):
            for j in range(len(self.Processing_time[i])):
                for k in range(len(self.Processing_time[i][j])):
                    if self.Processing_time[i][j][k] > 0:
                        # Max_Processing_time[k] += Processing_time[i][j][k]
                        self.Fle_Cap_Machine_num[k] += 1
                        self.Fle_Cap_Job_num[i] += 1


        # 反向的（softmax归一化处理时间比值）*正向处理时间，然后相加求平均得到一个工件工序的平均处理时间，更加贴近实际情况（选取更小的处理时间）
        for i in range(np.shape(self.Processing_time)[0]):
            for j in range(np.shape(self.Processing_time[i])[0]):
                Q = []
                W = []
                for k in range(len(self.Processing_time[i][j])):
                    if self.Processing_time[i][j][k] > 0:
                        Q.append(self.Processing_time[i][j][k])
                Qsum = sum(Q)
                QIndiv = [q / Qsum for q in Q]
                Q.sort()
                QIndiv.sort()
                QIndiv.reverse()
                W = [Q[l] * QIndiv[l] for l in range(len(Q))]
                self.UProcessing_time[i][j] = np.sum(W)


        # 工件集：
        self.Jobs = []
        for i in range(J_num):
            F = Object(i)
            self.Jobs.append(F)
        # 机器集
        self.Machines = []
        for i in range(M_num):
            F = Object(i)
            self.Machines.append(F)
        # self.Machine_idle_list = [[] for i in range(M_num)]       # 空闲时间的，可以用self.Machines.T取代
        # for i in range(M_num):
        #     self.Machine_idle_list[i] = Object.idle_time(self.Machines[i])
        # self.Machines_idle_time = [0 for i in range(M_num)]

        self.action_space = spaces.Discrete(26)
        high = np.array([1,1,1,1,1,1,1,])
        low = np.array([0,0,0,0,0,0,0,])
        self.observation_space = spaces.Box(low, high, dtype=np.float32)
        '''nongdaozhele '''
        self.seed()
        self.viewer = None
        self.state = None

        self.steps_beyond_done = None

    def _Update(self,Job,Machine):
        self.CTK[Machine] = max(self.Machines[Machine].End)  # 各机器上最后一道工序的完工时间列表
        self.OP[Job] += 1  # 各工件的已加工工序数列表
        self.UK[Machine] = sum(self.Machines[Machine].T) / self.CTK[Machine]  # 各机器的实际使用率
        self.CRJ[Job] = self.OP[Job] / self.J[Job]      # 工件完工率
        self.Iunt[Machine] = (self.CTK[Machine] - sum(self.Machines[Machine].T)) / self.CTK[Machine]  # 单机不可用时间
        On = self.OP[Job]-1
        for i in range(len(self.Processing_time[Job][On])):
            if self.Processing_time[Job][On][i] > 0 :
                self.Fle_Cap_Machine_num[i] -= 1
                self.Fle_Cap_Job_num[Job] -= 1
        max_machine = max(self.Fle_Cap_Machine_num)
        max_job = max(self.Fle_Cap_Job_num)
        min_machine = min(self.Fle_Cap_Machine_num)
        min_job = min(self.Fle_Cap_Job_num)
        for i in range(len(self.Fle_Cap_Job)):          # 工件的柔性能力
            if max_job - min_job == 0 :
                self.Fle_Cap_Job[i] = 0
            else:
                self.Fle_Cap_Job[i] = (self.Fle_Cap_Job_num[i] - min_job) / (max_job - min_job)
        for i in range(len(self.Fle_Cap_Machine)):      # 机器的柔性能力
            if max_machine - min_machine == 0 :
                self.Fle_Cap_Machine[i] = 0
            else:
                self.Fle_Cap_Machine[i] = (self.Fle_Cap_Machine_num[i] - min_machine) / (max_machine - min_machine)


        # for i in range(M_num):
        #     self.Machine_idle_list[i] = Object.idle_time(self.Machines[i])
        #     self.Machines_idle_time[i] = sum(self.Machine_idle_list[i])






    def Features(self):
        '''状态'''
        # 1 机器平均利用率
        U_ave = sum(self.UK)/self.M_num
        K = 0
        for uk in self.UK:
            K+=np.square(uk-U_ave)
        # 2 机器的使用率标准差
        U_std=np.sqrt(K/self.M_num)
        # 3 平均工序完成率
        CRO_ave=sum(self.OP)/self.O_num
        # 4 平均工件工序完成率
        CRJ_ave=sum(self.CRJ)/self.J_num
        K = 0
        for uk in self.CRJ:
            K += np.square(uk - CRJ_ave)
        # 5 工件工序完成率标准差
        CRJ_std = np.sqrt(K / self.J_num)
        # 6 后续未加工操作总时长占比平均值
        DUO_ratio = np.zeros(self.J_num)
        for i in range(self.J_num):
            try:
                DUO_ratio[i] = sum(self.UProcessing_time[i][:self.OP[i]]) / sum(self.UProcessing_time[i])
            except:
                DUO_ratio[i] = 0
        DUO_ave = sum(DUO_ratio)/self.J_num
        # 7 不可用时间平均占比
        UnT_ave = sum(self.Iunt) / M_num
        # # 8 工件的均值柔性
        # FoJ_ave = np.mean(self.Fle_Cap_Job)
        # Q = 0
        # for i in self.Fle_Cap_Job:
        #     Q += np.square(i - FoJ_ave)
        # # 9 机器的均值柔性
        # FoM_ave = np.mean(self.Fle_Cap_Machine)
        # W = 0
        # for i in self.Fle_Cap_Machine:
        #     W += np.square(i - FoM_ave)
        # # 10 工件的柔性的标准差
        # FoJ_std = np.sqrt(Q / self.J_num)
        # # 11 机器柔性的标准差
        # Fom_std = np.sqrt(W / self.M_num)




        return U_ave, U_std, CRO_ave, CRJ_ave, CRJ_std, DUO_ave, UnT_ave,\
               # FoJ_ave, FoM_ave, FoJ_std, Fom_std

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        # obs_t = [sum(self.UK)/self.M_num,sum(self.Iunt) / M_num]
        Time_t = max(self.CTK)
        Job, Machine = action[0], action[1]
        M_idle_time_t = self.CTK[Machine]-sum(self.Machines[Machine].T)
        M_Proc_time_t = sum(self.Machines[Machine].T)
        O_n = len(self.Jobs[Job].End)
        # print(Job, Machine,O_n)
        Idle = self.Machines[Machine].idle_time()
        try:
            last_ot = max(self.Jobs[Job].End)  # 上道工序加工时间
        except:
            last_ot = 0
        try:
            last_mt = max(self.Machines[Machine].End)  # 机器最后完工时间
        except:
            last_mt = 0
        Start_time = max(last_ot, last_mt)
        PT = self.Processing_time[Job][O_n][Machine]  # 工序加工时间
        end_time = Start_time + PT
        self.Machines[Machine]._add(Start_time, end_time, Job, PT)
        self.Jobs[Job]._add(Start_time, end_time, Machine, PT)
        self._Update(Job, Machine)

        self.state = self.Features()
        done = bool(
            sum(self.OP) == sum(self.J.values())
        )

        # obs_1 = [self.state[0],self.state[6]]
        M_idle_time_t1 = self.CTK[Machine] - sum(self.Machines[Machine].T)
        M_Proc_time_t1 = sum(self.Machines[Machine].T)
        Energy = (M_idle_time_t1-M_idle_time_t)*self.Idling_energy[Machine] + (M_Proc_time_t1-M_Proc_time_t)*self.Processing_energy[Machine]

        Time_t1 = max(self.CTK)
        reward = 0.0
        # if not done:
        #     # if obs_t[1] > obs_1[1]:
        #     #     reward = 0.01
        #     # else:
        #     #     if obs_t[1] < obs_1[1]:
        #     #         reward = -0.01
        #     #     else:
        #     #         if obs_1[1] == obs_t[1]:
        #     #             if obs_1[0] >= 0.8:
        #     #                 reward = 0.01
        #     #             else:
        #     #             # if obs_1[1] > obs_t[1]:
        #     #                 reward = -0.01
        #     #             # else:
        #     reward = 0.0
        # else:
        #     reward =  - (max(self.CTK))
        if not done:
            reward = 0.65 * (Time_t - Time_t1) - 0.35 * (Energy)
            # reward = (Time_t - Time_t1)
        else:
            reward = 0.0



        return np.array(self.state, dtype=np.float32), reward, done, {}

    def reset(self):
        U_ave, U_std, CRO_ave, CRJ_ave, CRJ_std, DUO_ratio, UnT_ave = [0, 0, 0, 0, 0, 0, 0]
        # U_ave, U_std, CRO_ave, CRJ_ave, CRJ_std, DUO_ratio, UnT_ave, FoJ_ave, FoM_ave, FoJ_std, Fom_std= [0,0,0,0,0,0,0,0,0,0,0]
        self.CTK = [0 for i in range(M_num)]  # 各机器上最后一道工序的完工时间列表
        self.OP = [0 for i in range(J_num)]  # 各工件的已加工工序数列表
        self.UK = [0 for i in range(M_num)]  # 各机器的实际使用率
        self.CRJ = [0 for i in range(J_num)]  # 工件完工率
        self.Iunt = [0 for i in range(M_num)]  # 单机不可用时间
        self.Jobs = []
        for i in range(J_num):
            F = Object(i)
            self.Jobs.append(F)
        # 机器集
        self.Machines = []
        for i in range(M_num):
            F = Object(i)
            self.Machines.append(F)

        self.Fle_Cap_Machine = [0 for i in range(M_num)]  # 机器剩余柔性程度
        self.Fle_Cap_Job = [0 for i in range(J_num)]  # 工件剩余柔性程度
        self.Fle_Cap_Job_num = [0 for i in range(J_num)]  # 工件剩余可加工工序可选择机器数量
        self.Fle_Cap_Machine_num = [0 for i in range(M_num)]  # 机器剩余可加工工序数量

        for i in range(len(self.Processing_time)):
            for j in range(len(self.Processing_time[i])):
                for k in range(len(self.Processing_time[i][j])):
                    if self.Processing_time[i][j][k] > 0:
                        # Max_Processing_time[k] += Processing_time[i][j][k]
                        self.Fle_Cap_Machine_num[k] += 1
                        self.Fle_Cap_Job_num[i] += 1

        return U_ave, U_std, CRO_ave, CRJ_ave, CRJ_std, DUO_ratio, UnT_ave,
               # FoJ_ave, FoM_ave, FoJ_std, Fom_std

    def render(self):
        pass

    def close(self):
        if self.viewer:
            self.viewer.close()
            self.viewer = None

    def rule1(self):
        UC_Job = [j for j in range(self.J_num) if
                  self.OP[j] < self.J[j]]  # 判断作业J是否已经全部完成，若没有，则加入待选工件集，这里只是选出工件，具体工序没有选出
        Jobs = []
        rpt_i = []          #剩余加工时长
        Min_Machine = np.argsort(self.UK)
        for j in range(len(Min_Machine)):
            Machine = Min_Machine[j]
            for i in UC_Job:
                if self.Processing_time[i][self.OP[i]][Min_Machine[j]] !=-1:
                    Jobs.append(i)
                    rpt_i.append(sum(self.UProcessing_time[i])-sum(self.UProcessing_time[i][:self.OP[i]]))
            if len(rpt_i)>0:
                break
        Job_i = np.argmax(rpt_i)
        Job_i = Jobs[Job_i]
        return Job_i,Machine

    def rule2(self):
        UC_Job = [j for j in range(self.J_num) if
                  self.OP[j] < self.J[j]]  # 判断作业J是否已经全部完成，若没有，则加入待选工件集，这里只是选出工件，具体工序没有选出
        Min_Machine = np.argsort(self.UK)
        Jobs = []
        rpo_i = []      # 剩余操作数量
        for j in range(len(Min_Machine)):
            Machine = Min_Machine[j]
            for i in UC_Job:
                if self.Processing_time[i][self.OP[i]][Machine] != -1:
                    Jobs.append(i)
                    rpo_i.append(self.J[i]-self.OP[i])
            if len(rpo_i)>0:
                break
        Job_i = np.argmax(rpo_i)
        Job_i = Jobs[Job_i]
        return Job_i, Machine

    def rule3(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        Minp_time = []
        for i in UC_Job:
            Minp_time.append(np.argmin(self.Processing_time[i][self.OP[i]]))
        Job_i = np.argmax(Minp_time)
        Job_i = UC_Job[Job_i]
        # Machine = np.argmin(self.Processing_time[Job_i][self.OP[Job_i]])
        Machines = []
        Times = []
        for i in range(len(self.Processing_time[Job_i][self.OP[Job_i]])):
            if self.Processing_time[Job_i][self.OP[Job_i]][i] > 0:
                Times.append(self.Processing_time[Job_i][self.OP[Job_i]][i])
                Machines.append(i)
        Machine = np.argmin(Times)
        Machine = Machines[Machine]
        return Job_i,Machine

    def rule4(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        Jobs = []
        rpt_i = []  # 剩余加工时长
        for i in UC_Job:
            rpt_i.append(sum(self.UProcessing_time[i])-sum(self.UProcessing_time[i][:self.OP[i]]))

        Job_i = np.argmax(rpt_i)
        Job_i = UC_Job[Job_i]
        try:
            C_ij = max(self.Jobs[Job_i].End)
        except:
            C_ij = 0
        On = len(self.Jobs[Job_i].End)  # 已加工工序个数
        Mk = []
        for i in range(len(self.CTK)):  # len(self.CTK)其实就是机器个数
            if self.Processing_time[Job_i][On][i] != -1:  # 因为On是len出来的，而self.Processing_time是从0开始算的，所有不用+1
                c_ij = C_ij + self.Processing_time[Job_i][On][i]
                Mk.append(max(c_ij, self.CTK[i]))  # C_ij为工序约束, A_ij为到达约束, self.CTK[i]为机器约束
            else:
                Mk.append(9999)
        Machine = np.argmin(Mk)  # 选择最小的一个
        return Job_i, Machine

    def rule5(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        rpo_i = []  # 剩余操作数量
        Jobs = []
        for i in UC_Job:
            rpo_i.append(self.J[i] - self.OP[i])
            Jobs.append(i)

        Job_i = np.argmax(rpo_i)
        Job_i = UC_Job[Job_i]
        try:
            C_ij = max(self.Jobs[Job_i].End)
        except:
            C_ij = 0
        On = len(self.Jobs[Job_i].End)  # 已加工工序个数
        Mk = []
        for i in range(len(self.CTK)):  # len(self.CTK)其实就是机器个数
            if self.Processing_time[Job_i][On][i] != -1:  # 因为On是len出来的，而self.Processing_time是从0开始算的，所有不用+1
                c_ij = C_ij+self.Processing_time[Job_i][On][i]
                Mk.append(max(c_ij, self.CTK[i]))  # C_ij为工序约束, A_ij为到达约束, self.CTK[i]为机器约束
            else:
                Mk.append(9999)
        Machine = np.argmin(Mk)  # 选择最小的一个
        return Job_i, Machine

    def rule6(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        Machine = np.argmin(self.UK)
        self.CTK[Machine]  # 机器最早开工时间
        Jobs = []
        for i in UC_Job:
            On = len(self.Jobs[i].End)
            try:
                C_ij = max(self.Jobs[Job_i].End)
            except:
                C_ij = 0
            if self.Processing_time[i][On][Machine] != -1:
                c_ij = C_ij+self.Processing_time[i][On][Machine]
                Jobs.append(max(c_ij, self.CTK[Machine]))
            else:
                Jobs.append(9999)
        Job_i = np.argmin(Jobs)
        Job_i = UC_Job[Job_i]
        return Job_i,Machine

    def rule7(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        rpo_i = []  # 剩余操作数量
        Jobs = []
        for i in UC_Job:
            rpo_i.append(self.J[i] - self.OP[i])
            Jobs.append(i)

        Job_i = np.argmax(rpo_i)
        Job_i = Jobs[Job_i]
        try:
            C_ij = max(self.Jobs[Job_i].End)
        except:
            C_ij = 0
        On = len(self.Jobs[Job_i].End)  # 已加工工序个数
        Machines = []
        Times = []
        for i in range(len(self.Processing_time[Job_i][On])):
            if self.Processing_time[Job_i][On][i] > 0:
                Times.append(self.Processing_time[Job_i][On][i])
                Machines.append(i)
        Machine = np.argmin(Times)
        Machine = Machines[Machine]
        return Job_i,Machine

    def rule8(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        Jobs = []
        rpt_i = []  # 剩余加工时长
        for i in UC_Job:
            rpt_i.append(sum(self.UProcessing_time[i]) - sum(self.UProcessing_time[i][:self.OP[i]]))

        Job_i = np.argmax(rpt_i)
        Job_i = UC_Job[Job_i]
        try:
            C_ij = max(self.Jobs[Job_i].End)
        except:
            C_ij = 0

        On = len(self.Jobs[Job_i].End)  # 已加工工序个数
        Machines = []
        Times = []
        for i in range(len(self.Processing_time[Job_i][On])):
            if self.Processing_time[Job_i][On][i] > 0:
                Times.append(self.Processing_time[Job_i][On][i])
                Machines.append(i)
        Machine = np.argmin(Times)
        Machine = Machines[Machine]
        return Job_i, Machine

    def rule9(self):
        UC_Job = [j for j in range(self.J_num) if
                  self.OP[j] < self.J[j]]  # 判断作业J是否已经全部完成，若没有，则加入待选工件集，这里只是选出工件，具体工序没有选出
        Job_i = random.choice(UC_Job)  # 随机选出一个工件J
        try:
            C_ij = max(self.Jobs[Job_i].End)
        except:
            C_ij = 0
        On = len(self.Jobs[Job_i].End)  # 已加工工序个数
        Mk = []
        for i in range(len(self.CTK)):  # len(self.CTK)其实就是机器个数
            if self.Processing_time[Job_i][On][i] != -1:  # 因为On是len出来的，而self.Processing_time是从0开始算的，所有不用+1
                c_ij = C_ij+self.Processing_time[Job_i][On][i]
                Mk.append(max(c_ij, self.CTK[i]))  # C_ij为工序约束, self.CTK[i]为机器约束
            else:
                Mk.append(9999)
        Machine = np.argmin(Mk)  # 选择最小的一个
        return Job_i, Machine


    def rule10(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        F_C = []
        Machinable=[]
        for i in UC_Job:
            On = len(self.Jobs[i].End)
            l = 0
            for j in self.Processing_time[i][On]:
                if j >0:
                    l+=1
            Machinable.append(l)
        Job_i = np.argmin(Machinable)
        Job_i = UC_Job[Job_i]
        try:
            C_ij = max(self.Jobs[Job_i].End)
        except:
            C_ij = 0
        On = len(self.Jobs[Job_i].End)  # 已加工工序个数
        Mk = []
        for i in range(len(self.CTK)):  # len(self.CTK)其实就是机器个数
            if self.Processing_time[Job_i][On][i] != -1:  # 因为On是len出来的，而self.Processing_time是从0开始算的，所有不用+1
                c_ij = C_ij + self.Processing_time[Job_i][On][i]
                Mk.append(max(c_ij, self.CTK[i]))  # C_ij为工序约束, A_ij为到达约束, self.CTK[i]为机器约束
            else:
                Mk.append(9999)
        Machine = np.argmin(Mk)  # 选择最小的一个
        return Job_i, Machine

    def rule11(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        F_C = []
        Machinable = []
        for i in UC_Job:
            On = len(self.Jobs[i].End)
            l = 0
            for j in self.Processing_time[i][On]:
                if j > 0:
                    l += 1
            Machinable.append(l)
        Job_i = np.argmin(Machinable)
        Job_i = UC_Job[Job_i]
        try:
            C_ij = max(self.Jobs[Job_i].End)
        except:
            C_ij = 0
        On = len(self.Jobs[Job_i].End)  # 已加工工序个数
        Machines = []
        Times = []
        for i in range(len(self.Processing_time[Job_i][On])):
            if self.Processing_time[Job_i][On][i] > 0:
                Times.append(self.Processing_time[Job_i][On][i])
                Machines.append(i)
        Machine = np.argmin(Times)
        Machine = Machines[Machine]
        return Job_i,Machine

    def rule12(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        F_C = []
        Machinable = []
        for i in UC_Job:
            On = len(self.Jobs[i].End)
            l = 0
            for j in self.Processing_time[i][On]:
                if j > 0:
                    l += 1
            Machinable.append(l)
        Job_i = np.argmin(Machinable)
        Job_i = UC_Job[Job_i]
        On1 = len(self.Jobs[Job_i].End)
        Machines = []
        UKs = []
        for i in range(len(self.Processing_time[Job_i][On1])):
            if self.Processing_time[Job_i][On1][i] > 0:
                Machines.append(i)
                UKs.append(self.UK[i])
        Machine = np.argmin(UKs)
        Machine = Machines[Machine]
        return Job_i,Machine

    def rule13(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        CTKs = []
        I = []
        for i in range(len(self.CTK)):
            I.append(i)
            CTKs.append(self.CTK[i])        # 各个机器上当前最后一道工序完成时间
        Machines = np.argsort(CTKs)         # 对各个机器上最后一道工序的完成时间排序，和机器序号直接对应了
        I = np.array(I)
        I = I[Machines]                     # 其实和Machines是一样的
        K = []
        for j in I:
            Machine = j
            for k in UC_Job:
                On = len(self.Jobs[k].End)
                if self.Processing_time[k][On][Machine] > 0:
                    K.append(k)     # 能在该机器上处理的工件工序
            if len(K) > 0:          # 如果>0则说明可以选择该机器
                break               # 机器号确定
        Times = []
        for l in K:                         # 能在该机器上加工的工件
            try:
                C_ij = max(self.Jobs[l].End)
            except:
                C_ij = 0
            Times.append(C_ij)              # 找出工序约束，添加到Times中
        Time = np.argmin(Times)             # 最小的工序约束的工件号，也就是最早能在该机器开工的工件
        Job_i = K[Time]                     # 得到最早能在该机器开工的工件号
        # On = len(self.Jobs[Job_i].End)      # 得到最早能在该机器开工的工件的工序号
        # for i in range(len(K)):         # 有几个工件能在该机器上加工，
        #     if Times[i] == Times[Time]:     # 查询是否有相同的最小工序约束
        #         On1 = len(self.Jobs[K[i]].End)      # 若有相同的最小工序约束，则得到该工件的工序号，工件号为K【i】
        #         if  self.Processing_time[Job_i][On][Machine] > self.Processing_time[K[i]][On1][Machine]:    # 如果该工件在机器上的处理时间小于先前得到的工件号，则更新工件号
        #             Job_i= K[i]

        return Job_i,Machine

    def rule14(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        CTKs = []
        I = []
        for i in range(len(self.CTK)):
            I.append(i)
            CTKs.append(self.CTK[i])
        Machines = np.argsort(CTKs)
        I = np.array(I)
        I = I[Machines]
        Jobs = []
        rpt_i = []
        for j in I:
            Machine = j
            for k in UC_Job:
                On = len(self.Jobs[k].End)
                if self.Processing_time[k][On][Machine] != -1:
                    Jobs.append(k)
                    rpt_i.append(sum(self.UProcessing_time[k]) - sum(self.UProcessing_time[k][:self.OP[k]]))
            if len(rpt_i) > 0:
                break
        Job_i = np.argmax(rpt_i)
        Job_i = Jobs[Job_i]
        return Job_i,Machine

    def rule15(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        CTKs = []
        I = []
        for i in range(len(self.CTK)):
            I.append(i)
            CTKs.append(self.CTK[i])
        Machines = np.argsort(CTKs)
        I = np.array(I)
        I = I[Machines]
        Jobs = []
        rpo_i = []
        for j in I:
            Machine = j
            for k in UC_Job:
                On = len(self.Jobs[k].End)
                if self.Processing_time[k][On][Machine] != -1:
                    Jobs.append(k)
                    rpo_i.append(self.J[k]-self.OP[k])
            if len(rpo_i) > 0:
                break
        Job_i = np.argmax(rpo_i)
        Job_i = Jobs[Job_i]
        return Job_i, Machine

    def rule16(self):
        UC_Job = [j for j in range(self.J_num) if
                  self.OP[j] < self.J[j]]  # 判断作业J是否已经全部完成，若没有，则加入待选工件集，这里只是选出工件，具体工序没有选出
        Jobs = []
        Machinable = []
        Min_Machine = np.argsort(self.UK)
        for j in range(len(Min_Machine)):
            Machine = Min_Machine[j]
            K=[]
            for i in UC_Job:
                On = len(self.Jobs[i].End)
                l = 0
                if self.Processing_time[i][On][Machine] > 0:
                    for j in self.Processing_time[i][On]:
                        if j > 0:
                            l += 1
                    Machinable.append(l)
                    K.append(i)
            if len(Machinable) > 0 :
                break

        Job_i = np.argmin(Machinable)
        Job_i = K[Job_i]
        return Job_i, Machine

    def rule17(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        Jobs = []
        rpt_i = []  # 剩余加工时长
        for i in UC_Job:
            rpt_i.append(sum(self.UProcessing_time[i]) - sum(self.UProcessing_time[i][:self.OP[i]]))

        Job_i = np.argmax(rpt_i)
        Job_i = UC_Job[Job_i]
        On = len(self.Jobs[Job_i].End)  # 已加工工序个数
        Uks = []
        Machines = []
        for i in range(len(self.Processing_time[Job_i][On])):
            if self.Processing_time[Job_i][On][i] > 0:
                Uks.append(self.UK[i])
                Machines.append(i)
        Machine = np.argmin(Uks)
        Machine = Machines[Machine]
        return Job_i,Machine

    def rule18(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        rpo_i = []  # 剩余操作数量
        Jobs = []
        for i in UC_Job:
            rpo_i.append(self.J[i] - self.OP[i])
            Jobs.append(i)

        Job_i = np.argmax(rpo_i)
        Job_i = UC_Job[Job_i]
        On = len(self.Jobs[Job_i].End)  # 已加工工序个数
        Uks = []
        Machines = []
        for i in range(len(self.Processing_time[Job_i][On])):
            if self.Processing_time[Job_i][On][i] > 0:
                Uks.append(self.UK[i])
                Machines.append(i)
        Machine = np.argmin(Uks)
        Machine = Machines[Machine]
        return Job_i, Machine

    def rule19(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        CTKs = []
        I = []
        for i in range(len(self.CTK)):
            I.append(i)
            CTKs.append(self.CTK[i])  # 各个机器上当前最后一道工序完成时间
        Machines = np.argsort(CTKs)  # 对各个机器上最后一道工序的完成时间排序，和机器序号直接对应了
        I = np.array(I)
        I = I[Machines]  # 其实和Machines是一样的
        K = []
        for j in I:
            Machine = j
            for k in UC_Job:
                On = len(self.Jobs[k].End)
                if self.Processing_time[k][On][Machine] > 0:
                    K.append(k)  # 能在该机器上处理的工件工序
            if len(K) > 0:  # 如果>0则说明可以选择该机器
                break  # 机器号确定
        Machinable = []
        for i in K:
            On = len(self.Jobs[i].End)
            l = 0
            for j in self.Processing_time[i][On]:
                if j >0:
                    l+=1
            Machinable.append(l)
        Job_i = np.argmin(Machinable)
        Job_i = K[Job_i]
        return Job_i,Machine

    def rule20(self):
        UC_Job = [j for j in range(self.J_num) if
                  self.OP[j] < self.J[j]]  # 判断作业J是否已经全部完成，若没有，则加入待选工件集，这里只是选出工件，具体工序没有选出
        Jobs = []
        rpt_i = []  # 剩余加工时长
        Min_Machine = np.argsort(self.UK)
        for j in range(len(Min_Machine)):
            Machine = Min_Machine[j]
            for i in UC_Job:
                if self.Processing_time[i][self.OP[i]][Min_Machine[j]] != -1:
                    Jobs.append(i)
                    rpt_i.append(sum(self.UProcessing_time[i]) - sum(self.UProcessing_time[i][:self.OP[i]]))
            if len(rpt_i) > 0:
                break
        Job_i = np.argmin(rpt_i)
        Job_i = Jobs[Job_i]
        return Job_i, Machine

    def rule21(self):
        UC_Job = [j for j in range(self.J_num) if
                  self.OP[j] < self.J[j]]  # 判断作业J是否已经全部完成，若没有，则加入待选工件集，这里只是选出工件，具体工序没有选出
        Min_Machine = np.argsort(self.UK)
        Jobs = []
        rpo_i = []  # 剩余操作数量
        for j in range(len(Min_Machine)):
            Machine = Min_Machine[j]
            for i in UC_Job:
                if self.Processing_time[i][self.OP[i]][Machine] != -1:
                    Jobs.append(i)
                    rpo_i.append(self.J[i] - self.OP[i])
            if len(rpo_i) > 0:
                break
        Job_i = np.argmin(rpo_i)
        Job_i = Jobs[Job_i]
        return Job_i, Machine

    def rule22(self):
        UC_Job = [j for j in range(self.J_num) if
                  self.OP[j] < self.J[j]]  # 判断作业J是否已经全部完成，若没有，则加入待选工件集，这里只是选出工件，具体工序没有选出
        Jobs = []
        Machinable = []
        Min_Machine = np.argsort(self.UK)
        for j in range(len(Min_Machine)):
            Machine = Min_Machine[j]
            for i in UC_Job:
                On = len(self.Jobs[i].End)
                l = 0
                for j in self.Processing_time[i][On]:
                    if j > 0:
                        l += 1
                Machinable.append(l)
        Job_i = np.argmax(Machinable)
        Job_i = UC_Job[Job_i]
        return Job_i, Machine

    def rule23(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        CTKs = []
        I = []
        for i in range(len(self.CTK)):
            I.append(i)
            CTKs.append(self.CTK[i])
        Machines = np.argsort(CTKs)
        I = np.array(I)
        I = I[Machines]
        Jobs = []
        rpt_i = []
        for j in I:
            Machine = j
            for k in UC_Job:
                On = len(self.Jobs[k].End)
                if self.Processing_time[k][On][Machine] != -1:
                    Jobs.append(k)
                    rpt_i.append(sum(self.UProcessing_time[k]) - sum(self.UProcessing_time[k][:self.OP[k]]))
            if len(rpt_i) > 0:
                break
        Job_i = np.argmin(rpt_i)
        Job_i = Jobs[Job_i]
        return Job_i, Machine

    def rule24(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        CTKs = []
        I = []
        for i in range(len(self.CTK)):
            I.append(i)
            CTKs.append(self.CTK[i])
        Machines = np.argsort(CTKs)
        I = np.array(I)
        I = I[Machines]
        Jobs = []
        rpo_i = []
        for j in I:
            Machine = j
            for k in UC_Job:
                On = len(self.Jobs[k].End)
                if self.Processing_time[k][On][Machine] != -1:
                    Jobs.append(k)
                    rpo_i.append(self.J[k] - self.OP[k])
            if len(rpo_i) > 0:
                break
        Job_i = np.argmin(rpo_i)
        Job_i = Jobs[Job_i]
        return Job_i, Machine

    def rule25(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        CTKs = []
        I = []
        for i in range(len(self.CTK)):
            I.append(i)
            CTKs.append(self.CTK[i])  # 各个机器上当前最后一道工序完成时间
        Machines = np.argsort(CTKs)  # 对各个机器上最后一道工序的完成时间排序，和机器序号直接对应了
        I = np.array(I)
        I = I[Machines]  # 其实和Machines是一样的
        K = []
        for j in I:
            Machine = j
            for k in UC_Job:
                On = len(self.Jobs[k].End)
                if self.Processing_time[k][On][Machine] > 0:
                    K.append(k)  # 能在该机器上处理的工件工序
            if len(K) > 0:  # 如果>0则说明可以选择该机器
                break  # 机器号确定
        Machinable = []
        for i in K:
            On = len(self.Jobs[i].End)
            l = 0
            for j in self.Processing_time[i][On]:
                if j > 0:
                    l += 1
            Machinable.append(l)
        Job_i = np.argmax(Machinable)
        Job_i = K[Job_i]
        return Job_i, Machine

    def rule26(self):
        UC_Job = [j for j in range(self.J_num) if self.OP[j] < self.J[j]]
        Minp_time = []
        for i in UC_Job:
            Minp_time.append(np.argmin(self.Processing_time[i][self.OP[i]]))
        Job_i = np.argmin(Minp_time)
        Job_i = UC_Job[Job_i]
        # Machine = np.argmin(self.Processing_time[Job_i][self.OP[Job_i]])
        Machines = []
        Times = []
        for i in range(len(self.Processing_time[Job_i][self.OP[Job_i]])):
            if self.Processing_time[Job_i][self.OP[Job_i]][i] > 0:
                Times.append(self.Processing_time[Job_i][self.OP[Job_i]][i])
                Machines.append(i)
        Machine = np.argmin(Times)
        Machine = Machines[Machine]
        return Job_i, Machine

    def Is_Done(self,done):
        if done:
            return self.Machines
