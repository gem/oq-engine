# The Hazard Library
# Copyright (C) 2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import numpy
import pytest

from openquake.hazardlib import correlation, cross_correlation
from openquake.hazardlib import correlation_models
from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCrossIMTCorrelationModel)
from openquake.hazardlib.correlation_models.cross_imt.baker_cornell_2006 import (
    BakerCornell2006)
from openquake.hazardlib.correlation_models.cross_imt.baker_jayaram_2008 import (
    BakerJayaram2008)
from openquake.hazardlib.correlation_models.cross_imt.bradley_2012 import (
    Bradley2012)
from openquake.hazardlib.correlation_models.cross_imt.goda_atkinson_2009 import (
    GodaAtkinson2009)
from openquake.hazardlib.correlation_models.registry import (
    get_model, get_model_class, get_model_specs)
from openquake.hazardlib.correlation_models.spatial.heresi_miranda_2019 import (
    HeresiMiranda2019)
from openquake.hazardlib.correlation_models.spatial.jayaram_baker_2009 import (
    JayaramBaker2009)
from openquake.hazardlib.correlation_models.spatial_cross_imt.\
    loth_baker_2013 import LothBaker2013
from openquake.hazardlib.correlation_models.spatial_cross_imt.\
    markhvida_et_al_2018 import MarkhvidaEtAl2018
from openquake.hazardlib.correlation_models.spatial_cross_imt.\
    wang_du_2013 import (
        WangDu2013PGAIAPGV, WangDu2013SpectralAcceleration)
from openquake.hazardlib.imt import PGA, SA


def test_registry_aliases_and_metadata():
    assert get_model_class('HM2018') is HeresiMiranda2019
    assert get_model_class('HM2019') is HeresiMiranda2019
    assert get_model_class('HeresiMiranda2019') is HeresiMiranda2019
    assert get_model_class('JB2009') is JayaramBaker2009
    assert get_model_class('JayaramBaker2009') is JayaramBaker2009
    assert get_model_class('GodaAtkinson2009') is GodaAtkinson2009
    assert get_model_class('Bradley2012') is Bradley2012
    assert get_model_class('BakerCornell2006') is BakerCornell2006
    specs = get_model_specs('spatial')
    assert specs['HeresiMiranda2019'].aliases == (
        'HM2019', 'HM2018', 'HM2018CorrelationModel')
    assert specs['JayaramBaker2009'].aliases == (
        'JB2009', 'JB2009CorrelationModel')
    assert specs['JayaramBaker2009'].calibrated_component == (
        ResidualComponent.WITHIN_EVENT)
    assert specs['JayaramBaker2009'].supported_imts == (
        'PGA', 'PGV', 'SA')
    cross_imt = get_model_specs('cross_imt')
    assert cross_imt['GodaAtkinson2009'].calibrated_component == (
        ResidualComponent.BETWEEN_EVENT)
    assert cross_imt['Bradley2012'].calibrated_component == (
        ResidualComponent.TOTAL)
    joint = get_model_specs('spatial_cross_imt')
    assert joint['LothBaker2013'].cls is LothBaker2013
    assert joint['LothBaker2013'].calibrated_component == (
        ResidualComponent.WITHIN_EVENT)
    assert joint['LothBaker2013'].supported_imts == ('PGA', 'SA')
    assert joint['MarkhvidaEtAl2018'].cls is MarkhvidaEtAl2018
    assert joint['MarkhvidaEtAl2018'].calibrated_component == (
        ResidualComponent.WITHIN_EVENT)
    assert joint['MarkhvidaEtAl2018'].supported_imts == ('PGA', 'SA')
    assert joint['MarkhvidaEtAl2018'].imc == 'RotD50'
    assert joint['WangDu2013PGAIAPGV'].cls is WangDu2013PGAIAPGV
    assert joint['WangDu2013PGAIAPGV'].calibrated_component == (
        ResidualComponent.WITHIN_EVENT)
    assert joint['WangDu2013PGAIAPGV'].supported_imts == (
        'PGA', 'IA', 'PGV')
    assert joint['WangDu2013SpectralAcceleration'].cls is (
        WangDu2013SpectralAcceleration)
    assert joint[
        'WangDu2013SpectralAcceleration'
    ].calibrated_component == ResidualComponent.WITHIN_EVENT
    assert joint['WangDu2013SpectralAcceleration'].supported_imts == ('SA',)


def test_registry_instantiation_and_type_validation():
    model = get_model(
        'JB2009', 'spatial', vs30_clustering=False)
    assert isinstance(model, JayaramBaker2009)
    with pytest.raises(TypeError, match='not spatial'):
        get_model_class('BakerJayaram2008', model_type='spatial')
    with pytest.raises(KeyError, match='Unknown correlation model'):
        get_model_class('MissingModel')


def test_package_does_not_reexport_models():
    assert not hasattr(correlation_models, 'JayaramBaker2009')
    assert not hasattr(correlation_models, 'get_model')


def test_residual_component_validation():
    model = BakerJayaram2008()
    assert model.rho(
        SA(0.1), SA(0.5), ResidualComponent.TOTAL
    ) == pytest.approx(0.4745240873)
    with pytest.raises(ValueError, match='provides total correlation'):
        model.rho(SA(0.1), SA(0.5),
                  ResidualComponent.WITHIN_EVENT)


def test_cross_im_covariance_uses_imt_major_ordering():
    model = BakerJayaram2008()
    imts = [PGA(), SA(0.5)]
    sites = range(2)
    correlation_value = model.rho(*imts)
    expected = numpy.array([
        [1, 0, correlation_value, 0],
        [0, 1, 0, correlation_value],
        [correlation_value, 0, 1, 0],
        [0, correlation_value, 0, 1],
    ])
    numpy.testing.assert_allclose(
        model.covariance(sites, imts), expected)


def test_default_factor_repairs_indefinite_covariance():
    class IndefiniteModel(SpatialCrossIMTCorrelationModel):
        def covariance(self, sites, imts, component=None, context=None):
            return numpy.array([[1.0, 1.01], [1.01, 1.0]])

    model = IndefiniteModel()
    with pytest.raises(numpy.linalg.LinAlgError):
        model.factor(None, None, ensure_psd=False)
    factor = model.factor(None, None)
    repaired = factor.lower_triangle @ factor.lower_triangle.T
    assert numpy.linalg.eigvalsh(repaired).min() > 0


def test_legacy_modules_export_canonical_classes():
    assert correlation.JB2009CorrelationModel is JayaramBaker2009
    assert correlation.HM2018CorrelationModel is HeresiMiranda2019
    assert cross_correlation.BakerJayaram2008 is BakerJayaram2008
    assert cross_correlation.GodaAtkinson2009 is GodaAtkinson2009
    assert issubclass(
        cross_correlation.NoCrossCorrelation,
        cross_correlation.CrossCorrelationBetween)
