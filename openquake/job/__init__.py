# -*- coding: utf-8 -*-

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""A single hazard/risk job."""

import os
import urlparse

from datetime import datetime

from openquake import flags
from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake.parser import exposure
from openquake.db.models import (OqCalculation, CalcStats, FloatArrayField,
                                 CharArrayField, InputSet, Input)
from openquake.job import config as conf
from openquake.job import params as job_params
from openquake.job.params import PARAMS, CALCULATION_MODE, ENUM_MAP
from openquake.kvs import mark_job_as_current
from openquake.logs import LOG
from openquake.utils import stats

FLAGS = flags.FLAGS

REVERSE_ENUM_MAP = dict((v, k) for k, v in ENUM_MAP.iteritems())


class CalculationProxy(object):
    """A job is a collection of parameters identified by a unique id."""

    def __init__(self, params, job_id, sections=list(), base_path=None,
                 serialize_results_to=list()):
        """
        :param dict params: Dict of job config params.
        :param int job_id: ID of the corresponding oq_calculation db record.
        :param list sections: List of config file sections. Example::
            ['HAZARD', 'RISK']
        :param str base_path: base directory containing job input files
        """
        self._job_id = job_id
        mark_job_as_current(job_id)  # enables KVS gc

        self.sites = []
        self.blocks_keys = []
        self.params = params
        self.sections = list(set(sections))
        self.serialize_results_to = []
        self.base_path = base_path
        self.serialize_results_to = list(serialize_results_to)

    @staticmethod
    def from_kvs(job_id):
        """Return the job in the underlying kvs system with the given id."""
        params = kvs.get_value_json_decoded(
            kvs.tokens.generate_job_key(job_id))
        job = Job(params, job_id)
        return job

    @staticmethod
    def get_status_from_db(job_id):
        """
        Get the status of the database record belonging to job ``job_id``.

        :returns: one of strings 'pending', 'running', 'succeeded', 'failed'.
        """
        return OqCalculation.objects.get(id=job_id).status

    @staticmethod
    def is_job_completed(job_id):
        """
        Return ``True`` if the :meth:`current status <get_status_from_db>`
        of the job ``job_id`` is either 'succeeded' or 'failed'. Returns
        ``False`` otherwise.
        """
        status = Job.get_status_from_db(job_id)
        return status == 'succeeded' or status == 'failed'

    def has(self, name):
        """Return false if this job doesn't have the given parameter defined,
        or parameter's string value otherwise."""
        return name in self.params and self.params[name]

    @property
    def job_id(self):
        """Return the id of this job."""
        return self._job_id

    @property
    def key(self):
        """Returns the kvs key for this job."""
        return kvs.tokens.generate_job_key(self.job_id)

    def set_status(self, status):
        """
        Set the status of the database record belonging to this job.

        :param status: one of 'pending', 'running', 'succeeded', 'failed'
        :type status: string
        """
        job = OqCalculation.objects.get(id=self.job_id)
        job.status = status
        job.save()

    @property
    def region(self):
        """Compute valid region with appropriate cell size from config file."""
        if not self.has('REGION_VERTEX'):
            return None

        region = shapes.RegionConstraint.from_coordinates(
            self._extract_coords('REGION_VERTEX'))

        region.cell_size = float(self['REGION_GRID_SPACING'])
        return region

    def __getitem__(self, name):
        defined_param = job_params.PARAMS.get(name)
        if (hasattr(defined_param, 'to_job')
            and defined_param.to_job is not None
            and self.params.get(name) is not None):
            return defined_param.to_job(self.params.get(name))
        return self.params.get(name)

    def __eq__(self, other):
        return self.params == other.params

    def __str__(self):
        return str(self.params)

    def _slurp_files(self):
        """Read referenced files and write them into kvs, keyed on their
        sha1s."""
        kvs_client = kvs.get_client()
        if self.base_path is None:
            LOG.debug("Can't slurp files without a base path, homie...")
            return
        for key, val in self.params.items():
            if key[-5:] == '_FILE':
                path = os.path.join(self.base_path, val)
                with open(path) as data_file:
                    LOG.debug("Slurping %s" % path)
                    blob = data_file.read()
                    file_key = kvs.tokens.generate_blob_key(self.job_id, blob)
                    kvs_client.set(file_key, blob)
                    self.params[key] = file_key
                    self.params[key + "_PATH"] = path

    def to_kvs(self):
        """Store this job into kvs."""
        self._slurp_files()
        key = kvs.tokens.generate_job_key(self.job_id)
        data = self.params.copy()
        data['debug'] = FLAGS.debug
        kvs.set_value_json_encoded(key, data)

    def sites_to_compute(self):
        """Return the sites used to trigger the computation on the
        hazard subsystem.

        If the SITES parameter is specified, the computation is triggered
        only on the sites specified in that parameter, otherwise
        the region is used.

        If the COMPUTE_HAZARD_AT_ASSETS_LOCATIONS parameter is specified,
        the hazard computation is triggered only on sites defined in the risk
        exposure file and located inside the region of interest.
        """

        if self.sites:
            return self.sites

        if conf.RISK_SECTION in self.sections \
                and self.has(conf.COMPUTE_HAZARD_AT_ASSETS):

            print "COMPUTE_HAZARD_AT_ASSETS_LOCATIONS selected, " \
                "computing hazard on exposure sites..."

            self.sites = read_sites_from_exposure(self)
        elif self.has(conf.SITES):

            coords = self._extract_coords(conf.SITES)
            sites = []

            for coord in coords:
                sites.append(shapes.Site(coord[0], coord[1]))

            self.sites = sites
        else:
            self.sites = self._sites_for_region()

        return self.sites

    def _extract_coords(self, config_param):
        """Extract from a configuration parameter the list of coordinates."""
        verts = self[config_param]
        return zip(verts[1::2], verts[::2])

    def _sites_for_region(self):
        """Return the list of sites for the region at hand."""
        region = shapes.Region.from_coordinates(
            self._extract_coords('REGION_VERTEX'))

        region.cell_size = self['REGION_GRID_SPACING']
        return [site for site in region]

    def build_nrml_path(self, nrml_file):
        """Return the complete output path for the given nrml_file"""
        return os.path.join(self['BASE_PATH'], self['OUTPUT_DIR'], nrml_file)

    def extract_values_from_config(self, param_name, separator=' ',
                                   check_value=lambda _: True):
        """Extract the set of valid values from the configuration file."""

        def _acceptable(value):
            """Return true if the value taken from the configuration
            file is valid, false otherwise."""
            try:
                value = float(value)
            except ValueError:
                return False
            else:
                return check_value(value)

        values = []

        if param_name in self.params:
            raw_values = self.params[param_name].split(separator)
            values = [float(x) for x in raw_values if _acceptable(x)]

        return values

    @property
    def imls(self):
        "Return the intensity measure levels as specified in the config file"
        if self.has('INTENSITY_MEASURE_LEVELS'):
            return self['INTENSITY_MEASURE_LEVELS']
        return None

    def _record_initial_stats(self):
        '''
        Report initial job stats (such as start time) by adding a
        uiapi.calc_stats record to the db.
        '''
        oq_calculation = OqCalculation.objects.get(id=self.job_id)

        calc_stats = CalcStats(oq_calculation=oq_calculation)
        calc_stats.start_time = datetime.utcnow()
        calc_stats.num_sites = len(self.sites_to_compute())

        calc_mode = CALCULATION_MODE[self['CALCULATION_MODE']]
        if conf.HAZARD_SECTION in self.sections:
            if calc_mode != 'scenario':
                calc_stats.realizations = self["NUMBER_OF_LOGIC_TREE_SAMPLES"]

        calc_stats.save()


def read_sites_from_exposure(a_job):
    """
    Given the exposure model specified in the job config, read all sites which
    are located within the region of interest.

    :param a_job: a Job object with an EXPOSURE parameter defined
    :type a_job: :py:class:`openquake.job.Job`

    :returns: a list of :py:class:`openquake.shapes.Site` objects
    """

    sites = []
    path = os.path.join(a_job.base_path, a_job.params[conf.EXPOSURE])

    reader = exposure.ExposurePortfolioFile(path)
    constraint = a_job.region

    LOG.debug(
        "Constraining exposure parsing to %s" % constraint)

    for site, _asset_data in reader.filter(constraint):

        # we don't want duplicates (bug 812395):
        if not site in sites:
            sites.append(site)

    return sites
