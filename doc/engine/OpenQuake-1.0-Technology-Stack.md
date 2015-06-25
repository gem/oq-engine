### Technology Stack

* Python - Implementation language
* Celery - Distributed task queue library
* Django - Used mostly just for its ORM
* Redis - KVS for progress counters and other calculation runtime information
* RabbitMQ - Message broker for Celery tasks, logging channels, and other signalling
* PostgreSQL/PostGIS - Persistent storage of calculation inputs/outputs
* Ubuntu Linux 12.04 LTS - Officially supported release platform

### Binary dependencies

Software  | Version(s)
--------- | ----------
Python | >= 2.7
RabbitMQ | 2.6, 2.7 and 2.8
Redis |
PostgreSQL | 9.1
PostGIS | 1.5


### Python dependencies

Software  | Version(s)
--------- | -----------
Celery | 2.4 and 2.5
Django | 1.3 and 1.4
Numpy | 1.6
Scipy | >= 0.9
lxml2 | >= 2.3
futures |
psutil |