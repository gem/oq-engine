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
"""Registry for ground-motion correlation models."""

from dataclasses import dataclass

from openquake.baselib.general import import_all
from openquake.hazardlib.correlation_models.base import (
    CorrelationModel, CrossIMTCorrelationModel, SpatialCorrelationModel,
    SpatialCrossIMTCorrelationModel)


@dataclass(frozen=True)
class ModelSpec:
    """Registration metadata for a correlation model."""

    name: str
    cls: type[CorrelationModel]
    aliases: tuple[str, ...]
    model_type: str
    description: str

    @property
    def residual_component(self):
        return self.cls.DEFINED_FOR_RESIDUAL_COMPONENT

    @property
    def supported_imts(self):
        return self.cls.DEFINED_FOR_INTENSITY_MEASURE_TYPES

    @property
    def calibrated_imts(self):
        return self.cls._calibrated_imts()

    @property
    def intensity_measure_type_approximations(self):
        return dict(self.cls.INTENSITY_MEASURE_TYPE_APPROXIMATIONS)

    @property
    def imc(self):
        return self.cls.DEFINED_FOR_INTENSITY_MEASURE_COMPONENT

    @property
    def sa_damping(self):
        return self.cls.DEFINED_FOR_SA_DAMPING

    @property
    def sa_period_range(self):
        return self.cls.DEFINED_FOR_SA_PERIOD_RANGE

    @property
    def region(self):
        return self.cls.DEFINED_FOR_REGION

    @property
    def required_context(self):
        return self.cls.required_context


registry = {}
_specs = {}
_models_loaded = False


def _load_models():
    """Import model modules the first time the registry is queried."""
    global _models_loaded
    if _models_loaded:
        return
    root = 'openquake.hazardlib.correlation_models'
    for model_type in ('spatial', 'cross_imt', 'spatial_cross_imt'):
        import_all(f'{root}.{model_type}')
    _models_loaded = True


def _model_type(cls):
    if issubclass(cls, SpatialCorrelationModel):
        return 'spatial'
    if issubclass(cls, CrossIMTCorrelationModel):
        return 'cross_imt'
    if issubclass(cls, SpatialCrossIMTCorrelationModel):
        return 'spatial_cross_imt'
    raise TypeError(f'{cls.__name__} is not a correlation model')


def register_model(*aliases, description=''):
    """Register a model class under its canonical name and aliases."""
    def decorator(cls):
        if not issubclass(cls, CorrelationModel):
            raise TypeError(f'{cls.__name__} is not a correlation model')
        name = cls.__name__
        keys = (name,) + tuple(aliases)
        duplicates = sorted(key for key in keys if key in registry)
        if duplicates:
            raise KeyError(
                f'Correlation model names already registered: {duplicates}')
        spec = ModelSpec(
            name, cls, tuple(aliases), _model_type(cls), description)
        _specs[name] = spec
        for key in keys:
            registry[key] = cls
        return cls
    return decorator


def get_model_class(name, model_type=None):
    """Return the class registered under ``name``."""
    _load_models()
    try:
        cls = registry[name]
    except KeyError as exc:
        available = ', '.join(sorted(registry))
        raise KeyError(
            f'Unknown correlation model {name!r}; available: {available}'
        ) from exc
    if model_type is not None and _model_type(cls) != model_type:
        raise TypeError(
            f'{name} is {_model_type(cls)}, not {model_type}')
    return cls


def get_model(name, model_type=None, **parameters):
    """Instantiate and validate the model registered under ``name``."""
    model = get_model_class(name, model_type)(**parameters)
    model.validate()
    return model


def get_model_specs(model_type=None):
    """Return canonical model specifications, optionally by model type."""
    _load_models()
    if model_type is None:
        return dict(_specs)
    return {name: spec for name, spec in _specs.items()
            if spec.model_type == model_type}
