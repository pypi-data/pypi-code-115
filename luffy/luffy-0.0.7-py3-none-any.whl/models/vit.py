import torch
import torch.nn as nn
from einops import repeat
from einops.layers.torch import Rearrange
from torch.nn.modules.utils import _pair

from .layers import Transformer

__all__ = ['ViTB16', 'ViTB32', 'ViTL16', 'ViTL32']


class ViT(nn.Module):
    def __init__(self, *, image_size, channels=3, patch_size, dim, emb_dropout=0., depth, num_heads, dim_head=None,
                 mlp_dim, dropout=0., num_classes, pool='cls'):
        super().__init__()
        image_height, image_width = _pair(image_size)
        patch_height, patch_width = _pair(patch_size)

        assert image_height % patch_height == 0 and image_width % patch_width == 0, \
            'Image size must be divisible by patch size!'

        seq_length = (image_height // patch_height) * (image_width // patch_width)
        patch_dim = channels * patch_height * patch_width
        assert pool in {'cls', 'mean'}, 'pool type must be either cls (cls token) or mean (mean pooling)'

        self.to_patch_embedding = nn.Sequential(
            Rearrange('b c (h p1) (w p2) -> b (h w) (p1 p2 c)', p1=patch_height, p2=patch_width),
            nn.Linear(patch_dim, dim))

        self.pos_embedding = nn.Parameter(torch.randn(1, seq_length + 1, dim))
        self.cls_token = nn.Parameter(torch.zeros(1, 1, dim))
        self.dropout = nn.Dropout(emb_dropout)

        self.transformer = Transformer(dim, depth, num_heads, dim_head, mlp_dim, dropout)

        self.pool = pool

        self.mlp_head = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, num_classes))

    def forward(self, img):
        x = self.to_patch_embedding(img)
        b, n, _ = x.shape

        cls_tokens = repeat(self.cls_token, '() n d -> b n d', b=b)
        x = torch.cat((cls_tokens, x), dim=1)
        x += self.pos_embedding[:, :(n + 1)]
        x = self.dropout(x)

        x = self.transformer(x)

        x = x.mean(dim=1) if self.pool == 'mean' else x[:, 0]

        return self.mlp_head(x)


def vit_params(model_name):
    params_dict = {
        'vit-b16': {'patch_size': 16, 'depth': 12, 'num_heads': 12, 'dim': 768, 'mlp_dim': 3072},
        'vit-b32': {'patch_size': 32, 'depth': 12, 'num_heads': 12, 'dim': 768, 'mlp_dim': 3072},
        'vit-l16': {'patch_size': 16, 'depth': 24, 'num_heads': 16, 'dim': 1024, 'mlp_dim': 4096},
        'vit-l32': {'patch_size': 32, 'depth': 24, 'num_heads': 16, 'dim': 1024, 'mlp_dim': 4096},
    }
    return params_dict[model_name]


class ViTB16(ViT):
    def __init__(self, **kwargs):
        super().__init__(**{**vit_params('vit-b16'), **kwargs})


class ViTB32(ViT):
    def __init__(self, **kwargs):
        super().__init__(**{**vit_params('vit-b32'), **kwargs})


class ViTL16(ViT):
    def __init__(self, **kwargs):
        super().__init__(**{**vit_params('vit-l16'), **kwargs})


class ViTL32(ViT):
    def __init__(self, **kwargs):
        super().__init__(**{**vit_params('vit-l32'), **kwargs})
