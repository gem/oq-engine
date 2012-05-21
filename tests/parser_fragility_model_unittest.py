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


import os
import unittest
import shutil

from openquake.parser import fragility
from openquake import xml

from tests.utils import helpers


CONTINUOUS_MODEL = os.path.join(helpers.SCHEMA_DIR, "examples/fragm_c.xml")
DISCRETE_MODEL = os.path.join(helpers.SCHEMA_DIR, "examples/fragm_d.xml")
TEMP_FILE = os.path.join(helpers.SCHEMA_DIR, "examples/temp.xml")


def setup_parser(content):
    path = helpers.touch(content=content.strip())
    return fragility.FragilityModelParser(path)


class FragilityModelParserTestCase(unittest.TestCase):
    """General fragility model parser tests."""

    def setUp(self):
        self.parser = None

    def tearDown(self):
        os.unlink(self.parser.path)

    def test_parser_with_invalid_format(self):
        # An invalid fragility model format results in errors.
        content = """
            <?xml version='1.0' encoding='utf-8'?>
            <nrml xmlns:gml="http://www.opengis.net/gml"
                  xmlns="http://openquake.org/xmlns/nrml/0.3"
                  gml:id="n2">
                <fragilityModel gml:id="ep2" format="--invalid--">
                </fragilityModel>
            </nrml>"""
        self.parser = setup_parser(content)

        with self.assertRaises(xml.XMLValidationError) as e:
            list(self.parser)

            self.assertTrue("'--invalid--' is not an element" in
                e.exception.mesagge)

    def test_parser_with_no_limit_states(self):
        # A fragility model without limit states results in errors.
        content = """
            <?xml version='1.0' encoding='utf-8'?>
            <nrml xmlns:gml="http://www.opengis.net/gml"
                  xmlns="http://openquake.org/xmlns/nrml/0.3"
                  gml:id="n2">
                <fragilityModel gml:id="ep2" format="discrete">
                </fragilityModel>
            </nrml>"""
        self.parser = setup_parser(content)

        with self.assertRaises(xml.XMLValidationError) as e:
            list(self.parser)

            self.assertTrue("limitStates" in e.exception.message)

    def test_parser_with_no_taxonomy(self):
        # A fragility function set without a taxonomy results in errors.
        content = """
            <?xml version='1.0' encoding='utf-8'?>
            <nrml xmlns:gml="http://www.opengis.net/gml"
                  xmlns="http://openquake.org/xmlns/nrml/0.3"
                  gml:id="n2">
                <fragilityModel gml:id="ep2" format="discrete">
                    <IML IMT="MMI">7 8</IML>
                    <limitStates>collapse</limitStates>
                    <ffs gml:id="PAV01-ff02-d">
                        <ffd ls="collapse"><poE>0.03 0.63</poE></ffd>
                    </ffs>
                </fragilityModel>
            </nrml>"""
        self.parser = setup_parser(content)

        with self.assertRaises(xml.XMLValidationError) as e:
            list(self.parser)

            self.assertTrue("taxonomy" in e.exception.message)

    def test_parser_with_invalid_limit_state(self):
        # A fragility function with an invalid limit state results in errors.
        content = """
            <?xml version='1.0' encoding='utf-8'?>
            <nrml xmlns:gml="http://www.opengis.net/gml"
                  xmlns="http://openquake.org/xmlns/nrml/0.3"
                  gml:id="n2">
                <fragilityModel gml:id="ep2" format="discrete">
                    <IML IMT="MMI">7 8</IML>
                    <limitStates>collapse</limitStates>
                    <ffs gml:id="PAV01-ff02-d">
                        <taxonomy>RC/DMRF-D/HR</taxonomy>
                        <ffd ls="!all-is-fine!"><poE>0.03 0.63</poE></ffd>
                    </ffs>
                </fragilityModel>
            </nrml>"""
        self.parser = setup_parser(content)

        with self.assertRaises(AssertionError) as e:
            list(self.parser)

            self.assertEqual("invalid limit state (!all-is-fine!) for "
                             "function with taxonomy RC/DMRF-D/HR",
                             e.exception.message)


class DiscreteFragilityModelParserTestCase(unittest.TestCase):
    """Tests for the discrete fragility model parser."""

    def setUp(self):
        self.parser = None

    def tearDown(self):
        os.unlink(self.parser.path)

    def test_parser(self):
        # A valid discrete fragility model is parsed without errors.
        expected = [
            fragility.FFD(taxonomy='RC/DMRF-D/LR', type=None, limit='minor',
                          poes=[0.0, 0.09, 0.56, 0.91, 0.98]),
            fragility.FFD(taxonomy='RC/DMRF-D/LR', type=None, limit='moderate',
                          poes=[0.0, 0.0, 0.04, 0.78, 0.96]),
            fragility.FFD(taxonomy='RC/DMRF-D/LR', type=None, limit='severe',
                          poes=[0.0, 0.0, 0.0, 0.29, 0.88]),
            fragility.FFD(taxonomy='RC/DMRF-D/LR', type=None, limit='collapse',
                          poes=[0.0, 0.0, 0.0, 0.03, 0.63]),
            fragility.FFD(taxonomy='RC/DMRF-D/HR', type=None, limit='minor',
                          poes=[0.0, 0.09, 0.56, 0.92, 0.99]),
            fragility.FFD(taxonomy='RC/DMRF-D/HR', type=None, limit='moderate',
                          poes=[0.0, 0.0, 0.04, 0.79, 0.97]),
            fragility.FFD(taxonomy='RC/DMRF-D/HR', type=None, limit='severe',
                          poes=[0.0, 0.0, 0.0, 0.3, 0.89]),
            fragility.FFD(taxonomy='RC/DMRF-D/HR', type=None, limit='collapse',
                          poes=[0.0, 0.0, 0.0, 0.04, 0.64])]
        shutil.copyfile(DISCRETE_MODEL, TEMP_FILE)
        self.parser = fragility.FragilityModelParser(TEMP_FILE)
        results = list(self.parser)

        self.assertEqual(expected, results)

        expected = fragility.FRAGM(
            id='ep1', format='discrete',
            limits=['minor', 'moderate', 'severe', 'collapse'],
            description='Fragility model for Pavia (discrete)',
            imls=[7.0, 8.0, 9.0, 10.0, 11.0], imt='MMI', iml_unit="g",
            max_iml=None, min_iml=None)

        self.assertEqual(expected, self.parser.model)

    def test_parser_with_no_imls(self):
        # A fragility model without IMLs results in errors.
        content = """
            <?xml version='1.0' encoding='utf-8'?>
            <nrml xmlns:gml="http://www.opengis.net/gml"
                  xmlns="http://openquake.org/xmlns/nrml/0.3"
                  gml:id="n2">
                <fragilityModel gml:id="ep2" format="discrete">
                    <limitStates>collapse</limitStates>
                    <ffs gml:id="PAV01-ff02-d">
                        <taxonomy>RC/DMRF-D/LR</taxonomy>
                        <ffd ls="collapse"><poE>0.03 0.63</poE></ffd>
                    </ffs>
                </fragilityModel>
            </nrml>"""
        self.parser = setup_parser(content)

        with self.assertRaises(AssertionError) as e:
            list(self.parser)

            self.assertEqual("IML not set", e.exception.message)

    def test_parser_with_no_poes(self):
        # A fragility function without poes will results in errors.
        content = """
            <?xml version='1.0' encoding='utf-8'?>
            <nrml xmlns:gml="http://www.opengis.net/gml"
                  xmlns="http://openquake.org/xmlns/nrml/0.3"
                  gml:id="n2">
                <fragilityModel gml:id="ep2" format="discrete">
                    <IML IMT="MMI">7 8</IML>
                    <limitStates>collapse</limitStates>
                    <ffs gml:id="PAV01-ff02-d">
                        <taxonomy>RC/DMRF-D/HR</taxonomy>
                        <ffd ls="collapse"></ffd>
                    </ffs>
                </fragilityModel>
            </nrml>"""
        self.parser = setup_parser(content)

        with self.assertRaises(xml.XMLValidationError) as e:
            list(self.parser)

            self.assertTrue("poE" in e.exception.message)

    def test_parser_with_max_iml(self):
        # A discrete fragility model with 'maxIML' results in errors.
        content = """
            <?xml version='1.0' encoding='utf-8'?>
            <nrml xmlns:gml="http://www.opengis.net/gml"
                  xmlns="http://openquake.org/xmlns/nrml/0.3"
                  gml:id="n2">
                <fragilityModel gml:id="ep2" format="discrete" maxIML="1.1">
                    <IML IMT="MMI">7 8</IML>
                    <limitStates>collapse</limitStates>
                    <ffs gml:id="PAV01-ff02-d">
                        <taxonomy>RC/DMRF-D/LR</taxonomy>
                        <ffd ls="collapse"><poE>0.03 0.63</poE></ffd>
                    </ffs>
                </fragilityModel>
            </nrml>"""
        self.parser = setup_parser(content)

        with self.assertRaises(AssertionError) as e:
            list(self.parser)

            self.assertEqual(
                "'maxIML' must not be set for discrete fragility models",
                e.exception.message)

    def test_parser_with_min_iml(self):
        # A discrete fragility model with 'minIML' results in errors.
        content = """
            <?xml version='1.0' encoding='utf-8'?>
            <nrml xmlns:gml="http://www.opengis.net/gml"
                  xmlns="http://openquake.org/xmlns/nrml/0.3"
                  gml:id="n2">
                <fragilityModel gml:id="ep2" format="discrete" minIML="1.1">
                    <IML IMT="MMI">7 8</IML>
                    <limitStates>collapse</limitStates>
                    <ffs gml:id="PAV01-ff02-d">
                        <taxonomy>RC/DMRF-D/LR</taxonomy>
                        <ffd ls="collapse"><poE>0.03 0.63</poE></ffd>
                    </ffs>
                </fragilityModel>
            </nrml>"""
        self.parser = setup_parser(content)

        with self.assertRaises(AssertionError) as e:
            list(self.parser)

            self.assertEqual(
                "'minIML' must not be set for discrete fragility models",
                e.exception.message)


class ContinuousFragilityModelParserTestCase(unittest.TestCase):
    """Tests for the continuous fragility model parser."""

    def setUp(self):
        self.parser = None

    def tearDown(self):
        os.unlink(self.parser.path)

    def test_parser(self):
        # A valid continuous fragility model is parsed without errors.

        expected = [
            fragility.FFC(taxonomy='RC/DMRF-D/LR', type='lognormal',
                          limit='slight', mean=11.19, stddev=8.27),
            fragility.FFC(taxonomy='RC/DMRF-D/LR', type='lognormal',
                          limit='moderate', mean=27.98, stddev=20.677),
            fragility.FFC(taxonomy='RC/DMRF-D/LR', type='lognormal',
                          limit='extensive', mean=48.05, stddev=42.49),
            fragility.FFC(taxonomy='RC/DMRF-D/LR', type='lognormal',
                          limit='complete', mean=108.9, stddev=123.7),
            fragility.FFC(taxonomy='RC/DMRF-D/HR', type=None,
                          limit='slight', mean=11.18, stddev=8.28),
            fragility.FFC(taxonomy='RC/DMRF-D/HR', type=None,
                          limit='moderate', mean=27.99, stddev=20.667),
            fragility.FFC(taxonomy='RC/DMRF-D/HR', type=None,
                          limit='extensive', mean=48.06, stddev=42.48),
            fragility.FFC(taxonomy='RC/DMRF-D/HR', type=None,
                          limit='complete', mean=108.8, stddev=123.6)]

        shutil.copyfile(CONTINUOUS_MODEL, TEMP_FILE)
        self.parser = fragility.FragilityModelParser(TEMP_FILE)
        results = list(self.parser)

        self.assertEqual(expected, results)

        expected = fragility.FRAGM(
            id='ep1', format='continuous',
            limits=['slight', 'moderate', 'extensive', 'complete'],
            description='Fragility model for Pavia (continuous)',
            imls=None, imt=None, iml_unit="m", max_iml="9.9", min_iml="0.1")

        self.assertEqual(expected, self.parser.model)

    def test_parser_with_no_params(self):
        # A continuous fragility function without parameters will result in
        # errors.
        content = """
            <?xml version='1.0' encoding='utf-8'?>
            <nrml xmlns:gml="http://www.opengis.net/gml"
                  xmlns="http://openquake.org/xmlns/nrml/0.3"
                  gml:id="n2">
                <fragilityModel gml:id="ep2" format="discrete">
                    <IML IMT="MMI">7 8 9 10 11</IML>
                    <limitStates>slight</limitStates>
                    <ffs gml:id="PAV01-ff02-c" type="lognormal">
                        <taxonomy>RC/DMRF-D/LR</taxonomy>
                        <ffc ls="slight"></ffc>
                    </ffs>
                </fragilityModel>
            </nrml>"""
        self.parser = setup_parser(content)

        with self.assertRaises(xml.XMLValidationError) as e:
            list(self.parser)

            self.assertTrue("params" in e.exception.message)

    def test_parser_with_params_but_no_means(self):
        # A continuous fragility function without a mean parameter will result
        # in errors.
        content = """
            <?xml version='1.0' encoding='utf-8'?>
            <nrml xmlns:gml="http://www.opengis.net/gml"
                  xmlns="http://openquake.org/xmlns/nrml/0.3"
                  gml:id="n2">
                <fragilityModel gml:id="ep2" format="discrete">
                    <IML IMT="MMI">7 8 9 10 11</IML>
                    <limitStates>slight</limitStates>
                    <ffs gml:id="PAV01-ff02-c" type="lognormal">
                        <taxonomy>RC/DMRF-D/LR</taxonomy>
                        <ffc ls="slight">
                            <params stddev="8.27" />
                        </ffc>
                    </ffs>
                </fragilityModel>
            </nrml>"""
        self.parser = setup_parser(content)

        with self.assertRaises(xml.XMLValidationError) as e:
            list(self.parser)

            self.assertTrue("'mean' is required but missing"
                                in e.exception.message)

    def test_parser_with_params_but_no_stddevs(self):
        # A continuous fragility function without a stddev parameter will
        # result in errors.
        content = """
            <?xml version='1.0' encoding='utf-8'?>
            <nrml xmlns:gml="http://www.opengis.net/gml"
                  xmlns="http://openquake.org/xmlns/nrml/0.3"
                  gml:id="n2">
                <fragilityModel gml:id="ep2" format="discrete">
                    <IML IMT="MMI">7 8 9 10 11</IML>
                    <limitStates>slight</limitStates>
                    <ffs gml:id="PAV01-ff02-c" type="lognormal">
                        <taxonomy>RC/DMRF-D/LR</taxonomy>
                        <ffc ls="slight">
                            <params mean="8.27" />
                        </ffc>
                    </ffs>
                </fragilityModel>
            </nrml>"""
        self.parser = setup_parser(content)

        with self.assertRaises(xml.XMLValidationError) as e:
            list(self.parser)

            self.assertTrue("'stddev' is required but missing"
                                in e.exception.message)
