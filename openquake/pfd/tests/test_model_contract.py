# -*- coding: utf-8 -*-
"""
C4 model contract: every registered FD displacement model must declare a
valid DISPLACEMENT_DEFINITION / DISPLACEMENT_COMPONENT (Sarmiento et al.
2025, Table 1 taxonomy), and distributed models may declare an
APPLICABILITY_RANGE in their own distance metric.

The exact per-model assignments are frozen here on purpose: changing a
model's definition changes kernel routing (aggregate single-bucket path,
FDLT-013/014 guards), so any change must be a conscious, cited edit of both
the model class and this table.
"""
import inspect

import numpy as np
import pytest

from openquake.pfd import primary_surf_displ, secondary_surf_displ
from openquake.pfd.adapter import effective_displacement_definition
from openquake.pfd.primary_surf_displ.base import (
    BasePrimarySurfDispl,
    BaseSecondarySurfDispl,
    DISPLACEMENT_COMPONENTS,
    DISPLACEMENT_DEFINITIONS,
)



def _registered(package, base):
    out = []
    for name in sorted(vars(package)):
        obj = getattr(package, name)
        if inspect.isclass(obj) and issubclass(obj, base) and obj is not base:
            out.append(obj)
    return out


PRIMARY_FD_CLASSES = _registered(primary_surf_displ, BasePrimarySurfDispl)
SECONDARY_FD_CLASSES = _registered(secondary_surf_displ, BaseSecondarySurfDispl)
ALL_FD_CLASSES = PRIMARY_FD_CLASSES + SECONDARY_FD_CLASSES

# Frozen contract: class name -> (definition, component). Sources are cited
# in each class docstring (Sarmiento et al. 2025 Table 1 / Valentini et al.
# 2025 Table 4 / the model papers themselves).
EXPECTED_CONTRACT = {
    # primary slot
    "Youngs2003PrimaryFD": ("principal", "vertical"),
    "Petersen2011PrimaryFD": ("principal", "lateral"),
    "MossRoss2011PrimaryFD": ("principal", "vertical"),
    "Moss2022PrimaryFD": ("principal", "vertical"),
    "Moss2024PrimaryFD": ("principal", "vertical"),
    "Takao2013PrimaryFD": ("principal", "net"),
    "Lavrentiadis2023PrimaryFD_aggregate": ("aggregate", "net"),
    "Lavrentiadis2023PrimaryFD_principal": ("sum-of-principal", "net"),
    "Kuehn2024PrimaryFD": ("aggregate", "net"),
    "Chiou2025PrimaryFD": ("sum-of-principal", "net"),
    # secondary slot
    "Youngs2003SecondaryFD": ("distributed", "vertical"),
    "Takao2013SecondaryFD": ("distributed", "net"),
    "Petersen2011SecondaryFD": ("distributed", "lateral"),
    "Visini2025SecondaryFD": ("distributed", "vertical"),
    "Moss2022SecondaryFD": ("distributed", "vertical"),
}

_ALLOWED_RANGE_KEYS = {
    "r_min_km", "r_max_km", "r_max_hw_km", "r_max_fw_km", "source",
}


@pytest.mark.parametrize(
    "cls", ALL_FD_CLASSES, ids=lambda c: c.__name__)
def test_every_registered_fd_model_declares_a_valid_contract(cls):
    assert cls.DISPLACEMENT_DEFINITION in DISPLACEMENT_DEFINITIONS, (
        f"{cls.__name__}.DISPLACEMENT_DEFINITION = "
        f"{cls.DISPLACEMENT_DEFINITION!r} is not one of "
        f"{DISPLACEMENT_DEFINITIONS}")
    assert cls.DISPLACEMENT_COMPONENT in DISPLACEMENT_COMPONENTS, (
        f"{cls.__name__}.DISPLACEMENT_COMPONENT = "
        f"{cls.DISPLACEMENT_COMPONENT!r} is not one of "
        f"{DISPLACEMENT_COMPONENTS}")
    # The single lookup point reads the same static attribute.
    assert effective_displacement_definition(cls) == (
        cls.DISPLACEMENT_DEFINITION)


@pytest.mark.parametrize(
    "cls", PRIMARY_FD_CLASSES, ids=lambda c: c.__name__)
def test_primary_slot_models_are_not_distributed_definition(cls):
    assert cls.DISPLACEMENT_DEFINITION != "distributed"


@pytest.mark.parametrize(
    "cls", SECONDARY_FD_CLASSES, ids=lambda c: c.__name__)
def test_secondary_slot_models_are_distributed_definition(cls):
    assert cls.DISPLACEMENT_DEFINITION == "distributed"


@pytest.mark.parametrize(
    "cls", ALL_FD_CLASSES, ids=lambda c: c.__name__)
def test_frozen_per_model_assignments(cls):
    assert cls.__name__ in EXPECTED_CONTRACT, (
        f"New FD model {cls.__name__}: add its (definition, component) to "
        "EXPECTED_CONTRACT with a citation in the class docstring")
    exp_def, exp_comp = EXPECTED_CONTRACT[cls.__name__]
    assert cls.DISPLACEMENT_DEFINITION == exp_def
    assert cls.DISPLACEMENT_COMPONENT == exp_comp


def test_expected_contract_has_no_stale_entries():
    registered = {c.__name__ for c in ALL_FD_CLASSES}
    assert set(EXPECTED_CONTRACT) <= registered


def test_lavrentiadis_two_classes_static_contracts():
    """LA23 publishes two displacement definitions, and the class choice IS
    the definition (Petersen2011PrimaryFD_* variant idiom): the parent class
    serves the aggregate variants, the _principal subclass the
    sum-of-principal disp_prnc_prime metric. Contracts are static - no
    parameter can re-route them."""
    parent = primary_surf_displ.Lavrentiadis2023PrimaryFD_aggregate
    principal = primary_surf_displ.Lavrentiadis2023PrimaryFD_principal
    assert effective_displacement_definition(parent) == "aggregate"
    assert effective_displacement_definition(principal) == "sum-of-principal"
    assert issubclass(principal, parent)


def test_lavrentiadis_parent_rejects_prnc_output_type():
    """The aggregate class refuses to evaluate the sum-of-principal metric;
    the error names the class to use instead."""
    model = primary_surf_displ.Lavrentiadis2023PrimaryFD_aggregate()
    with pytest.raises(ValueError,
                       match="Lavrentiadis2023PrimaryFD_principal"):
        model.get_prob(d=np.array([0.1]), X_L_ratio=np.array([0.5]),
                       mag=7.0, style="normal",
                       output_type="disp_prnc_prime")


@pytest.mark.parametrize("output_type", [
    "disp_prnc_prime", "disp_agg_prime", "disp_agg_seg", "bogus"])
def test_lavrentiadis_principal_rejects_any_explicit_output_type(output_type):
    """output_type is fixed by the class choice - even the redundant
    disp_prnc_prime is rejected to keep configurations canonical."""
    model = primary_surf_displ.Lavrentiadis2023PrimaryFD_principal()
    with pytest.raises(ValueError, match="fixed by the class choice"):
        model.get_prob(d=np.array([0.1]), X_L_ratio=np.array([0.5]),
                       mag=7.0, style="normal", output_type=output_type)


def test_lavrentiadis_principal_numerical_identity():
    """Lavrentiadis2023PrimaryFD_principal.get_prob must reproduce the old
    single-class disp_prnc_prime evaluation EXACTLY (the IAEA L23 chains
    were converted to the new class on this guarantee). Compared against
    the shared implementation the parent evaluates for its own variants."""
    parent = primary_surf_displ.Lavrentiadis2023PrimaryFD_aggregate()
    principal = primary_surf_displ.Lavrentiadis2023PrimaryFD_principal()
    d = np.array([0.01, 0.1, 0.5, 2.0, 10.0])
    for mag in (6.0, 7.0, 7.8):
        for x_l in (np.array([0.05, 0.25, 0.5]), np.array([0.0, 1.0])):
            for style in ("normal", "strike-slip", "reverse"):
                for zero_slip in (False, True):
                    got = principal.get_prob(
                        d=d, X_L_ratio=x_l, mag=mag, style=style,
                        include_zero_slip=zero_slip)
                    expected = parent._evaluate(
                        d, x_l, mag, style=style,
                        output_type="disp_prnc_prime",
                        include_zero_slip=zero_slip)
                    np.testing.assert_array_equal(
                        got, expected,
                        err_msg=(f"mismatch at mag={mag} style={style} "
                                 f"zero_slip={zero_slip}"))
                    # and it must differ from the aggregate variant
                    # (different definition, different numbers)
                    agg = parent.get_prob(
                        d=d, X_L_ratio=x_l, mag=mag, style=style,
                        include_zero_slip=zero_slip)
                    assert not np.array_equal(got, agg)


def test_kuehn_contract_is_static_aggregate():
    cls = primary_surf_displ.Kuehn2024PrimaryFD
    assert effective_displacement_definition(cls) == "aggregate"
    assert cls.DISPLACEMENT_DEFINITION == "aggregate"


@pytest.mark.parametrize(
    "cls", SECONDARY_FD_CLASSES, ids=lambda c: c.__name__)
def test_applicability_range_structure(cls):
    rng = cls.APPLICABILITY_RANGE
    if rng is None:
        return
    assert isinstance(rng, dict)
    assert set(rng) <= _ALLOWED_RANGE_KEYS, (
        f"{cls.__name__}.APPLICABILITY_RANGE has unknown keys "
        f"{set(rng) - _ALLOWED_RANGE_KEYS}")
    assert rng.get("source"), (
        f"{cls.__name__}.APPLICABILITY_RANGE must cite its source")
    for key in set(rng) - {"source"}:
        assert float(rng[key]) > 0.0
    if "r_min_km" in rng:
        outer = [rng[k] for k in
                 ("r_max_km", "r_max_hw_km", "r_max_fw_km") if k in rng]
        assert all(float(rng["r_min_km"]) < float(v) for v in outer)


def test_declared_applicability_values():
    """The task-pinned ranges: Petersen distributed data end at 2 km; Visini
    excludes < 5 m and its dataset envelope is HW 10 km / FW 8 km (in its
    own segments-r metric)."""
    pet = secondary_surf_displ.Petersen2011SecondaryFD.APPLICABILITY_RANGE
    assert pet["r_max_km"] == 2.0

    vis = secondary_surf_displ.Visini2025SecondaryFD.APPLICABILITY_RANGE
    assert vis["r_min_km"] == 0.005
    assert vis["r_max_hw_km"] == 10.0
    assert vis["r_max_fw_km"] == 8.0
    # Range must be declared in the model's own metric.
    assert secondary_surf_displ.Visini2025SecondaryFD.\
        MULTIFAULT_REFERENCE_LINE == "segments"

    assert secondary_surf_displ.Moss2022SecondaryFD.APPLICABILITY_RANGE is None
