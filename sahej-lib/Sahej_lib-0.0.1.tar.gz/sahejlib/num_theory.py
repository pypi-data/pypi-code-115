'''
sum of n+1 consecutive squares, starting with 2n2+n is equal to n consecutive squares starting with 2n2+2n+1 where n>0
'''
def pythagorous(n:int):
    s=''
    thing = 2*(n**2) + n
    for i in range(n+1):
        s = s + "{} squared".format(thing)
        if i<n:
            s=s+' + '
        thing += 1
    
    s = s+' = '
    
    for j in range(n):
        s = s + "{} squared".format(thing)
        if j<n-1:
            s=s+' + '
        thing += 1
    
    return s