#!/usr/bin/env python
import pika
import sys
import signal
import json
import logging
from optparse import OptionParser

counter = 0

def on_message(channel, method_frame, header_frame, body):
    logging.debug("Count: "+str(counter))
    logging.debug(method_frame.delivery_tag)
    logging.debug(body)
    logging.debug(header_frame)
    try:
        command = json.loads(body)
        logging.info("Command: "+command["operation"]+" for: "+command["name"]+", source is: "+command["source"])
    except:
        logging.exception("Can't convert body to json: "+str(sys.exc_info()[0]))
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)

def signal_handler(sig, frame):
    logging.info("Interrupted with: "+str(sig)+", exit now!")
    channel.stop_consuming()
    connection.close()
    sys.exit(0)

parser = OptionParser()

parser.add_option("-q", "--queue", help="queue name", type="string", dest="queue", default="test")
parser.add_option("-l", "--log-level", help="log level", dest="log_level", type="int", default=1)

(options, args) = parser.parse_args()

if options.log_level == 1:
    log_level = logging.INFO
elif options.log_level >= 2:
    log_level = logging.DEBUG

logging.basicConfig(level=log_level)

logging.info("Start reciever on queue: "+options.queue)

signal.signal(signal.SIGHUP, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGQUIT, signal_handler)

connection = pika.BlockingConnection()
channel = connection.channel()
channel.queue_declare(queue=options.queue)
channel.basic_consume(on_message, queue=options.queue)
channel.start_consuming()

