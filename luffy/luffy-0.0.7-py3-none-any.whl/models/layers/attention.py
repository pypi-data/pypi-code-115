import torch
from einops import rearrange
from torch import nn, einsum

__all__ = ['MultiHeadAttention']


class MultiHeadAttention(nn.Module):
    def __init__(self, dim, heads=8, dim_head=None, dropout=0.):
        super().__init__()
        assert dim_head is None or dim_head > 0
        if dim_head is None:
            dim_head = dim // heads

        self.heads = heads
        self.scale = dim_head ** -0.5
        inner_dim = dim_head * heads
        self.to_qkv = nn.Linear(dim, inner_dim * 3, bias=False)
        self.dropout = nn.Dropout(dropout)
        self.to_out = nn.Linear(inner_dim, dim)

    def forward(self, x, mask=None):
        q, k, v = self.to_qkv(x).chunk(3, dim=-1)
        q, k, v = map(lambda t: rearrange(t, 'b n (h d) -> b h n d', h=self.heads), (q, k, v))
        q = q * self.scale
        sim = einsum('b h i d, b h j d -> b h i j', q, k)
        # TODO: other mask types?
        if mask is not None:
            b, _, n, n = sim.shape
            assert mask.shape == (b, n, n), 'mask has incorrect dimensions'
            sim.masked_fill_(~mask, -torch.finfo(sim.dtype).max)
            del mask
        attn = sim.softmax(dim=-1)
        attn = self.dropout(attn)

        out = einsum('b h i j, b h j d -> b h i d', attn, v)
        out = rearrange(out, 'b h n d -> b n (h d)')
        return self.to_out(out)
