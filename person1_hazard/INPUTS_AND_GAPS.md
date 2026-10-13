# Scenario inputs and modelling gaps

This is the supplied Nepal `demos/risk/ScenarioDamage` demonstration.
It establishes that the hazard-to-damage workflow runs with supplied
inputs. It does not establish a calibrated Tokyo hazard or damage model.

## Earthquake and shaking inputs

| Input | Supplied value | Meaning |
| --- | --- | --- |
| Calculation | `scenario` | Shaking conditional on one earthquake rupture |
| Magnitude | 7.0 | Rupture magnitude; GMPE calculations use Mw |
| Rake | 90 degrees | Reverse faulting |
| Hypocentre | 84.4 E, 27.6 N, depth 30 km | Rupture initiation location |
| Fault trace | 85.0 E, 27.3 N to 83.8 E, 27.8 N | Surface trace endpoints |
| Dip | 30 degrees | Inclination of the fault surface |
| Fault depths | Upper 20 km; lower 50 km | Vertical extent of rupture |
| Rupture mesh spacing | 15 km | Discretisation of rupture geometry |
| GMPE branch 1 | `BooreAtkinson2008`, weight 0.75 | Ground-motion model |
| GMPE branch 2 | `ChiouYoungs2008`, weight 0.25 | Alternative model |
| Tectonic label | `Active Shallow Crust` | Supplied GMPE branch setting |
| Sites | Locations from `exposure_model.xml`/CSV | Nepal asset locations |
| Vs30 | 760 m/s at every site | Mean shear-wave speed in upper 30 m |
| Vs30 type | `measured` flag | Configuration flag, not survey evidence |
| z1.0 | 100 m at every site | Depth to the 1.0 km/s velocity layer |
| z2.5 | 5 km at every site | Depth to the 2.5 km/s velocity layer |
| Intensity measure | `PGA` | Peak ground acceleration, expressed in g |
| Maximum distance | 200 km | Site distance cutoff used by calculation |
| Residual truncation | 3.0 | Limit for sampled ground-motion residuals |
| Spatial correlation | None specified | No chosen spatial correlation model |
| Seed | `ses_seed = 42` | Reproducibility setting in supplied job |
| GMF samples | 100 per GMPE; 200 total | Verified in initial run, ID 1 |

The completed initial run retained **1,406 sites and 5,662 assets** after
the distance filter, from 2,253 supplied locations and 9,063 assets.
It generated 281,200 site/event PGA values, with no missing shaking sites.
The weighted arithmetic mean PGA ranges from approximately 0.014 to
0.656 g across those sites; individual samples cover a wider range.

**Observed geometry adjustment:** the engine found the supplied
hypocentre outside the rupture surface. It automatically moved it to
84.64713 E, 28.051522 N, depth **35 km**, the surface midpoint.
The input XML remains unchanged at 84.4 E, 27.6 N, depth 30 km.
The map and summary distinguish supplied and effective hypocentres.
See `hazard_engine.log` and `plots/plot_summary.json` in the handoff.
Resolve this geometry inconsistency when choosing a Tokyo source model.

The site values are uniform demonstration assumptions. Although the
configuration labels Vs30 as `measured`, no measured field dataset is
supplied to establish those values for every site. Keep this distinction
when explaining the example or planning a Tokyo site model.

Values come from [the hazard job][hazard], [rupture XML][rupture] and
[GMPE logic tree][gsims]. Site parameter units are defined in
[`Site`][site-code]; PGA units are defined in [`PGA`][imt-code]. The
[local consequence-model documentation][gmf-count] describes two sets
of 100 ground-motion fields for this demo, one for each GMPE.

Each GMF contains intensity values at sites for one sampled realization.
For a combined mean PGA map, calculate the mean within each GMPE branch
and combine those means with weights 0.75 and 0.25. State the aggregation
used in the figure; a mean map is a summary of sampled shaking.

## Inputs needed for a Tokyo scenario

- Choose a named earthquake scenario and document the magnitude scale,
  source type and source authority. Replace the Nepal magnitude,
  hypocentre, fault trace, dip, rake and fault depths using the chosen
  source model. Tokyo's official assessment contains a chapter covering
  scenario selection and source models. [Tokyo assessment][tokyo]
- Replace Nepal asset/site coordinates with Tokyo locations. Person 2
  must also replace the Nepal boundary in [the risk job][risk] and supply
  exposure classes matched to appropriate fragility curves.
- Review the GMPE for the selected crustal, subduction-interface or
  intraslab source and for its magnitude, distance and site conditions.
  Review logic-tree weights rather than transferring the demo weights.
  NIED's Morikawa-Fujiwara guide distinguishes these source types and
  includes shallow-soil and deep-sediment corrections. [NIED guide][mf]
- Supply spatially varying site properties required by that GMPE.
  J-SHIS AVS30 is estimated from geomorphology; its amplification layer
  is relative to engineering bedrock. Document the data's resolution,
  units and inferred/measured status. [J-SHIS user guide][jshis]
- As one candidate to investigate, the local MorikawaFujiwara2013 family
  has crustal, interface and slab variants. It requires `vs30`, `z1pt4`,
  longitude and latitude; `z1pt4` is depth in metres. Its applicability
  and variant must be checked before adoption. [Local implementation][mf-code]
- Agree intensity measures with Person 2 and Person 3: PGA for the supplied
  PGA fragility curves, and suitable SA periods if needed for structures.
  Label the current map PGA (g). JMA instrumental intensity uses filtered
  three-component motion and a duration criterion. [JMA method][jma]
- Review rupture mesh spacing, distance cutoff, sampling count and spatial
  correlation for the chosen source and study region. Compare results
  with a compatible scenario product. J-SHIS distinguishes scenario
  shaking maps from probabilistic hazard maps. [Map definitions][maps]

No Tokyo source, site dataset or GMPE is selected by this feasibility run.

## Missing waveform step for Person 3

OpenQuake scenario GMFs supply sampled intensity values, as documented in
the [scenario workflow][oq]. They do not contain acceleration against
time. Event IDs identify realizations; they are not waveform time steps.
PGA alone cannot determine frequency content, phase or shaking duration.

An additional record-selection or simulation step must produce a waveform
compatible with the scenario, site and target spectrum. Review relevant
spectral periods, source properties, duration and scaling with Person 3.
Conditional-spectrum selection, spectrum matching and directivity are
established considerations. [NIST record-selection guidance][nist]

Japanese accelerograms are available from [K-NET/KiK-net][knet], with
registration required for downloads. Preserve component direction and
sample interval, convert counts using the record's scale factor, and
distinguish surface from borehole recordings. NIED specifies that
`dt = 1 / sampling_frequency` and 1 gal = 1 cm/s squared. [NIED FAQ][faq]

Pass the resulting acceleration history, units and `dt` into OpenSees
`Path`/`UniformExcitation`. That load pattern reports node responses
relative to ground motion. [OpenSees documentation][opensees]
The 0.5x/1.0x/1.5x runs test amplitude sensitivity; waveform suitability
still requires checking against the selected earthquake and structure.

[hazard]: ../demos/risk/ScenarioDamage/job_hazard.ini
[rupture]: ../demos/risk/ScenarioDamage/fault_rupture.xml
[gsims]: ../demos/risk/ScenarioDamage/gsim_logic_tree.xml
[risk]: ../demos/risk/ScenarioDamage/job_risk.ini
[site-code]: ../openquake/hazardlib/site.py
[imt-code]: ../openquake/hazardlib/imt.py
[gmf-count]: ../doc/user-guide/inputs/consequence-models-inputs.rst
[mf-code]: ../openquake/hazardlib/gsim/morikawa_fujiwara_2013.py
[tokyo]: https://www.bousai.metro.tokyo.lg.jp/taisaku/torikumi/1000902/1021571.html
[mf]: https://www.j-shis.bosai.go.jp/en/labs/mf2013/
[jshis]: https://www.j-shis.bosai.go.jp/map/JSHIS2/man/en/man_top.html
[jma]: https://www.jma.go.jp/jma/kishou/know/jishin/kyoshin/kaisetsu/calc_sindo.html
[maps]: https://www.j-shis.bosai.go.jp/en/shm
[oq]: https://docs.openquake.org/oq-engine/3.25/manual/user-guide/workflows/scenario-hazard.html
[nist]: https://www.nist.gov/publications/selecting-and-scaling-earthquake-ground-motions-performing-response-history-analyses
[knet]: https://www.kyoshin.bosai.go.jp/en/
[faq]: https://www.kyoshin.bosai.go.jp/en/faq/
[opensees]: https://opensees.github.io/OpenSeesDocumentation/user/manual/model/pattern/uniformExcitationPattern.html
