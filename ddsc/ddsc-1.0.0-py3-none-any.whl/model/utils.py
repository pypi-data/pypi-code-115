import os
import torch
import numpy as np
import datetime
import matplotlib.pyplot as plt
from numpy import array
from torch.utils.data import DataLoader

def utils():
    print("====start utils====")

def makedirs(path): 
    try: 
        os.makedirs(path)
    except OSError: 
        if not os.path.isdir(path): 
            raise

def write_model_params(model_i, now_epoch, file_path_i, model_config):
    makedirs(file_path_i+"//model")

    pt_file_path = file_path_i + "model//epoch_" + str(now_epoch)+".pt"
    bin_file_path = file_path_i + "model//epoch_" + str(now_epoch)+".bin"

    torch.save(model_i.state_dict(), pt_file_path)

    output_file = open(bin_file_path, "wb")
    num_of_layer = [model_config["num_of_hidden_layers"]+2] #num of layer
    data = array(num_of_layer,'int')
    data.tofile(output_file)
    output_file.close()
    output_file = open(bin_file_path, "ab")

    row_size_list = []
    column_size_list = []

    for i in range(num_of_layer[0]):
        if i == 0:
            row_size_list.append(model_i.fc1.out_features)
            column_size_list.append(model_i.fc1.in_features)
        elif i >= 1 and i<=model_config["num_of_hidden_layers"]:
            row_size_list.append(model_i.fc2.out_features)
            column_size_list.append(model_i.fc2.in_features)
        elif i == model_config["num_of_hidden_layers"]+1 :
            row_size_list.append(model_i.fc3.out_features)
            column_size_list.append(model_i.fc3.in_features) 

    for i in range(num_of_layer[0]):
        data = array(row_size_list[i],'int')
        data.tofile(output_file)
        data = array(column_size_list[i], 'int')
        data.tofile(output_file)
        if i == 0:
            data = array(model_i.fc1.weight.flatten().tolist(), "double")
            data.tofile(output_file)
            data = array(model_i.fc1.bias.tolist(), "double")
            data.tofile(output_file)
        elif i >=1 and i<=model_config["num_of_hidden_layers"]:
            data = array(model_i.fc2.weight.flatten().tolist(), "double")
            data.tofile(output_file)
            data = array(model_i.fc2.bias.tolist(), "double")
            data.tofile(output_file)
        elif i == model_config["num_of_hidden_layers"]+1 :
            data = array(model_i.fc3.weight.flatten().tolist(), "double")
            data.tofile(output_file)
            data = array(model_i.fc3.bias.tolist(), "double")
            data.tofile(output_file)
    output_file.close()      

def draw_loss_graph(loss_list_i, file_path_i):
    fig = plt.figure()
    fig_file_path = file_path_i +"loss\\"+ "epoch_" + str(len(loss_list_i[1]))+"_" + str(loss_list_i[1][-1])+".png"
    makedirs("{}loss\\".format(file_path_i))
    plt.plot(loss_list_i[0], label="train_loss")
    plt.plot(loss_list_i[1], label="test_loss")
    plt.legend()
    plt.savefig(fig_file_path)
    plt.close(fig)

def predict_model(data_loader_i, model_i,  hyperparams_i, now_epoch,file_path_i):
    validation_pred, validation_real, loss = test(model_i, hyperparams_i, data_loader_i)

    fig = plt.figure(figsize=(5,5))
    fig_file_path = file_path_i + "training_regression\\" + "epoch_" + str(now_epoch) +".png"
    makedirs("{}training_regression\\".format(file_path_i))

    plt.scatter(torch.cat(validation_real),torch.cat(validation_pred), s = 0.1)
    plt.plot([0,1],[0,1], c = "r")
    plt.title("test set regression")
    plt.xlabel("MLP limiter functions")
    plt.ylabel("FCNN limiter function")
    plt.savefig(fig_file_path)
    plt.close(fig)

