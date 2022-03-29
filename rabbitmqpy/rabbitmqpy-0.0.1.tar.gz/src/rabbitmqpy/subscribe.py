#coding:utf-8

import json
import logging
import pika
import functools
from pika.exchange_type import ExchangeType


class Subscriber(object):

    def __init__(self, amqp_url, exchange, exchange_type, queue, routing_key=None, **kwargs):
        self._connection = None
        self._channel = None
        self._url = amqp_url
        self._exchange = exchange
        self._exchange_type = exchange_type
        self._routing_key = routing_key
        self._queue = queue
        self._passive = kwargs.get("passive", False)
        self._durable = kwargs.get("durable", False)
        self._auto_delete = kwargs.get("auto_delete", True)
        self._auto_ack = kwargs.get("auto_ack", True)
        self.connect()

    def connect(self):
        print('Connecting to %s', self._url)
        self._connection = pika.BlockingConnection(
            pika.URLParameters(self._url))
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=self._exchange,
            exchange_type=self._exchange_type,
            passive=self._passive,
            durable=self._durable,
            auto_delete=self._auto_delete
        )
        self._channel.queue_declare(queue=self._queue, auto_delete=self._auto_delete)
        self._channel.queue_bind(
            queue=self._queue, exchange=self._exchange, routing_key=self._routing_key)
        self._channel.basic_qos(prefetch_count=1)

        on_message_callback = functools.partial(
            self.on_message, userdata='on_message_userdata')

        self._channel.basic_consume(self._queue, on_message_callback, auto_ack=self._auto_ack)


    def on_message(self, chan, method_frame, header_frame, body, userdata=None):
        print('Delivery properties: %s, message metadata: %s', method_frame, header_frame)
        print('Userdata: %s, message body: %s', userdata, body)
        # chan.basic_ack(delivery_tag=method_frame.delivery_tag)


    def start(self):
        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            self._channel.stop_consuming()

    def __del__(self):
        self._connection.close()


if __name__=='__main__':

    subs = Subscriber(
        'amqp://10.12.3.162:31911',
        'imlf-1',
        'direct',
        'predict',
        'predict'
    )
    subs.start()
