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

# pylint: disable=W0232

"""
This module performs hazard calculations using the deterministic
event based approach.
"""

import os
import math
import jpype
import json

from openquake import java
from openquake import kvs
from openquake import shapes
from openquake.hazard.job import general
from openquake.hazard.job.opensha import BasePSHAMixin


class DeterministicEventBasedMixin(BasePSHAMixin):
    """Deterministic Event Based method for performing hazard calculations.

    Note that this mixin, during execution, will always be an instance of the
    Job class, and thus has access to the self.params dict, full of config
    params loaded from the job configuration file."""

    @java.jexception
    def execute(self):
        """Entry point to trigger the computation."""

        random_generator = java.jclass(
            "Random")(int(self.params["GMF_RANDOM_SEED"]))

        encoder = json.JSONEncoder()
        kvs_client = kvs.get_client()

        grid = self.region.grid

        for _ in xrange(self._number_of_calculations()):
            gmf = self.compute_ground_motion_field(random_generator)

            for gmv in gmf_to_dict(
                gmf, self.params["INTENSITY_MEASURE_TYPE"]):

                site = shapes.Site(gmv["site_lon"], gmv["site_lat"])
                point = grid.point_at(site)

                key = kvs.tokens.ground_motion_values_key(
                    self.job_id, point)

                kvs_client.rpush(key, encoder.encode(gmv))

    def _number_of_calculations(self):
        """Return the number of calculations to trigger.

        NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS is the key used
        in the configuration file.

        :returns: the number of computations to trigger.
        """

        value = int(self.params["NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS"])

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

        calculator = self.gmf_calculator(self.sites_to_compute())

        if self.params["GROUND_MOTION_CORRELATION"].lower() == "true":
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

        rel_path = self.params["SINGLE_RUPTURE_MODEL"]
        abs_path = os.path.join(self.params["BASE_PATH"], rel_path)
        grid_spacing = float(self.params["RUPTURE_SURFACE_DISCRETIZATION"])

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
        class_name = self.params["GMPE_MODEL_NAME"]
        fqn = package_name + "." + class_name

        gmpe = deserializer.deserialize(
            java.jclass("JsonPrimitive")(fqn), None, None)

        tree_data = java.jclass("GmpeLogicTreeData")()

        tree_data.setGmpeParams(
            self.params["COMPONENT"],
            self.params["INTENSITY_MEASURE_TYPE"],
            jpype.JDouble(float(self.params["PERIOD"])),
            jpype.JDouble(float(self.params["DAMPING"])),
            self.params["GMPE_TRUNCATION_TYPE"],
            jpype.JDouble(float(self.params["TRUNCATION_LEVEL"])), "Total",
            jpype.JDouble(float(self.params["REFERENCE_VS30_VALUE"])),
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


general.HazJobMixin.register(
    "Deterministic", DeterministicEventBasedMixin, order=2)
