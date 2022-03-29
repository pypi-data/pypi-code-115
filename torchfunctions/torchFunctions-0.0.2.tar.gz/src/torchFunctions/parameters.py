import torch
import pandas as pd
import torch
import torch.nn as nn


class parameters:
    def __init__(self) -> None:
        pass

    def count_params(self,model):
        model_params = {"Modules": list(), "Parameters": list()}
        total = {"trainable": 0, "non_trainable": 0} 
        for name, parameters in model.named_parameters():
            param = parameters.numel()
            if not parameters.requires_grad:
                total["non_trainable"] += param
                continue
            model_params["Modules"].append(name)
            model_params["Parameters"].append(param)
            total["trainable"] += param
        df = pd.DataFrame(model_params)
        df = df.style.set_caption(f"Total parameters: {total}")
        return df