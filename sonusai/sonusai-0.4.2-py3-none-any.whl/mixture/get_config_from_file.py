import yaml

import sonusai
from sonusai import SonusAIError
from sonusai import logger


def get_default_config(file: str = None) -> dict:
    if file is None:
        file = sonusai.mixture.default_config

    try:
        with open(file=file, mode='r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f'Error loading genmixdb default config: {e}')
        raise SonusAIError


def check_truth_settings(truth_settings: list, default: list = None) -> None:
    if default is not None and len(truth_settings) != len(default):
        logger.error(f'Not enough items in truth_settings')
        raise SonusAIError

    required_keys = [
        'function',
        'config',
        'index',
    ]
    for n in range(len(truth_settings)):
        for key in required_keys:
            if key not in truth_settings[n]:
                if default is not None and key in default[n]:
                    truth_settings[n][key] = default[n][key]
                else:
                    logger.error(f'Missing {key} in truth_settings')
                    raise SonusAIError


def get_config_from_file(config_name: str, default_name: str = None) -> dict:
    config = get_default_config(default_name)

    try:
        # Load given config
        with open(file=config_name, mode='r') as file:
            given_config = yaml.safe_load(file)

        # Use default config as base and overwrite with given config keys as found
        for key in config:
            if key in given_config:
                if key == 'truth_settings':
                    for ts_key in given_config[key]:
                        config[key][ts_key] = given_config[key][ts_key]
                else:
                    config[key] = given_config[key]

        required_keys = [
            'class_labels',
            'class_weights_threshold',
            'dither',
            'feature',
            'frame_size',
            'noises',
            'noise_augmentations',
            'num_classes',
            'seed',
            'target_augmentations',
            'targets',
            'truth_settings',
            'truth_mode',
            'truth_reduction_function',
        ]
        for key in required_keys:
            if key not in config:
                logger.error(f'Missing {key} in config')
                raise SonusAIError

        if not isinstance(config['truth_settings'], list):
            config['truth_settings'] = [config['truth_settings']]

        check_truth_settings(config['truth_settings'])

        return config
    except Exception as e:
        logger.error(f'Error preparing genmixdb config: {e}')
        raise SonusAIError
