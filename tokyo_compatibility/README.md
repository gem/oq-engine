# Imported shaking to OpenQuake damage

This workflow prepares externally supplied scenario shaking, building
exposure and discrete fragility curves for `scenario_damage`. It avoids
recomputing shaking when a compatible scenario dataset already exists.
It does not require acceleration waveforms or applied forces.

The implementation targets this checkout's editable OpenQuake 3.27.0
installation. PGA is the control case. Native JMA instrumental intensity
uses a small extension in this fork, limited to damage calculations with
imported ground-motion fields. It does not enable JMA hazard generation,
other risk calculation modes, or an intensity conversion.

Review the input contract and modelling limits below before replacing the
test data with research data.

## JMA compatibility decision

JMA instrumental intensity and its reported classes are distinct inputs.
The converter accepts numerical instrumental values, such as `5.2`, with
`imt = JMA` and `units = instrumental`. Labels such as `5 lower`, `5+`,
`6 weak` and `6 strong` are not numerical instrumental measurements.
Category-only maps require a separate, documented interval or category
method before use. A category must not be replaced silently by a midpoint.
[JMA's calculation and class definitions][jma-calculation] explain this
distinction.

JMA is not PGA or Modified Mercalli Intensity (MMI). JMA's filtered,
three-component acceleration and duration definition prevents direct
recovery of PGA from a JMA value. Renaming a CSV header to PGA or MMI does
not convert the measure. This implementation performs no such conversion.

This initial converter requires nonnegative numerical shaking values.
Instrumental JMA can have negative values at very weak shaking. Such data
needs a documented treatment consistent with the fragility's no-damage
range; do not silently clamp or relabel it to satisfy the file checks.

The engine already defines `JMA` in [hazardlib/imt.py][local-imt], but this
checkout's unmodified risk input whitelist excludes it. The fork permits
it only in
`scenario_damage` with imported GMFs, in
[commonlib/oqvalidation.py][local-validation]. Use this checkout's
environment for the JMA example; stock installations with the same version
number may still reject it. The version number alone does not identify
the extension: retain the Git commit and patch with any handoff.

Passing software validation proves that the data can be calculated. It
does not validate the selected earthquake, exposure or fragility study.

## Prepare the environment

From the repository root in PowerShell:

```powershell
. "$HOME/openquake/Scripts/Activate.ps1"
$env:OQ_DISTRIBUTE = 'no'
oq --version
python -c "import openquake; print(openquake.__path__)"
```

The module path must point at this checkout for the JMA extension. Keep
`ruff`, `pytest-xdist` and `pytest-django` installed as required by the
repository's contributor instructions.

## Input contract

All input CSVs are UTF-8. Coordinates are WGS84 longitude and latitude in
decimal degrees, with longitude first. The first version handles one
intensity measure per prepared job and discrete fragility curves.

### Shaking CSV

Required default columns:

```csv
lon,lat,event_id,value
139.7671,35.6812,0,5.0
139.7006,35.6896,0,6.0
```

An event is one complete spatial scenario field. It is not a time step.
Provide exactly one finite, nonnegative value for every site in every
event. Repeated coordinates within an event and incomplete site coverage
are errors. Event IDs must be nonnegative integers. If the event column
is omitted, all rows form event 0. Keep distinct scenarios in separate
prepared jobs. Output site coordinates are rounded to five decimal
places; source coordinates that collide at that precision are rejected.

Use `--lon-column`, `--lat-column`, `--event-column` and `--value-column`
when the source uses different headers. Source event identifiers are
mapped to OpenQuake's contiguous event IDs; inspect `manifest.json` for
the mapping. The converter does not invent extra events or uncertainty.
A single mean or median map remains a single input field and does not
become an ensemble of sampled shaking fields.

### Shaking metadata JSON

Required keys are `scenario_name`, `source_url`, `source_version`, `imt`,
`units`, `ground_level` and `component`. `exposure_count_type` records
whether the building numbers are integer observations or estimates.

The supported input measures and unit strings are:

| Measure | Accepted units | Written to OpenQuake |
| --- | --- | --- |
| PGA or SA(period) | `g`, `m/s2`, `gal`, `percent_g` | g |
| PGV | `cm/s`, `m/s` | cm/s |
| JMA | `instrumental` | unchanged numerical intensity |

`SA(period)` must contain the numerical period in seconds, for example
`SA(0.3)`. SA requires `damping_percent = 5` in both metadata and fragility
JSON. Document the component separately in the source record. Unit
conversion is applied to both shaking values and fragility intensity
levels, not to probabilities. No intensity-measure conversion is performed.

Ground level and component must match the fragility metadata exactly.
The current converter requires `ground_level = surface`; bedrock inputs
must first undergo a justified site-response treatment. For actual data,
describe that surface reference and the component convention precisely.
Equal strings do not establish scientific equivalence; the research team
must check the underlying definitions.

Keep the source coordinate reference system, spatial resolution, map
statistic, event meaning, uncertainty treatment, licensing and download
date in the accompanying research record. The converter cannot infer them.

### Exposure CSV

Required columns are `id,lon,lat,number,taxonomy`:

```csv
id,lon,lat,number,taxonomy
A1,139.7671,35.6812,10,DEMO_WOOD
```

IDs must be unique. `number` is the positive count of buildings represented
by that row; one row may represent one building or an aggregated group.
Different groups can share coordinates. Taxonomy must match a fragility
function ID exactly. Reclassify source building attributes using a
documented study-specific crosswalk before preparing this CSV.

The prepared job computes expected damage, so fractional expected counts
are valid outputs. If the exposure contains estimated counts, describe
their basis and uncertainty. It does not include casualties, replacement
costs, monetary losses or network connectivity.

Every asset must have a shaking site within `--max-asset-distance-km`
(default 0.1 km). This deliberately small tolerance prevents an accidental
match across distant locations. Choose a different distance only after
reviewing the source resolution and inspect `asset_site_assignments.csv`.
Nearest-site assignment is not interpolation or ground amplification.

### Fragility JSON

The required model fields are `imt`, `units`, `ground_level`, `component`,
`source_url`, `limit_states` and `functions`. See
[jma_fragility.json](examples/jma_fragility.json) for the complete schema.

Each function supplies an `id`, at least two strictly increasing
nonnegative `imls`, a justified `no_damage_limit`, and `poes` arrays for
every limit state.
`limit_states` are ordered from least to most severe. Probabilities must
be between zero and one, increase or remain constant with intensity, and
decrease or remain constant as severity increases. Array lengths must
match the intensity levels. Curves must cover the input values assigned
to assets of that class; do not depend on silent extrapolation.

The `poes` are probabilities of reaching or exceeding each damage state,
not mutually exclusive damage-state probabilities. A building taxonomy
must have the full set of curves. Curve IDs and damage-state meanings
come from the chosen study, not from the Nepal demonstration model.
Input at or below `no_damage_limit` is treated as no damage. Document that
threshold from the study; it must not contradict positive probabilities
at supplied curve points.

This converter writes discrete NRML 0.5 curves. If the published study
uses a normal CDF in JMA intensity, evaluate that published equation on
a documented intensity grid and supply the resulting probabilities.
Do not put its normal-distribution parameters into OpenQuake's continuous
`logncdf` schema; that would change the mathematical model. Check the
discretisation error against the original equation, refine the grid as
needed and preserve the valid range. See [OpenQuake fragility inputs]
[oq-fragility] for discrete and lognormal schema definitions.

## Run the synthetic compatibility examples

The [examples](examples/README.md) are invented software fixtures with
two sites, two fields and three asset groups totalling 60 buildings.
Their curves do not represent Japanese building performance. The JMA and
PGA cases use separate axes with identical test probability tables; this
is not a conversion between them.

The validation runner prepares both cases, executes the calculations and
checks their damage against independently calculated expected totals:

```powershell
python tokyo_compatibility/validate_compatibility.py
```

It writes its generated jobs, calculation results and validation report
under `tokyo_compatibility/runs/`, which is excluded from Git. The report
is `compatibility_report.json`, with `pga/` and `jma/` calculation folders.
An optional `--output-dir` selects a fresh destination.

To recheck completed fixture datastores after a report-check failure, use
`--resume --output-dir <existing run folder>`. This reads the saved result;
a fresh run is the check that executes the current calculator code.

The tiny validation jobs call the OpenQuake calculator directly, save
their HDF5 datastores and register normal calculation IDs and completion
status. The production command below uses the normal engine command,
including its system-memory admission checks.

To prepare only the JMA fixture:

```powershell
python tokyo_compatibility/prepare_inputs.py `
    --shaking-csv tokyo_compatibility/examples/jma_shaking.csv `
    --exposure-csv tokyo_compatibility/examples/exposure.csv `
    --fragility-json tokyo_compatibility/examples/jma_fragility.json `
    --metadata-json tokyo_compatibility/examples/jma_metadata.json `
    --output-dir tokyo_compatibility/runs/manual_jma
oq engine --run tokyo_compatibility/runs/manual_jma/job_damage.ini
```

For PGA, replace `jma_` with `pga_` in the shaking, fragility and metadata
filenames, and choose a fresh output directory. For research data, replace
all four input files with compatible, reviewed datasets.

### Generated inputs and provenance

| File | Purpose |
| --- | --- |
| `sites.csv` | Site IDs and coordinates |
| `gmfs.csv` | Site/event IDs and `gmv_JMA`, `gmv_PGA`, etc. |
| `exposure.csv` | Normalised asset groups |
| `exposure.xml` | NRML wrapper referencing the exposure CSV |
| `fragility.xml` | Discrete structural fragility model in NRML 0.5 |
| `job_damage.ini` | Imported-GMF `scenario_damage` configuration |
| `asset_site_assignments.csv` | Nearest site and distance for every asset |
| `manifest.json` | Input provenance, conversion and identifier mappings |

OpenQuake's imported-GMF configuration and exposure formats are described
in [scenario damage inputs][oq-scenario] and [exposure inputs][oq-exposure].
The generated job uses `gmfs_file` and `sites_csv`, and computes expected
damage with `discrete_damage_distribution = false`.

## Handoff and limits

Give Person 2 the whole prepared folder, research record and validation
report, along with the engine version and exact Git commit. A native JMA
job also needs this fork's extension. Keep a fixed shaking file when
comparing alternative fragility assumptions, and retain its checksum.

The fixture checks file ingestion, unit/measure matching, taxonomy
assignment and expected damage. Actual Tokyo feasibility still depends
on finding compatible scenario data, exposure attributes and published
curves. Bedrock maps need a justified surface treatment where required;
this converter provides no amplification model. Category-only JMA maps,
missing classes, uncertain site matches and study applicability require
explicit research decisions.

For JMA plots, retain the original map's declared statistic. This imported
CSV route stores an arithmetic average and standard deviation across the
supplied fields in `avg_gmf`; their interpretation depends on what the
source fields represent. Averaging damage over fields is also different
from evaluating a fragility curve at the mean shaking value. The report
checks the field-by-field calculation and expected damage counts.

## Verified local result

On 14 October 2026, OpenQuake 3.27.0 with Python 3.13.7 completed the
synthetic PGA and JMA cases as calculations 6 and 7. Both preserved four
site/event values and all three asset groups, representing 60 buildings.
Both matched the hand-calculated mean counts: 37.75 without damage,
12.25 with slight damage only, and 10 with complete damage.

The converter tests passed 38 cases. The risk-validator suite passed 66
tests, with two skips and eight passing subtests. Ruff checks passed.
These are software checks using invented curves, not Tokyo damage results.

The local report is
[compatibility_report.json](runs/20261014_163446_078127_SGT/compatibility_report.json).
Generated files are ignored by Git; share the report separately.

[jma-calculation]: https://www.jma.go.jp/jma/kishou/know/jishin/kyoshin/kaisetsu/calc_sindo.html
[oq-scenario]: https://docs.openquake.org/oq-engine/manual/master/user-guide/configuration-file/scenario-risk-config.html
[oq-exposure]: https://docs.openquake.org/oq-engine/manual/master/user-guide/inputs/exposure-models-inputs.html
[oq-fragility]: https://docs.openquake.org/oq-engine/manual/master/user-guide/inputs/fragility-models-inputs.html
[local-imt]: ../openquake/hazardlib/imt.py
[local-validation]: ../openquake/commonlib/oqvalidation.py
