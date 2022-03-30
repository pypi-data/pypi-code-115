import json
from argparse import ArgumentParser

import torch


def add_general_arguments(parser: ArgumentParser):
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        help="Path to source input image. Can either be a DICOM Series or a single Image (like Nifti)",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path to output directory. Will be created if non-existent",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        help="Path to target input image. Can either be a DICOM Series or a single Image (like Nifti)",
        required=True,
    )
    parser.add_argument(
        "-d",
        "--device",
        type=torch.device,
        help="The kind of device to use. Defaults to None which will use gpu if available "
        " and fall back to cpu if necessary",
    )
    return parser


def add_affine_arguments(parser: ArgumentParser):
    group = parser.add_argument_group(title="Affine Registration Parameters")
    group.add_argument(
        "--affine_learning_rate",
        type=float,
        help="The learnining rate to use for affine registration",
        default=0.05,
    )
    group.add_argument(
        "--affine_num_iterations",
        type=float,
        help="The number of iterations to do for affine registration",
        default=75,
    )

    return parser


def add_demons_arguments(parser: ArgumentParser):
    group = parser.add_argument_group("Diffeomorphic Demons Registration Parameters")
    group.add_argument(
        "--demons_shrink_factors",
        type=json.loads,
        help="Shrinking Factors for different resolution levels."
        " Can be either a sequence of ints which will apply the same factor"
        " to each dimension or a sequence of sequence of ints, where the inner"
        " sequences should contain one value per dimension."
        " Note that there will always be a stage with full resolution at the end"
        " that does not have to be specified here!",
        default=[4, 2],
    )
    group.add_argument(
        "--demons_num_iterations",
        type=json.loads,
        help="The number of demons iterations to use at each resolution level."
        " Usually it is best to start with higher numbers and decrease the numbers"
        " with increasing resolution to reduce the runtime. Can either be an integer"
        " (where the same number of iterations will be applied to each stage) or a "
        " sequence of integers (one per stage; Note that there is an implicit stage at"
        " full resolution that also needs to have a specified number of iterations)",
        default=(80, 40, 20),
    )
    group.add_argument(
        "--demons_regulariser_sigmas",
        type=json.loads,
        help="The sigma values for the gaussian demons regulariser."
        " Can be either an int where each stage and each dimension will get the same value,"
        " a sequence of ints where each dimension at the current stage will get the same "
        "value or a sequence of sequence of ints to provide unique values for dimensionality"
        " and resolution stages. Note that there is an implicit stage at full resolution"
        " that also needs to have a specified sigma value",
        default=(3, 3, 3),
    )
    parser.add_argument(
        "--demons_learning_rates",
        type=json.loads,
        help="The learning rates for the demons registration. Can either be a float"
        " where each resolution gets the same learning rate or a sequence of floats"
        " with one value per resolution stage (including the implicit full resolution)",
        default=(0.1, 0.1, 0.001),
    )
    return parser


def add_landmark_arguments(parser: ArgumentParser):
    parser.add_argument(
        "--reference_landmarks",
        type=str,
        help="Path to the file containing all reference landmarks.",
    )
    parser.add_argument(
        "--landmarks_zyx",
        action="store_true",
        help="Set if landmarks inside the file are stored as zyx landmarks",
    )

    return parser
