# -*- encoding: utf-8 -*-
# @Author: haogooder
# @Date:
# @Description:
import json
from typing import Union, Dict, List

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError


class RecordMeta:
    def __init__(self, topic: str, partition: str, offset: int):
        self.topic = topic
        self.partition = partition
        self.offset = offset


class KafkaProducerUtil(object):
    def __init__(self, brokers, retry=30):
        self.producer = KafkaProducer(bootstrap_servers=brokers,
                                      value_serializer=lambda m: json.dumps(m, ensure_ascii=False).encode('utf-8'),
                                      retries=retry)

    def get_producer(self):
        """
        获取producer
        :return:
        """
        return self.producer

    def send_async(self, topic: str, value: Union[Dict | List | str | int | float], key: bytes,
                   callback=None, errback=None):
        future = self.producer.send(topic=topic, value=value, key=key)
        if callback:
            future.add_callback(callback)
        if errback:
            future.add_errback(errback)

    def flush(self, timeout: int = None):
        self.producer.flush(timeout)

    def send_sync(self, topic: str, value: Union[Dict | List | str | int | float], key: bytes) -> RecordMeta:
        future = self.producer.send(topic=topic, value=value, key=key)
        try:
            record_metadata = future.get(timeout=10)
            topic = record_metadata.topic
            partition = record_metadata.partition
            offset = record_metadata.offset
            return RecordMeta(topic=topic, partition=partition, offset=offset)
        except KafkaError:
            # Decide what to do if produce request failed...
            pass


class KafkaConsumerUtil(object):
    def __init__(self, brokers, topic, group_id,
                 is_earliest=False, auto_commit=True):
        self.is_earliest = is_earliest
        if self.is_earliest:
            auto_offset_reset = "earliest"
        else:
            auto_offset_reset = "latest"
        self.auto_commit = auto_commit
        self.consumer = KafkaConsumer(topic, group_id=group_id, bootstrap_servers=brokers,
                                      auto_offset_reset=auto_offset_reset, enable_auto_commit=self.auto_commit,
                                      value_deserializer=lambda m: json.loads(m.decode('utf-8')))

    def get_consumer(self):
        """

        :return:
        """
        return self.consumer


if __name__ == "__main__":
    pass
