def LCM(x, y):
    #not my code, math.lcm didnt exist????
        if x > y:    
                greater = x    
        else:    
                greater = y    
        while(True):    
                if((greater % x == 0) and (greater % y == 0)):    
                        lcm = greater    
                        break    
                greater += 1    
        return lcm
    
def REP(x):
    nums = []
    for i in range(x):
        nums.append(i+1)
    if len(nums) == 1: return nums[0]
    else:
        c = LCM(nums[0], nums[1])
        if len(nums) >= 2:
            for i in range(2, len(nums)):
                c = LCM(c, nums[i])
    
    return c