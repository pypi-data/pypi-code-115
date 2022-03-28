def echox(x):

    """tmd"""
    for i in x:
        if isinstance(i,list ):
            echox(i)
        else:
            print(i)
            



