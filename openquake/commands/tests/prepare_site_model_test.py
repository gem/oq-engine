# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""Opt-in projected grids, leaving existing command options unchanged."""
from pathlib import Path

import numpy
import pytest

from openquake.baselib import sap
from openquake.commands import prepare_site_model as command
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.regular_grid import regular_grid
from openquake.hazardlib.correlation_models.circulant_embedding import (
    RegularGridLayout)

OPENQUAKE = Path(__file__).resolve().parents[2]

EXPOSURE = '''<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
  <exposureModel id="grid" category="buildings" taxonomySource="test">
    <description>Two asset locations defining grid bounds</description>
    <conversions><costTypes>
      <costType name="structural" type="aggregated" unit="USD"/>
    </costTypes></conversions>
    <assets>
      <asset id="A" taxonomy="test" number="1">
        <location lon="14.7" lat="41.7"/>
        <costs><cost type="structural" value="1000"/></costs>
      </asset>
      <asset id="B" taxonomy="test" number="1">
        <location lon="15.1" lat="41.9"/>
        <costs><cost type="structural" value="1000"/></costs>
      </asset>
    </assets>
  </exposureModel>
</nrml>
'''


@pytest.mark.parametrize('source', ['sites', 'exposure'])
def test_csv_grid(tmp_path, source):
    sites = tmp_path / 'sites.csv'
    sites.write_text('lon,lat\n14.7,41.7\n15.1,41.9\n')
    exposure = tmp_path / 'exposure.xml'
    exposure.write_text(EXPOSURE)
    vs30 = tmp_path / 'vs30.csv'
    vs30.write_text('14.9,41.8,760\n')
    output = tmp_path / 'site_model.csv'
    options = ({'sites_csv': [str(sites)]} if source == 'sites'
               else {'exposure_xml': [str(exposure)]})
    grid = regular_grid(Mesh(numpy.array([14.7, 15.1]),
                             numpy.array([41.7, 41.9])), 1)
    sitecol = command.main(
        [str(vs30)], z1pt0=True, z2pt5=True, vs30measured=True,
        sentinel_z=True, regular_grid=True, grid_spacing=1,
        output=str(output), **options)
    data = numpy.genfromtxt(output, names=True, delimiter=',')
    # Nearest-Vs30 assignment must retain every cell, including empty ones.
    assert len(sitecol) == len(data) == len(grid.lons)
    numpy.testing.assert_array_equal(data['lon'], grid.lons)
    numpy.testing.assert_array_equal(data['lat'], grid.lats)
    assert (data['vs30'] == 760).all()
    assert (data['z1pt0'] == -999).all()
    assert (data['z2pt5'] == -999).all()
    assert (data['vs30measured'] == 0).all()
    layout = RegularGridLayout.from_sites(Mesh(data['lon'], data['lat']))
    assert numpy.prod(layout.grid_shape) == len(data)
    assert layout.maximum_error < 1


def test_asset_diagnostics(tmp_path):
    exposure = tmp_path / 'exposure.xml'
    exposure.write_text(EXPOSURE)
    diagnostics = {}
    sitecol = command._exposure_sites(
        [str(exposure)], 1, True, {'vs30'}, diagnostics)
    assert len(diagnostics['assetcol']) == 2
    assert len(sitecol) > 2
    assert 'discarded' not in diagnostics


@pytest.mark.parametrize('filename', [
    'qa_tests_data/scenario/case_26/earthquake_rupture_model_GCMT.xml',
    'qa_tests_data/scenario/case_36/rupture.csv',
    'qa_tests_data/scenario/case_31/rupture.csv',
    'commonlib/tests/data/multi-planes-rupture.xml'])
def test_rupture_grid(tmp_path, filename):
    vs30 = tmp_path / 'vs30.csv'
    vs30.write_text('14.88,41.8,760\n')
    output = tmp_path / 'site_model.csv'
    # --rupture selects UTM gridding without also needing --regular-grid.
    sitecol = command.main(
        [str(vs30)], rupture=str(OPENQUAKE / filename),
        grid_spacing=1, maximum_distance=20, output=str(output),
        assoc_distance=20000)
    data = numpy.genfromtxt(output, names=True, delimiter=',')
    # SiteCollection normalizes longitudes; compare at CSV precision.
    numpy.testing.assert_array_equal(data['lon'], numpy.round(sitecol.lons, 5))
    numpy.testing.assert_array_equal(data['lat'], numpy.round(sitecol.lats, 5))
    layout = RegularGridLayout.from_sites(Mesh(data['lon'], data['lat']))
    assert numpy.prod(layout.grid_shape) == len(data)


def test_rupture_count(tmp_path):
    xml_path = (OPENQUAKE / 'qa_tests_data/scenario/case_26/'
                'earthquake_rupture_model_GCMT.xml')
    xml = xml_path.read_text()
    node = xml[xml.index('    <singlePlaneRupture>'):xml.index('</nrml>')]
    path = tmp_path / 'ruptures.xml'
    path.write_text(xml.replace('</nrml>', node + '</nrml>'))
    with pytest.raises(ValueError, match='exactly one rupture'):
        command._rupture_sites(path, 1, 20, 1, {'vs30'})
    csv_path = OPENQUAKE / 'qa_tests_data/scenario/case_36/rupture.csv'
    csv = csv_path.read_text()
    path = tmp_path / 'ruptures.csv'
    path.write_text(csv + csv.splitlines()[-1] + '\n')
    with pytest.raises(ValueError, match='exactly one rupture'):
        command._rupture_sites(path, 1, 20, 1, {'vs30'})
    path.write_text('\n'.join(csv.splitlines()[:2]) + '\n')
    with pytest.raises(ValueError, match='exactly one rupture'):
        command._rupture_sites(path, 1, 20, 1, {'vs30'})


def test_rupture_format():
    with pytest.raises(ValueError, match='XML/NRML'):
        command._rupture_sites('rupture.json', 1, 20, 1, {'vs30'})


@pytest.mark.parametrize('options,message', [
    ({}, 'positive --grid-spacing'),
    ({'grid_spacing': -1}, 'positive --grid-spacing'),
    ({'grid_spacing': numpy.nan}, 'positive --grid-spacing'),
    ({'grid_spacing': 1}, 'exactly one'),
    ({'grid_spacing': 1, 'exposure_xml': ['x.xml'],
      'sites_csv': ['x.csv']}, 'exactly one'),
    ({'rupture': 'x.xml', 'grid_spacing': 1}, 'Maximum distance'),
    ({'rupture': 'x.xml', 'grid_spacing': 1, 'maximum_distance': -1},
     'Maximum distance'),
    ({'rupture': 'x.xml', 'grid_spacing': 1, 'maximum_distance': 20,
      'rupture_mesh_spacing': 0}, 'Rupture mesh spacing'),
    ({'rupture': 'x.xml', 'grid_spacing': 1, 'maximum_distance': 20,
      'sites_csv': ['x.csv']}, 'exactly one'),
    ({'grid_spacing': 1, 'sites_csv': ['x.csv'], 'maximum_distance': 20},
     'require --rupture')])
def test_options(options, message):
    with pytest.raises(ValueError, match=message):
        command.main(['missing-vs30.csv'], regular_grid=True, **options)


def test_cli_options():
    parser = sap.parser(command.main)
    defaults = parser.parse_args(['vs30.csv', '--sites-csv', 'sites.csv'])
    assert not defaults.regular_grid
    options = parser.parse_args([
        'vs30.csv', '--sites-csv', 'sites.csv', '--regular-grid',
        '--grid-spacing', '1', '-123', '-999'])
    assert options.regular_grid and options.grid_spacing == 1
    assert options.z1pt0 and options.z2pt5 and options.vs30measured
    assert options.sentinel_z
    options = parser.parse_args([
        'vs30.csv', '--rupture', 'rupture.xml', '--grid-spacing', '1',
        '--maximum-distance', '90'])
    assert options.rupture == 'rupture.xml'
    assert options.maximum_distance == 90
    assert options.rupture_mesh_spacing == 1
