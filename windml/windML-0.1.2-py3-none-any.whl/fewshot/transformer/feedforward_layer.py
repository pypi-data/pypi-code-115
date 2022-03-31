from numpy.random import randn
from numpy import sqrt, ndarray

class FeedForward:
    
    def __init__(self,n_heads:int,embedding_dimension:int,output_dimension:int) -> None:
        self.weights = randn(n_heads,embedding_dimension,output_dimension) 
        self.weights *= sqrt(2/(n_heads*embedding_dimension))
        self.v_w = 0
        self.s_w = 0
        
    def forward(self,inputs:ndarray) -> ndarray:
        return inputs @ self.weights 
        
    
    def backward(self,inputs:ndarray,grads,step_size):
        nabla_w = np.matmul(inputs.transpose(0,1,-1,-2),grads).sum(axis=0)
        nabla_inps = np.matmul(grads,self.weights.transpose(0,-1,1)) 
        self.weights -= step_size*nabla_w
        if self.biases is not 0:
            nabla_b = grads.sum(axis=0,keepdims=True).sum(axis=2,keepdims=True)
            self.adam_optim(nabla_w, d_b=nabla_b,alpha=step_size)
        else:
            self.adam_optim(nabla_w,alpha=step_size)
        return nabla_inps
    
    def adam_optim(self,d_w,alpha,d_b=None,B1=0.9,B2=0.98):
        if self.v_w is 0:
            self.v_w = d_w
            self.s_w = d_w**2
            
        if d_b is not None:
            if self.v_b is 0:
                self.v_b = d_b
                self.s_b = d_b**2
            
            self.v_b = B1*self.v_b + (1-B1)*d_b
            self.s_b = B2*self.s_b + (1-B2)*(d_b**2)

            self.biases -= alpha*self.v_b/(np.sqrt(self.s_b)+1e-8)
            
        self.v_w = B1*self.v_w + (1-B1)*d_w
        self.s_w = B2*self.s_w + (1-B2)*(d_w**2)

        self.weights -= alpha*self.v_w/(np.sqrt(self.s_w)+1e-8)
        