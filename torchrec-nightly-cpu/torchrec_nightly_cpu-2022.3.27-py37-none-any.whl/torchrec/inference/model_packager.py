#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import abc
from pathlib import Path
from typing import Dict, Any, Union, BinaryIO, Type, TypeVar

from torch.package import PackageExporter
from torchrec.inference.modules import PredictFactory

LOADER_MODULE = "__module_loader"
LOADER_FACTORY = "MODULE_FACTORY"
LOADER_CODE = f"""
import %PACKAGE%

{LOADER_FACTORY}=%PACKAGE%.%CLASS%
"""
CONFIG_MODULE = "__configs"

T = TypeVar("T")


try:
    # pyre-fixme[21]: Could not find module `torch_package_importer`.
    import torch_package_importer  # @manual
except ImportError:
    pass


def load_config_text(name: str) -> str:
    return torch_package_importer.load_text("__configs", name)


def load_pickle_config(name: str, clazz: Type[T]) -> T:
    loaded_obj = torch_package_importer.load_pickle("__configs", name)
    assert isinstance(
        loaded_obj, clazz
    ), f"The loaded config {type(loaded_obj)} is not of type {clazz}"
    return loaded_obj


class PredictFactoryPackager:
    @classmethod
    @abc.abstractclassmethod
    def set_extern_modules(cls, pe: PackageExporter) -> None:
        pass

    @classmethod
    @abc.abstractclassmethod
    def set_mocked_modules(cls, pe: PackageExporter) -> None:
        pass

    @classmethod
    def save_predict_factory(
        cls,
        predict_factory: Type[PredictFactory],
        configs: Dict[str, Any],
        output: Union[str, Path, BinaryIO],
    ) -> None:
        with PackageExporter(output) as pe:
            cls.set_extern_modules(pe)
            cls.set_mocked_modules(pe)
            pe.intern("**")
            cls._save_predict_factory(pe, predict_factory, configs)

    @classmethod
    def _save_predict_factory(
        cls,
        pe: PackageExporter,
        predict_factory: Type[PredictFactory],
        configs: Dict[str, Any],
    ) -> None:
        # Save loader entry point.
        code = LOADER_CODE.replace("%PACKAGE%", predict_factory.__module__).replace(
            "%CLASS%", predict_factory.__name__
        )
        pe.save_source_string(module_name=LOADER_MODULE, src=code)

        # Save configs
        for name, config in configs.items():
            if isinstance(config, str):
                pe.save_text(CONFIG_MODULE, name, config)
            else:
                pe.save_pickle(CONFIG_MODULE, name, config)

        # Save predict factory.
        pe.save_module(predict_factory.__module__)
