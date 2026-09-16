# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 Yen-Shin Chen, OGS
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
Legacy model adapter for FDHA calculations.

``LegacyModelAdapter`` bridges the hazard kernel's fixed calling convention
to the heterogeneous model APIs: it inspects each model's signature to pass
only the keyword arguments it accepts, assembles the model inputs from the
the engine rupture/site context, reduces internal
Monte-Carlo / epistemic sample dimensions by the mean, normalizes output
shapes, and applies the near-field distance floor to the models that declare
it. It is scheduled for removal once the models expose a fixed, vectorized
``compute(ctx)`` interface (see docs/EngineIntegration.md, sections 4.2 and
8).
"""

import numpy as np
import inspect
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Near-field displacement floor: the smallest across-strike distance (km) fed to
# a distributed displacement regression that diverges as r -> 0 (Petersen 2011
# eq.18, ln r term). Fixed at half a 25-m Petersen cell (12.5 m). It exists only
# to tame the divergence, so it is a constant -- deliberately NOT the footprint
# z, which is a per-model occurrence-table cell size and can legitimately be
# hundreds of metres. Hard-coded and not exposed in job configuration.
# See docs/design/rupture_location_uncertainty.md (D7).
NEAR_FIELD_FLOOR_KM = 0.0125


def effective_displacement_definition(model):
    """Return a model's declared displacement definition (C4 contract).

    FDHA displacement models declare their Sarmiento et al. (2025, Table 1)
    displacement definition as the ``DISPLACEMENT_DEFINITION`` class
    attribute. The contract is STATIC -- the class choice IS the definition
    (papers publishing several definitions expose one class per definition,
    e.g. ``Lavrentiadis2023PrimaryFD_aggregate`` vs
    ``Lavrentiadis2023PrimaryFD_principal``); no model parameter may change
    it. This helper is the single lookup point used by the hazard kernel
    (single-bucket routing of aggregate models), by the calculator
    configuration guard, and by the logic-tree validators (FDLT-013/014).

    :param model: model instance or class (may be a duck-typed stub).
    :returns: one of ``primary_surf_displ.base.DISPLACEMENT_DEFINITIONS``
        or ``None`` when the model declares no contract (non-FD stubs).
    """
    return getattr(model, 'DISPLACEMENT_DEFINITION', None)


def style_from_rake(rake):
    """Return the faulting style for a rake angle in degrees.

    The thresholds match the oq-pfdha ``classify_style`` helper: the
    engine's :class:`~openquake.hazardlib.contexts.RuptureContext` carries
    ``rake`` where the FDHA context exposes a derived ``style`` array.
    """
    rake = float(rake)
    if -150.0 <= rake <= -30.0:
        return 'normal'
    if 30.0 <= rake <= 150.0:
        return 'reverse'
    return 'strike-slip'


class LegacyModelAdapter:
    """
    Wraps legacy FDHA models for use with FDHAContext.

    Provides backward compatibility during migration to context-based
    calculations. Automatically detects model type and handles parameter
    extraction from context objects.

    Example:
        adapter = LegacyModelAdapter(my_model, {'style': 'normal'})
        P_sr = adapter.compute_primary_sr(ctx, red_cfg)
    """

    def __init__(self, model: Any, model_params: Dict[str, Any] = None):
        """
        Initialize adapter for a model.

        Args:
            model: Model instance with get_prob() method
            model_params: Default parameters for model calls
        """
        self.model = model
        self.model_params = model_params or {}
        self._signature_cache: Dict[tuple, set] = {}

        # Auto-detect model type from class name
        class_name = model.__class__.__name__
        if 'PrimarySR' in class_name or 'PrimarySurfRup' in class_name:
            self.model_type = 'primary_sr'
        elif 'PrimaryFD' in class_name or 'PrimaryDispl' in class_name or 'PrimarySurfDispl' in class_name:
            self.model_type = 'primary_fd'
        elif 'SecondarySR' in class_name or 'SecondarySurfRup' in class_name:
            self.model_type = 'secondary_sr'
        elif 'SecondaryFD' in class_name or 'SecondaryDispl' in class_name or 'SecondarySurfDispl' in class_name:
            self.model_type = 'secondary_fd'
        else:
            self.model_type = 'unknown'
            logger.warning("Could not determine model type for: %s", class_name)

    def _resolve_style(self, ctx: 'Any', ini_section: str) -> str:
        """Resolve the faulting style for a model call.

        Priority: explicit ``style`` model parameter, else derived from the
        rupture rake (``ctx.style``). Models with restricted style support
        (Youngs2003*: only 'all'/'normal') reject anything else with a
        configuration-level message pointing at ``ini_section``.
        """
        style = self.model_params.get('style')
        if style is None:
            # FDHAContext exposes a derived `style` array; the engine's
            # RuptureContext carries `rake` instead (PR-4 wiring).
            style_arr = getattr(ctx, 'style', None)
            if style_arr is None:
                style = style_from_rake(ctx.rake[0])
            else:
                style = style_arr[0]
        model_name = self.model.__class__.__name__
        if 'Youngs2003' in model_name and style not in ('all', 'normal'):
            raise ValueError(
                f"Model {model_name} only supports style='all' or style='normal', "
                f"but got '{style}' (derived from rake={ctx.rake[0]}). "
                f"Please specify style explicitly in job.ini:\n"
                f"  [models.{ini_section}.parameters]\n"
                f"  style = all"
            )
        return style

    def _get_method_params(self, method_name: str) -> set:
        """
        Get valid parameter names for a method (cached).

        Args:
            method_name: Name of the method

        Returns:
            Set of valid parameter names
        """
        cache_key = (id(self.model.__class__), method_name)

        if cache_key not in self._signature_cache:
            method = getattr(self.model, method_name, None)
            if method is None:
                self._signature_cache[cache_key] = set()
            else:
                try:
                    sig = inspect.signature(method)
                    self._signature_cache[cache_key] = set(sig.parameters)
                except (ValueError, TypeError):
                    self._signature_cache[cache_key] = set()

        return self._signature_cache[cache_key]

    def _call_model(self, method_name: str, **kwargs) -> Any:
        """
        Call a model method with only the parameters it accepts.

        Errors propagate: a crashing model must fail the job, not be
        converted into a silently-zero hazard contribution. A model
        returning None is a contract violation and is rejected too.

        Args:
            method_name: Name of method to call
            **kwargs: All possible parameters

        Returns:
            Method result (never None)
        """
        valid_params = self._get_method_params(method_name)
        filtered = {k: v for k, v in kwargs.items() if k in valid_params}

        method = getattr(self.model, method_name)
        try:
            result = method(**filtered)
        except Exception as e:
            raise RuntimeError(
                f"{self.model.__class__.__name__}.{method_name} failed: {e}"
            ) from e
        if result is None:
            raise RuntimeError(
                f"{self.model.__class__.__name__}.{method_name} returned "
                f"None; models must return probabilities")
        return result

    def _ctx_metrics(self, ctx: 'Any'):
        """(r, x_L, L) arrays for this model's declared reference-line method.

        Each FDHA model declares how multi-section (multiFaultSource)
        rupture distances must be measured via its MULTIFAULT_REFERENCE_LINE
        class attribute (ecs | lcp | segments); the context carries one
        metric set per method required by the configured models. For
        single-strand ruptures this is simply the canonical trace-based set.

        Three context shapes are supported, in priority order: an explicit
        per-method ``ref_metrics`` mapping (multi-fault, PR-8), an
        ``FDHAContext``-style ``metrics_for`` method, and finally the
        engine's :class:`~openquake.hazardlib.contexts.RuptureContext`
        distance/rupture-parameter fields added by PR-3 (``rtor``, ``x_l``,
        ``length``). Until multi-fault routing lands (PR-8) every method
        resolves to the single top-trace metric.
        """
        method = getattr(self.model, 'MULTIFAULT_REFERENCE_LINE', 'lcp')
        ref_metrics = getattr(ctx, 'ref_metrics', None)
        if ref_metrics and method in ref_metrics:
            m = ref_metrics[method]
            return m['r'], m['x_L'], m['L']
        metrics_for = getattr(ctx, 'metrics_for', None)
        if metrics_for is not None:
            return metrics_for(method)
        # engine RuptureContext (hazardlib PR-3 fields)
        return ctx.rtor, ctx.x_l, ctx.length

    def compute_primary_sr(
        self,
        ctx: 'Any',
        red_cfg: Dict[str, Any]
    ) -> np.ndarray:
        """
        Compute primary surface rupture probability.

        Primary SR is typically magnitude-dependent only, but some models
        may include epistemic uncertainty (MC samples).

        Args:
            ctx: FDHA context with rupture/site parameters
            red_cfg: MC reduction config {'method': 'median', 'q': 50}

        Returns:
            Array of shape (N,); model errors propagate
        """
        from openquake.pfd.probability import _reduce_mc

        N = len(ctx)

        style = self._resolve_style(ctx, 'primary_surf_rup')

        # Build kwargs; vs30 comes from the site collection (with NaN for
        # sites lacking a value and no reference_vs30_value configured).
        # NaN is converted to None so that models requiring vs30 (e.g.
        # Moss2013PrimarySR) reject the job with their own clear message
        # instead of silently misclassifying the site (NaN fails every
        # comparison, which would have meant "soft soil").
        _vs30_0 = float(ctx.vs30[0])
        kwargs = {
            'mag': float(ctx.mag[0]),
            'dip': float(ctx.dip[0]),
            'dip_mu': float(ctx.dip[0]),
            'seismothickness': self.model_params.get('seismothickness', 15.0),
            'vs30': _vs30_0 if np.isfinite(_vs30_0) else None,
            'style': style,
            **{k: v for k, v in self.model_params.items() if k != 'style'},
        }

        def _reduced_scalar(res):
            res_red = _reduce_mc(
                res,
                method=red_cfg.get('method', 'median'),
                q=red_cfg.get('q', 50)
            )
            return float(np.atleast_1d(res_red).flat[0])

        # vs30-dependent models (e.g. Moss 2013) give a different P_sr per
        # site when the site collection carries heterogeneous vs30 values;
        # evaluate once per unique vs30 instead of broadcasting site 0's.
        unique_vs30 = np.unique(ctx.vs30)
        if unique_vs30.size > 1 and 'vs30' in self._get_method_params('get_prob'):
            out = np.zeros(N, dtype=np.float64)
            for v in unique_vs30:
                v = float(v)
                result = self._call_model('get_prob', **{
                    **kwargs, 'vs30': v if np.isfinite(v) else None})
                mask = np.isnan(ctx.vs30) if np.isnan(v) else ctx.vs30 == v
                out[mask] = _reduced_scalar(result)
            return out

        # Call model
        result = self._call_model('get_prob', **kwargs)

        # Broadcast to all sites
        return np.full(N, _reduced_scalar(result), dtype=np.float64)

    def compute_primary_fd(
        self,
        ctx: 'Any',
        displacements: np.ndarray,
        red_cfg: Dict[str, Any]
    ) -> np.ndarray:
        """
        Compute primary fault displacement probability.

        Uses fully vectorized operations - no per-displacement fallback loops.

        Args:
            ctx: FDHA context
            displacements: Target displacement levels (m)
            red_cfg: MC reduction config

        Returns:
            Array of shape (N, D); model errors propagate
        """
        from openquake.pfd.probability import _to_sites_x_displ

        N = len(ctx)
        D = len(displacements)

        style = self._resolve_style(ctx, 'primary_surf_displ')
        model_name = self.model.__class__.__name__

        # Wrong-class output_type misconfiguration (C4 contract): raise here
        # with a configuration-level message before the model call (same
        # pre-call pattern as the Youngs2003 style check above). The class
        # choice IS the displacement definition - Lavrentiadis2023PrimaryFD_aggregate
        # serves only the aggregate variants; the sum-of-principal
        # disp_prnc_prime metric lives in Lavrentiadis2023PrimaryFD_principal
        # (which in turn accepts no explicit output_type at all). Logic-tree
        # jobs are already rejected at validation time (FDLT-015).
        _output_type = self.model_params.get('output_type')
        if model_name == 'Lavrentiadis2023PrimaryFD_aggregate' \
                and str(_output_type) == 'disp_prnc_prime':
            raise ValueError(
                "Lavrentiadis2023PrimaryFD_aggregate is the AGGREGATE-definition model; "
                "output_type = disp_prnc_prime (sum-of-principal) is served "
                "by the Lavrentiadis2023PrimaryFD_principal model class. "
                "Select that class instead of passing output_type."
            )
        if model_name == 'Lavrentiadis2023PrimaryFD_principal' \
                and _output_type is not None:
            raise ValueError(
                "Lavrentiadis2023PrimaryFD_principal evaluates the "
                "disp_prnc_prime (sum-of-principal) metric; output_type is "
                f"fixed by the class choice (got '{_output_type}'). Remove "
                "the output_type parameter."
            )

        # Build kwargs with vectorized arrays; x_L follows the model's
        # declared multi-fault reference line (e.g. Chiou2025 -> ECS).
        _r_sel, x_L_sel, _L_sel = self._ctx_metrics(ctx)
        kwargs = {
            'mag': float(ctx.mag[0]),
            'd': displacements,
            'X_L_ratio': x_L_sel,
            'x_L': x_L_sel,
            'style': style,
            **{k: v for k, v in self.model_params.items() if k != 'style'},
        }

        # Vectorized call - no fallback loops; errors propagate
        result = self._call_model('get_prob', **kwargs)

        arr = np.asarray(result)

        # Handle different output shapes
        if arr.shape == (N, D):
            return arr.astype(np.float64)
        elif arr.shape == (D, N):
            return arr.T.astype(np.float64)
        elif arr.ndim >= 2:
            return _to_sites_x_displ(arr, N, D, red_cfg)
        elif arr.ndim == 1:
            # 1D array - try to reshape
            if arr.size == N * D:
                return arr.reshape(N, D).astype(np.float64)
            elif arr.size == D:
                # Same probability for all sites - broadcast
                return np.broadcast_to(arr.reshape(1, D), (N, D)).copy().astype(np.float64)
            elif arr.size == N:
                # Per-site scalar - broadcast to all displacements
                return np.broadcast_to(arr.reshape(N, 1), (N, D)).copy().astype(np.float64)

        # Scalar or unknown shape - use _to_sites_x_displ for normalization
        return _to_sites_x_displ(arr, N, D, red_cfg)

    def compute_secondary_sr(
        self,
        ctx: 'Any',
        red_cfg: Dict[str, Any]
    ) -> np.ndarray:
        """
        Compute secondary (distributed) surface rupture probability.

        Uses fully vectorized operations - no per-site fallback loops.

        Args:
            ctx: FDHA context
            red_cfg: MC reduction config

        Returns:
            Array of shape (N,)
        """
        from openquake.pfd.probability import _reduce_mc

        N = len(ctx)

        style = self._resolve_style(ctx, 'secondary_surf_rup')

        # Build kwargs with vectorized arrays; r follows the model's declared
        # multi-fault reference line (e.g. Visini2025 -> nearest segment).
        r_sel, _x_L_sel, _L_sel = self._ctx_metrics(ctx)
        kwargs = {
            'mag': float(ctx.mag[0]),
            'r': r_sel,
            'rx': ctx.rx,
            's': r_sel * 1000.0,
            'style': style,
            **{k: v for k, v in self.model_params.items() if k != 'style'},
        }

        # Ensure version is string if present (Youngs2003SecondarySR expects string)
        if 'version' in kwargs:
            kwargs['version'] = str(kwargs['version'])

        # Vectorized call - no fallback to per-site loops; errors propagate
        result = self._call_model('get_prob', **kwargs)

        arr = np.asarray(result)

        def _red(a):
            return _reduce_mc(a, method=red_cfg.get('method', 'median'),
                              q=red_cfg.get('q', 50))

        def _per_site_or_broadcast(reduced):
            result_arr = np.atleast_1d(reduced)
            if result_arr.size == N:
                return result_arr.astype(np.float64)
            return np.full(N, float(result_arr.flat[0]), dtype=np.float64)

        # Handle different output shapes
        if arr.ndim == 0:
            # Scalar result - broadcast to all sites
            return np.full(N, float(arr), dtype=np.float64)

        if arr.ndim == 1:
            if arr.size == N:
                # Per-site results
                return arr.astype(np.float64)
            elif arr.size == 1:
                # Single value - broadcast
                return np.full(N, float(arr[0]), dtype=np.float64)
            else:
                # Reduce MC samples and broadcast
                return _per_site_or_broadcast(_red(arr))

        if arr.ndim == 2:
            # (N, n_mc) or (n_mc, N) shape - reduce MC dimension
            if arr.shape[0] == N:
                return _per_site_or_broadcast(_red(arr))
            elif arr.shape[1] == N:
                return _per_site_or_broadcast(_red(arr.T))
            else:
                # Unknown shape - reduce and broadcast
                return np.full(N, float(np.atleast_1d(_red(arr)).flat[0]),
                               dtype=np.float64)

        # Higher dimensional - reduce and broadcast
        return np.full(N, float(np.atleast_1d(_red(arr)).flat[0]),
                       dtype=np.float64)

    def compute_secondary_fd(
        self,
        ctx: 'Any',
        displacements: np.ndarray,
        red_cfg: Dict[str, Any],
    ) -> np.ndarray:
        """
        Compute secondary fault displacement probability.

        Args:
            ctx: FDHA context
            displacements: Target displacement levels (m)
            red_cfg: MC reduction config

        The near-field distance floor is the fixed NEAR_FIELD_FLOOR_KM
        constant; the distributed occurrence cell size lives with the
        secondary_surf_rup model's own pixel_size (FD logic tree). Neither
        is a caller-supplied parameter.

        Returns:
            Array of shape (N, D)
        """
        from openquake.pfd.probability import _to_sites_x_displ

        N = len(ctx)
        D = len(displacements)

        style = self._resolve_style(ctx, 'secondary_surf_displ')

        # Build kwargs; r/x_L/L follow the model's declared multi-fault
        # reference line (e.g. Visini2025 -> nearest segment, raw GC2 x/L).
        r_sel, x_L_sel, L_sel = self._ctx_metrics(ctx)

        # Near-field floor (D7). Petersen (2011) eq.18 diverges as r -> 0; a
        # model declaring NEAR_FIELD_FLOOR == 'footprint_half' has the distance
        # fed to its displacement regression clamped to max(r, NEAR_FIELD_FLOOR_KM).
        # The floor is a FIXED 12.5 m (= half a 25-m Petersen cell), deliberately
        # decoupled from the footprint z: z can be a large model-specific cell
        # (e.g. 500 m selects a coarser occurrence table via pixel_size), and a
        # z/2 = 250 m floor would silently erase the near-trace distributed
        # hazard the model exists to produce -- it would push every on-trace
        # site out past the entire distributed zone. 12.5 m only tames ln(r),
        # nothing more. Hard-coded, not user-facing. The clamp lives here, at the
        # adapter boundary, so the model's get_prob stays paper-faithful. Bounded
        # models (Visini, Takao) declare nothing and are untouched.
        # See docs/design/rupture_location_uncertainty.md.
        if getattr(self.model, 'NEAR_FIELD_FLOOR', None) == 'footprint_half':
            r_sel = np.maximum(np.asarray(r_sel, dtype=np.float64),
                               NEAR_FIELD_FLOOR_KM)

        kwargs = {
            'mag': float(ctx.mag[0]),
            'd': displacements,
            'r': r_sel,
            'rx': ctx.rx,
            's': r_sel * 1000.0,
            'X_L_ratio': x_L_sel,
            'x_L': x_L_sel,
            'dip': ctx.dip,
            'L': L_sel,
            'style': style,
            **{k: v for k, v in self.model_params.items() if k != 'style'},
        }

        # Ensure percentile is string if present (Youngs2003SecondaryFD expects string)
        if 'percentile' in kwargs:
            kwargs['percentile'] = str(kwargs['percentile'])

        # Vectorized call; errors propagate
        result = self._call_model('get_prob', **kwargs)
        return _to_sites_x_displ(result, N, D, red_cfg)