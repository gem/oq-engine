# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2012, GEM Foundation.
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

import collections
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

from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture
from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo.surface.planar import PlanarSurface
from openquake.hazardlib.tom import PoissonTOM

from django.core import exceptions

from openquake.engine.db import models
from openquake.engine import engine
from openquake.engine import logs
from openquake.engine.utils import config, get_calculator_class
from openquake.engine.job.validation import validate


CD = os.path.dirname(__file__)  # current directory

RUNNER = os.path.abspath(os.path.join(CD, '../../../../bin/openquake'))

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


def run_job(cfg, exports=None, hazard_calculation_id=None,
            hazard_output_id=None):
    """
    Given the path to a job config file and a hazard_calculation_id
    or a output, run the job.
    """
    if exports is None:
        exports = []

    job = get_job(cfg, hazard_calculation_id=hazard_calculation_id,
                  hazard_output_id=hazard_output_id)
    job.is_running = True
    job.save()

    models.JobStats.objects.create(oq_job=job)

    if hazard_calculation_id or hazard_output_id:
        rc = job.risk_calculation
        calc = get_calculator_class('risk', rc.calculation_mode)(job)
        logs.set_level('ERROR')
        job = engine._do_run_calc(job, exports, calc, 'risk')
        job.is_running = False
        job.save()
    else:
        hc = job.hazard_calculation
        calc = get_calculator_class('hazard', hc.calculation_mode)(job)
        logs.set_level('ERROR')
        job = engine._do_run_calc(job, exports, calc, 'hazard')
        job.is_running = False
        job.save()

    return job


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


def touch(content=None, dir=None, prefix="tmp", suffix="tmp"):
    """Create temporary file with the given content.

    Please note: the temporary file must be deleted bu the caller.

    :param string content: the content to write to the temporary file.
    :param string dir: directory where the file should be created
    :param string prefix: file name prefix
    :param string suffix: file name suffix
    :returns: a string with the path to the temporary file
    """
    if dir is not None:
        if not os.path.exists(dir):
            os.makedirs(dir)
    fh, path = tempfile.mkstemp(dir=dir, prefix=prefix, suffix=suffix)
    if content:
        fh = os.fdopen(fh, "w")
        fh.write(content)
        fh.close()
    return path


class ConfigTestCase(object):
    """Class which contains various configuration- and environment-related
    testing helpers."""

    def setup_config(self):
        self.orig_env = os.environ.copy()
        os.environ.clear()
        # Move the local configuration file out of the way if it exists.
        # Otherwise the tests that follow will break.
        local_path = "%s/openquake.cfg" % os.path.abspath(os.getcwd())
        if os.path.isfile(local_path):
            shutil.move(local_path, "%s.test_bakk" % local_path)

    def teardown_config(self):
        os.environ.clear()
        os.environ.update(self.orig_env)
        # Move the local configuration file back into place if it was stashed
        # away.
        local_path = "%s/openquake.cfg" % os.path.abspath(os.getcwd())
        if os.path.isfile("%s.test_bakk" % local_path):
            shutil.move("%s.test_bakk" % local_path, local_path)
        config.Config().cfg.clear()
        config.Config()._load_from_file()

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
        config.Config().cfg.clear()
        config.Config()._load_from_file()


def random_string(length=16):
    """Generate a random string of the given length."""
    result = ""
    while len(result) < length:
        result += random.choice(string.letters + string.digits)
    return result


def deep_eq(a, b, decimal=7, exclude=None):
    """Deep compare two objects for equality by traversing __dict__ and
    __slots__.

    Caution: This function will exhaust generators.

    :param decimal:
        Desired precision (digits after the decimal point) for numerical
        comparisons.

    :param exclude: a list of attributes that will be excluded when
    traversing objects

    :returns:
        Return `True` or `False` (to indicate if objects are equal) and a `str`
        message. If the two objects are equal, the message is empty. If the two
        objects are not equal, the message indicates which part of the
        comparison failed.
    """
    exclude = exclude or []

    try:
        _deep_eq(a, b, decimal=decimal, exclude=exclude)
    except AssertionError, err:
        return False, err.message
    return True, ''


def _deep_eq(a, b, decimal, exclude=None):
    """Do the actual deep comparison. If the two items up for comparison are
    not equal, a :exception:`AssertionError` is raised (to
    :function:`deep_eq`).
    """

    exclude = exclude or []

    def _test_dict(a, b):
        """Compare `dict` types recursively."""
        assert len(a) == len(b), (
            "Dicts %(a)s and %(b)s do not have the same length."
            " Actual lengths: %(len_a)s and %(len_b)s") % dict(
                a=a, b=b, len_a=len(a), len_b=len(b))

        for key in a:
            if not key in exclude:
                _deep_eq(a[key], b[key], decimal)

    def _test_seq(a, b):
        """Compare `list` or `tuple` types recursively."""
        assert len(a) == len(b), (
            "Sequences %(a)s and %(b)s do not have the same length."
            " Actual lengths: %(len_a)s and %(len_b)s") % \
            dict(a=a, b=b, len_a=len(a), len_b=len(b))

        for i, item in enumerate(a):
            _deep_eq(item, b[i], decimal)

    # lists or tuples
    if isinstance(a, (list, tuple)):
        _test_seq(a, b)
    # dicts
    elif isinstance(a, dict):
        _test_dict(a, b)
    # objects with a __dict__
    elif hasattr(a, '__dict__'):
        assert a.__class__ == b.__class__, (
            "%s and %s are different classes") % (a.__class__, b.__class__)
        _test_dict(a.__dict__, b.__dict__)
    # iterables (not strings)
    elif isinstance(a, collections.Iterable) and not isinstance(a, str):
        # If there's a generator or another type of iterable, treat it as a
        # `list`. NOTE: Generators will be exhausted if you do this.
        _test_seq(list(a), list(b))
    # objects with __slots__
    elif hasattr(a, '__slots__'):
        assert a.__class__ == b.__class__, (
            "%s and %s are different classes") % (a.__class__, b.__class__)
        assert a.__slots__ == b.__slots__, (
            "slots %s and %s are not the same") % (a.__slots__, b.__slots__)
        for slot in a.__slots__:
            if not slot in exclude:
                _deep_eq(getattr(a, slot), getattr(b, slot), decimal)
    else:
        # Objects must be primitives

        # Are they numbers?
        if isinstance(a, (int, long, float, complex)):
            numpy.testing.assert_almost_equal(a, b, decimal=decimal)
        else:
            assert a == b, "%s != %s" % (a, b)


def get_job(cfg, username="openquake", hazard_calculation_id=None,
            hazard_output_id=None):
    """
    Given a path to a config file and a hazard_calculation_id
    (or, alternatively, a hazard_output_id, create a
    :class:`openquake.engine.db.models.OqJob` object for a risk calculation.
    """
    if hazard_calculation_id is None and hazard_output_id is None:
        return engine.job_from_file(cfg, username, 'error', [])

    job = engine.prepare_job(username)
    params = engine.parse_config(open(cfg, 'r'))

    params.update(
        dict(hazard_output_id=hazard_output_id,
             hazard_calculation_id=hazard_calculation_id)
    )

    risk_calc = engine.create_calculation(
        models.RiskCalculation, params)
    risk_calc = models.RiskCalculation.objects.get(id=risk_calc.id)
    job.risk_calculation = risk_calc
    job.save()
    return job


def create_gmf(hazard_job, rlz=None):
    """
    Returns the created Gmf object.
    """
    hc = hazard_job.hazard_calculation

    rlz = rlz or models.LtRealization.objects.create(
        hazard_calculation=hc, ordinal=0, seed=1, weight=None,
        sm_lt_path="test_sm", gsim_lt_path="test_gsim")

    gmf = models.Gmf.objects.create(
        output=models.Output.objects.create_output(
            hazard_job, "Test Hazard output", "gmf"),
        lt_realization=rlz)

    return gmf


def create_gmf_data_records(hazard_job, rlz=None, ses_coll=None, points=None):
    """
    Returns the created records.
    """
    gmf = create_gmf(hazard_job, rlz)
    ses_coll = ses_coll or models.SESCollection.objects.create(
        output=models.Output.objects.create_output(
            hazard_job, "Test SES Collection", "ses"),
        lt_realization_ids=[gmf.lt_realization.id],
        ordinal=0)
    ruptures = create_ses_ruptures(hazard_job, ses_coll, 3)
    records = []
    if points is None:
        points = [(15.310, 38.225), (15.71, 37.225),
                  (15.48, 38.091), (15.565, 38.17),
                  (15.481, 38.25)]
    for site_id in hazard_job.hazard_calculation.save_sites(points):
        records.append(models.GmfData.objects.create(
            gmf=gmf,
            task_no=0,
            imt="PGA",
            gmvs=[0.1, 0.2, 0.3],
            rupture_ids=[r.id for r in ruptures],
            site_id=site_id))

    return records


# NB: create_gmf_from_csv and populate_gmf_data_from_csv
# will be unified in the future
def create_gmf_from_csv(job, fname):
    """
    Populate the gmf_data table for an event_based calculation.
    """
    hc = job.hazard_calculation
    hc.investigation_time = 50
    hc.ses_per_logic_tree_path = 1
    hc.save()

    # tricks to fool the oqtask decorator
    job.is_running = True
    job.status = 'post_processing'
    job.save()

    gmf = create_gmf(job)

    ses_coll = models.SESCollection.objects.create(
        output=models.Output.objects.create_output(
            job, "Test SES Collection", "ses"),
        lt_realization_ids=[gmf.lt_realization.id],
        ordinal=0)
    with open(fname, 'rb') as csvfile:
        gmfreader = csv.reader(csvfile, delimiter=',')
        locations = gmfreader.next()

        gmv_matrix = numpy.array(
            [map(float, row) for row in gmfreader]).transpose()

        ruptures = create_ses_ruptures(job, ses_coll, len(gmv_matrix[0]))

        for i, gmvs in enumerate(gmv_matrix):
            point = tuple(map(float, locations[i].split()))
            [site_id] = job.hazard_calculation.save_sites([point])
            models.GmfData.objects.create(
                gmf=gmf,
                task_no=0,
                imt="PGA", gmvs=gmvs,
                rupture_ids=[r.id for r in ruptures],
                site_id=site_id)

    return gmf


def populate_gmf_data_from_csv(job, fname):
    """
    Populate the gmf_data table for a scenario calculation.
    """
    # tricks to fool the oqtask decorator
    job.is_running = True
    job.status = 'post_processing'
    job.save()

    gmf = models.Gmf.objects.create(
        output=models.Output.objects.create_output(
            job, "Test Hazard output", "gmf_scenario"))

    with open(fname, 'rb') as csvfile:
        gmfreader = csv.reader(csvfile, delimiter=',')
        locations = gmfreader.next()

        gmv_matrix = numpy.array(
            [map(float, row) for row in gmfreader]).transpose()

        for i, gmvs in enumerate(gmv_matrix):
            point = tuple(map(float, locations[i].split()))
            [site_id] = job.hazard_calculation.save_sites([point])
            models.GmfData.objects.create(
                task_no=0,
                imt="PGA",
                gmf=gmf,
                gmvs=gmvs,
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
    hc = hazard_job.hazard_calculation

    rlz = models.LtRealization.objects.create(
        hazard_calculation=hazard_job.hazard_calculation,
        ordinal=1, seed=1, weight=None,
        sm_lt_path="test_sm", gsim_lt_path="test_gsim")

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
            models.HazardCurveData.objects.create(
                hazard_curve=hazard_output,
                poes=[0.1, 0.2, 0.3],
                location="%s" % point)

    elif output_type == "gmf_scenario":
        hazard_output = models.Gmf.objects.create(
            output=models.Output.objects.create_output(
                hazard_job, "Test gmf scenario output", "gmf_scenario"))

        site_ids = hazard_job.hazard_calculation.save_sites(
            [(15.48, 38.0900001), (15.565, 38.17), (15.481, 38.25)])
        for site_id in site_ids:
            models.GmfData.objects.create(
                gmf=hazard_output,
                task_no=0,
                imt="PGA",
                site_id=site_id,
                gmvs=[0.1, 0.2, 0.3])

    elif output_type in ("ses", "gmf"):
        hazard_output = create_gmf_data_records(hazard_job, rlz)[0].gmf

    else:
        raise RuntimeError('Unexpected output_type: %s' % output_type)

    hazard_job.status = "complete"
    hazard_job.save()
    job = engine.prepare_job(username)
    params = engine.parse_config(open(risk_cfg, 'r'))

    params.update(dict(hazard_output_id=hazard_output.output.id))

    risk_calc = engine.create_calculation(models.RiskCalculation, params)
    job.risk_calculation = risk_calc
    job.save()
    error_message = validate(job, 'risk', params, [])

    # reload risk calculation to have all the types converted properly
    job.risk_calculation = models.RiskCalculation.objects.get(id=risk_calc.id)
    if error_message:
        raise RuntimeError(error_message)
    return job, set(params['inputs'])


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
    ses = models.SES.objects.create(
        ses_collection=ses_collection,
        investigation_time=job.hazard_calculation.investigation_time,
        ordinal=1)
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
    seed = 42
    pr = models.ProbabilisticRupture.create(rupture, ses_collection)
    return [models.SESRupture.create(pr, ses, 'test', i, seed + i)
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
