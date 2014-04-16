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
Hazard getters for Risk calculators.

A HazardGetter is responsible fo getting hazard outputs needed by a risk
calculation.
"""

import collections
import numpy

from openquake.hazardlib.imt import from_string
from openquake.risklib.scientific import make_epsilons

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.performance import DummyMonitor
from django.db import connections


# all hazard getters are to be considered private, they should be called by
# the GetterBuilder only
class HazardGetter(object):
    """
    Base abstract class of an Hazard Getter.

    An Hazard Getter is used to query for the closest hazard data for
    each given asset. An Hazard Getter must be pickable such that it
    should be possible to use different strategies (e.g. distributed
    or not, using postgis or not).

    :attr hazard_output:
        A :class:`openquake.engine.db.models.Output` instance

    :attr assets:
        The assets for which we wants to compute.

    :attr imt:
        The imt (in long form) for which data have to be retrieved
    """
    @property
    def hid(self):
        """Return the id of the given hazard output"""
        return self.hazard_output.id

    @property
    def weight(self):
        """Return the weight of the realization of the hazard output"""
        h = self.hazard_output.output_container
        if hasattr(h, 'lt_realization') and h.lt_realization:
            return h.lt_realization.weight

    def __init__(self, hazard_output, assets, asset_site, imt):
        self.hazard_output = hazard_output
        self.assets = assets
        self.asset_site = asset_site
        self.imt = imt
        self.imt_type, self.sa_period, self.sa_damping = from_string(imt)
        self.epsilons = None

    def __repr__(self):
        return "<%s assets=%s>" % (
            self.__class__.__name__, [a.id for a in self.assets])

    def get_data(self, monitor):
        """
        Subclasses must implement this.
        """
        raise NotImplementedError

    def __call__(self, monitor=None):
        """
        :param monitor: a performance monitor or None
        :returns:
            A tuple with two elements. The first is an array of instances of
            :class:`openquake.engine.db.models.ExposureData`, the second is
            the corresponding hazard data.
        """
        return self.get_data(monitor or DummyMonitor())


class HazardCurveGetterPerAsset(HazardGetter):
    """
    Simple HazardCurve Getter that performs a spatial query for each
    asset.

    :attr imls:
        The intensity measure levels of the curves we are going to get.
    """
    def get_data(self, monitor):
        """
        Calls ``get_by_site`` for each asset and pack the results as
        requested by the :meth:`HazardGetter.get_data` interface.
        """
        oc = self.hazard_output.output_container
        if oc.output.output_type == 'hazard_curve':
            imls = oc.imls
        elif oc.output.output_type == 'hazard_curve_multi':
            oc = models.HazardCurve.objects.get(
                output__oq_job=oc.output.oq_job,
                output__output_type='hazard_curve',
                statistics=oc.statistics,
                lt_realization=oc.lt_realization,
                imt=self.imt_type,
                sa_period=self.sa_period,
                sa_damping=self.sa_damping)
            imls = oc.imls

        all_curves = []
        with monitor.copy('getting closest hazard curves'):
            for asset in self.assets:
                site_id = self.asset_site[asset.id]
                site = models.HazardSite.objects.get(pk=site_id)
                [poes] = self.get_by_site(site, oc.id)
                curve = zip(imls, poes)
                all_curves.append(curve)
        return all_curves

    def get_by_site(self, site, hazard_id):
        """
        :param site:
            An instance of :class:`django.contrib.gis.geos.point.Point`
            corresponding to the location of an asset.
        """
        cursor = models.getcursor('job_init')

        query = """\
        SELECT hzrdr.hazard_curve_data.poes
        FROM hzrdr.hazard_curve_data
        WHERE hazard_curve_id = %s AND location = %s
        """
        cursor.execute(query, (hazard_id, 'SRID=4326; ' + site.location.wkt))
        return cursor.fetchone()


class ScenarioGetter(HazardGetter):
    """
    Hazard getter for loading ground motion values. It is instantiated
    with a set of assets all of the same taxonomy.
    """
    epsilons = None  # set by the GetterBuilder

    def get_gmvs(self, site_id):
        """
        :returns: gmvs and ruptures for the given site and IMT
        """
        gmvs = []
        for gmf in models.GmfData.objects.filter(
                gmf=self.hazard_output.output_container,
                site=site_id, imt=self.imt_type, sa_period=self.sa_period,
                sa_damping=self.sa_damping):  # ordered by task_no
            gmvs.extend(gmf.gmvs)
            if not gmvs:
                logs.LOG.warn('No gmvs for site %s, IMT=%s', site_id, self.imt)
        return gmvs

    def get_data(self, monitor):
        """
        :returns: the assets and the corresponding ground motion values
        """
        all_gmvs = []
        with monitor.copy('getting gmvs and ruptures'):
            for asset in self.assets:
                site_id = self.asset_site[asset.id]
                gmvs = self.get_gmvs(site_id)
                all_gmvs.append(gmvs)
        return all_gmvs


class GroundMotionValuesGetter(HazardGetter):
    """
    Hazard getter for loading ground motion values. It is instantiated
    with a set of assets all of the same taxonomy.
    """
    rupture_ids = None  # set by the GetterBuilder
    epsilons = None  # set by the GetterBuilder

    def get_gmv_dict(self, site_id):
        """
        :returns: a dictionary {rupture_id: gmv}
        """
        gmvs = []
        ruptures = []
        for gmf in models.GmfData.objects.filter(
                gmf=self.hazard_output.output_container,
                site=site_id, imt=self.imt_type, sa_period=self.sa_period,
                sa_damping=self.sa_damping):  # ordered by task_no
            gmvs.extend(gmf.gmvs)
            ruptures.extend(gmf.rupture_ids)
        if not gmvs:
            logs.LOG.warn('No gmvs for site %s, IMT=%s', site_id, self.imt)
        return dict(zip(ruptures, gmvs))

    def get_data(self, monitor):
        all_gmvs = []
        with monitor.copy('getting gmvs and ruptures'):
            for asset in self.assets:
                site_id = self.asset_site[asset.id]
                gmv = self.get_gmv_dict(site_id)
                array = numpy.array([gmv.get(r, 0.) for r in self.rupture_ids])
                all_gmvs.append(array)
        return all_gmvs


class BCRGetter(object):
    def __init__(self, getter_orig, getter_retro):
        self.assets = getter_orig.assets
        self.hid = getter_orig.hid
        self.weight = getter_orig.hid
        #if hasattr(getter_orig, 'rupture_ids'):
        #    self.ruptures = getter_orig.rupture_ids
        #if hasattr(getter_orig, 'epsilons'):
        #    self.epsilons = getter_orig.epsilons

        self.getter_orig = getter_orig
        self.getter_retro = getter_retro

    def __call__(self, monitor):
        return self.getter_orig(monitor), self.getter_retro(monitor)


class GetterBuilder(object):
    """
    .asset_ids
    .site_ids

    Warning: instantiating a GetterBuilder performs a potentially
    expensive geospatial query.
    """
    def __init__(self, gettercls, riskmodel, rc):
        self.gettercls = gettercls
        self.riskmodel = riskmodel
        self.rc = rc
        self.hc = rc.get_hazard_calculation()
        self.max_dist = rc.best_maximum_distance * 1000  # km to meters
        cursor = connections['job_init'].cursor()
        cursor.execute("""
SELECT DISTINCT ON (exp.id) exp.id AS asset_id, hsite.id AS site_id
FROM riski.exposure_data AS exp
JOIN hzrdi.hazard_site AS hsite
ON ST_DWithin(exp.site, hsite.location, %s)
WHERE hsite.hazard_calculation_id = %s
AND exposure_model_id = %s AND taxonomy=%s
AND ST_COVERS(ST_GeographyFromText(%s), exp.site)
ORDER BY exp.id, ST_Distance(exp.site, hsite.location, false)
""", (self.max_dist, self.hc.id, rc.exposure_model.id,
            self.riskmodel.taxonomy, rc.region_constraint.wkt))
        self.asset_ids, self.site_ids = zip(*cursor.fetchall())
        self.rupture_ids = {}
        self.epsilons = {}
        if self.hc.calculation_mode == 'event_based':
            ses_collections = models.SESCollection.objects.filter(
                lt_model__hazard_calculation=self.hc)
            for ses_coll in ses_collections:  # only if hc was an event based
                scid = ses_coll.id
                self.rupture_ids[scid] = rupture_ids = ses_coll.get_ruptures(
                    ).values_list('id', flat=True)
                self.epsilons[scid] = self.make_epsilons(len(rupture_ids))
        elif self.hc.calculation_mode == 'scenario':
            self.epsilons[0] = self.make_epsilons(
                self.hc.number_of_ground_motion_fields)

    def make_epsilons(self, num_samples):
        zeros = numpy.zeros((len(self.asset_ids), num_samples))
        return make_epsilons(
            zeros, self.rc.master_seed, self.rc.asset_correlation)

    def indices_asset_site(self, all_assets):
        indices = []
        assets = []
        asset_site = {}
        for asset in all_assets:
            try:
                idx = self.asset_ids.index(asset.id)
            except ValueError:  # asset.id not in list
                logs.LOG.info(
                    "No hazard with imt %s has been found for "
                    "the asset %s within %s km", self.riskmodel.imt,
                    asset, self.max_dist)
            else:
                asset_site[asset.id] = self.site_ids[idx]
                assets.append(asset)
                indices.append(idx)
        return indices, assets, asset_site

    def init_getters(self, hazard_outputs, asset_block):
        indices, assets, asset_site = self.indices_asset_site(asset_block)
        getters = []
        for ho in hazard_outputs:
            getter = self.gettercls(
                ho, assets, asset_site, self.riskmodel.imt)
            if self.hc.calculation_mode == 'event_based':
                ses_coll = models.SESCollection.objects.get(
                    lt_model=ho.output_container.lt_realization.lt_model)
                getter.rupture_ids = self.rupture_ids[ses_coll.id]
                getter.epsilons = self.epsilons[ses_coll.id][indices]
            elif self.hc.calculation_mode == 'scenario':
                getter.epsilons = self.epsilons[0][indices]
            getters.append(getter)
        self.riskmodel.getters = getters
