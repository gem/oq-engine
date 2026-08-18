# Implementing a new correlation model in hazardlib

Ground-motion correlation models describe dependence between residuals at
different sites, between different intensity measure types (IMTs), or both.
They are used when generating ground-motion fields, conditioning fields on
observations, and computing products such as conditional spectra.

Before contributing a model, read the
[development guidelines](development-guidelines.md) and the
[testing guide](testing.md). The scientific terminology used below is
introduced in the
[ground-motion correlation](../underlying-science/correlation-models.rst)
page.

## Establish the scientific specification

Whenever possible, implement the model from its publication rather than
translating an existing software implementation. Check for any published
errata and later corrections. If reference implementations disagree, resolve
the difference from the publication and its calibration domain.

Record the following before writing code:

- the residual component for which the model was calibrated:
  `WITHIN_EVENT`, `BETWEEN_EVENT`, or `TOTAL`
- whether it describes spatial, cross-IMT, or joint spatial-cross-IMT
  correlation
- the supported IMTs, spectral-period range, damping, and intensity measure
  component definition
- the definition and units of separation distance
- regional, magnitude, site or rupture restrictions
- required model parameters and rupture context
- interpolation, extrapolation and boundary rules
- whether the resulting matrices are expected to be positive semidefinite


## Select the model interface

The base interfaces are defined in
`openquake/hazardlib/correlation_models/base.py`.

- Subclass `SpatialCorrelationModel` when the model correlates one IMT across
  sites. Implement `correlation_matrix`.
- Subclass `CrossIMTCorrelationModel` when the model correlates different IMTs
  at one site. Implement `rho`.
- Subclass `SpatialCrossIMTCorrelationModel` when the model directly describes
  a joint field across sites and IMTs. Implement `correlation_block`.

A joint model should implement `correlation_block` rather than only
`covariance`. Conditioning requires rectangular covariance blocks between two
different collections of sites and IMTs. The returned rows and columns must be
in IMT-major order: all sites for the first IMT, followed by all sites for the
second IMT, and so on.

Place the implementation in the matching package:

```text
openquake/hazardlib/correlation_models/
    spatial/
    cross_imt/
    spatial_cross_imt/
```

Use a lowercase file name and a CamelCase class name containing the authors'
names and publication year. For example, `loth_baker_2013.py` contains
`LothBaker2013`. Each model should be implemented in its own dedicated file.

## Declare model metadata

Every model class must declare enough metadata for configuration validation and
scientific review:

```python
name = 'ExampleModel2026'
calibrated_component = ResidualComponent.WITHIN_EVENT
supported_imts = ('SA',)
imc = 'RotD50'
damping = 5.0
required_context = ('mag',)
```

The fields have the following meanings:

- `name` is the canonical configuration name and normally matches the class.
- `calibrated_component` is `WITHIN_EVENT`, `BETWEEN_EVENT`, or `TOTAL`.
- `supported_imts` lists only the IMTs supported by the original publication.
- `imc` identifies the intensity measure component for which the model was
  derived.
- `damping` gives the supported spectral damping, when applicable.
- `required_context` lists predictors obtained from `CorrelationContext`.

Use `None` only when a field genuinely does not apply or the model is not
restricted. The base class validates IMT names and residual components. Do not
represent an unsupported IMT using a proxy SA period unless the publication
defines that mapping. Implement any additional validation required for
spectral periods, damping, component definitions, context values and
constructor parameters.

## Register the model

Decorate the class with `register_model`:

```python
@register_model(
    description='Example within-event joint correlation')
class ExampleModel2026(SpatialCrossIMTCorrelationModel):
    ...
```

The registry discovers model modules lazily. Do not import them from package
`__init__.py` files.

Constructor arguments become the values accepted by the corresponding
`*_correlation_params` job parameter. Constructors should retain only validated
configuration and inexpensive reusable data. If loading or interpolation setup
is expensive, perform it once at construction and make sure the object remains
serializable.

## Implement the numerical model

Correlation methods return dimensionless correlation coefficients.
The GMF calculators then combine the normalized correlated
residuals with the appropriate GSIM-provided `phi` and `tau` values.

Implementations should:

- use kilometres for site separation
- accept NumPy arrays and vectorize over site pairs where practical
- preserve symmetry under exchange of sites and IMTs
- return a unit diagonal when required by the model
- avoid modifying input arrays
- retain coefficient precision supplied by the model authors

Return the correlation defined by the model without silently repairing it.
Generic positive-semidefinite repair, when needed for sampling, belongs in the
common factorization machinery.

## Add independent verification tests

Reference values should be produced independently of the hazardlib
implementation. Use values or tables preferably published by the authors or
author-maintained software, or otherwise generated by an independent
implementation. Store only small immutable verification tables in the
repository, and record their source and version, input grid, and tolerances.

Use both relative and absolute tolerances because valid correlations can be
zero or close to zero. A model test should cover:

- tabulated nodes and interior interpolation points
- period and distance boundaries
- invalid IMTs, periods, damping and parameters
- symmetry and the diagonal
- representative bounds and positive-semidefinite matrices
- IMT-major matrix ordering
- rectangular blocks for direct joint models
- factor reconstruction

Use deterministic matrix tests rather than large Monte Carlo tests. Sampling
statistics are tested by the common factorization tests and need not
be implemented at the individual model level.

Shared interface and registry tests belong in
`openquake/hazardlib/tests/correlation_models_test.py`.

Put new model-specific material under:

```text
openquake/hazardlib/tests/correlation_models/
    <model_name>_test.py
    data/<MODEL_NAME>/
```

Keep each model's numerical tests and reference data in its own test module and
data directory.

During development, run the model test and correlation tests frequently
locally. Then run hazardlib, the relevant calculator tests, `ruff`, and finally
the complete oq-engine test suite before opening the pull request. See the
[testing guide](testing.md) for the standard commands.

## Document and submit the model

The model module must list the complete bibliographic reference and its DOI,
when one exists. Also:

- add its module to the correlation-model API reference
- update the scientific page if the model introduces a new model family,
  residual component or limitation
- update `debian/changelog`
- keep the implementation, reference data and tests in the same pull request

The pull request should explain the calibration domain, reference-data
provenance, maximum discrepancies, and any choices made where publications or
external implementations disagree.
