# -*- coding: utf-8 -*-
# pylint: enable=W0511,W0142,I0011,E1101,E0611,F0401,E1103,R0801,W0232

# Copyright (c) 2010-2013, GEM Foundation.
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
This module defines some classes useful to perform bulk insert of
statistical outputs (mean curves, quantile curves, hazard maps, etc.)
"""

import shapely

from openquake.writer import BulkInserter
from openquake.db import models
from django.db import transaction


class AggregateResultWriter(object):
    """
    Manager to serialize to db Aggregate results (Mean curves,
    Quantile Curves, Maps, etc.).

    It implements the context manager pattern to take care of the
    transaction management

    :attribute _job
      The current job

    :attribute _imt
      The intensity measure type for this aggregate result
    """

    def __init__(self, job, imt):
        self._job = job
        self._imt = imt
        self._inserter = BulkInserter(self.__class__.model)
        self._aggregate_result = None
        self._transaction_handler = None

    def _create_output(self):
        """
        Create an Output object related to the aggregate result
        """
        output = models.Output.objects.create_output(
            job=self._job,
            output_type=self.__class__.output_type,
            display_name=self.display_name())
        return output

    def display_name(self):
        """
        The display name of the output being created (used for the
        Output object)
        """
        raise NotImplementedError

    def create_aggregate_result(self):
        """
        Create an Aggregate result (both the Output object and the
        corresponding curve/map/etc. object
        """
        output = self._create_output()
        self._aggregate_result = self._create_aggregate_result_item(output)
        return self._aggregate_result, output

    def _create_aggregate_result_item(self, output):
        """
        Create an aggregate result item (only the HazardCurve /
        HazardMap). Abstract method
        """
        raise NotImplementedError

    def add_data(self, location, _):
        """
        Add a aggregate result data (to be serialized when flush is
        called). Abstract method
        """
        raise NotImplementedError

    def __enter__(self):
        self._transaction_handler = transaction.commit_on_success(
            using='reslt_writer')
        self._transaction_handler.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            self._flush_data()
        else:
            raise exc_val
        self._transaction_handler.__exit__(exc_type, exc_val, exc_tb)

    def _flush_data(self):
        """
        Flush the data to the db
        """
        self._inserter.flush()


class AggregateCurveWriter(AggregateResultWriter):
    """
    Manager to serialize to db Aggregate curves (Mean and quantile
    curves).

    See base class for details
    """
    model = models.HazardCurveData
    output_type = "hazard_curve"

    def _create_aggregate_result_item(self, output):
        raise NotImplementedError

    def add_data(self, location, poes):
        """
       Add an aggregate curve data related to the current output item
        being processed

        :param location
          a buffer object pointing to wkb data
        :param poes
          a list of poe
        """

        location_wkt = shapely.wkb.loads(str(location)).wkt
        self._inserter.add_entry(location=location_wkt, poes=poes,
                                 hazard_curve_id=self._aggregate_result.pk)


class MeanCurveWriter(AggregateCurveWriter):
    """
    Serialize mean curves to the db
    """
    statistics = "mean"

    def display_name(self):
        return "mean curve for %s" % self._imt

    def _create_aggregate_result_item(self, output):
        return models.HazardCurve.objects.create_aggregate_curve(
            imt=self._imt,
            output=output,
            statistics=self.__class__.statistics)


class QuantileCurveWriter(AggregateCurveWriter):
    """
    Serialize quantile curves to the db
    """
    statistics = "quantile"

    def __init__(self, job, imt, quantile):
        super(QuantileCurveWriter, self).__init__(job, imt)
        self._quantile = quantile

    def display_name(self):
        return "quantile curve (poe >= %s) for imt %s" % (
            self._quantile, self._imt)

    def _create_aggregate_result_item(self, output):
        return models.HazardCurve.objects.create_aggregate_curve(
            imt=self._imt,
            output=output,
            statistics=self.__class__.statistics,
            quantile=self._quantile)
