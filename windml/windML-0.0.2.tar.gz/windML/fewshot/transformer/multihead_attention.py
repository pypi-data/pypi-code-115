class MultiHeadAttention():
    
    def __init__(self,num_head,d_model):
        
        self.num_head = num_head
        self.d_model = d_model
        
        self.q_w1 = LinearLayer3d(num_head,d_model,int(d_model/num_head)) 
        self.k_w1 = LinearLayer3d(num_head,d_model,int(d_model/num_head))
        self.v_w1 = LinearLayer3d(num_head,d_model,int(d_model/num_head))
        self.o_w1 = LinearLayer3d(1,d_model,d_model)

        self.sm = Softmax()
        

    def forward(self,query,key,value,valid_lens=None,attn_mask=False):
        self.mh_q = self.q_w1.forward(query) #multiheaded queries
        self.mh_k = self.k_w1.forward(key) #multiheaded keys
        self.mh_v = self.v_w1.forward(value) #multiheaded values

        score = self.mh_q@self.mh_k.transpose(0,1,-1,-2) #attention score
        score /= np.sqrt(self.d_model) #scaled attention score
        
        if valid_lens is not None:
            mask = MultiHeadAttention.get_mask(valid_lens,score.shape)
            score += mask
        if attn_mask:
            shp = score.shape
            attn_mask = np.tile(np.triu(np.ones(shp[-1],shp[-1]),1)*-1e+9,(shp[0],shp[1],1,1))
            score += mask
        
        self.sm_score = self.sm.forward(score)
        a_o = (self.sm_score@self.mh_v) #(10, 8, 9, 64) #attention output

        ccat_o = a_o.transpose(0,2,1,3).reshape(-1,1,a_o.shape[2],512) #concatenated output
        return self.o_w1.forward(ccat_o) #applying linear transformation


    def backward(self,grads,step_size):

        d_ccat_o = self.o_w1.backward(grads,step_size)
        d_mh_o = d_ccat_o.reshape(-1,d_ccat_o.shape[2],self.num_head,int(self.d_model/self.num_head)).transpose(0,2,1,3)

        d_sm_score = d_mh_o@self.mh_v.transpose(0,1,3,2)
        d_mh_v = self.sm_score.transpose(0,1,3,2)@d_mh_o
        d_score = self.sm.backward(d_sm_score)
        d_score *= np.sqrt(self.d_model)

        d_mh_q = d_score@self.mh_k
        d_mh_k = d_score.transpose(0,1,-1,-2)@self.mh_q

        d_q = self.q_w1.backward(d_mh_q,step_size).sum(axis=1,keepdims=True)
        d_v = self.v_w1.backward(d_mh_v,step_size).sum(axis=1,keepdims=True)

        d_k = self.k_w1.backward(d_mh_k,step_size).sum(axis=1,keepdims=True)
        
        return d_q,d_k,d_v  #gradients of query,value,key
    
    
    @staticmethod
    def get_mask(valid_lens,shape):
        valid_lens = valid_lens.squeeze()
        mask = np.zeros((shape[0],shape[2]))
        x1 = np.arange(1,1+shape[2])[np.newaxis,:].repeat(shape[0],axis=0)
        x2 = valid_lens[:,np.newaxis].repeat(shape[2],axis=1)
        mask[x1>x2] = -1e+9
        return mask[:,:,np.newaxis].repeat(shape[3],axis=2)[:,np.newaxis].transpose(0,1,-1,2)
    
        