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
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

"""
Module :mod:`openquake.hmtk.parsers.catalogue.base` defines an abstract base
class for :class:`CatalogueParser <BaseCatalogueParser>`.
"""
import abc
import os.path


class BaseCatalogueParser(object):
    """
    A base class for a Catalogue Parser
    """

    def __init__(self, input_file):
        """
        Initialise the object and check input file existance
        """
        self.input_file = input_file
        if not os.path.exists(self.input_file):
            raise IOError("File not found: %s" % input_file)

    @abc.abstractmethod
    def read_file(self):
        """
        Return an instance of the class :class:`Catalogue`
        """


class BaseCatalogueWriter(object):
    """
    A base class for a Catalogue writer
    """

    def __init__(self, output_file):
        """
        Initialise the object and check output file existance. If file already
        exists then raise error
        """
        self.output_file = output_file
        if os.path.exists(self.output_file):
            raise IOError(
                "Catalogue output file %s already exists!" % self.output_file
            )

    @abc.abstractmethod
    def write_file(self):
        """
        Return an instance of the class :class:`Catalogue`
        """
