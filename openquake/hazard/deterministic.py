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

from openquake import java
from openquake import kvs
from openquake import shapes
from openquake.hazard import job


class DeterministicEventBasedMixin:
    """Deterministic Event Based method for performing hazard calculations.

    Note that this mixin, during execution, will always be an instance of the
    Job class, and thus has access to the self.params dict, full of config
    params loaded from the job configuration file."""

    def execute(self):
        """Entry point for triggering the computation."""

        for i in xrange(self._number_of_calculations()):
            gmf = self.compute_ground_motion_field()

# TODO (ac): Add doc, saying that we might store multiple sites for each key
            for gmv in gmf_to_dict(gmf):
                site = shapes.Site(gmv["site_lon"], gmv["site_lat"])

                kvs.set_value_json_encoded(
                    kvs.tokens.ground_motion_value_key(
                    self.job_id, site.hash(), i + 1), gmv)

        return [True]

    def _number_of_calculations(self):
        """Return the number of calculations to trigger."""

        value = int(self.params["NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS"])

        if value <= 0:
            raise ValueError("NUMBER_OF_GROUND_MOTION_FIELDS_CALCULATIONS "
                             "must be grater than zero.")

        return value

# TODO (ac): Add doc, saying that there's no way to split the computation
    def compute_ground_motion_field(self):
        """Compute the ground motion field for the entire region."""
        
        rupture = self._load_rupture_model()
        gmpe = self._load_gmpe()

        calculator = java.jclass("GMFCalculator")(gmpe, rupture, self._sites())
        random_generator = java.jclass("Random")(int(self.params["GMF_RANDOM_SEED"]))

        if self.params["GROUND_MOTION_CORRELATION"].lower() == "true":
            return calculator.getUncorrelatedGroundMotionField(
                random_generator)
        else:
            return calculator.getCorrelatedGroundMotionField_JB2009(
                random_generator)

    def _sites(self):
        sites = java.jclass("ArrayList")()

# TODO (ac): Refactoring, already coded in opensha.py
        for site in self.sites_for_region():
            jsite = site.to_java()
            
            vs30 = java.jclass("DoubleParameter")(jpype.JString("Vs30"))
            vs30.setValue(float(self.params["REFERENCE_VS30_VALUE"]))
            depth25 = java.jclass("DoubleParameter")("Depth 2.5 km/sec")

            depth25.setValue(float(
                    self.params["REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM"]))

            sadigh = java.jclass("StringParameter")("Sadigh Site Type")
            sadigh.setValue(self.params["SADIGH_SITE_TYPE"])

            jsite.addParameter(vs30)
            jsite.addParameter(depth25)
            jsite.addParameter(sadigh)

            sites.add(jsite)

        return sites

    def _load_rupture_model(self):
        """Load the rupture model specified in the configuration file."""
        
        rel_path = self.params["SINGLE_RUPTURE_MODEL"]
        abs_path = os.path.join(self.params["BASE_PATH"], rel_path)
        grid_spacing = self.params["REGION_GRID_SPACING"]

        return java.jclass("RuptureReader")(abs_path, grid_spacing).read()

    def _load_gmpe(self):
        """Load the ground motion prediction equation specified
        in the configuration file."""
        
        deserializer = java.jclass("GMPEDeserializer")()
        class_name = self.params["GMPE_MODEL_NAME"]
        
        gmpe = deserializer.deserialize(
            java.jclass("JsonPrimitive")(class_name), None, None)
        
        tree_data = java.jclass("GmpeLogicTreeData")()

        tree_data.setGmpeParams(
            self.params["COMPONENT"],
            self.params["INTENSITY_MEASURE_TYPE"],
            jpype.JDouble(float(self.params["PERIOD"])),
            jpype.JDouble(float(self.params["DAMPING"])),
            self.params["GMPE_TRUNCATION_TYPE"],
            jpype.JDouble(float(self.params["TRUNCATION_LEVEL"])),
            self.params["STANDARD_DEVIATION_TYPE"],
            jpype.JDouble(float(self.params["REFERENCE_VS30_VALUE"])),
            jpype.JObject(gmpe, java.jclass("AttenuationRelationship")))

        return gmpe


def gmf_to_dict(hashmap):
    """Transform the ground motion field as returned by the java
    calculator into a simple dict.

    The java calculator returns an implementation of java.util.Map
    where the key is an instance of org.opensha.commons.data.Site
    and the value is an instance of java.lang.Double.

    This function is implemented as an iterator.
    """

    for site in hashmap.keySet():
        mag = hashmap.get(site).doubleValue()
        lat = site.getLocation().getLatitude()
        lon = site.getLocation().getLongitude()

        gmv = {"site_lat": lat, "site_lon": lon, "mag": math.exp(mag)}
        yield gmv


job.HazJobMixin.register(
    "Deterministic", DeterministicEventBasedMixin, order=2)
