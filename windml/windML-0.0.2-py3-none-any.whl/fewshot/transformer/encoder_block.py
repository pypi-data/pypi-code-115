class EncoderBlock():
    
    def __init__(self,num_heads, d_model, drop_prob):
        self.Ln1 = LayerNorm()
        self.Ln2 = LayerNorm()
        self.ff1 = LinearLayer3d(1,d_model,d_model*4,biases=True)
        self.ff2 = LinearLayer3d(1,d_model*4,d_model,biases=True)
        self.mha = MultiHeadAttention(num_heads, d_model)
        self.dp1 = Dropout(drop_prob)
        self.dp2 = Dropout(drop_prob)
        
        
    def forward(self,inp, valid_lens=None):
        
        attn_o = self.mha.forward(inp,inp,inp,valid_lens)

        dp1_o = self.dp1.forward(attn_o)
        norm1 = self.Ln1.forward(dp1_o+inp)
        
        ff1_out = self.ff1.forward(norm1)
        self.reLu = ff1_out<0
        ff1_out[self.reLu] = 0
        ff2_out = self.ff2.forward(ff1_out)
        
        dp2_o = self.dp2.forward(ff2_out)
        norm2 = self.Ln2.forward(dp2_o+attn_o)
        
        return norm2
    
    
    def backward(self,grads,step_size):
        
        d_add1 = self.Ln2.backward(grads)
        d_ff2_out = self.dp2.backward(d_add1)
        d_ff1_out = self.ff2.backward(d_ff2_out,step_size)
        d_ff1_out[self.reLu] = 0
        d_dp_o = self.Ln1.backward(self.ff1.backward(d_ff1_out,step_size))
        
        d_q1 = d_dp_o
        d_attn_o = self.dp1.backward(d_dp_o) + d_add1

        d_q2, d_k, d_v = self.mha.backward(d_attn_o, step_size)
        
        return d_q1 + d_q2 + d_k + d_v