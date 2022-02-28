import logging
import sys

from confluent_kafka import Consumer, KafkaException


def get_logger():
    """
    Create logger for consumer (logs will be emitted when poll() is called)
    """
    logger = logging.getLogger('consumer')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)-15s %(levelname)-8s %(message)s'))
    logger.addHandler(handler)
    return logger


def print_assignment(consumer, partitions):
    print('Assignment:', partitions)


def run():
    settings: dict = {}
    kwargs: dict = {}
    topics: list = []
    logger = get_logger()
    c = Consumer(settings, logger=logger, **kwargs)
    # Subscribe to topics
    c.subscribe(topics, on_assign=print_assignment)
    while True:
        logger.info("start")
        msg = c.poll(timeout=1.0)
        if msg is None:
            logger.info("get None")
            continue
        if msg.error():
            logger.error("KafkaException")
            raise KafkaException(msg.error())
        else:
            # Proper message
            sys.stderr.write('%% %s [%d] at offset %d with key %s:\n' %
                             (msg.topic(), msg.partition(), msg.offset(),
                              str(msg.key())))
            print(msg.value())


if __name__ == '__main__':
    run()
