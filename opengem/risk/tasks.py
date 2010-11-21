# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Tasks in the risk engine include the following:

 * Input parsing
 * Various calculation steps
 * Output generation
"""

from celery.decorators import task

from opengem import flags
from opengem import job
from opengem.job import mixins
from opengem import kvs 
from opengem import risk

from opengem.risk import engines
from opengem.risk import job as riskjob

FLAGS = flags.FLAGS



@task
def compute_risk(job_id, block_id, conditional_loss_poe=None, **kwargs):
    engine = job.Job.from_kvs(job_id)
    with mixins.Mixin(engine, riskjob.RiskJobMixin, key="risk") as mixed:
        mixed.compute_risk(block_id, conditional_loss_poe, **kwargs)


