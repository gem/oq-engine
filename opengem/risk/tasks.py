"""
Generic Tasks for testing celery
"""

from celery.decorators import task

@task
def risk_add(x, y):
    return x + y