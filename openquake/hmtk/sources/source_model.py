# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Module implements
:class:`openquake.hmtk.sources.source_model.mtkSourceModel`, the
general class to describe a set of seismogenic sources
"""

from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.sourcewriter import write_source_model
from openquake.hmtk.sources.point_source import mtkPointSource
from openquake.hmtk.sources.area_source import mtkAreaSource
from openquake.hmtk.sources.simple_fault_source import mtkSimpleFaultSource
from openquake.hmtk.sources.complex_fault_source import mtkComplexFaultSource


class mtkSourceModel(object):
    """
    Object to describe a seismogenic source model (composite of
    multiple sources with mixed typologies)

    :param str id:
        Identifier for the source model
    :param str name:
        Source model name
    :param list sources:
        List of seismogenic sources
    """

    def __init__(self, identifier=None, name=None, sources=None):
        self.id = identifier
        self.name = name
        if isinstance(sources, list):
            self.sources = sources
        else:
            if sources:
                raise ValueError("Sources must be input as list!")
            self.sources = []

    def __iter__(self):
        for source in self.sources:
            yield source

    def __len__(self):
        return len(self.sources)

    def get_number_sources(self):
        """
        Returns the number of sources in the model
        """
        return len(self.sources)

    def serialise_to_nrml(
        self,
        filename,
        mesh_spacing=2,
        complex_mesh_spacing=2,
        use_defaults=False,
    ):
        """
        Writes the source model to a nrml source model file given by the
        filename

        :param str filename:
            Path to output file

        :param bool use_defaults:
            Boolean to indicate whether to use default values (True) or not.
            If set to False, ValueErrors will be raised when an essential
            attribute is missing.
        """
        source_model = self.convert_to_oqhazardlib(
            PoissonTOM(1.0),
            mesh_spacing,
            complex_mesh_spacing,
            10.0,
            use_defaults=use_defaults,
        )
        write_source_model(filename, source_model, name=self.name)

    def convert_to_oqhazardlib(
        self,
        tom,
        simple_mesh_spacing=1.0,
        complex_mesh_spacing=2.0,
        area_discretisation=10.0,
        use_defaults=False,
    ):
        """
        Converts the source model to an iterator of sources of :class:
        `openquake.hazardlib.source.base.BaseSeismicSource`
        """
        oq_source_model = []
        for source in self.sources:
            if isinstance(source, mtkAreaSource):
                oq_source_model.append(
                    source.create_oqhazardlib_source(
                        tom,
                        simple_mesh_spacing,
                        area_discretisation,
                        use_defaults,
                    )
                )
            elif isinstance(source, mtkPointSource):
                oq_source_model.append(
                    source.create_oqhazardlib_source(
                        tom, simple_mesh_spacing, use_defaults
                    )
                )
            elif isinstance(source, mtkSimpleFaultSource):
                oq_source_model.append(
                    source.create_oqhazardlib_source(
                        tom, simple_mesh_spacing, use_defaults
                    )
                )
            elif isinstance(source, mtkComplexFaultSource):
                oq_source_model.append(
                    source.create_oqhazardlib_source(
                        tom, complex_mesh_spacing, use_defaults
                    )
                )
            else:
                raise ValueError("Source type not recognised!")
        return oq_source_model
