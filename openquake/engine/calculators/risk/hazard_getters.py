# -*- coding: utf-8 -*-

# Copyright (c) 2012-2014, GEM Foundation.
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
Hazard input management for Risk calculators.
"""
import itertools
import operator

import numpy

from openquake.hazardlib.imt import from_string
from openquake.risklib import scientific

from openquake.engine import logs
from openquake.engine.db import models
from django.db import transaction


BYTES_PER_FLOAT = numpy.zeros(1, dtype=float).nbytes


class AssetSiteAssociationError(Exception):
    pass


class Hazard(object):
    """
    Hazard objects have attributes .hazard_output, .data and .imt.
    Moreover you can extract the .hid (hazard_output.id) and the
    .weight associated to the underlying realization.
    The hazard .data is a numpy array of shape (N, R) where N is the
    number of assets and R the number of seismic events (ruptures)
    or the resolution of the hazard curve, depending on the calculator.
    """
    def __init__(self, hazard_output, data, imt):
        self.hazard_output = hazard_output
        self.data = data
        self.imt = imt

    @property
    def hid(self):
        """Return the id of the given hazard output"""
        return self.hazard_output.id

    @property
    def weight(self):
        """Return the realization weight of the hazard output"""
        h = self.hazard_output.output_container
        if hasattr(h, 'lt_realization') and h.lt_realization:
            return h.lt_realization.weight


def make_epsilons(asset_count, num_samples, seed, correlation):
    """
    :param int asset_count: the number of assets
    :param int num_ruptures: the number of ruptures
    :param int seed: a random seed
    :param float correlation: the correlation coefficient
    """
    zeros = numpy.zeros((asset_count, num_samples))
    return scientific.make_epsilons(zeros, seed, correlation)


class HazardGetter(object):
    """
    A HazardGetter instance stores a chunk of assets and their associated
    hazard data. In the case of scenario and event based calculators it
    also stores the ruptures and the epsilons.
    The HazardGetter must be pickable such that it
    should be possible to use different strategies (e.g. distributed
    or not, using postgis or not).

    :attr assets:
        The assets for which we want to extract the hazard

   :attr site_ids:
        The ids of the sites associated to the hazards
    """
    def __init__(self, imt, taxonomy, hazard_outputs, assets):
        self.imt = imt
        self.taxonomy = taxonomy
        self.hazard_outputs = hazard_outputs
        self.assets = assets
        self.site_ids = []
        self.asset_site_ids = []
        # asset_site associations
        for asset in self.assets:
            asset_site_id = asset.asset_site_id
            assoc = models.AssetSite.objects.get(pk=asset_site_id)
            self.site_ids.append(assoc.site.id)
            self.asset_site_ids.append(asset_site_id)

    def get_hazards(self):
        """
        Return a list of Hazard instances for the given IMT.
        """
        return [Hazard(ho, self._get_data(ho), self.imt)
                for ho in self.hazard_outputs]

    def get_data(self):
        """
        Shortcut returning the hazard data when there is a single realization
        """
        [hazard] = self.get_hazards()
        return hazard.data

    @property
    def hid(self):
        """
        Return the id of the hazard output, when there is a single realization
        """
        [ho] = self.hazard_outputs
        return ho.id

    def __repr__(self):
        eps = getattr(self, 'epsilons', None)
        eps = '' if eps is None else ', %s epsilons' % str(eps.shape)
        return "<%s %d assets%s, taxonomy=%s>" % (
            self.__class__.__name__, len(self.assets), eps,
            self.taxonomy)


class HazardCurveGetter(HazardGetter):
    """
    Simple HazardCurve Getter that performs a spatial query for each
    asset.
    """ + HazardGetter.__doc__

    def _get_data(self, ho):
        # extract the poes for each site from the given hazard output
        imt_type, sa_period, sa_damping = from_string(self.imt)
        oc = ho.output_container
        if oc.output.output_type == 'hazard_curve_multi':
            oc = models.HazardCurve.objects.get(
                output__oq_job=oc.output.oq_job,
                output__output_type='hazard_curve',
                statistics=oc.statistics,
                lt_realization=oc.lt_realization,
                imt=imt_type,
                sa_period=sa_period,
                sa_damping=sa_damping)

        cursor = models.getcursor('job_init')
        query = """\
        SELECT hzrdr.hazard_curve_data.poes
        FROM hzrdr.hazard_curve_data
        WHERE hazard_curve_id = %s
        AND ST_X(location) = %s AND ST_Y(location) = %s
        """
        all_curves = []
        for site_id in self.site_ids:
            site = models.HazardSite.objects.get(pk=site_id)
            cursor.execute(query, (oc.id, site.lon, site.lat))
            poes = cursor.fetchall()[0][0]
            all_curves.append(poes)
        return all_curves


def expand(array, N):
    """
    Given a non-empty array with n elements, expands it to a larger
    array with N elements.

    >>> expand([1], 3)
    array([1, 1, 1])
    >>> expand([1, 2, 3], 10)
    array([1, 2, 3, 1, 2, 3, 1, 2, 3, 1])
    >>> expand(numpy.zeros((2, 10)), 5).shape
    (5, 10)
    """
    n = len(array)
    assert n > 0, 'Empty array'
    if n >= N:
        raise ValueError('Cannot expand an array of %d elements to %d',
                         n, N)
    return numpy.array([array[i % n] for i in xrange(N)])


def haz_out_to_ses_coll(ho):
    if ho.output_type == 'gmf_scenario':
        out = models.Output.objects.get(output_type='ses', oq_job=ho.oq_job)
        return [out.ses]

    return models.SESCollection.objects.filter(
        trt_model__lt_model=ho.output_container.lt_realization.lt_model)


class RiskInitializer(object):
    """
    A facility providing the brigde between the hazard (sites and outputs)
    and the risk (assets and risk models). When .init_assocs is called,
    populates the `asset_site` table with the associations between the assets
    in the current exposure model and the sites in the previous hazard
    calculation.

    :param hazard_outputs:
        outputs of the previous hazard calculation
    :param taxonomy:
        the taxonomy of the assets we are interested in
    :param calc:
        a risk calculator

    Warning: instantiating a RiskInitializer may perform a potentially
    expensive geospatial query.
    """
    def __init__(self, taxonomy, calc):
        self.exposure_model = calc.exposure_model
        self.hazard_outputs = calc.get_hazard_outputs()
        self.taxonomy = taxonomy
        self.calc = calc
        self.oqparam = models.OqJob.objects.get(
            pk=calc.oqparam.hazard_calculation_id)
        self.calculation_mode = self.calc.oqparam.calculation_mode
        self.number_of_ground_motion_fields = self.oqparam.get_param(
            'number_of_ground_motion_fields', 0)
        max_dist = calc.best_maximum_distance * 1000  # km to meters
        self.cursor = models.getcursor('job_init')

        hazard_exposure = models.extract_from([self.oqparam], 'exposuremodel')
        if self.exposure_model and hazard_exposure and \
           self.exposure_model.id == hazard_exposure.id:
            # no need of geospatial queries, just join on the location
            self.assoc_query = self.cursor.mogrify("""\
WITH assocs AS (
  SELECT %s, exp.id, hsite.id
  FROM riski.exposure_data AS exp
  JOIN (SELECT id, lon, lat FROM hzrdi.hazard_site
  WHERE hazard_calculation_id = %s
  AND ST_Covers(ST_GeometryFromText(%s), ST_MakePoint(lon, lat))) AS hsite
  ON ST_X(exp.site::GEOMETRY) = hsite.lon
  AND ST_Y(exp.site::GEOMETRY) = hsite.lat
  WHERE exposure_model_id = %s AND taxonomy=%s
)
INSERT INTO riskr.asset_site (job_id, asset_id, site_id)
SELECT * FROM assocs""", (self.calc.job.id, self.oqparam.id,
                          self.calc.oqparam.region_constraint,
                          self.exposure_model.id, taxonomy))
        else:
            # associate each asset to the closest hazard site
            self.assoc_query = self.cursor.mogrify("""\
WITH assocs AS (
  SELECT DISTINCT ON (exp.id) %s, exp.id, hsite.id
  FROM riski.exposure_data AS exp
  JOIN (SELECT id, lon, lat FROM hzrdi.hazard_site
  WHERE hazard_calculation_id = %s
  AND ST_Covers(ST_GeometryFromText(%s), ST_MakePoint(lon, lat))) AS hsite
  ON ST_DWithin(exp.site, ST_MakePoint(hsite.lon, hsite.lat)::geography, %s)
  WHERE exposure_model_id = %s AND taxonomy=%s
  ORDER BY exp.id, ST_Distance(
  exp.site, ST_MakePoint(hsite.lon, hsite.lat)::geography, false)
)
INSERT INTO riskr.asset_site (job_id, asset_id, site_id)
SELECT * FROM assocs""", (self.calc.job.id, self.oqparam.id,
                          self.calc.oqparam.region_constraint, max_dist,
                          self.exposure_model.id, taxonomy))
        self.num_assets = 0
        self._rupture_ids = {}
        self.epsilons_shape = {}

    def init_assocs(self):
        """
        Stores the associations asset <-> site into the database
        """
        with transaction.atomic(using='job_init'):
            # insert the associations for the current taxonomy
            self.cursor.execute(self.assoc_query)
            # now read the associations just inserted
            self.num_assets = models.AssetSite.objects.filter(
                job=self.calc.job, asset__taxonomy=self.taxonomy).count()

        # check if there are no associations
        if self.num_assets == 0:
            raise AssetSiteAssociationError(
                'Could not associate any asset of taxonomy %s to '
                'hazard sites within the distance of %s km'
                % (self.taxonomy, self.calc.best_maximum_distance))
