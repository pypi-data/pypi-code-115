import torch
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import torch.utils.data as data
from torch.utils.data.dataset import random_split
from torch.utils.data import DataLoader

def dataset_loader():
    print("====start load dataset====")



def load_and_split_data(file_path, rate_i, train_batch_size_i, test_batch_size_i):
    dataset = DATASET(file_path)
    train_idx = int(len(dataset)*rate_i)
    test_idx = len(dataset)-train_idx
    train_dataset, test_dataset = random_split(dataset, [train_idx,test_idx])
    train_loader_o = DataLoader(dataset=train_dataset, batch_size= train_batch_size_i,shuffle=True)
    test_loader_o = DataLoader(dataset=test_dataset, batch_size=test_batch_size_i, shuffle=False)
    print("num of data = {}".format(len(dataset)))
    print("num of train data = {}".format(train_idx))
    print("num of test data = {}".format(test_idx))
    return dataset, train_loader_o, test_loader_o

class DATASET(data.Dataset):
    def __init__(self,file_path):
        super(DATASET, self).__init__()
        df = pd.read_pickle(file_path)
        self.x = [torch.tensor(v) for v in df["feature"].values]
        self.y =  df["label"].values
        plt.hist(self.y, bins = 10)

    def __getitem__(self, index):
        self.x_data = self.x[index]
        self.y_data = self.y[index]
        return self.x_data, self.y_data

    def __len__(self):
        return len(self.y)


