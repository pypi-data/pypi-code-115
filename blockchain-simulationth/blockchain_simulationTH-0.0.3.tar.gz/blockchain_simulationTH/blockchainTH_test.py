# -*- coding: utf-8 -*-
################################################################Simulation#################################################################################################
#from blockchain_testfinalfriendly01 import *
from blockchainTH import *
#-*-coding: utf-8 -*-
#ขั้นตอนที่ 1
#สร้างผู้ใช้
#class Client('name',b'phrase')
# ชื่อตัวแปร(เป็นอะไรก็ได้)   =  Client('ชื่อของผู้ใช้',b'อะไรก็ได้')
#Client A
A = Client('A')


#Client B
B = Client('B')
#print(B)

#Client C
C = Client('C')
#print(C)

#ขั้นตอนที่ 2 
#สร้าง Coinbase Transaction
#class Coinbass(self,receiver,amount)
#เงินตั้งต้น
#ชื่อตัวแปร(เป็นอะไรก็ได้) = Coinbase(ชื่อธุรกรรม(เป็นอะไรก็ได้) ,ชื่อตัวแปรผู้ใช้ในขั้นตอนที่ 1 ,ปริมาณเงินที่ต้องการ)
coinbasetx1 = Coinbase('coin1',A,1000)
coinbasetx2 = Coinbase('coin2',B,1000)
coinbasetx3 = Coinbase('coin3',C,1000)

#print(A.view_balance())
#print(B.view_balance())
#print(C.view_balance())

#ขั้นตอนที่ 3 
#สร้าง Block แรกของระบบ
#ชื่อตัวแปร(เป็นอะไรก็ได้)  = Genesisblock(ชื่อธุรกรรมในขั้นตอนที่แล้ว)
#ปล.ใส่ transaction ลงใน block ได้ จำนวน 3 transaction

block = Genesisblock('coin1','coin2','coin3')
#print(block)

#ขั้นตอนที่ 4
#ทำการ POW
#mine(block, prefix_zeros)
##ชื่อตัวแปร(เป็นอะไรก็ได้)  = mine(ชื่อบล็อกในขั้นตอนที่แล้ว,difficulty)
#ปล.ยิ่งเพิ่มค่า difficulty เวลาที่ใช้ในการ POW ก็จะนานขึ้น
#for i in range(1,11):
#     POW = mine(block,3)

POW = mine(block,0)

#ขั้นตอนที่ 5
#สร้าง  Transaction
#class Transaction(txname,sender,receiver,value,fromtx,index)
#ชื่อตัวแปร(เป็นอะไรก็ได้) = Transaction(ชื่อธุรกรรม(เป็นอะไรก็ได้), ชื่อของผู้ใช้ที่ต้องการให้เป็นผู้ส่ง, ชื่อของผู้ใช้ที่ต้องการให้เป็นผู้รับ,-
#ปริมาณเงินที่ผู้ส่งจะโอนไปยังผู้รับ, ชื่อของธุรกรรมที่อ้างอิงถึง,ลำดับของเอาต์พุตของธุรกรรมที่ผู้ส่งอ้างอิงถึงนั้น)  
#ปล. Coinbase Transaction มีแค่ index= 0 แต่ Transaction ทั่วไป index = 0 คือ ส่งกลับให้ตัวเอง และ index = 1 คือ ส่งให้ผู้อื่น
tx1 = Transaction('tx1',A,B,50,'coin1',0)
tx2 = Transaction('tx2',B,C,100,'coin2',0)
tx3 = Transaction('tx3',C,A,70,'coin3',0)


#ขั้นตอนที่ 6
#ชื่อตัวแปร(เป็นอะไรก็ได้)  = Block(ชื่อธุรกรรมในขั้นตอนที่แล้ว)
#ปล.ใส่ transaction ลงใน block ได้ จำนวน 3 transaction
block1 = Block('tx1','tx2','tx3')


#ขั้นตอนที่ 7
#ทำการ POW
#mine(block, prefix_zeros)
#ชื่อตัวแปร(เป็นอะไรก็ได้)  = mine(ชื่อบล็อกในขั้นตอนที่แล้ว,difficulty)
#ปล.ยิ่งเพิ่มค่า difficulty เวลาที่ใช้ในการ POW ก็จะนานขึ้น

POW = mine(block1,1)
#for i in range(1,11):
 #      POW = mine(block1,1)

#ขั้นตอนที่ 8
#ตรวจสอบเงินในบัญชีผู้ใช้แต่ละคน
#print(ชื่อของผู้ใช้ในขั้นตอนที่ 1.view_balance())
print(A.view_balance())
print(B.view_balance())
print(C.view_balance())
'''
#ขั้นตอนที่ 5.1
#สร้าง  Transaction
#class Transaction(txname,sender,receiver,value,name)
#ชื่อตัวแปร(เป็นอะไรก็ได้) = Transaction(ชื่อธุรกรรม(เป็นอะไรก็ได้) ,ชื่อตัวแปรผู้ใช้ในขั้นตอนที่ 1 (ผู้ส่ง) ,ชื่อตัวแปรผู้ใช้ในขั้นตอนที่ 1 (ผู้รับ),ปริมาณเงินที่ต้องการทำธุรกรรม,ชื่อธุรกรรมในขั้นตอนที่ 2,index)  
#ปล. Coinbase Transaction มีแค่ index= 0 แต่ Transaction ทั่วไป index = 0 คือ ส่งกลับให้ตัวเอง และ index = 1 คือ ส่งให้ผู้อื่น
tx4 = Transaction('tx4',A,B,50,'tx1',0)
tx5 = Transaction('tx5',B,C,100,'tx2',0)
tx6 = Transaction('tx6',C,A,70,'tx3',0)

#ขั้นตอนที่ 6.1
#ชื่อตัวแปร(เป็นอะไรก็ได้)  = Block(ชื่อธุรกรรมในขั้นตอนที่แล้ว)
#ปล.ใส่ transaction ลงใน block ได้ จำนวน 3 transaction
block2 = Block('tx4','tx5','tx6')


#ขั้นตอนที่ 7.1
#ทำการ POW
#mine(block, prefix_zeros)
#ชื่อตัวแปร(เป็นอะไรก็ได้)  = mine(ชื่อบล็อกในขั้นตอนที่แล้ว,difficulty)
#ปล.ยิ่งเพิ่มค่า difficulty เวลาที่ใช้ในการ POW ก็จะนานขึ้น
for i in range(1,11):
       POW = mine(block2,1)
#POW = mine(block2,0)

#ขั้นตอนที่ 8.1
#ตรวจสอบเงินในบัญชีผู้ใช้แต่ละคน
#print(ชื่อตัวแปรของผู้ใช้ในขั้นตอนที่ 1.view_balance())
#print(A.view_balance())
#print(B.view_balance())
#print(C.view_balance())
'''
