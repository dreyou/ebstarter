#!/usr/bin/env python
import pika
import sys
import signal
import json
import logging
from optparse import OptionParser
import eblocal

def createApplication(command):
    res = eblocal.createApp(command["name"], command["source"])
    if res is None:
        logging.error("Can't create application")
        return
    res = eblocal.createEnv(command["name"], command["source"])
    if res is None:
        logging.error("Can't create application environment, deleting application")
        eblocal.deleteApp(command["name"])
        return
    logging.info("Application: "+command["name"]+" created")

def rebuildApplicationEnvironment(command):
    res = eblocal.getEnv(command["name"])
    if res is None:
        logging.error("No application environment present, creating")
        createApplication(command)
        return
    res = eblocal.rebuildEnv(command["name"])
    if res is None:
        logging.error("Can't rebuild environment")

def deleteApplication(command):
    res = eblocal.deleteApp(command["name"])
    if res is None:
        logging.error("Can't delete application")

def deleteAgedApplication(command):
    age = eblocal.getEnvAge(command["name"])
    if age is None:
        logging.error("Can't detect environment age")
        return
    if age < options.max_age:
        return
    logging.info("Environment age > "+str(options.max_age)+" hrs, deleting.")
    res = eblocal.deleteApp(command["name"])
    if res is None:
        logging.error("Can't delete application")

operations = dict()
operations['create'] = createApplication
operations['rebuild'] = rebuildApplicationEnvironment
operations['delete'] = deleteApplication
operations['deleteaged'] = deleteAgedApplication

def on_message(channel, method_frame, header_frame, body):
    logging.debug(method_frame.delivery_tag)
    logging.debug(body)
    logging.debug(header_frame)
    try:
        command = json.loads(body)
        logging.info("Command: "+command["operation"]+" for: "+command["name"]+", source is: "+command["source"])
        if command["operation"] in operations:
            if options.run == "yes":
                logging.info("Run operation: "+command["operation"])
                operations[command["operation"]](command)
            else:
                logging.info("Simulate run operation: "+command["operation"])
    except:
        logging.exception("Error while running command: "+str(sys.exc_info()[0]))
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)

def signal_handler(sig, frame):
    logging.info("Interrupted with: "+str(sig)+", exit now!")
    channel.stop_consuming()
    connection.close()
    sys.exit(0)

parser = OptionParser()

parser.add_option("-r", "--run", type="string", help="if not set to \"yes\", do really nothing, just accept messages", dest="run", default="no")
parser.add_option("-q", "--queue", help="queue name", type="string", dest="queue", default="test")
parser.add_option("-l", "--log-level", help="log level", dest="log_level", type="int", default=1)
parser.add_option("-m", "--max-age", help="maximum application age in hours", dest="max_age", type="int", default=6)

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
channel.exchange_declare(exchange='commands', type='fanout')
channel.queue_bind(exchange='commands', queue=options.queue)
channel.basic_consume(on_message, queue=options.queue)
channel.start_consuming()

