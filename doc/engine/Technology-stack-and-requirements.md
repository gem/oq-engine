### Technology Stack

* Python - Implementation language
* Celery - Distributed task queue library, usisng the `iterator_native()`
* Django - Used mostly just for its ORM
* RabbitMQ - Message broker for Celery tasks, logging channels, and other signalling
* PostgreSQL - Persistent storage of calculation inputs/outputs

### Binary dependencies

Software  | Version(s)
--------- | ----------
Python | 2.7
RabbitMQ | 2.6 to 3.2
PostgreSQL | 9.1 to 9.4
libgeos | >= 3.2.2


### Python dependencies

Software  | Version(s)
--------- | -----------
Celery | 2.4.6 to 3.1
Django | 1.6
Numpy | 1.6 to 1.8
Scipy | 0.9 to 0.13
h5py | >= 2.2.1
docutils |
futures | >= 2.1.6
psutil | < 3.0
