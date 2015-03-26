# ebstarter
Sample set of python scripts to control Amazon Elastic Beanstalk Docker applications

Used RabbitMQ to process application commands such as create/rebuild/delete/deleteaged

Contains sample nginx virtual host configuration file and perl handler to run application on demand

Required rpm packages:
 rabbitmq-server
 python-pika
 python-demjson