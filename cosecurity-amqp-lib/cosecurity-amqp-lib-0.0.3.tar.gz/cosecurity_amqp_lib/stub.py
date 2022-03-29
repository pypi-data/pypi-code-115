import numpy as np

from setting import Setting
from typing import Any, Dict
from producer import Producer


class Stub:
    def __init__(self, destination:str) -> None:
        self._producer = Producer()
        self._destination = destination
    
    def _send(self, primitive:str, content:Dict[str, Any]) -> None:
        self._producer.send_message(
            destination_queue=self._destination, 
            primitive=primitive, 
            content=content
        )

class DetectionStub(Stub):
    def __init__(self):
        super().__init__(
            destination='detection_model'
        )

    def find_objects(self, camera_hash:str, image_hash:str, image:np.ndarray) -> None:
        self._send(
            primitive='find_objects',  
            content={
                'camera_hash': camera_hash,
                'image_hash': image_hash,
                'image': image
            }
        )
