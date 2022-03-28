def echox(x,level=0):

    """tmd"""
    for i in x:
        if isinstance(i,list ):
            echox(i)
        else:
            for tab_stop in range(level):
                print ("\t",end="")
            print(i)
            



cd=["134","343","4343"]
echox(cd,7)
