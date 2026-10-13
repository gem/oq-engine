"""Run the unchanged ScenarioDamage hazard demo and prepare a handoff."""
import getpass
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'person1_hazard'
DEMO = ROOT / 'demos' / 'risk' / 'ScenarioDamage'
SGT = timezone(timedelta(hours=8))


def sha256(path):
    """Return a file digest without loading the whole datastore into RAM."""
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def check_environment():
    """Require the project environment before running scientific code."""
    expected = Path.home() / 'openquake'
    active = Path(os.environ.get('VIRTUAL_ENV', '.')).resolve()
    if active != expected.resolve():
        raise RuntimeError('Activate ~/openquake before running this script')
    for package in ('ruff', 'pytest-xdist', 'pytest-django'):
        version(package)


def run_calculation(exports, log_file):
    """Measure the full hazard command, including startup and exports."""
    os.environ['OQ_DISTRIBUTE'] = 'no'
    os.environ['PYTHONUTF8'] = '1'
    command = [sys.executable, '-m', 'openquake.commands', 'engine',
               '--run', str(DEMO / 'job_hazard.ini'), '--exports', 'csv,hdf5',
               '--param', 'export_dir=' + str(exports),
               '--log-file', str(log_file), '--no-distribute']
    start = datetime.now(SGT)
    tick = time.perf_counter()
    subprocess.run(command, cwd=ROOT, check=True)
    elapsed = time.perf_counter() - tick
    return command, start.isoformat(), elapsed


def copy_calculation(handoff):
    """Copy the completed full datastore and unchanged demo inputs."""
    from openquake.commonlib import datastore, logs
    job = logs.dbcmd('get_job', -1, getpass.getuser())
    if job.status != 'complete' or job.calculation_mode != 'scenario':
        raise RuntimeError('The latest job is not a completed hazard job')
    source = Path(job.ds_calc_dir + '.hdf5')
    with datastore.read(str(source)) as store:
        actual = Path(store['oqparam'].inputs['job_ini']).resolve()
        if actual != (DEMO / 'job_hazard.ini').resolve():
            raise RuntimeError('The latest calculation used another input')
    target = handoff / source.name
    shutil.copy2(source, target)
    inputs = handoff / 'inputs'
    shutil.copytree(DEMO, inputs)
    hashes = {path.name: sha256(path) for path in inputs.iterdir()
              if path.is_file()}
    for name, digest in hashes.items():
        if digest != sha256(DEMO / name):
            raise RuntimeError('A demo input changed during copying')
    return job.id, source, target, hashes


def copy_gap_notes(handoff, commit):
    """Make source links work both locally and in the standalone ZIP."""
    notes = (WORK / 'INPUTS_AND_GAPS.md').read_text(encoding='utf-8')
    notes = notes.replace('../demos/risk/ScenarioDamage/', 'inputs/')
    github = f'https://github.com/gem/oq-engine/blob/{commit}/'
    for directory in ('openquake', 'doc'):
        notes = notes.replace(f'../{directory}/', github + directory + '/')
    (handoff / 'INPUTS_AND_GAPS.md').write_text(notes, encoding='utf-8')


def calculation_runtime(path):
    """Read the calculator timer, which excludes the startup memory wait."""
    from openquake.commonlib import datastore
    with datastore.read(str(path)) as store:
        records = store['performance_data'][()]
    timers = [float(row['time_sec']) for row in records
              if row['operation'].decode('utf-8').endswith('.run')]
    if len(timers) != 1:
        raise RuntimeError('Expected exactly one calculator runtime record')
    return timers[0]


def write_handoff_notes(handoff, calc_id, metadata):
    """Describe how Person 2 can reuse the same shaking and model weights."""
    text = f"""# Person 1 hazard handoff

Hazard calculation ID on the original installation: **{calc_id}**.
OpenQuake {metadata['openquake_version']}, commit {metadata['git_commit']}.
Hazard command wall time: **{metadata['wall_runtime_seconds']:.3f} s**.
Calculator runtime: **{metadata['calculation_runtime_seconds']:.3f} s**.
Wall time includes CLI startup, any memory wait, calculation and exports;
the calculator timer excludes startup and waiting for available memory.
The demo inputs in `inputs/` are unchanged; compare the SHA256 manifest.

On the original installation, from the repository root:

```powershell
oq engine --run demos/risk/ScenarioDamage/job_risk.ini --hc {calc_id}
```

On another machine with the same engine version/commit, from this folder:

```powershell
$hazard = (Resolve-Path './calc_{calc_id}.hdf5').Path
oq engine --run inputs/job_risk.ini --hc $hazard
```

Use the full `calc_{calc_id}.hdf5` for damage and fragility sensitivity runs.
It preserves the 0.75/0.25 model weights and exact ground-motion values.
The GMF-only HDF5 and CSV exports are for inspection: importing them as
`gmfs_file` loses this demo's two-branch weighting. CSV is also rounded.
Keep the parent hazard unchanged when modifying fragility assumptions.

`plots/` contains the weighted arithmetic mean PGA map in g, site-level
branch means and the event-to-realization mapping. The map is a summary;
damage calculations should reuse the individual GMFs in the full datastore.
`run_metadata.json` records runtime, command, hashes and software versions.
`INPUTS_AND_GAPS.md` describes the inputs and changes needed for Tokyo.
"""
    (handoff / 'README.md').write_text(text, encoding='utf-8')


def main():
    """Create a separate results folder for each run and a sharing ZIP."""
    check_environment()
    stamp = datetime.now(SGT).strftime('%Y%m%d_%H%M%S_SGT')
    run_dir = WORK / 'runs' / stamp
    handoff = run_dir / 'handoff'
    exports = handoff / 'exports'
    exports.mkdir(parents=True, exist_ok=False)
    log_file = handoff / 'hazard_engine.log'
    command, started, elapsed = run_calculation(exports, log_file)
    calc_id, source, target, hashes = copy_calculation(handoff)
    from openquake.baselib import __version__
    commit = subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    metadata = dict(hazard_calculation_id=calc_id, status='complete',
                    started_at_singapore=started,
                    finished_at_singapore=datetime.now(SGT).isoformat(),
                    wall_runtime_seconds=elapsed,
                    calculation_runtime_seconds=calculation_runtime(target),
                    runtime_scope='CLI startup, memory wait, calc, exports',
                    openquake_version=__version__, git_commit=commit,
                    python_version=platform.python_version(),
                    platform=platform.platform(), oq_distribute='no',
                    command=command, source_datastore=str(source),
                    datastore=target.name, datastore_sha256=sha256(target),
                    unchanged_input_sha256=hashes)
    (handoff / 'run_metadata.json').write_text(
        json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    freeze = subprocess.check_output(
        [sys.executable, '-m', 'pip', 'freeze'], text=True)
    (handoff / 'environment_freeze.txt').write_text(freeze, encoding='utf-8')
    shutil.copy2(ROOT / 'requirements-py313-win64.txt', handoff)
    copy_gap_notes(handoff, commit)
    subprocess.run([sys.executable, str(WORK / 'plot_shaking.py'), str(target),
                    '--rupture', str(handoff / 'inputs/fault_rupture.xml'),
                    '--output-dir', str(handoff / 'plots')], check=True)
    write_handoff_notes(handoff, calc_id, metadata)
    archive = shutil.make_archive(str(run_dir / 'person1_handoff'), 'zip',
                                  root_dir=handoff)
    print(f'\nHazard ID: {calc_id}; command wall time: {elapsed:.3f} s')
    print(f'Handoff: {handoff}\nShareable ZIP: {archive}')


if __name__ == '__main__':
    main()
