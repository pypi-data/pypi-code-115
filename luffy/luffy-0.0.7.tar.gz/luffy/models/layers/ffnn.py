from torch import nn

__all__ = ['FFNN']


class FFNN(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim, num_layers=2, dropout=0., act_fct=nn.GELU):
        super().__init__()
        self.net = nn.ModuleList()
        if num_layers == 1:
            self.net.append(nn.Linear(input_dim, output_dim))
        else:
            self.net.append(nn.Sequential(nn.Linear(input_dim, hidden_dim), act_fct(), nn.Dropout(dropout)))
            for _ in range(num_layers - 2):
                self.net.append(nn.Sequential(nn.Linear(hidden_dim, hidden_dim), act_fct(), nn.Dropout(dropout)))
            self.net.append(nn.Linear(hidden_dim, output_dim))
        self.net = nn.Sequential(*self.net)

    def forward(self, x):
        return self.net(x)
