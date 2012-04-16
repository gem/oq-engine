# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


"""Fragility model NRML parser"""

from collections import namedtuple
from lxml import etree

from openquake import producer
from openquake import xml
from openquake.nrml import nrml_schema_file


# Disabling pylint checks: too many local vars
# pylint: disable=R0914


FRAGM = namedtuple("FRAGM", "id, format, limits, description, imls, imt, "
                   "iml_unit, max_iml, min_iml")
FFD = namedtuple("FFD", "taxonomy, type, limit, poes")
FFC = namedtuple("FFC", "taxonomy, type, limit, mean, stddev")


class FragilityModelParser(producer.FileProducer):
    """Parses fragility models in NRML representation"""

    def __init__(self, path):
        super(FragilityModelParser, self).__init__(path)
        self.model = None
        self.ffs = None
        self.discrete = False

    def _parse(self):
        try:
            for i in self._do_parse():
                yield i
        except etree.XMLSyntaxError as ex:
            raise xml.XMLValidationError(ex.message, self.file.name)

    def _do_parse(self):
        """parser implementation"""
        # The tags we expect to see:
        ffs_tag = '%sffs' % xml.NRML
        ffc_tag = '%sffc' % xml.NRML
        ffd_tag = '%sffd' % xml.NRML

        first_ffs = True

        schema = etree.XMLSchema(etree.parse(nrml_schema_file()))
        parse_args = dict(source=self.file, events=("end",), schema=schema)

        for _, element in etree.iterparse(**parse_args):
            # start: fragility model
            if element.tag == ffs_tag:
                if first_ffs:
                    # parse the "fragilityModel" element data only once
                    self._parse_model(element.getparent())
                    first_ffs = False
                self.ffs = dict(type=None)
                self.ffs["type"] = element.get('type')
                taxonomy = element.find('%staxonomy' % xml.NRML)
                assert taxonomy is not None, "taxonomy not set"
                self.ffs["taxonomy"] = taxonomy.text.strip()
                tag, func = ((ffd_tag, self._parse_ffd) if self.discrete
                             else (ffc_tag, self._parse_ffc))
                for child in element.iterchildren(tag=tag):
                    yield func(child)

    def _parse_model(self, element):
        """Parse the fragility model."""
        mdl = dict(description=None, imls=None, imt=None)
        mdl["id"] = element.get('%sid' % xml.GML)

        mdl["format"] = element.get('format')
        assert mdl["format"] in ("continuous", "discrete"), (
            "invalid fragility model format (%s)" % mdl["format"])
        if mdl["format"] == "discrete":
            self.discrete = True

        attr_data = (("iml_unit", "imlUnit"), ("max_iml", "maxIML"),
                     ("min_iml", "minIML"))
        for key, attr in attr_data:
            mdl[key] = element.get(attr)

        limits = element.find('%slimitStates' % xml.NRML)
        assert limits is not None, "no limit states found"
        mdl["limits"] = [ls.strip() for ls in limits.text.split()]

        imls = element.find('%sIML' % xml.NRML)
        if self.discrete:
            assert imls is not None, "IML not set"
            mdl["imls"] = [float(iml) for iml in imls.text.split()]
            mdl["imt"] = imls.get('IMT')
            assert mdl["maxIML"] is None, (
                "'maxIML' is invalid for discrete fragility models")
            assert mdl["minIML"] is None, (
                "'minIML' is invalid for discrete fragility models")

        desc = element.find('%sdescription' % xml.GML)
        if desc is not None:
            mdl["description"] = desc.text
        self.model = mdl = FRAGM(**mdl)

    def _parse_ffd(self, element):
        """Parses a discrete fragility function tag."""
        assert self.discrete, ("invalid model format (%s) for discrete "
            "fragility function" % self.model.format)
        ffd = dict(**self.ffs)
        ff_ls = element.get('ls').strip()
        assert ff_ls in self.model.limits, (
            "invalid limit state (%s) for function with taxonomy %s"
            % (ff_ls, self.ffs["taxonomy"]))
        ffd["limit"] = ff_ls
        poes = element.find('%spoE' % xml.NRML)
        assert poes is not None, "poes not set"
        ffd["poes"] = [float(poe) for poe in poes.text.split()]
        del element
        return FFD(**ffd)

    def _parse_ffc(self, element):
        """Parses a continuous fragility function tag."""
        assert not self.discrete, (
            "invalid model format (%s) for continuous fragility "
            "function" % self.model.format)
        ffc = dict(**self.ffs)
        ff_ls = element.get('ls').strip()
        assert ff_ls in self.model.limits, (
            "invalid limit state (%s) for function with taxonomy %s"
            % (ff_ls, self.ffs["taxonomy"]))
        ffc["limit"] = ff_ls
        params = element.find('%sparams' % xml.NRML)
        assert params is not None, "params not set"
        ffc["mean"] = float(params.get("mean"))
        ffc["stddev"] = float(params.get("stddev"))
        del element
        return FFC(**ffc)
