import torch
import torch.nn as nn

class FCNN(nn.Module):
    def __init__(self, model_config):
        super(FCNN, self).__init__()
        self.num_of_hidden_layers = model_config["num_of_hidden_layers"]
        self.num_of_hidden_neurons = model_config["num_of_hidden_neurons"]
        self.num_of_input_features = model_config["num_of_input_features"]
        self.output_function = model_config["output_function"]
        self.fc1 = nn.Linear(self.num_of_input_features, self.num_of_hidden_neurons)
        self.fc2 = nn.Linear(self.num_of_hidden_neurons,self.num_of_hidden_neurons)
        self.fc3 = nn.Linear(self.num_of_hidden_neurons, 1)
        if self.output_function == "sigmoid":
            self.output = nn.Sigmoid()
        elif self.output_function == "hardtanh":
            self.output = nn.Hardtanh(min_val = 0, max_valu = 1)
        self.relu = nn.ReLU()
    def forward(self, x):
        x = self.fc1(x.to("cuda"))
        x = self.relu(x)
        for i in range(self.num_of_hidden_layers):
            x = self.fc2(x)
            x = self.relu(x)
        x = self.fc3(x)
        x = self.output(x)
        return x

def train(model_i, hyperparams_i, train_loader_i):
    model_i.train()
    optimizer = hyperparams_i["optimizer"]
    scheduler = hyperparams_i["scheduler"]
    loss_function = hyperparams_i["loss_function"]
    for x,y in train_loader_i: 
        x = x.float().to(device = "cuda")
        y = y.float().to(device = "cuda").view([len(y),1])
        y_fcnn = model_i(x) 
        loss = loss_function(y_fcnn, y)
        optimizer.zero_grad() 
        loss.backward()
        optimizer.step() 
        scheduler.step()
    return loss

@torch.no_grad()
def test(model_i, hyperparams_i, test_loader_i):
    model_i.eval()
    loss_function = hyperparams_i["loss_function"]
    y_fcnn_list = []
    y_mlp_list = []
    for x,y in test_loader_i: 
        x = x.float().to("cuda")
        y = y.float().to("cuda").view([len(y), 1])
        y_fcnn = model_i(x)
        y_mlp_list.append(y.cpu().flatten())
        y_fcnn_list.append(y_fcnn.cpu().flatten())
        loss = loss_function(y_fcnn, y)
    return y_fcnn_list, y_mlp_list, loss


def trainer():
    print("====start trainer====")
    """
    #training
    loss_list = [[],[]]
    for epoch in range(1, maximum_epoch+1):
        train_loss = train(model,hyperparams_config, train_loader)
        test_pred, test_real, test_loss = test(model, hyperparams_config,test_loader)
        loss_list[0].append(train_loss.item())
        loss_list[1].append(test_loss.item())
        print(f'Epoch: {(epoch):03d}, Train Loss: {train_loss:.6f}, Test Loss: {test_loss:.6f}')
        write_model_params(model, epoch, result_file_path, model_config)
        if (epoch % 10 == 0):
            draw_loss_graph(loss_list, result_file_path)
            predict_model(test_loader, model, hyperparams_config, epoch, result_file_path)
    """