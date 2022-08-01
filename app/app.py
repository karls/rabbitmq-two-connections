import logging
import logging.config
import signal
import sys
import threading
import traceback
from time import sleep
from typing import Optional

from pika import ConnectionParameters, PlainCredentials
from pika.adapters import BlockingConnection
from pika.channel import Channel

logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {
            "simple": {"format": "[%(levelname)s] [thread:%(threadName)s] %(msg)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
            }
        },
        "loggers": {
            __name__: {
                "handlers": ["console"],
                "propagate": False,
                "level": "INFO",
            }
        },
        "root": {"handlers": ["console"]},
    }
)

logger = logging.getLogger(__name__)


class Publisher(threading.Thread):
    def __init__(
        self,
        connection_params: ConnectionParameters,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.daemon = True
        self.is_running = True
        self.name = "Publisher"
        self.queue = "downstream_queue"
        self.connection = BlockingConnection(connection_params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, auto_delete=True)
        self.channel.confirm_delivery()

    def run(self):
        # Uncomment `pass` and comment the `while` to simulate
        # the not handling heartbeats properly

        # pass

        while self.is_running:
            self.connection.process_data_events(time_limit=1)

    def _publish(self, message):
        logger.info("Calling '_publish'")
        self.channel.basic_publish("", self.queue, body=message.encode())

    def publish(self, message):
        logger.info("Calling 'publish'")
        self.connection.add_callback_threadsafe(lambda: self._publish(message))

    def stop(self):
        logger.info("Stopping...")
        self.is_running = False
        self.connection.sleep(2)
        if self.connection.is_open:
            self.connection.close()
            logger.info("Connection closed")
        logger.info("Stopped")


class Consumer:
    def __init__(
        self,
        connection_params: ConnectionParameters,
        publisher: Optional["Publisher"] = None,
    ):
        self.publisher = publisher
        self.queue = "upstream_queue"
        self.connection = BlockingConnection(connection_params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, auto_delete=True)
        self.channel.basic_qos(prefetch_count=1)

    def start(self):
        self.channel.basic_consume(
            queue=self.queue, on_message_callback=self.on_message
        )
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Warm shutdown requested...")
        except Exception:
            traceback.print_exception(*sys.exc_info())
        finally:
            self.stop()

    def on_message(self, _channel: Channel, m, _properties, body):
        try:
            message = body.decode()
            logger.info(f"Got: {message!r}")
            if self.publisher:
                self.publisher.publish(message)
            else:
                logger.info(f"No publisher provided, printing message: {message!r}")
            self.channel.basic_ack(delivery_tag=m.delivery_tag)
        except Exception:
            traceback.print_exception(*sys.exc_info())
            self.channel.basic_nack(delivery_tag=m.delivery_tag, requeue=False)

    def stop(self):
        logger.info("Stopping consuming...")
        if self.connection.is_open:
            logger.info("Closing connection...")
            self.connection.close()

        if self.publisher:
            self.publisher.stop()

        logger.info("Stopped")


if __name__ == "__main__":
    creds = PlainCredentials("guest", "guest")
    upstream_rmq = ConnectionParameters(
        host="rabbitmq_upstream",
        virtual_host="/",
        credentials=creds,
    )
    # The heartbeat value is set to a purposefully low number to demonstrate
    # that heartbeats are correctly handled
    downstream_rmq = ConnectionParameters(
        host="rabbitmq_downstream",
        virtual_host="/",
        credentials=creds,
        heartbeat=10,
    )

    publisher = Publisher(downstream_rmq)
    publisher.start()
    logger.info(f"Started Publisher")

    consumer = Consumer(upstream_rmq, publisher)
    logger.info(f"Started Consumer")
    logger.info(
        "Go to http://localhost:7001/#/queues/%2F/upstream_queue and post a message into the 'upstream_queue'."
    )
    try:
        consumer.start()
    except KeyboardInterrupt:
        consumer.stop()
