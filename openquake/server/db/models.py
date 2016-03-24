# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2016 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

# Disable:
# - 'Maximum number of public methods for a class'
# - 'Missing docstring' (because of all of the model Meta)
# pylint: disable=R0904,C0111

'''
Model representations of the OpenQuake DB tables.
'''
import os
from datetime import datetime

from openquake.commonlib import datastore
from openquake.commonlib.oqvalidation import OqParam, RISK_CALCULATORS
import django
if hasattr(django, 'setup'):
    django.setup()  # for Django >= 1.7
from django.db import models as djm
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

#: Kind of supported curve statistics
STAT_CHOICES = (
    (u'mean', u'Mean'),
    (u'quantile', u'Quantile'))


#: System Reference ID used for geometry objects
DEFAULT_SRID = 4326


VS30_TYPE_CHOICES = (
    (u"measured", u"Value obtained from on-site measurements"),
    (u"inferred", u"Estimated value"),
)

IMT_CHOICES = (
    (u'PGA', u'Peak Ground Acceleration'),
    (u'PGV', u'Peak Ground Velocity'),
    (u'PGD', u'Peak Ground Displacement'),
    (u'SA', u'Spectral Acceleration'),
    (u'IA', u'Arias Intensity'),
    (u'RSD', u'Relative Significant Duration'),
    (u'MMI', u'Modified Mercalli Intensity'),
)

#: Minimum value for a seed number
MIN_SINT_32 = -(2 ** 31)
#: Maximum value for a seed number
MAX_SINT_32 = (2 ** 31) - 1


#: Kind of supported type of loss outputs
LOSS_TYPES = ["structural", "nonstructural", "fatalities", "contents"]

#: relative tolerance to consider two risk outputs (almost) equal
RISK_RTOL = 0.05


#: absolute tolerance to consider two risk outputs (almost) equal
RISK_ATOL = 0.01

# TODO: these want to be dictionaries
INPUT_TYPE_CHOICES = (
    (u'unknown', u'Unknown'),
    (u'source', u'Source Model'),
    (u'source_model_logic_tree', u'Source Model Logic Tree'),
    (u'gsim_logic_tree', u'Ground Shaking Intensity Model Logic Tree'),
    (u'exposure', u'Exposure'),
    (u'fragility', u'Fragility'),
    (u'site_model', u'Site Model'),
    (u'rupture_model', u'Rupture Model'),

    # vulnerability models
    (u'structural_vulnerability', u'Structural Vulnerability'),
    (u'nonstructural_vulnerability', u'Non Structural Vulnerability'),
    (u'contents_vulnerability', u'Contents Vulnerability'),
    (u'business_interruption_vulnerability',
     u'Business Interruption Vulnerability'),
    (u'occupants_vulnerability', u'Occupants Vulnerability'),
    (u'structural_vulnerability_retrofitted',
     u'Structural Vulnerability Retrofitted'))


# Tables in the 'uiapi' schema.

class OqJob(djm.Model):
    '''
    An OpenQuake engine run started by the user
    '''
    description = djm.TextField()
    user_name = djm.TextField()
    calculation_mode = djm.TextField()
    hazard_calculation = djm.ForeignKey('OqJob', null=True)
    STATUS_CHOICES = (
        (u'created', u'Created'),
        (u'executing', u'Executing'),
        (u'post_executing', u'Post-Executing'),
        (u'post_processing', u'Post-Processing'),
        (u'export', u'Exporting results'),
        (u'clean_up', u'Cleaning up'),
        (u'complete', u'Complete'),
    )
    status = djm.TextField(choices=STATUS_CHOICES, default='executing')
    is_running = djm.BooleanField(default=True)
    start_time = djm.DateTimeField(editable=False, default=datetime.utcnow)
    stop_time = djm.DateTimeField(editable=False)
    relevant = djm.BooleanField(null=False, default=True)
    ds_calc_dir = djm.TextField(null=False, blank=True)  # datastore calc_dir

    class Meta:
        db_table = 'job'

    @property
    def job_type(self):
        """
        'hazard' or 'risk'
        """
        # the calculation mode can be unknown if the job parameters
        # have not been written on the database yet
        return ('risk' if self.calculation_mode in RISK_CALCULATORS
                else 'hazard')

    def get_or_create_output(self, display_name, ds_key):
        """
        :param disp_name: display name of the output
        :returns: an Output instance
        """
        try:
            output = Output.objects.get(
                oq_job=self, display_name=display_name)
        except ObjectDoesNotExist:
            output = Output.objects.create_output(
                self, display_name, ds_key)
        return output

    def get_oqparam(self):
        """
        Return an OqParam object as read from the database
        """
        datadir = os.path.dirname(self.ds_calc_dir)
        dstore = datastore.read(self.id, datadir=datadir)
        oqparam = OqParam.from_(dstore.attrs)
        return oqparam

    def __repr__(self):
        return '<%s %d, %s>' % (self.__class__.__name__,
                                self.id, self.job_type)


def oqparam(job_id):
    """
    :param job_id: ID of :class:`openquake.server.db.models.OqJob`
    :returns: instance of :class:`openquake.commonlib.oqvalidation.OqParam`
    """
    return OqJob.objects.get(pk=job_id).get_oqparam()


class Performance(djm.Model):
    '''
    Contains performance information about a job.
    '''
    job = djm.ForeignKey('OqJob')
    operation = djm.TextField(null=False)
    time_sec = djm.FloatField(null=False)
    memory_mb = djm.FloatField(null=False)
    counts = djm.IntegerField(null=False)

    class Meta:
        db_table = 'performance'


class Log(djm.Model):
    '''
    Log table for calculations
    '''
    job = djm.ForeignKey('OqJob', null=True)
    timestamp = djm.DateTimeField(editable=False, default=datetime.utcnow)
    LOG_LEVEL_CHOICES = (
        (u'debug', u'Debug'),
        (u'info', u'Info'),
        (u'warn', u'Warn'),
        (u'error', u'Error'),
        (u'critical', u'Critical'),
    )
    level = djm.TextField(choices=LOG_LEVEL_CHOICES)
    process = djm.TextField(null=False)
    message = djm.TextField(null=False)

    class Meta:
        db_table = 'log'
        ordering = ['id']


def extract_from(objlist, attr):
    """
    Extract an attribute from a list of Django objects, by scanning
    them in order until a not None attribute is found. If nothing is
    found, or if an exception ObjectDoesNotExist is raised, return None.

    :param objlist: the list of Django objects
    :param str attr: the name of the attribute to look for
    """
    for obj in objlist:
        try:
            value = getattr(obj, attr, None)
        except ObjectDoesNotExist:
            value = None
        if value is not None:
            return value


class OutputManager(djm.Manager):
    """
    Manager class to filter and create Output objects
    """
    def create_output(self, job, display_name, ds_key):
        """
        Create an output for the given `job`, `display_name` and
        `ds_key`
        """
        return self.create(oq_job=job,
                           display_name=display_name,
                           ds_key=ds_key)


class Output(djm.Model):
    '''
    A single artifact which is a result of an OpenQuake job.
    The data may reside in a file or in the database.
    '''
    oq_job = djm.ForeignKey('OqJob', null=False)
    display_name = djm.TextField()
    last_update = djm.DateTimeField(editable=False, default=datetime.utcnow)
    ds_key = djm.TextField(null=False, blank=True)  # datastore key

    objects = OutputManager()

    def __str__(self):
        return "%d||%s" % (self.id, self.display_name)

    class Meta:
        db_table = 'output'
        ordering = ['id']
