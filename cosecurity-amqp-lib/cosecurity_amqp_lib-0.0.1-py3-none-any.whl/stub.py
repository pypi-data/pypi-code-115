import numpy as np

from setting import Setting
from typing import Any, Dict
from producer import Producer


class Stub:
    def __init__(self, destination_queue:str) -> None:
        self._producer = Producer(host=Setting.get('AMQP', 'HOST'))
        self._queue_name = destination_queue
    
    def _send(self, primitive:str, content:Dict[str, Any]) -> None:
        self._producer.send_message(
            destination_queue=self._queue_name, 
            primitive=primitive, 
            content=content
        )

class DetectionStub(Stub):
    def __init__(self):
        super().__init__(Setting.get('QUEUE', 'DETECTION_MODEL'))

    def find_objects(self, camera_hash:str, image_hash:str, image:np.ndarray) -> None:
        self._send(
            primitive='find_objects',  
            content={
                'camera_hash': camera_hash,
                'image_hash': image_hash,
                'image': image
            }
        )
