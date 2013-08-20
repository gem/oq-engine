from celery.task import task

from openquake.engine import engine
from openquake.engine.db import models as oqe_models

DEFAULT_LOG_LEVEL = 'progress'


@task(ignore_result=True)
def run_hazard_calc(calc_id):
    """
    Run a hazard calculation given the calculation ID. It is assumed that the
    entire calculation profile is already loaded into the oq-engine database
    and is ready to execute.
    """
    job = oqe_models.OqJob.objects.get(hazard_calculation=calc_id)
    exports = []
    # TODO: Log to file somewhere. But where?
    log_file = None
    engine.run_calc(job, DEFAULT_LOG_LEVEL, log_file, exports, 'hazard')
    # TODO: Signal job completion somehow.


@task(ignore_result=True)
def run_risk_calc(calc_id):
    """
    Run a risk calculation given the calculation ID. It is assumed that the
    entire calculation profile is already loaded into the oq-engine database
    and is ready to execute.
    """
    job = oqe_models.OqJob.objects.get(risk_calculation=calc_id)
    exports = []
    # TODO: Log to file somewhere. But where?
    log_file = None
    engine.run_calc(job, DEFAULT_LOG_LEVEL, log_file, exports, 'risk')
    # TODO: Signal job completion somehow.
