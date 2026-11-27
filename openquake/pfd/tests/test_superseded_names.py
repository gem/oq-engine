# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen (OGS), GEM Foundation
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
The PFD model classes were renamed after the GSIM convention
(``<Surname><Year>``, ``<Surname1><Surname2><Year>``,
``<FirstSurname>EtAl<Year>``). The former names must keep working, warn,
and stay out of the model listings.
"""
import importlib
import os
import re
import types
import warnings

import numpy
import pytest

from openquake import qa_tests_data
from openquake.baselib.general import DeprecationWarning
from openquake.calculators.displacement import pfd_methods
from openquake.pfd.adapter import PFDModelAdapter
from openquake.pfd.meta import canonical
from openquake.pfd.registry import SLOTS, get_available

# former name -> current name
RENAMED = {
    'WC1993PrimarySR': 'WellsCoppersmith1993PrimarySR',
    'Youngs2003PrimarySR': 'YoungsEtAl2003PrimarySR',
    'Moss2013PrimarySR': 'MossEtAl2013PrimarySR',
    'Takao2013PrimarySR': 'TakaoEtAl2013PrimarySR',
    'Yang2021PrimarySR': 'YangEtAl2021PrimarySR',
    'Pizza2023PrimarySR': 'PizzaEtAl2023PrimarySR',
    'Mammarella2024PrimarySR': 'MammarellaEtAl2024PrimarySR',
    'Youngs2003PrimaryFD': 'YoungsEtAl2003PrimaryFD',
    'Petersen2011PrimaryFD': 'PetersenEtAl2011PrimaryFD',
    'Takao2013PrimaryFD': 'TakaoEtAl2013PrimaryFD',
    'Moss2022PrimaryFD': 'MossEtAl2022PrimaryFD',
    'Moss2024PrimaryFD': 'MossEtAl2024PrimaryFD',
    'Lavrentiadis2023PrimaryFD_aggregate':
        'LavrentiadisAbrahamson2023PrimaryFDAggregate',
    'Lavrentiadis2023PrimaryFD_principal':
        'LavrentiadisAbrahamson2023PrimaryFDSumOfPrincipal',
    'Kuehn2024PrimaryFD': 'KuehnEtAl2024PrimaryFD',
    'Chiou2025PrimaryFD': 'ChiouEtAl2025PrimaryFD',
    'Youngs2003SecondarySR': 'YoungsEtAl2003SecondarySR',
    'Petersen2011SecondarySR': 'PetersenEtAl2011SecondarySR',
    'Petersen2011SecondarySR_default': 'PetersenEtAl2011SecondarySR',
    'Takao2013SecondarySR': 'TakaoEtAl2013SecondarySR',
    'Takao2014SecondarySR': 'TakaoEtAl2014SecondarySR',
    'Rodriguez2023SecondarySR': 'RodriguezPadillaOskin2023SecondarySR',
    'Moss2022SecondarySR': 'MossEtAl2022SecondarySR',
    'Visini2025SecondarySR': 'VisiniEtAl2025SecondarySR',
    'Youngs2003SecondaryFD': 'YoungsEtAl2003SecondaryFD',
    'Petersen2011SecondaryFD': 'PetersenEtAl2011SecondaryFD',
    'Takao2013SecondaryFD': 'TakaoEtAl2013SecondaryFD',
    'Takao2016SecondaryFD': 'TakaoEtAl2016SecondaryFD',
    'Moss2022SecondaryFD': 'MossEtAl2022SecondaryFD',
    'Visini2025SecondaryFD': 'VisiniEtAl2025SecondaryFD',
}


def _slot_of(name):
    for slot in SLOTS:
        if name in get_available(slot):
            return slot
    raise KeyError(name)


def test_listings_hold_only_current_names():
    current = {name for slot in SLOTS
               for name in get_available(slot, superseded=False)}
    assert not current & set(RENAMED)
    assert set(RENAMED.values()) <= current
    # 32 published models plus FixedPrimarySR and FixedSecondarySR
    assert len(current) == 34


@pytest.mark.parametrize('old, new', sorted(RENAMED.items()))
def test_former_name_resolves_to_current_class(old, new):
    slot = _slot_of(old)
    available = get_available(slot)
    assert _slot_of(new) == slot
    assert available[old].superseded_by is available[new]
    assert canonical(available[old]) is available[new]
    assert canonical(available[new]) is available[new]
    assert issubclass(available[old], available[new])


def test_former_name_warns_when_instantiated():
    old = get_available('primary_surf_rup')['Youngs2003PrimarySR']
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        # the warning is cached per class: clear it for this test
        from openquake.pfd.meta import warn_superseded_by
        warn_superseded_by.cache_clear()
        old()
    msgs = [str(w.message) for w in caught
            if issubclass(w.category, DeprecationWarning)]
    assert msgs == ['Youngs2003PrimarySR is deprecated and will be removed '
                    'in a future version - use YoungsEtAl2003PrimarySR '
                    'instead']


def test_current_name_does_not_warn():
    new = get_available('primary_surf_rup')['YoungsEtAl2003PrimarySR']
    with warnings.catch_warnings():
        warnings.simplefilter('error', DeprecationWarning)
        new()


def test_former_name_gives_identical_values():
    surf_rup = get_available('primary_surf_rup')
    mags = numpy.array([5.5, 6.0, 6.5, 7.0])
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        old = surf_rup['WC1993PrimarySR']()
    new = surf_rup['WellsCoppersmith1993PrimarySR']()
    numpy.testing.assert_array_equal(old.get_prob(mags), new.get_prob(mags))


def test_youngs_style_check_applies_to_former_name():
    cls = get_available('primary_surf_rup')['Youngs2003PrimarySR']
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        adapter = PFDModelAdapter(cls(), {})
    ctx = types.SimpleNamespace(rake=numpy.array([90.]))  # reverse
    with pytest.raises(ValueError, match='YoungsEtAl2003PrimarySR only '
                       'supports'):
        adapter._resolve_style(ctx, 'primary_surf_rup')


def test_multifault_reference_line_of_former_name():
    # MULTIFAULT_REFERENCE_LINE is read from the class __dict__, so a
    # deprecated subclass must be resolved to its current class first
    def lt(utype, name):
        branch = types.SimpleNamespace(value=(name, {}))
        bset = types.SimpleNamespace(uncertainty_type=utype,
                                     branches=[branch])
        return types.SimpleNamespace(branchsets=[bset])
    fd = 'fdhaPrimaryFDModel'
    assert pfd_methods(lt(fd, 'ChiouEtAl2025PrimaryFD')) == {'segments', 'ecs'}
    assert pfd_methods(lt(fd, 'Chiou2025PrimaryFD')) == {'segments', 'ecs'}
    # no declaration of its own: only the raw sections
    assert pfd_methods(lt(fd, 'KuehnEtAl2024PrimaryFD')) == {'segments'}
    assert pfd_methods(lt(fd, 'Kuehn2024PrimaryFD')) == {'segments'}


def test_engine_inputs_use_current_names_only():
    # the former names are kept only for the users' existing inputs and will
    # be removed: the QA inputs of the engine must not depend on them
    former = re.compile(r'\b(%s)\b' % '|'.join(map(re.escape, RENAMED)))
    qa_dir = os.path.join(os.path.dirname(qa_tests_data.__file__), 'pfd')
    found = []
    for cwd, _dirs, files in os.walk(qa_dir):
        for fname in files:
            if fname.endswith(('.xml', '.ini', '.toml')):
                path = os.path.join(cwd, fname)
                with open(path, encoding='utf-8') as f:
                    if former.search(f.read()):
                        found.append(os.path.relpath(path, qa_dir))
    assert not found, 'former PFD model names in %s' % found


@pytest.mark.parametrize('slot', sorted(SLOTS))
def test_slot_package_exports_both_names(slot):
    # `from openquake.pfd.<slot> import <name>` must keep working for the
    # former names during the transition, and work for the current ones
    pkg = importlib.import_module('openquake.pfd.' + slot)
    for name, cls in get_available(slot).items():
        assert getattr(pkg, name, None) is cls, name
