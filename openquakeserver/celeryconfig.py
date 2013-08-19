import os

BROKER_HOST = 'localhost'
BROKER_PORT = 5672
BROKER_USER = 'guest'
BROKER_PASSWORD = 'guest'
BROKER_VHOST = '/'

CELERY_RESULT_BACKEND = 'amqp'
CELERY_DEFAULT_QUEUE = 'oqengineserver'
CELERY_DEFAULT_EXCHANGE = 'oqengineserver'
CELERY_DEFAULT_ROUTING_KEY = 'oqengineserver'

# CELERY_ACKS_LATE and CELERYD_PREFETCH_MULTIPLIER settings help evenly
# distribute tasks across the cluster. This configuration is intended
# make worker processes reserve only a single task at any given time.
# (The default settings for prefetching define that each worker process will
# reserve 4 tasks at once. For long running calculations with lots of long,
# heavy tasks, this greedy prefetching is not recommended and can result in
# performance issues with respect to cluster utilization.)
CELERY_ACKS_LATE = True
CELERYD_PREFETCH_MULTIPLIER = 1

CELERY_IMPORTS = ('engine.tasks', )

os.environ['DJANGO_SETTINGS_MODULE'] = 'openquake.engine.settings'
