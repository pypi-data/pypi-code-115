import json
import numpy as np

from typing import Any, Dict
from json import JSONEncoder
from pika import BlockingConnection, ConnectionParameters


class ProducerEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

class ProducerChannel:
    def __init__(self, host:str, heartbeat:bool):
        self._connection = BlockingConnection(
            ConnectionParameters(
                host=host, 
                heartbeat=heartbeat
            )
        )
        self._channel = self._connection.channel()

    def __enter__(self):
        return self

    def __exit__(self, type:Any, value:Any, traceback:Any):
        self._channel.close()
        self._connection.close()


class Producer:
    def __init__(self, host:str, heartbeat:bool=False) -> None:
        self._host = host
        self._heartbeat = heartbeat

    def send_message(self, destination_queue:str, primitive:str, content:Dict[str, Any]) -> None:
        with ProducerChannel(self._host, self._heartbeat) as channel:
            channel.basic_publish(
                exchange='', 
                routing_key=destination_queue, 
                body=json.dumps(
                    obj={ 
                        'primitive': primitive, 
                        'content': content 
                    }, 
                    cls=ProducerEncoder
                )
            )
            print(f'Sent to {destination_queue}')
