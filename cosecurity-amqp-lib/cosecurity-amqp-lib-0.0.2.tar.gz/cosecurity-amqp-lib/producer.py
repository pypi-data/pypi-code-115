import json
import numpy as np

from logger import logger
from setting import Setting
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
    def __init__(self) -> None:
        self._host = Setting.get('AMQP', 'HOST')
        self._heartbeat = Setting.get_bool('AMQP', 'HEARTBEAT')

    def send_message(self, destination:str, primitive:str, content:Dict[str, Any]) -> None:
        destination_queue = Setting.get('QUEUE', destination.upper(), None)
        if destination_queue is None:
            raise Exception('Recipient queue not found in configuration file, please review!')

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
        
        logger.info(f'Sent to {destination}')
