import time
s = time.time()

for i in range(10*1000*1000*1000):
    pass
e = time.time()
print(e-s)
