from torch import nn

from .attention import MultiHeadAttention
from .ffnn import FFNN

__all__ = ['Transformer']


class Transformer(nn.Module):
    def __init__(self, dim, depth, heads, dim_head, mlp_dim, dropout=0.):
        super().__init__()
        self.layers = nn.ModuleList([])
        for _ in range(depth):
            self.layers.append(nn.ModuleList([
                nn.Sequential(
                    nn.LayerNorm(dim),
                    MultiHeadAttention(dim, heads=heads, dim_head=dim_head, dropout=dropout),
                    nn.Dropout(dropout)),
                nn.Sequential(
                    nn.LayerNorm(dim),
                    FFNN(dim, dim, mlp_dim, dropout=dropout),
                    nn.Dropout(dropout))]))

    def forward(self, x):
        for attn, ff in self.layers:
            x = attn(x) + x
            x = ff(x) + x

        return x
