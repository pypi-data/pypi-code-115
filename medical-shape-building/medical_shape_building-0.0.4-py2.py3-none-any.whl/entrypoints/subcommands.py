import os
from argparse import ArgumentParser, Namespace

import torchio as tio
from medical_shape.io.read import point_reader

from medical_shape_building.airlab import affine_registration
from medical_shape_building.airlab.affine_demons import (
    affine_multiscale_demons_registration,
)
from medical_shape_building.airlab.demons import multiscale_demons_registration
from medical_shape_building.airlab.image import RegistrationImage
from medical_shape_building.entrypoints.get_parser import (
    add_affine_arguments,
    add_demons_arguments,
    add_general_arguments,
)
from medical_shape_building.transfer_landmarks import transfer_landmarks_by_registration


def _register_affine(args: Namespace):
    source = tio.data.Image(args.source)
    target = tio.data.Image(args.target)
    image, _, _ = affine_registration(
        target_image=RegistrationImage.from_torchio(target),
        source_image=RegistrationImage.from_torchio(source),
        learning_rate=args.affine_learning_rate,
        num_iterations=args.affine_num_iterations,
        device=args.device,
    )

    os.makedirs(args.output, exist_ok=True)
    image.to_torchio().save(os.path.join(args.output, "result_image.nii.gz"))


def _register_demons(args: Namespace):
    source = tio.data.Image(args.source)
    target = tio.data.Image(args.target)
    image, _, _ = multiscale_demons_registration(
        target_image=RegistrationImage.from_torchio(target),
        source_image=RegistrationImage.from_torchio(source),
        shrink_factors=args.demons_shrink_factors,
        num_iterations=args.demons_num_iterations,
        sigmas=args.demons_regulariser_sigmas,
        learning_rates=args.demons_learning_rates,
        device=args.device,
    )

    os.makedirs(args.output, exist_ok=True)
    image.to_torchio().save(os.path.join(args.output, "result_image.nii.gz"))


def _register_affine_demons(args: Namespace):
    source = tio.data.Image(args.source)
    target = tio.data.Image(args.target)
    image, _, _ = affine_multiscale_demons_registration(
        target_image=RegistrationImage.from_torchio(target),
        source_image=RegistrationImage.from_torchio(source),
        learning_rate_affine=args.affine_learning_rate,
        num_iterations_affine=args.affine_num_iterations,
        shrink_factors_demons=args.demons_shrink_factors,
        num_iterations_demons=args.demons_num_iterations,
        sigmas_demons=args.demons_regulariser_sigmas,
        device=args.device,
    )

    os.makedirs(args.output, exist_ok=True)
    image.to_torchio().save(os.path.join(args.output, "result_image.nii.gz"))


def _transfer_landmarks(args: Namespace):
    source = tio.data.Image(args.source)
    target = tio.data.Image(args.target)
    transformed_landmarks, image, _, _ = transfer_landmarks_by_registration(
        source_image=RegistrationImage.from_torchio(source),
        target_image=RegistrationImage.from_torchio(target),
        landmarks=point_reader(args.reference_landmarks),
        learning_rate_affine=args.affine_learning_rate,
        num_iterations_affine=args.affine_num_iterations,
        shrink_factors_demons=args.demons_shrink_factors,
        num_iterations_demons=args.demons_num_iterations,
        sigmas_demons=args.demons_regulariser_sigmas,
        snapping_strategy=args.snapping_strategy,
        device=args.device,
        landmarks_zyx=args.landmarks_zyx,
    )
    os.makedirs(args.output, exist_ok=True)
    transformed_landmarks.save(os.path.join(args.output, "result_landmarks.mjson"))
    image.save(os.path.join(args.output, "result_image.nii.gz"))


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_affine = subparsers.add_parser("affine", help="Affine Image Registration")
    parser_demons = subparsers.add_parser(
        "demons", help="(Multilevel) Diffeomorphic Demons Image Registration"
    )
    parser_affine_demons = subparsers.add_parser(
        "affine_demons",
        help="Affine Image Pre-Registration followed by a (Multilevel) Diffeomorphic Demons Image Registration",
    )
    parser_landmarks = subparsers.add_parser(
        "landmarks",
        help="Transfer Landmarks for via Affine and Diffeomorphic Demons Image Registration",
    )

    parser_affine = add_general_arguments(parser_affine)
    parser_affine = add_affine_arguments(parser_affine)
    parser_affine.set_defaults(func=_register_affine)

    parser_demons = add_general_arguments(parser_demons)
    parser_demons = add_demons_arguments(parser_demons)
    parser_demons.set_defaults(func=_register_demons)

    parser_affine_demons = add_general_arguments(parser_affine_demons)
    parser_affine_demons = add_affine_arguments(parser_affine_demons)
    parser_affine_demons = add_demons_arguments(parser_affine_demons)
    parser_affine_demons.set_defaults(func=_register_affine_demons)

    parser_landmarks = add_general_arguments(parser_landmarks)
    parser_landmarks = add_affine_arguments(parser_landmarks)
    parser_landmarks = add_demons_arguments(parser_landmarks)
    parser_landmarks.set_defaults(func=_transfer_landmarks)

    args = parser.parse_args()
    args.func(args)
