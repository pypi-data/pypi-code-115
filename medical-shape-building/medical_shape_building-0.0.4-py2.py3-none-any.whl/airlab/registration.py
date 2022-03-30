import logging
from functools import partial
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

import torch
import torchio as tio
from pytorch_lightning.lite import LightningLite
from tqdm import tqdm

from medical_shape_building.airlab.image import (
    RegistrationDisplacement,
    RegistrationImage,
)
from medical_shape_building.airlab.loss import MSE
from medical_shape_building.airlab.regulariser import GaussianRegulariser
from medical_shape_building.airlab.transformation import (
    AffineTransformation,
    NonParametricTransformation,
    RigidTransformation,
    SimilarityTransformation,
    Transformation,
)
from medical_shape_building.airlab.utils import (
    create_image_pyramid,
    upsample_displacement,
    warp_image,
)
from medical_shape_building.logging_tqdm import TqdmToLogger

_logger = logging.getLogger(__name__)


class Registration(LightningLite):
    def run(
        self,
        transformation: Transformation,
        num_iterations: int,
        learning_rate: float,
        image_losses: torch.nn.ModuleList,
        regularisers: Optional[torch.nn.ModuleList] = None,
        optimizer_cls=torch.optim.Adam,
    ):
        if regularisers is None:
            regularisers = torch.nn.ModuleList()

        optimizer = optimizer_cls(transformation.parameters(), learning_rate)
        model, optimizer = self.setup(transformation, optimizer)
        image_losses = self.setup(image_losses)
        assert isinstance(image_losses, torch.nn.Module)
        assert isinstance(image_losses.module, torch.nn.ModuleList)

        regularisers = self.setup(regularisers)
        assert isinstance(regularisers, torch.nn.Module)
        assert isinstance(regularisers.module, torch.nn.ModuleList)

        for _ in tqdm(
            range(num_iterations),
            file=TqdmToLogger(logger=_logger, level=logging.DEBUG),
            desc="Registration Iterations",
        ):
            optimizer.zero_grad()
            displacement = model()

            losses: Dict[str, torch.Tensor] = {}

            for loss_fn in image_losses.module:
                losses[loss_fn.name] = loss_fn(displacement)

            loss_strs = []
            for k, v in losses.items():
                loss_strs.append(f"{k}: {v:.3f}")

            total_loss = torch.stack(list(losses.values())).sum()
            self.backward(total_loss)
            optimizer.step()

            for regulariser in regularisers.module:
                regulariser(model.parameters())

        # references in multiple classes -> move everything back to cpu to avoid device mismatches
        model = model.cpu()
        # TODO: Remove once resolved in PL
        # BODY https://github.com/PyTorchLightning/pytorch-lightning/issues/10556
        model.module.cpu()
        image_losses = image_losses.cpu()
        regularisers = regularisers.cpu()
        return model.module.get_flow().to("cpu")

    def register(
        self,
        target_image: Union[RegistrationImage, tio.data.Image],
        source_image: Union[RegistrationImage, tio.data.Image],
        num_iterations: Sequence[int],
        shrink_factors: Sequence[Sequence[int]],
        sigmas: Sequence[Sequence[int]],
        learning_rates: Sequence[float],
        transformation: Union[Callable, str],
        regulariser: Union[Callable, str, None],
        loss_functions: Sequence[Union[Callable, str]] = ("mse",),
        optimizer_cls=torch.optim.Adam,
    ) -> Tuple[RegistrationImage, RegistrationDisplacement]:
        assert (
            len(shrink_factors) == len(num_iterations) - 1
        ), "len(iterations) must be equal to len(shrink_factors)+1"
        if sigmas or shrink_factors:
            assert (
                len(shrink_factors) == len(sigmas) - 1
            ), "len(sigmas) must be equal to len(shrink_factors)+1"
        assert (
            len(shrink_factors) == len(learning_rates) - 1
        ), "len(lrs) must be equal to len(shrink_factors)+1"

        if isinstance(target_image, tio.data.Image):
            target_image = RegistrationImage.from_torchio(tio.data.Image)

        if isinstance(source_image, tio.data.Image):
            source_image = RegistrationImage.from_torchio(tio.data.Image)

        fixed_image_pyramid = create_image_pyramid(target_image, shrink_factors)
        moving_image_pyramid = create_image_pyramid(source_image, shrink_factors)

        iterable = list(zip(moving_image_pyramid, fixed_image_pyramid))

        if isinstance(transformation, str):
            if transformation == "demons":
                transformation = partial(
                    NonParametricTransformation, diffeomorphic=True
                )
            elif transformation == "nonparametric":
                transformation = partial(
                    NonParametricTransformation, diffeomorphic=False
                )
            elif transformation == "affine":
                transformation = partial(AffineTransformation, opt_cm=False)
            elif transformation == "similarity":
                transformation = partial(SimilarityTransformation, opt_cm=False)
            elif transformation == "rigid":
                transformation = partial(RigidTransformation, opt_cm=False)
            else:
                raise ValueError(
                    f"transformation must be callable or one of demons, nonparametric, affine, "
                    f"similarity, rigid. Found {transformation}"
                )

        if isinstance(regulariser, str) and regulariser == "gaussian":
            regulariser = GaussianRegulariser

        assert regulariser is None or (
            isinstance(regulariser, type)
            and issubclass(regulariser, GaussianRegulariser)
        )
        image_losses: List[Union[Callable, torch.nn.Module]] = []
        for lfn in loss_functions:
            if isinstance(lfn, str) and lfn == "mse":
                lfn = partial(MSE, size_average=True, reduce=True)
            image_losses.append(lfn)

        trafo: Optional[Transformation] = None
        constant_flow = None
        for idx, (moving, fixed) in enumerate(
            tqdm(
                iterable,
                file=TqdmToLogger(logger=_logger, level=logging.DEBUG),
                desc="Resolution Levels",
            )
        ):
            trafo = transformation(moving, fixed)
            assert trafo is not None
            if idx:
                with torch.no_grad():
                    constant_flow = upsample_displacement(
                        constant_flow, fixed.image_size, interpolation="linear"
                    )

                    trafo.set_constant_flow(constant_flow)

            _regularisers: Optional[torch.nn.ModuleList] = None
            if regulariser is not None:
                _regularisers = torch.nn.ModuleList(
                    [regulariser(fixed.spacing, sigmas[idx])]
                )

            constant_flow = self.run(
                transformation=trafo,
                num_iterations=num_iterations[idx],
                learning_rate=learning_rates[idx],
                image_losses=torch.nn.ModuleList(
                    [v(fixed, moving) for v in image_losses]
                ),
                regularisers=_regularisers,
                optimizer_cls=optimizer_cls,
            )

        assert trafo is not None
        with torch.no_grad():
            displacement = trafo.get_displacement()
            warped_image = warp_image(source_image, displacement)
            warped_image.image = warped_image.image.detach()

            displacement = RegistrationDisplacement.from_torch(
                displacement.unsqueeze(0).unsqueeze(0).detach(),
                source_image.affine,
            )

        return warped_image, displacement
