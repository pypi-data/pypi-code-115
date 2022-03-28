"""
This module is a modified version of PointNet++ py-torch based on https://github.com/yanx27/Pointnet_Pointnet2_pytorch
"""
from typing import Tuple, Union

import torch
import torch.nn.functional as F
from einops import repeat  # type: ignore
from torch import Tensor
from torch.nn import BatchNorm1d, Conv1d, Dropout, Linear, Module, ReLU, Sequential

from pycarus.learning.models.pointnet import TNet
from pycarus.learning.models.pointnet2_utils import PointNetFeaturePropagation
from pycarus.learning.models.pointnet2_utils import PointNetSetAbstraction
from pycarus.learning.models.pointnet2_utils import PointNetSetAbstractionMsg


class PointNet2EncoderMSG(Module):
    """Model class respresenting the PointNet++ Encoder network as proposed in:

    "Qi, C. R., Yi, L., Su, H., & Guibas, L. J. (2017).
    Pointnet++: Deep hierarchical feature learning on point sets in a metric space.
    Advances in Neural Information Processing Systems."
    """

    def __init__(
        self,
        size_latent: int = 1024,
        use_tnet: bool = True,
        use_normals: bool = False,
    ) -> None:
        """Create a new instance of PointNet++ Encoder.

        Args:
            size_latent (optional): the size for the global feature. Defaults to 1024.
            use_tnet (optional): if True use the points T-Net. Defaults to False.
            use_normals (optional): if True aspect as input also point normals. Defaults to False.
        """
        super(PointNet2EncoderMSG, self).__init__()

        self.use_normals = use_normals
        self.use_tnet = use_tnet
        self.size_latent = size_latent
        self.num_channels = 3 if self.use_normals else 0

        if self.use_tnet:
            self.tnet = TNet()

        self.sa_1 = PointNetSetAbstractionMsg(
            512,
            [0.1, 0.2, 0.4],
            [16, 32, 128],
            self.num_channels,
            [[32, 32, 64], [64, 64, 128], [64, 96, 128]],
        )
        self.sa_2 = PointNetSetAbstractionMsg(
            128,
            [0.2, 0.4, 0.8],
            [32, 64, 128],
            320,
            [[64, 64, 128], [128, 128, 256], [128, 128, 256]],
        )
        self.sa_3 = PointNetSetAbstraction(
            0,
            0,
            0,
            640 + 3,
            [256, 512, self.size_latent],
            True,
        )

    def forward(self, x: Tensor) -> Tuple[Tensor, Tensor, Union[Tensor, None]]:
        """Process input point cloud and produce point net++ features.

        Args:
            x: The input point cloud(s) with shape (B, NUM_POINTS, D + features).

        Raises:
            ValueError: If use normals is True but only point coordinates are provided.

        Returns:
            - The computed global feature vector with shape (B, SIZE_LATENT).
            - The sampled point at the last layer (B, NUM_PTS).
            - The learned transformation matrix for the input points.
        """

        if self.use_normals and x.shape[-1] == 3:
            raise ValueError("Use normals is True but only points are provided.")

        xyz = x[:, :, :3]
        normals = x[:, :, 3:] if self.use_normals else None

        if self.use_tnet:
            xyz = torch.transpose(xyz, 2, 1)
            trans_pts = self.tnet(xyz)
            xyz = xyz.transpose(2, 1)
            xyz = torch.bmm(xyz, trans_pts)

            if self.use_normals:
                normals = torch.bmm(normals, trans_pts)  # type: ignore
        else:
            trans_pts = None

        xyz_l1, feats_l1 = self.sa_1(xyz, normals)
        xyz_l2, feats_l2 = self.sa_2(xyz_l1, feats_l1)
        xyz_l3, feats_l3 = self.sa_3(xyz_l2, feats_l2)
        global_feature = feats_l3.squeeze(1).view(-1, self.size_latent)

        return global_feature, xyz_l3, trans_pts


class PointNet2ClassificationMSG(Module):
    def __init__(
        self,
        use_tnet: bool = True,
        use_normals: bool = False,
        dropout_p: float = 0.5,
        num_classes: int = 10,
    ) -> None:
        """Create a new instance of PointNet++ Classification Network.

        Args:
            use_pts_tnet (optional): If True use the points T-Net. Defaults to True.
            use_normals (optional): if True aspect as input also point normals. Defaults to False.
            dropout_p (optional): the dropout probability. Defaults to 0.5.
            num_classes (optional): the number of classes. Defaults to 10.
        """

        super(PointNet2ClassificationMSG, self).__init__()
        self.encoder = PointNet2EncoderMSG(
            size_latent=1024, use_tnet=use_tnet, use_normals=use_normals
        )

        self.fc_layers = Sequential(
            Linear(1024, 512, bias=False),
            BatchNorm1d(512),  # type: ignore
            ReLU(True),
            Linear(512, 256, bias=False),
            BatchNorm1d(256),  # type: ignore
            ReLU(True),
            Dropout(dropout_p),
            Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> Tuple[Tensor, Union[Tensor, None]]:
        """Process input point clouds and produces claffication scores.

        Args:
            x: The input clouds with shape (B, NUM_PTS, DIM). The method internally
            transposes the data tensor to correctly operate with PyTorch convetion (B CH N).

        Returns:
            A tuple containing:
                - The computed classification scores with shape (B, NUM_CLASSES).
                - The learned transformation matrix for the input points.
        """
        global_feature, _, trans = self.encoder(x)
        return self.fc_layers(global_feature), trans


class PointNet2PartSegmentationMSG(Module):
    def __init__(
        self,
        use_tnet: bool = False,
        use_normals: bool = False,
        dropout_p: float = 0.5,
        num_classes: int = 16,
        num_classes_part: int = 10,
    ) -> None:
        """Create a new instance of PointNet++ Part Segmentation Network.

        Args:
        """
        super(PointNet2PartSegmentationMSG, self).__init__()

        self.use_normals = use_normals
        ch_feats = 3 if use_normals else 0

        self.use_tnet = use_tnet
        if self.use_tnet:
            self.tnet = TNet()

        self.sa_1 = PointNetSetAbstractionMsg(
            512,
            [0.1, 0.2, 0.4],
            [32, 64, 128],
            3 + ch_feats,
            [[32, 32, 64], [64, 64, 128], [64, 96, 128]],
        )

        self.sa_2 = PointNetSetAbstractionMsg(
            128,
            [0.4, 0.8],
            [64, 128],
            128 + 128 + 64,
            [[128, 128, 256], [128, 196, 256]],
        )

        self.sa_3 = PointNetSetAbstraction(
            num_point=0,
            radius=0,
            num_samples=0,
            in_channel=512 + 3,
            mlp=[256, 512, 1024],
            group_all=True,
        )

        self.fp_1 = PointNetFeaturePropagation(in_channel=150 + ch_feats, mlp=[128, 128])
        self.fp_2 = PointNetFeaturePropagation(in_channel=576, mlp=[256, 128])
        self.fp_3 = PointNetFeaturePropagation(in_channel=1536, mlp=[256, 256])

        self.num_classes = num_classes
        self.conv_1 = Conv1d(128, 128, 1)
        self.bn_1 = BatchNorm1d(128)  # type: ignore
        self.drop_1 = Dropout(dropout_p)
        self.conv_2 = Conv1d(128, num_classes_part, 1)

    def forward(self, x: Tensor, vector_cat: Tensor) -> Tuple[Tensor, Union[Tensor, None]]:
        """Process input point clouds and produces per points claffication scores.

        Args:
            x: The input clouds with shape (B, NUM_PTS, DIM).
            vector_cat: the one hot encoding categorical vector (B, NUM_CLASSES).

        Returns:
            A tuple containing:
                - The computed classification scores with shape (B, NUM_PTS, NUM_CLASSES_PART).
                - The learned transformation matrix for the input points.
        """
        _, num_points, _ = x.shape

        if self.use_normals:
            feats_l0 = x
            xyz = x[:, :, :3]
        else:
            feats_l0 = x
            xyz = x

        if self.use_tnet:
            xyz = torch.transpose(xyz, 2, 1)
            trans = self.tnet(xyz)
            xyz = torch.bmm(xyz.transpose(2, 1), trans)

            if self.use_normals:
                normals = feats_l0[:, :, 3:]
                normals = torch.bmm(normals, trans)
                feats_l0 = torch.cat([xyz, normals], -1)
        else:
            trans = None

        xyz_l1, feats_l1 = self.sa_1(xyz, feats_l0)
        xyz_l2, feats_l2 = self.sa_2(xyz_l1, feats_l1)
        xyz_l3, feats_l3 = self.sa_3(xyz_l2, feats_l2)

        # Feature Propagation layers
        feats_l2 = self.fp_3(xyz_l2, xyz_l3, feats_l2, feats_l3)
        feats_l1 = self.fp_2(xyz_l1, xyz_l2, feats_l1, feats_l2)

        one_hot_enc = repeat(vector_cat, "b n -> b r n", r=num_points)

        feats_l0 = self.fp_1(
            xyz,
            xyz_l1,
            torch.cat([one_hot_enc, xyz, feats_l0], -1),
            feats_l1,
        )

        feats_l0 = torch.transpose(feats_l0, 2, 1)
        feats_out = F.relu(self.bn_1(self.conv_1(feats_l0)))
        feats_out = self.drop_1(feats_out)
        feats_out = self.conv_2(feats_out)
        feats_out = feats_out.permute(0, 2, 1)

        return feats_out, trans
