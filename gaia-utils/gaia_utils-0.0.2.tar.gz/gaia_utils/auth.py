
# 全局信息
GAIA_TOKEN = ""


def set_token(token: str):
    """
        设置全局 key
    """
    global GAIA_TOKEN
    GAIA_TOKEN = token
    return


def get_token():
    global GAIA_TOKEN
    return GAIA_TOKEN


def request_login(func):
    def wrapper(*args, **kargs):
        global GAIA_TOKEN
        if not GAIA_TOKEN:
            print(f"执行 func {func.__name__} 需要设置 token ")
            return
        return func(*args, **kargs)
    return wrapper
