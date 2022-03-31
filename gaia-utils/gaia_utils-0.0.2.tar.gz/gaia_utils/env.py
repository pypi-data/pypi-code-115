
ENV_PROD = 'prod'
ENV_DEV = 'dev'

# 全局信息
GAIA_ENV = ENV_DEV
GAIA_DEBUG_MODEL = False


def set_env(env: str):
    global GAIA_ENV
    GAIA_ENV = env
    return


def get_env():
    global GAIA_ENV
    return GAIA_ENV


def is_prod():
    global GAIA_ENV
    return GAIA_ENV == ENV_PROD


def set_debug(debug: bool):
    global GAIA_DEBUG_MODEL
    GAIA_DEBUG_MODEL = debug
    return


def is_debug():
    global GAIA_DEBUG_MODEL
    return GAIA_DEBUG_MODEL
