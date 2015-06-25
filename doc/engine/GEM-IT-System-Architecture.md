Given the amount of data we are going to handle at GEM, our software must be able to scale across a large amount of computational resources. To achieve this, we built OpenQuake on top of some key concepts: we store our results into a distributed key-value store system, called [Redis](http://code.google.com/p/redis/), and we split the computational process into a set of tasks than can be distributed and executed across serveral remote machines. This job is done by a library called [Celery](http://celeryproject.org/).

The goal is being able to scale 1) on the amount of space we need to store the results 2) on the amount of power we need to speed up the overall computation. Below find an overview of the system architecture:
![System Architecture](http://openquake.org/wp-content/uploads/2011/03/Graph-architecture.jpg)

The diagram above is a simplified illustration of how computations are performed in OpenQuake.

* Computations are functions decorated with @task from Celery.
* Tasks are serialized and pushed into RabbitMQ’s task queue for processing while the application code waits for a task response.
* An available Celery daemon will pick up the task from RabbitMQ and spawn a worker to run the task.
* Celery workers can be distributed across multiple nodes/machines to easily scale computational resources.
* When the task is complete, the worker places a response in RabbitMQ’s task response queue.
* The worker will also store resultant data (if any) in the available KVS, where it can be accessed by the application code.

Back to [[Blueprints|BluePrints]]

Back to [Wiki Home](https://github.com/gem/oq-engine/wiki)
