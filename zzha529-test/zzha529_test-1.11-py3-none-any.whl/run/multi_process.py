import json
import time
import multiprocessing
import traceback

from run.exception.local_exceptions import NumberProcessException
from run.redis_connector import RedisPool

pool = RedisPool()


# rpop from redis given key as list name
# return rpop result
def single_start(key, pid, func):
    """
    read list-key from redis,
    pop list element,
    call function with popped element as param
    :param key: model name defined in tool and model
    :param pid: process id
    :param func: call model function
    """
    # conn = s_list[0]
    # key = s_list[1]
    print('process start: 【'+str(pid)+'】')
    conn = pool.connector()

    while True:
        val = conn.brpop(key)
        print(id, val[1])

        # do ack
        # do persistance work

        val_json = json.loads(val[1])

        try:
            func(val_json)
            # do exception work
        except:
            traceback.print_exc()
            conn.lpush('failed_'+key, val[1])


def start(key: str, func, np: int = 5):
    """
    call np number of processes,
    do work
    :param key: model name defined in tool and model
    :param func: call model function
    :param np: number of processes, default 5
    """

    if np < 1:
        raise NumberProcessException(np)
        return

    for i in range(np):
        p = multiprocessing.Process(target=single_start, kwargs={"key": key, "pid": i, "func": func})
        p.start()
        time.sleep(0.5)
