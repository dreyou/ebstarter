#!/usr/bin/env python
import pika
import json
from optparse import OptionParser
import logging

parser = OptionParser()

parser.add_option("-a", "--application", help="application name", type="string", dest="name", default="")
parser.add_option("-o", "--operation", help="operation create|update|delete", type="string", dest="operation", default="")
parser.add_option("-s", "--source", help="s3 source url", type="string", dest="source", default="")
parser.add_option("-q", "--queue", help="queue name", type="string", dest="queue", default="test")
parser.add_option("-l", "--log-level", help="log level", dest="log_level", type="int", default=1)

(options, args) = parser.parse_args()

if options.log_level == 1:
    log_level = logging.INFO
elif options.log_level >= 2:
    log_level = logging.DEBUG

logging.basicConfig(level=log_level)

logging.info("Send data to queue: "+options.queue)

connection = pika.BlockingConnection()

channel = connection.channel()
channel.exchange_declare(exchange='commands', type='fanout')
channel.queue_bind(exchange='commands', queue=options.queue)

message = dict()
message["name"] = options.name
message["operation"] = options.operation
message["source"] = options.source

message_json = json.dumps(message)

logging.debug("Sending json: "+str(message_json))

channel.basic_publish("commands", "", message_json)

connection.close()