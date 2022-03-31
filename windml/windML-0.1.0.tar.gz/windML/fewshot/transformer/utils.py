def get_pos_encoding(n_pos,d_model):
    angles = np.fromfunction(lambda i,j:i/10000**(2*j/d_model),(n_pos,int(d_model/2)))
    pos_enc = np.ones((n_pos,d_model))
    pos_enc[:,::2] = np.sin(angles)
    pos_enc[:,1::2] = np.cos(angles)
    return pos_enc
    #https://github.com/SwikarGautam/Transformer/blob/master/transformer.ipynb