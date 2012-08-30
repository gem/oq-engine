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

# pylint: disable=W0232

"""
This module performs hazard calculations using the scenario
event based approach.
"""

import os
import math
import jpype
import json

from openquake import java
from openquake import kvs
from openquake import logs
from openquake import shapes
from openquake.calculators.hazard.general import BaseHazardCalculator
from openquake.output import hazard as hazard_output
from openquake.utils import stats


class ScenarioHazardCalculator(BaseHazardCalculator):
    """Scenario Event Based method for performing hazard calculations."""

    def initialize_pr_data(self, num_calculations):
        """
        Record the total/completed number of work items.

        This is needed for the purpose of providing an indication of progress
        to the end user."""
        stats.pk_set(self.job_ctxt.job_id, "lvr", 0)
        stats.pk_set(self.job_ctxt.job_id, "nhzrd_total", num_calculations)
        stats.pk_set(self.job_ctxt.job_id, "nhzrd_done", 0)

    @java.unpack_exception
    def execute(self):
        """Entry point to trigger the computation."""

        random_generator = java.jclass(
            "Random")(int(self.job_ctxt.params["GMF_RANDOM_SEED"]))

        encoder = json.JSONEncoder()
        kvs_client = kvs.get_client()

        num_calculations = self._number_of_calculations()
        self.initialize_pr_data(num_calculations)

        for cnum in xrange(num_calculations):
            try:
                gmf = self.compute_ground_motion_field(random_generator)
                stats.pk_inc(self.job_ctxt.job_id, "nhzrd_done", 1)
            except:
                # Count failure
                stats.pk_inc(self.job_ctxt.job_id, "nhzrd_failed", 1)
                raise
            logs.log_percent_complete(self.job_ctxt.job_id, "hazard")
            imt = self.job_ctxt.params["INTENSITY_MEASURE_TYPE"]
            self._serialize_gmf(gmf, imt, cnum)

            for gmv in gmf_to_dict(gmf, imt):
                site = shapes.Site(gmv["site_lon"], gmv["site_lat"])

                key = kvs.tokens.ground_motion_values_key(
                    self.job_ctxt.job_id, site)
                kvs_client.rpush(key, encoder.encode(gmv))

    def _serialize_gmf(self, hashmap, imt, cnum):
        """Write the GMF as returned by the java calculator to file.

        The java calculator returns an implementation of java.util.Map
        where the key is an instance of org.opensha.commons.data.Site
        and the value is an instance of java.lang.Double.

        :param hashmap: map containing the ground motion field.
        :type hashmap: jpype wrapper around java.util.Map. The map
            contains instances of org.opensha.commons.data.Site as
            keys and java.lang.Double as values (the ground motion
            value for that specific site)
        :param str imt: the intensity measure type specified for this job.
            If the type is not "MMI" we need to save the exponential.
        :param int cnum: the calculation number, part of the GMF file name.
        :returns: `True` if the GMF contained in the `hashmap` was serialized,
            `False` otherwise.
        """
        if not self.job_ctxt['SAVE_GMFS']:
            return False

        path = os.path.join(self.job_ctxt.base_path,
                            self.job_ctxt['OUTPUT_DIR'], "gmf-%s.xml" % cnum)
        gmf_writer = hazard_output.create_gmf_writer(
            self.job_ctxt.job_id, self.job_ctxt.serialize_results_to, path)

        gmf_data = _prepare_gmf_serialization(hashmap, imt)
        gmf_writer.serialize(gmf_data)

        return True

    def _number_of_calculations(self):
        """Return the number of calculations to trigger.

        NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS is the key used
        in the configuration file.

        :returns: the number of computations to trigger.
        """

        value = int(self.job_ctxt.params[
            "NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS"])

        if value <= 0:
            raise ValueError("NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS "
                             "must be grater than zero.")

        return value

    def compute_ground_motion_field(self, random_generator):
        """Compute the ground motion field for the entire region.

        :param random_generator: a generator used internally
            by the calculator.
        :type random_generator: jpype wrapper around an instance of
            java.util.Random
        :returns: the computed ground motion field as a jpype wrapper
            around an instance of java.util.Map.
        """

        calculator = self.gmf_calculator(self.job_ctxt.sites_to_compute())

        if (self.job_ctxt.params["GROUND_MOTION_CORRELATION"].lower()
            == "true"):
            return calculator.getCorrelatedGroundMotionField_JB2009(
                random_generator)
        else:
            return calculator.getUncorrelatedGroundMotionField(
                random_generator)

    def gmf_calculator(self, sites):
        """Return the ground motion field calculator.

        :param sites: sites used to compute the ground motion field.
        :type sites: list of :py:class:`shapes.Site`
        :returns: jpype wrapper around an instance of
            org.gem.calc.GroundMotionFieldCalculator.
        """

        calculator = getattr(self, "calculator", None)

        if calculator is None:
            sites = self.parameterize_sites(sites)

            calculator = java.jclass(
                "GMFCalculator")(self.gmpe, self.rupture_model, sites)

            setattr(self, "calculator", calculator)

        return self.calculator

    @property
    def rupture_model(self):
        """Load the rupture model specified in the configuration file.

        The key used in the configuration file is SINGLE_RUPTURE_MODEL.

        :returns: jpype wrapper around an instance of
            org.opensha.sha.earthquake.EqkRupture.
        """

        rel_path = self.job_ctxt.params["SINGLE_RUPTURE_MODEL"]
        abs_path = os.path.join(self.job_ctxt.params["BASE_PATH"], rel_path)
        grid_spacing = float(
            self.job_ctxt.params["RUPTURE_SURFACE_DISCRETIZATION"])

        return java.jclass("RuptureReader")(abs_path, grid_spacing).read()

    @property
    def gmpe(self):
        """Load the ground motion prediction equation specified
        in the configuration file.

        The key used in the configuration file is GMPE_MODEL_NAME.

        :returns: jpype wrapper around an instance of the
            ground motion prediction equation.
        """

        deserializer = java.jclass("GMPEDeserializer")()

        package_name = "org.opensha.sha.imr.attenRelImpl"
        class_name = self.job_ctxt.params["GMPE_MODEL_NAME"]
        fqn = package_name + "." + class_name

        gmpe = deserializer.deserialize(
            java.jclass("JsonPrimitive")(fqn), None, None)

        tree_data = java.jclass("GmpeLogicTreeData")

        tree_data.setGmpeParams(
            self.job_ctxt.params["COMPONENT"],
            self.job_ctxt.params["INTENSITY_MEASURE_TYPE"],
            jpype.JDouble(float(self.job_ctxt.params["PERIOD"])),
            jpype.JDouble(float(self.job_ctxt.params["DAMPING"])),
            self.job_ctxt.params["GMPE_TRUNCATION_TYPE"],
            jpype.JDouble(float(self.job_ctxt.params["TRUNCATION_LEVEL"])),
            "Total",
            jpype.JObject(gmpe, java.jclass("AttenuationRelationship")))

        return gmpe


def gmf_to_dict(hashmap, intensity_measure_type):
    """Transform the ground motion field as returned by the java
    calculator into a simple dict.

    The java calculator returns an implementation of java.util.Map
    where the key is an instance of org.opensha.commons.data.Site
    and the value is an instance of java.lang.Double.

    This function is implemented as an iterator.

    :param hashmap: map containing the ground motion field.
    :type hashmap: jpype wrapper around java.util.Map. The map
        contains instances of org.opensha.commons.data.Site as
        keys and java.lang.Double as values (the ground motion
        value for that specific site)
    :param intensity_measure_type: the intensity measure type
        specified for this job. If the type is not "MMI" we
        need to save the exponential.
    :returns: the ground motion field as :py:class:`dict`.
        The dictionary contians the following keys:
        **site_lat** - the latitude of the site
        **site_lon** - the longitude of the site
        **mag** - the ground motion value
    """

    for site in hashmap.keySet():
        mag = hashmap.get(site).doubleValue()

        if intensity_measure_type.lower() != "mmi":
            mag = math.exp(mag)

        lat = site.getLocation().getLatitude()
        lon = site.getLocation().getLongitude()

        gmv = {"site_lat": lat, "site_lon": lon, "mag": mag}
        yield gmv


def _prepare_gmf_serialization(hashmap, imt):
    """Returns a GMF in the format expected by the GMF serializer.

    The java calculator returns an implementation of java.util.Map
    where the key is an instance of org.opensha.commons.data.Site
    and the value is an instance of java.lang.Double.

    :param hashmap: map containing the ground motion field.
    :type hashmap: jpype wrapper around java.util.Map. The map
        contains instances of org.opensha.commons.data.Site as
        keys and java.lang.Double as values (the ground motion
        value for that specific site)
    :param str imt: the intensity measure type specified for this job.
        If the type is not "MMI" we need to save the exponential.
    :returns: the ground motion field as :py:class:`dict`.
        The dictionary key is the site, the value is another `dict`
        with the GMF value.
    """
    gmf_data = {}
    for site in hashmap.keySet():
        gmf_value = hashmap.get(site).doubleValue()

        if imt.lower() != "mmi":
            gmf_value = math.exp(gmf_value)

        lat = site.getLocation().getLatitude()
        lon = site.getLocation().getLongitude()
        site = shapes.Site(lon, lat)
        gmf_data[site] = {'groundMotion': gmf_value}

    return gmf_data
