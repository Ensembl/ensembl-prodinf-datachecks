from contextlib import contextmanager
import logging
from kombu import Connection, Exchange
from kombu.pools import producers


OPTIONS = {
    'serializer': 'json',
    'delivery_mode': 2,
    'retry': True,
    # 'compression': 'zlib',
    'retry_policy': {
        'max_retries': 3
    }
}


logger = logging.getLogger(__name__)


class AMQPPublisher:
    def __init__(self, uri, exchange_name, exchange_type='topic', routing_key=None, formatter=None, **options):
        self.connection = Connection(uri)
        self.exchange = Exchange(exchange_name, type=exchange_type)
        self.routing_key = routing_key
        self.formatter = formatter
        self.options = {**OPTIONS, **options}


    class AMQPProducer:
        def __init__(self, producer, exchange, routing_key, formatter, options):
            self.producer = producer
            self.exchange = exchange
            self.routing_key = routing_key
            self.formatter = formatter
            self.options = options

        def publish(self, msg, routing_key=None):
            body = self.formatter.format(msg) if self.formatter is not None else msg
            key = routing_key if routing_key else self.routing_key
            if not key:
                raise ValueError('Invalid routing_key: {} (Producer routing_key is: {})'.format(
                    routing_key, self.routing_key
                    ))
            self.producer.publish(body,
                                  exchange=self.exchange,
                                  routing_key=self.routing_key,
                                  declare=(self.exchange,),
                                  **self.options)
            logger.debug('Published AMQP message. Exchange: %s, Routing Key: %s, Body: %s',
                         self.exchange,
                         self.routing_key,
                         str(body))


    @contextmanager
    def acquire_producer(self, block=True):
        with producers[self.connection].acquire(block=block) as producer:
            yield self.AMQPProducer(producer,
                                    self.exchange,
                                    self.routing_key,
                                    self.formatter,
                                    self.options)

    def publish(self, msg, routing_key=None):
        with self.acquire_producer() as producer:
            producer.publish(msg, routing_key)

