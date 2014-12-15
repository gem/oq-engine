# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Helper functions for our unit and smoke tests.
"""

import functools
import logging
import mock as mock_module
import numpy
import os
import csv
import random
import shutil
import string
import sys
import tempfile
import textwrap
import time

from django.core import exceptions

from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.tom import PoissonTOM
from openquake.baselib.general import writetmp as touch

from openquake.engine.db import models
from openquake.engine import engine
from openquake.engine import logs
from openquake.engine.utils import config

CD = os.path.dirname(__file__)  # current directory

RUNNER = os.path.abspath(os.path.join(CD, '../../../../bin/oq-engine'))

DATA_DIR = os.path.abspath(os.path.join(CD, '../data'))

OUTPUT_DIR = os.path.abspath(os.path.join(CD, '../data/output'))

WAIT_TIME_STEP_FOR_TASK_SECS = 0.5
MAX_WAIT_LOOPS = 10


#: Wraps mock.patch() to make mocksignature=True by default.
patch = functools.partial(mock_module.patch, mocksignature=True)


def default_user():
    """Return the default user to be used for test setups."""
    return "openquake"


def _patched_mocksignature(func, mock=None, skipfirst=False):
    """
    Fixes arguments order and support of staticmethods in mock.mocksignature.
    """
    static = False
    if isinstance(func, staticmethod):
        static = True
        func = func.__func__

    if mock is None:
        mock = mock_module.Mock()
    signature, func = mock_module._getsignature(func, skipfirst)

    checker = eval("lambda %s: None" % signature)
    mock_module._copy_func_details(func, checker)

    def funcopy(*args, **kwargs):
        checker(*args, **kwargs)
        return mock(*args, **kwargs)

    if not hasattr(mock_module, '_setup_func'):
        # compatibility with mock < 0.8
        funcopy.mock = mock
    else:
        mock_module._setup_func(funcopy, mock)
    if static:
        funcopy = staticmethod(funcopy)
    return funcopy
mock_module.mocksignature = _patched_mocksignature


def get_data_path(file_name):
    return os.path.join(DATA_DIR, file_name)


def demo_file(file_name):
    """
    Take a file name and return the full path to the file in the demos
    directory.
    """
    return os.path.join(
        os.path.dirname(__file__), "../../demos", file_name)


def run_job(cfg, exports='xml,csv', hazard_calculation_id=None,
            hazard_output_id=None, **params):
    """
    Given the path to a job config file and a hazard_calculation_id
    or a output, run the job.

    :returns: a calculator object
    """
    job = get_job(cfg, hazard_calculation_id=hazard_calculation_id,
                  hazard_output_id=hazard_output_id, **params)
    job.is_running = True
    job.save()

    logfile = os.path.join(tempfile.gettempdir(), 'qatest.log')

    return engine.run_calc(job, 'error', logfile, exports)


def timeit(method):
    """Decorator for timing methods"""

    def _timed(*args, **kw):
        """Wrapped function for timed methods"""
        timestart = time.time()
        result = method(*args, **kw)
        timeend = time.time()

        print '%r (%r, %r) %2.2f sec' % (
            method.__name__, args, kw, timeend - timestart)
        return result
    try:
        import nose
        return nose.tools.make_decorator(method)(_timed)
    except ImportError:
        pass
    return _timed


def assertDeepAlmostEqual(test_case, expected, actual, *args, **kwargs):
    """
    Assert that two complex structures have almost equal contents.

    Compares lists, dicts and tuples recursively. Checks numeric values
    using test_case's :py:meth:`unittest.TestCase.assertAlmostEqual` and
    checks all other values with :py:meth:`unittest.TestCase.assertEqual`.
    Accepts additional positional and keyword arguments and pass those
    intact to assertAlmostEqual() (that's how you specify comparison
    precision).

    :param test_case: TestCase object on which we can call all of the basic
        'assert' methods.
    :type test_case: :py:class:`unittest.TestCase` object
    """
    is_root = not '__trace' in kwargs
    trace = kwargs.pop('__trace', 'ROOT')
    try:
        if isinstance(expected, (int, float, long, complex)):
            test_case.assertAlmostEqual(expected, actual, *args, **kwargs)
        elif isinstance(expected, (list, tuple, numpy.ndarray)):
            test_case.assertEqual(len(expected), len(actual))
            for index in xrange(len(expected)):
                v1, v2 = expected[index], actual[index]
                assertDeepAlmostEqual(test_case, v1, v2,
                                      __trace=repr(index), *args, **kwargs)
        elif isinstance(expected, dict):
            test_case.assertEqual(set(expected), set(actual))
            for key in expected:
                assertDeepAlmostEqual(test_case, expected[key], actual[key],
                                      __trace=repr(key), *args, **kwargs)
        else:
            test_case.assertEqual(expected, actual)
    except AssertionError as exc:
        exc.__dict__.setdefault('traces', []).append(trace)
        if is_root:
            trace = ' -> '.join(reversed(exc.traces))
            exc = AssertionError("%s\nTRACE: %s" % (exc.message, trace))
        raise exc


def assertModelAlmostEqual(test_case, expected, actual):
    """
    Assert that two Django models are equal. For values which are numbers,
    we use :py:meth:`unittest.TestCase.assertAlmostEqual` for number
    comparisons with a reasonable precision tolerance.

    If the `expected` input value contains nested models, this function
    will recurse through them and check for equality.

    :param test_case: TestCase object on which we can call all of the basic
        'assert' methods.
    :type test_case: :py:class:`unittest.TestCase` object
    :type expected: dict
    :type actual: dict
    """

    from django.contrib.gis.db import models as gis_models

    test_case.assertEqual(type(expected), type(actual))

    def getattr_or_none(model, field):
        try:
            return getattr(model, field.name)
        except exceptions.ObjectDoesNotExist:
            return None

    for field in expected._meta.fields:
        if field.name == 'last_update':
            continue

        exp_val = getattr_or_none(expected, field)
        act_val = getattr_or_none(actual, field)

        # If it's a number, use assertAlmostEqual to compare
        # the values with a reasonable tolerance.
        if isinstance(exp_val, (int, float, long, complex)):
            test_case.assertAlmostEqual(exp_val, act_val)
        elif isinstance(exp_val, gis_models.Model):
            # make a recursive call in case there are nested models
            assertModelAlmostEqual(test_case, exp_val, act_val)
        else:
            test_case.assertEqual(exp_val, act_val)


# preserve stdout/stderr (note: we want the nose-manipulated stdout/stderr,
# otherwise we could just use __stdout__/__stderr__)
STDOUT = sys.stdout
STDERR = sys.stderr


def cleanup_loggers():
    root = logging.getLogger()

    for h in list(root.handlers):
        if (isinstance(h, logging.FileHandler) or
            isinstance(h, logging.StreamHandler) or
                isinstance(h, logs.AMQPHandler)):
            root.removeHandler(h)

    # restore the damage created by redirect_stdouts_to_logger; this is only
    # necessary because tests perform multiple log initializations, sometimes
    # for AMQP, sometimes for console
    sys.stdout = STDOUT
    sys.stderr = STDERR


class ConfigTestCase(object):
    """Class which contains various configuration- and environment-related
    testing helpers."""

    def setup_config(self):
        self.orig_env = os.environ.copy()
        os.environ.clear()
        # Move the local configuration file out of the way if it exists.
        # Otherwise the tests that follow will break.
        local_path = "%s/openquake.cfg" % os.path.abspath(config.OQDIR)
        if os.path.isfile(local_path):
            shutil.move(local_path, "%s.test_bakk" % local_path)

    def teardown_config(self):
        os.environ.clear()
        os.environ.update(self.orig_env)
        # Move the local configuration file back into place if it was stashed
        # away.
        local_path = "%s/openquake.cfg" % os.path.abspath(config.OQDIR)
        if os.path.isfile("%s.test_bakk" % local_path):
            shutil.move("%s.test_bakk" % local_path, local_path)
        config.cfg.cfg.clear()
        config.cfg._load_from_file()

    def prepare_config(self, section, data=None):
        """Set up a configuration with the given `max_mem` value."""
        if data is not None:
            data = '\n'.join(["%s=%s" % item for item in data.iteritems()])
            content = """
                [%s]
                %s""" % (section, data)
        else:
            content = ""
        site_path = touch(content=textwrap.dedent(content))
        os.environ["OQ_SITE_CFG_PATH"] = site_path
        config.cfg.cfg.clear()
        config.cfg._load_from_file()


def random_string(length=16):
    """Generate a random string of the given length."""
    result = ""
    while len(result) < length:
        result += random.choice(string.letters + string.digits)
    return result


def get_job(cfg, username="openquake", hazard_calculation_id=None,
            hazard_output_id=None, **extras):
    """
    Given a path to a config file and a hazard_calculation_id
    (or, alternatively, a hazard_output_id, create a
    :class:`openquake.engine.db.models.OqJob` object for a risk calculation.
    """
    if hazard_output_id and not hazard_calculation_id:
        hazard_calculation_id = models.Output.objects.get(
            pk=hazard_output_id).oq_job.id
    return engine.job_from_file(
        cfg, username, 'error', [],
        hazard_calculation_id=hazard_calculation_id,
        hazard_output_id=hazard_output_id, **extras)


def create_gmf_sescoll(output, output_type='gmf'):
    """
    Returns Gmf and SESCollection instances.

    :param output: a :class:`openquake.engine.db.models.Ouput` instance
    :param output_type: a string with the output type
    """
    sescoll = models.SESCollection.create(output)

    rlz = models.LtRealization.objects.create(
        lt_model=sescoll.trt_model.lt_model, ordinal=0, weight=1,
        gsim_lt_path="test_gsim")

    gmf = models.Gmf.objects.create(
        output=models.Output.objects.create_output(
            output.oq_job, "Test Hazard output", output_type),
        lt_realization=rlz)

    return gmf, sescoll


def create_gmf_data_records(hazard_job, coordinates=None):
    """
    Returns the created records.

    :param hazard_joint: a :class:`openquake.engine.db.models.OqJob` instance
    :param coordinates: a list of (lon, lat) pairs

    If the coordinates are not set, a list of 5 predefined locations is used
    """
    output = models.Output.objects.create_output(
        hazard_job, "Test SES Collection", "ses")
    gmf, ses_coll = create_gmf_sescoll(output)
    ruptures = create_ses_ruptures(hazard_job, ses_coll, 3)
    records = []
    if coordinates is None:
        coordinates = [(15.310, 38.225), (15.71, 37.225),
                       (15.48, 38.091), (15.565, 38.17),
                       (15.481, 38.25)]
    for site_id in models.save_sites(hazard_job, coordinates):
        records.append(models.GmfData.objects.create(
            gmf=gmf,
            task_no=0,
            imt="PGA",
            gmvs=[0.1, 0.2, 0.3],
            rupture_ids=[r.id for r in ruptures],
            site_id=site_id))

    return records


def create_gmf_from_csv(job, fname, output_type='gmf'):
    """
    Populate the gmf_data table for an event_based (default)
    or scenario calculation (output_type="gmf_scenario").

    :param job: an :class:`openquake.engine.db.models.OqJob` instance
    :param output_type: a string with the output type
    """
    hc = job.get_oqparam()
    if output_type == "gmf":  # event based
        hc.investigation_time = 50
        hc.ses_per_logic_tree_path = 1

    # tricks to fool the oqtask decorator
    job.is_running = True
    job.status = 'post_processing'
    job.save()

    output = models.Output.objects.create_output(
        job, "Test SES Collection", "ses")
    gmf, ses_coll = create_gmf_sescoll(output, output_type=output_type)

    with open(fname, 'rb') as csvfile:
        gmfreader = csv.reader(csvfile, delimiter=',')
        locations = gmfreader.next()

        gmv_matrix = numpy.array(
            [map(float, row) for row in gmfreader]).transpose()

        ruptures = create_ses_ruptures(job, ses_coll, len(gmv_matrix[0]))

        for i, gmvs in enumerate(gmv_matrix):
            point = tuple(map(float, locations[i].split()))
            [site_id] = models.save_sites(job, [point])
            models.GmfData.objects.create(
                gmf=gmf,
                task_no=0,
                imt="PGA", gmvs=gmvs,
                rupture_ids=[r.id for r in ruptures],
                site_id=site_id)

    return gmf


def get_fake_risk_job(risk_cfg, hazard_cfg, output_type="curve",
                      username="openquake"):
    """
    Takes in input the paths to a risk job config file and a hazard job config
    file.

    Creates fake hazard outputs suitable to be used by a risk
    calculation and then creates a :class:`openquake.engine.db.models.OqJob`
    object for a risk calculation. It also returns the input files
    referenced by the risk config file.

    :param output_type: gmf, gmf_scenario, or curve
    """

    hazard_job = get_job(hazard_cfg, username)
    hc = hazard_job.get_oqparam()

    lt_model = models.LtSourceModel.objects.create(
        hazard_calculation=hazard_job,
        ordinal=1, sm_lt_path="test_sm")

    rlz = models.LtRealization.objects.create(
        lt_model=lt_model, ordinal=1, weight=1,
        gsim_lt_path="test_gsim")

    if output_type == "curve":
        models.HazardCurve.objects.create(
            lt_realization=rlz,
            output=models.Output.objects.create_output(
                hazard_job, "Test Hazard output", "hazard_curve_multi"),
            investigation_time=hc.investigation_time)

        hazard_output = models.HazardCurve.objects.create(
            lt_realization=rlz,
            output=models.Output.objects.create_output(
                hazard_job, "Test Hazard output", "hazard_curve"),
            investigation_time=hc.investigation_time,
            imt="PGA", imls=[0.1, 0.2, 0.3])

        for point in ["POINT(-1.01 1.01)", "POINT(0.9 1.01)",
                      "POINT(0.01 0.01)", "POINT(0.9 0.9)"]:
            models.HazardSite.objects.create(
                hazard_calculation=hazard_job, location=point)
            models.HazardCurveData.objects.create(
                hazard_curve=hazard_output,
                poes=[0.1, 0.2, 0.3],
                location="%s" % point)

    elif output_type == "gmf_scenario":
        hazard_output = models.Gmf.objects.create(
            output=models.Output.objects.create_output(
                hazard_job, "Test gmf scenario output", "gmf_scenario"))

        models.SESCollection.create(
            output=models.Output.objects.create_output(
                hazard_job, "Test SES Collection", "ses"))
        site_ids = models.save_sites(
            hazard_job,
            [(15.48, 38.0900001), (15.565, 38.17), (15.481, 38.25)])
        for site_id in site_ids:
            models.GmfData.objects.create(
                gmf=hazard_output,
                task_no=0,
                imt="PGA",
                site_id=site_id,
                gmvs=[0.1, 0.2, 0.3],
                rupture_ids=[0, 1, 2])

    elif output_type in ("ses", "gmf"):
        hazard_output = create_gmf_data_records(hazard_job)[0].gmf

    else:
        raise RuntimeError('Unexpected output_type: %s' % output_type)

    hazard_job.status = "complete"
    hazard_job.save()
    risk_job = get_job(risk_cfg, username,
                       hazard_output_id=hazard_output.output.id)
    return risk_job, set(risk_job.get_param('inputs'))


def create_ses_ruptures(job, ses_collection, num):
    """
    :param job:
        the current job, an instance of `openquake.engine.db.models.OqJob`
    :param ses_collection:
        an instance of :class:`openquake.engine.db.models.SESCollection`
        to be associated with the newly created SES object
    :param int num:
        the number of ruptures to create
    :returns:
        a list of newly created ruptures associated with `job`.

    It also creates a father :class:`openquake.engine.db.models.SES`.
    Each rupture has a magnitude ranging from 0 to 10 and no geographic
    information.
    """
    rupture = ParametricProbabilisticRupture(
        mag=1 + 10. / float(num), rake=0,
        tectonic_region_type="test region type",
        hypocenter=Point(0, 0, 0.1),
        surface=PlanarSurface(
            10, 11, 12, Point(0, 0, 1), Point(1, 0, 1),
            Point(1, 0, 2), Point(0, 0, 2)),
        occurrence_rate=1,
        temporal_occurrence_model=PoissonTOM(10),
        source_typology=object())
    ses_ordinal = 1
    seed = 42
    pr = models.ProbabilisticRupture.create(rupture, ses_collection)
    return [models.SESRupture.create(pr, ses_ordinal, 'test', 1, i, seed + i)
            for i in range(num)]


class MultiMock(object):
    """
    Context-managed multi-mock object. This is useful if you need to mock
    multiple things at once. So instead of creating individual patch+mock
    objects for each, you can define them basically as a dictionary. You can
    also use the mock context managers without having to nest `with`
    statements.

    Example usage:

    .. code-block:: python

        # First, define your mock targets as a dictionary.
        # The value of each item is the path to the function/method you wish to
        # mock. The key is basically a shortcut to the mock.
        mocks = {
            'touch': 'openquake.engine.engine.touch_log_file',
            'job': 'openquake.engine.engine.job_from_file',
        }
        multi_mock = MultiMock(**mocks)

        # To start mocking, start the context manager using `with`:
        # with multi_mock:
        with multi_mock:
            # You can mock return values, for example, just as you would with
            # any other Mock object:
            multi_mock['job'].return_value = 'foo'

            # call the function under test which will calls the mocked
            # functions
            engine.run_job('job.ini', 'debug', 'oq.log', ['geojson'])

            # To test the mocks, you can simply access each mock from
            # `multi_mock` like a dict:
            assert multi_mock['touch'].call_count == 1
    """

    def __init__(self, **mocks):
        # dict of mock names -> mock paths
        self._mocks = mocks
        self.active_patches = {}
        self.active_mocks = {}

    def __enter__(self):
        for key, value in self._mocks.iteritems():
            the_patch = mock_module.patch(value)
            self.active_patches[key] = the_patch
            self.active_mocks[key] = the_patch.start()
        return self

    def __exit__(self, *args):
        for each_mock in self.active_mocks.itervalues():
            each_mock.stop()
        for each_patch in self.active_patches.itervalues():
            each_patch.stop()

    def __iter__(self):
        return self.active_mocks.itervalues()

    def __getitem__(self, key):
        return self.active_mocks.get(key)
