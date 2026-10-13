# Person 1: scenario hazard feasibility check

Use the supplied `demos/risk/ScenarioDamage` Nepal demonstration unchanged.
The Python scripts here run its hazard job, export shaking, make a PGA map
and package the inputs and full calculation for Person 2. Scientific
parameters in the original demo are unchanged; only execution and export
options are supplied by the runner.

## Completed initial calculation

- Hazard calculation ID: **1**; OpenQuake **3.27.0** development checkout,
  commit `8330aea312e7d7fe7ba1c87b1375ba4770fd64a4`; Python **3.13.7**.
- Calculator runtime: **2.688 s** including exports. Hazard command wall
  time: **206.883 s**, including startup and waiting for free RAM.
- Retained sites/assets: **1,406 / 5,662**. Sampled fields: **200**,
  100 per ground-motion model; **281,200** site/event PGA values.
- Mean PGA map: **0.014-0.656 g**, combining branch means at 0.75/0.25.
- The engine moved the inconsistent supplied hypocentre from depth 30 km
  to its rupture-surface midpoint at depth 35 km; see the input/gap notes.

[Open the handoff ZIP](runs/20261014_015206_SGT/person1_handoff.zip),
[PGA map](runs/20261014_015206_SGT/handoff/plots/shaking_pga.png) or
[runtime manifest](runs/20261014_015206_SGT/handoff/run_metadata.json).

Handoff validation passed: damage calculations **2** (hazard ID 1) and
**3** (copied full datastore) reused identical shaking, weights and asset
assignments and produced identical damage arrays. The original hazard
and its copy remained unchanged. The bundle includes
[`validation_report.json`](runs/20261014_015206_SGT/handoff/validation_report.json).
Use the explicit hazard ID 1; the latest calculation is now a damage job.

Person 2 can use this same installation from the repository root:

```powershell
. "$env:USERPROFILE/openquake/Scripts/Activate.ps1"
$env:OQ_DISTRIBUTE = 'no'
oq engine --run demos/risk/ScenarioDamage/job_risk.ini --hc 1
```

## Run on this Windows installation

From the repository root in PowerShell:

```powershell
. "$env:USERPROFILE/openquake/Scripts/Activate.ps1"
$env:OQ_DISTRIBUTE = 'no'
python person1_hazard/run_hazard.py
```

Each execution creates a new `runs/<Singapore timestamp>/` folder with a
`handoff/` directory and `person1_handoff.zip`. Command wall time includes
startup, any memory wait, calculation and exports; installation and
plotting are excluded. The separate calculator timer excludes startup
and memory waiting. OpenQuake waits to start until RAM usage is below 80%.

Outputs include:

- `run_metadata.json`: actual hazard ID, runtime, version, Git commit,
  command and input/datastore SHA256 hashes.
- `calc_<id>.hdf5`: full hazard datastore, including the logic tree.
- `inputs/`: unchanged exposure, rupture, fragility and job files.
- `exports/`: native OpenQuake CSV and GMF-only HDF5 exports.
- `plots/shaking_pga.png` and `.pdf`: weighted arithmetic mean PGA map.
- `plots/site_pga_means.csv`: coordinates, branch means and weighted means.
- `plots/event_realizations.csv`: event IDs and logic-tree realizations.
- `plots/plot_summary.json`: counts, weights, checks and PGA ranges.
- `environment_freeze.txt`: installed package versions.

The map averages all sampled PGA values within each model branch, then
combines the branch means using stored weights. It shows shaking at the
supplied exposure sites; it is not an interpolated continuous hazard map.
The full individual GMFs are needed for damage, rather than the mean map.

## Person 2 handoff

On the same installation, use the explicit hazard ID printed by the run:

```powershell
oq engine --run demos/risk/ScenarioDamage/job_risk.ini --hc <hazard_id>
```

The generated handoff README contains this command with the actual ID.
It also gives a full-datastore path command for a separate machine using
the same engine version and commit. Share the generated ZIP as a bundle.

Keep the hazard parent fixed while Person 2 changes fragility curves.
Reimporting GMF-only HDF5 or CSV as `gmfs_file` replaces this example's
two-branch logic tree with a single realization, losing its 0.75/0.25
weights. CSV is also rounded. Reuse the **full** datastore for consistency.

## Environment setup on a fresh Windows machine

The checkout recommends Python 3.13 and supplies matching Windows wheels.
Create the environment once, then activate it for every Python command:

```powershell
py -3.13 -m venv "$env:USERPROFILE/openquake"
. "$env:USERPROFILE/openquake/Scripts/Activate.ps1"
python -m pip install --upgrade pip ruff pytest-xdist pytest-django
python -m pip install -r requirements-py313-win64.txt
python -m pip install --no-deps -e .
python -m pip check
```

See [OpenQuake installation documentation][installation] and
[the local development guide](../doc/contributing/developing-with-the-engine.rst).

## Inputs and gaps

Read [INPUTS_AND_GAPS.md](INPUTS_AND_GAPS.md) for the rupture geometry,
GMPE and site assumptions, the Tokyo data changes and the missing
waveform step between OpenQuake and OpenSees.

[installation]: https://docs.openquake.org/oq-engine/master/manual/getting-started/installation-instructions/development.html
