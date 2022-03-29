import asyncio
import json
import logging
import os
import shutil
import tempfile

from math import ceil
from typing import Any
from typing import Dict
from zipfile import ZipFile

import numpy as np

from tpu_tlm_is.base import TensorDescription
from tpu_tlm_is.base.number_types import UserNumberType
from tpu_tlm_is.base.number_types import TpuNumberType
from tpu_tlm_is.base.number_types import STR_TO_USER_NUMBER_TYPE
from tpu_tlm_is.base.number_types import STR_TO_TPU_NUMBER_TYPE
from tpu_tlm_is.models.iotools import post_process
from tpu_tlm_is.models.iotools import pre_process
from pytpu.pytpu import TPUDevice, TPUProgram, TPUInference, ProcessingMode  # type: ignore
from ..tools.helpers import get_tpu_devices
from ..tools.helpers import get_tpu_parameters
from ..tools.helpers import to_raw

LOGGER = logging.getLogger(__name__)


def _get_tensor_description(io_: Dict[str, Any], cwl: int) -> TensorDescription:
    if 'user_shape' in io_.keys():
        LOGGER.debug('Generate NON-RAW descriptions')
        return TensorDescription(
            user_shape_mask=tuple(tuple([True, ] * abs(p[0]) + [False, ] * s + [True, ] * abs(p[1])
                                  for p, s in zip(io_['padding'], io_['user_shape']))),
            user_order=io_['user_order'],
            user_dtype=STR_TO_USER_NUMBER_TYPE[io_['user_dtype']],
            tpu_shape=io_['tpu_shape'],
            tpu_order=io_['tpu_order'],
            tpu_dtype=STR_TO_TPU_NUMBER_TYPE[io_['tpu_dtype']],
            scales=tuple([float(s) for s in io_['scales']]),
            anchor=io_['anchor'],
        )
    else:
        LOGGER.debug('Generate RAW descriptions')
        return TensorDescription(
            user_shape_mask=((False, ), tuple([False, ] * int(io_['size'])), ),
            user_order=('N', 'C', ),
            user_dtype=UserNumberType.INT8,
            tpu_shape=(1, ceil(int(io_['size']) / cwl), np.minimum(cwl, int(io_['size']))),
            tpu_order=('N', 'C', 'B'),
            tpu_dtype=TpuNumberType.INT8,
            scales=(1.0, ),
        )


def pyrun_tpu(program: str, input_data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:

    LOGGER.debug(f'Run program: {program}')

    tpu_device_names = get_tpu_devices()
    LOGGER.debug(f'TPU devices found: {tpu_device_names}')

    with tempfile.TemporaryDirectory() as tempdir:
        with ZipFile(program, 'r') as zip_obj:
            zip_obj.extractall(tempdir)

        with open(os.path.join(tempdir, 'metadata.json'), 'r') as metadata_file:
            metadata = json.load(metadata_file)

        tpu_par = get_tpu_parameters(metadata['hardware_parameters'])

        tensor_descriptions: Dict[str, TensorDescription] = dict()
        for _, region in metadata['inputs'].items():
            for name, io_ in region.items():
                tensor_descriptions[name] = _get_tensor_description(io_, tpu_par.cache_word_length)
                LOGGER.debug(f'Input: {name}, {[len(s) for s in tensor_descriptions[name].user_shape_mask]}, '
                             f'{tensor_descriptions[name].user_dtype}')

        input_binary_data_ = pre_process(tpu_par, input_data, tensor_descriptions)
        # Convert to raw program format
        input_binary_data = {n: v.reshape((1, -1)).view(np.int8) for n, v in input_binary_data_.items()}

        for _, region in metadata['outputs'].items():
            for name, io_ in region.items():
                tensor_descriptions[name] = _get_tensor_description(io_, tpu_par.cache_word_length)

        with open(os.path.join(tempdir, 'metadata.json'), 'w') as metadata_file:
            raw_metadata = to_raw(metadata)
            json.dump(raw_metadata, metadata_file)

        with tempfile.NamedTemporaryFile() as temp_file:
            program_path = os.path.join(tempdir, 'program_raw.tpu')
            shutil.make_archive(temp_file.name, 'zip', tempdir)
            os.rename(temp_file.name + '.zip', program_path)
        LOGGER.debug(f'Raw program saved to {program_path}')

        # Init device
        tpu_device = TPUDevice.open(tpu_device_names[0])
        tpu_program = TPUProgram(program_path)
        tpu_device.load_program(tpu_program)
        inference = TPUInference(tpu_program)

        mode = ProcessingMode.FULL
        inference.load(input_binary_data, mode=mode)
        asyncio.get_event_loop().run_until_complete(tpu_device.load_inference(inference))
        output_binary_data = inference.get(as_dict=True, mode=mode)
        LOGGER.debug('TPU execution DONE!')

        output_data = post_process(tpu_par, output_binary_data, tensor_descriptions)
        LOGGER.debug('Postprocessing DONE!')

        return output_data
