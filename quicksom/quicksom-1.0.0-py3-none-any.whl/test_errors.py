#!/usr/bin/env python3

import pickle
import sys

import numpy
import torch

sys.path.append('../')
from som import SOM

import argparse

parser = argparse.ArgumentParser()
# In/Out
parser.add_argument("-o", "--out_name", default='data/som.p', help="name of pickle to dump")
args, _ = parser.parse_known_args()

device = 'cuda' if torch.cuda.is_available() else 'cpu'

X = numpy.load('data/x.npy')
X = torch.from_numpy(X)
X = X.float()
X = X.to(device)
dim = X.shape[1]
print(X.shape)
# som = pickle.load(open(args.out_name, 'rb'))
som = SOM(10, 5, dim, niter=10, device=device)
som.fit(X)
quantization_error, topo_error = som.compute_error(samples=X)
som.plot_component_plane(plane=1)
