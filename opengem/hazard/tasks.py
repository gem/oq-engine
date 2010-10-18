"""
Generic Tasks for testing celery
"""

from celery.decorators import task

@task
def hazard_add(x, y):
    return x + y