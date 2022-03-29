class DecoderBlock():
    def __init__(self,num_heads,d_model,drop_prob):  
        
        self.Ln1 = LayerNorm()
        self.Ln2 = LayerNorm()
        self.Ln3 = LayerNorm()
        
        self.dp1 = Dropout(drop_prob)
        self.dp2 = Dropout(drop_prob)
        self.dp3 = Dropout(drop_prob)
        
        self.ff1 = LinearLayer3d(1,d_model,d_model*4)
        self.ff2 = LinearLayer3d(1,d_model*4,d_model)
        
        self.masked_mh_attn = MultiHeadAttention(num_heads,d_model)
        self.mh_attn = MultiHeadAttention(num_heads,d_model)
        
        
    def forward(self,inp,enc_o,src_valid_lens=None,trg_valid_lens=None):
        
        attn1_out = self.masked_mh_attn.forward(inp,inp,inp,trg_valid_lens,attn_mask=True)
        dp1_o = self.dp1.forward(attn1_out)
        norm1_out = self.Ln1.forward(dp1_o+inp)
        
        attn2_out = self.mh_attn.forward(norm1_out,enc_o,enc_o,src_valid_lens)
        dp2_o = self.dp2.forward(attn2_out)
        norm2_out = self.Ln2.forward(dp2_o+norm1_out)
        
        ff1_out = self.ff1.forward(norm2_out)
        self.reLu = ff1_out < 0
        ff1_out[self.reLu] = 0
        ff2_out = self.ff2.forward(ff1_out)
        dp3_o = self.dp3.forward(ff2_out)
        norm3_out = self.Ln3.forward(dp3_o+norm2_out)
        
        return norm3_out
        
        
    def backward(self,grads,step_size):
        
        d_add3 = self.Ln3.backward(grads)
        d_ff2 = self.dp3.backward(d_add3)
        d_ff1_out = self.ff2.backward(d_ff2,step_size)
        d_ff1_out[self.reLu] = 0
        d_norm2 = self.ff1.backward(d_ff1_out,step_size) + d_add3
        d_add2 = self.Ln2.backward(d_norm2)
        
        d_mh_attn = self.dp2.backward(d_add2) 
        d_norm1, d_enc_o1, d_enc_o2 = self.mh_attn.backward(d_mh_attn, step_size)  
        d_norm1 += d_add2
        d_add1 = self.Ln1.backward(d_norm1)
        
        d_masked_mh_attn = self.dp1.backward(d_add1)
        d_inp, d_k, d_v = self.masked_mh_attn.backward(d_masked_mh_attn, step_size)
        
        d_inp = d_inp + d_k + d_v + d_add1
        d_enc_o = d_enc_o1 + d_enc_o2
        return d_inp, d_enc_o