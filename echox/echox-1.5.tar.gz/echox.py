def echox(x,indent=False,level=0):

    """tmd"""
    for i in x:
        if isinstance(i,list ):
            echox(i)
        else:
            if indent:
            #for tab_stop in range(level):
                print ("\t"*level,end="")
            print(i)
            



cd=["134","343","4343"]
echox(cd,True,7)
