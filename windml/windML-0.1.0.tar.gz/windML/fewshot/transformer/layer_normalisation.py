from numpy import ndarray, var, mean, sqrt

class LayerNorm:
    def forward(self,inputs:ndarray) -> ndarray:
        self.inputs = inputs
        self.var = var(self.inputs,axis=-1,keepdims=True)
        self.normalised = (
            self.inputs - mean(inputs,axis=-1,keepdims=True)
        ) / sqrt(self.var)
        return self.normalised
    
    def backward(self,error:ndarray) -> ndarray:
        batch_size = self.normalised.shape[-1]
        normalised_inputs = self.inputs-mean(self.inputs,axis=-1,keepdims=True)
        normalised_error = normalised_inputs*error
        total_normalised_error = normalised_error.sum(axis=-1,keepdims=True)
        total_error = error.sum(axis=-1,keepdims=True)
        batch_error = batch_size*error-total_error
        a = sqrt(self.var)*batch_error-self.norm*total_normalised_error
        b = batch_size*self.var
        return a / b