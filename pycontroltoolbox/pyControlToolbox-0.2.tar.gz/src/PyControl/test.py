import models as m
import time_response as tr

s = m.tf([1, 2.5], [1, 2, 1.18])

sssys = m.tf2ss(s)
# print(sssys)

A = [[-4, 0],
     [1.5, -2.1]]
B = [1, 5]
C = [3.2, 1]
D = [0]

sys = m.ss(A,B,C,D)
m.phasePortrait(sys ,t=10)

