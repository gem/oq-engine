import urllib
import urllib2

from celery.task import task

from openquake.engine import engine
from openquake.engine.db import models as oqe_models

DEFAULT_LOG_LEVEL = 'progress'


@task(ignore_result=True)
def run_hazard_calc(calc_id, migration_callback_url=None, owner_user=None,
                    results_url=None):
    """
    Run a hazard calculation given the calculation ID. It is assumed that the
    entire calculation profile is already loaded into the oq-engine database
    and is ready to execute.
    """
    job = oqe_models.OqJob.objects.get(hazard_calculation=calc_id)
    exports = []
    # TODO: Log to file somewhere. But where?
    log_file = None
    # NOTE: Supervision MUST be turned off, or else the celeryd cluster
    # handling this task will leak processes!!!
    engine.run_calc(job, DEFAULT_LOG_LEVEL, log_file, exports, 'hazard',
                    supervised=False)

    # If requested to, signal job completion and trigger a migration of
    # results.
    if not None in (migration_callback_url, owner_user, results_url):
        _trigger_migration(migration_callback_url, owner_user, results_url)


@task(ignore_result=True)
def run_risk_calc(calc_id, migration_callback_url=None, owner_user=None,
                  results_url=None):
    """
    Run a risk calculation given the calculation ID. It is assumed that the
    entire calculation profile is already loaded into the oq-engine database
    and is ready to execute.
    """
    job = oqe_models.OqJob.objects.get(risk_calculation=calc_id)
    exports = []
    # TODO: Log to file somewhere. But where?
    log_file = None
    # NOTE: Supervision MUST be turned off, or else the celeryd cluster
    # handling this task will leak processes!!!
    engine.run_calc(job, DEFAULT_LOG_LEVEL, log_file, exports, 'risk',
                    supervised=False)

    # If requested to, signal job completion and trigger a migration of
    # results.
    if not None in (migration_callback_url, owner_user, results_url):
        _trigger_migration(migration_callback_url, owner_user, results_url)


def _trigger_migration(callback_url, owner, import_url):
    """
    Helper function to initiate a post-calculation migration of results.

    :param str callback_url:
        A URL to POST a request to for pulling results out of the
        oq-engine-server.
    :param str owner:
        Username of the user who will be identified with the migrated results.
        This is a username relevant to the service which provides a response to
        the ``callback_url`` POST.
    :param str import_url:
        A location (hosted by the oq-engine-server) where a list of calculation
        results can be found. For example, this could be the URL
        `http://whatever.foo/v1/calc/hazard/1234/results`. See oq-engine-server
        docs for more details.
    """
    params = urllib.urlencode(dict(import_url=import_url, owner=owner))
    try:
        # post to an external service, asking it to pull calculation results
        url = urllib2.urlopen(callback_url, params)
    except urllib2.HTTPError:
        pass  # TODO: what to do with this?
    else:
        url.close()
