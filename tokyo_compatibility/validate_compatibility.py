"""Run tiny synthetic PGA and native-JMA scenario-damage checks."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy


ROOT = Path(__file__).resolve().parent
SGT = ZoneInfo('Asia/Singapore')
STATES = ['no_damage', 'slight', 'complete']
EXPECTED_EVENTS = numpy.array([[43, 11, 6], [32.5, 13.5, 14]])
EXPECTED_ASSETS = {'A1': [8, 1.5, 0.5], 'A2': [17.75, 1.75, 0.5],
                   'A3': [12, 9, 9]}


def _sha256(path):
    # Hash the exact bytes supplied to the calculator.
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(value):
    # HDF5 identifiers can be stored as bytes.
    return value.decode() if isinstance(value, bytes) else str(value)


def _provenance():
    # Identify an uncommitted fork extension by source hashes as well as HEAD.
    repository = ROOT.parent
    result = {}
    for name, argument in (('git_head', 'HEAD'),
                            ('branch', '--abbrev-ref HEAD')):
        command = ['git', 'rev-parse'] + argument.split()
        process = subprocess.run(command, cwd=repository, capture_output=True,
                                 text=True, check=True)
        result[name] = process.stdout.strip()
    paths = [repository / 'openquake/commonlib/oqvalidation.py',
             repository / 'openquake/hazardlib/imt.py',
             ROOT / 'prepare_inputs.py', Path(__file__).resolve()]
    result['source_sha256'] = {
        str(path.relative_to(repository)): _sha256(path) for path in paths}
    result['python_environment'] = sys.prefix
    return result


def _prepare(case, output):
    # Use the public converter CLI, as the research team will do.
    examples = ROOT / 'examples'
    command = [sys.executable, str(ROOT / 'prepare_inputs.py'),
               '--shaking-csv', str(examples / f'{case}_shaking.csv'),
               '--exposure-csv', str(examples / 'exposure.csv'),
               '--fragility-json', str(examples / f'{case}_fragility.json'),
               '--metadata-json', str(examples / f'{case}_metadata.json'),
               '--output-dir', str(output)]
    result = subprocess.run(command, capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return command


def _reuse_calculation(folder):
    # Resume a completed fixture by its own log, never by the latest job ID.
    from openquake.commonlib import logs
    saved = folder / 'calculation.json'
    if saved.exists():
        return json.loads(saved.read_text(encoding='utf-8'))
    contents = (folder / 'engine.log').read_text(encoding='utf-8')
    ids = set(re.findall(r'#(\d+)\s', contents))
    if len(ids) != 1:
        raise ValueError('Cannot identify exactly one completed calculation')
    calc_id = int(ids.pop())
    job = logs.dbcmd('get_job', calc_id)
    if job.status != 'complete' or job.calculation_mode != 'scenario_damage':
        raise ValueError('Only a completed damage fixture can be resumed')
    return dict(calculation_id=calc_id, datastore=job.ds_calc_dir + '.hdf5',
                status=job.status, wall_seconds=None,
                execution='Recovered completed direct-calculator fixture')


def _calculate(folder):
    # Run only the tiny fixture through the same engine calculator as tests.
    # Production jobs should use oq engine, including its RAM admission check.
    from openquake.calculators import base
    from openquake.commonlib import logs
    tick = time.perf_counter()
    log_file = folder / 'engine.log'
    with logs.init(str(folder / 'job_damage.ini'),
                   log_file=str(log_file)) as log:
        calc = base.calculators(log.get_oqparam(), log.calc_id)
        calc.run(concurrent_tasks=0, exports='csv')
        datastore = calc.datastore.filename
        calc.datastore.close()
    job = logs.dbcmd('get_job', log.calc_id)
    if job.status != 'complete':
        raise RuntimeError(f'Calculation {log.calc_id}: {job.status}')
    return dict(calculation_id=log.calc_id, datastore=datastore,
                status=job.status, wall_seconds=time.perf_counter() - tick,
                execution='Direct calculator, tiny synthetic fixture only')


def _check_shaking(store, folder, imt):
    # Compare every imported site/event value, including the native IMT name.
    with (folder / 'gmfs.csv').open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    expected = {(int(row['site_id']), int(row['event_id'])):
                float(row[f'gmv_{imt}']) for row in rows}
    group = store['gmf_data']
    if imt not in group:
        raise ValueError(f'Native {imt} column was not retained')
    actual = {(int(sid), int(eid)): float(value) for sid, eid, value in zip(
        group['sid'][()], group['eid'][()], group[imt][()])}
    if actual.keys() != expected.keys():
        raise ValueError('Imported site/event coverage changed')
    for key in expected:
        numpy.testing.assert_allclose(actual[key], expected[key],
                                      rtol=1e-6, atol=1e-7)
    average = store['avg_gmf'][()]
    for sid in sorted({key[0] for key in expected}):
        values = [value for key, value in expected.items() if key[0] == sid]
        numpy.testing.assert_allclose(
            average[:, sid, 0], [numpy.mean(values), numpy.std(values)],
            rtol=2e-6, atol=1e-7)
    numpy.testing.assert_array_equal(store['weights'][()], [1.0])
    if imt == 'JMA' and ('PGA' in group or 'MMI' in group):
        raise ValueError('JMA was mislabelled as PGA or MMI')
    return dict(imt=imt, row_count=len(actual), unchanged=True,
                arithmetic_intensity_statistics_passed=True,
                realization_weights=[1.0])


def _check_assets(store, folder):
    # Require all three original assets and their intended shaking locations.
    with (folder / 'exposure.csv').open(newline='',
                                       encoding='utf-8') as stream:
        source = {row['id']: row for row in csv.DictReader(stream)}
    assets = store['assetcol']
    ids = [_text(value) for value in assets['id']]
    if set(ids) != set(source) or len(ids) != len(source):
        raise ValueError('An asset was excluded, duplicated, or renamed')
    sites = store['sitecol'].complete.array
    for aid, sid, number in zip(ids, assets['site_id'],
                                assets['value-number']):
        row = source[aid]
        numpy.testing.assert_allclose(number, float(row['number']))
        numpy.testing.assert_allclose(
            [sites['lon'][sid], sites['lat'][sid]],
            [float(row['lon']), float(row['lat'])], rtol=0, atol=1e-5)
    return ids


def _check_damage(store, ids):
    # Compare against hand-calculated counts, independently of the converter.
    damages = store['damages-rlzs'][()]
    expected = numpy.array([EXPECTED_ASSETS[aid] for aid in ids])
    actual = numpy.column_stack([
        damages[f'structural-{state}'][:, 0] for state in STATES])
    numpy.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-6)
    if 'damages-stats' in store:
        stats = store['damages-stats'][()]
        for index, state in enumerate(STATES):
            numpy.testing.assert_allclose(
                stats[f'structural-{state}'][:, 0], expected[:, index],
                rtol=1e-6, atol=1e-6)
    numbers = store['assetcol']['value-number']
    numpy.testing.assert_allclose(actual.sum(axis=1), numbers,
                                  rtol=1e-6, atol=1e-6)
    by_event = store.read_df('risk_by_event')
    portfolio_id = len(store['agg_keys']) if 'agg_keys' in store else 0
    portfolio = by_event[by_event.agg_id == portfolio_id].sort_values(
        'event_id')
    damaged = portfolio[['dmg_1', 'dmg_2']].to_numpy()
    event_values = numpy.column_stack([60 - damaged.sum(axis=1), damaged])
    numpy.testing.assert_allclose(event_values, EXPECTED_EVENTS,
                                  rtol=1e-6, atol=1e-6)
    return dict(states=STATES, asset_count=len(ids), building_count=60,
                mean_counts=actual.sum(axis=0).tolist(),
                event_counts=event_values.tolist(),
                independent_oracle_passed=True, conservation_passed=True)


def _check_result(result, folder, imt):
    # Inspect the saved engine result, not just the converter's output.
    from openquake.commonlib import datastore
    with datastore.read(result['datastore']) as store:
        result['shaking'] = _check_shaking(store, folder, imt)
        ids = _check_assets(store, folder)
        result['damage'] = _check_damage(store, ids)
        performance = store['performance_data'][()]
        result['calculator_seconds'] = sum(
            float(row['time_sec']) for row in performance
            if _text(row['operation']).endswith('.run'))
    return result


def _run_case(case, folder, resume=False):
    # Preserve and verify every prepared input file across the calculation.
    if folder.exists():
        if not resume:
            raise ValueError('Existing fixture requires --resume')
        manifest = json.loads((folder / 'manifest.json').read_text(
            encoding='utf-8'))
        inputs = manifest['output_sha256']
        for name, expected in inputs.items():
            if _sha256(folder / name) != expected:
                raise ValueError(f'Prepared input changed: {name}')
        result = _reuse_calculation(folder)
        command = None
    else:
        command = _prepare(case, folder)
        inputs = {path.name: _sha256(path) for path in folder.iterdir()
                  if path.is_file()}
        result = _calculate(folder)
    (folder / 'calculation.json').write_text(
        json.dumps(result, indent=2), encoding='utf-8')
    _check_result(result, folder, case.upper())
    after = {name: _sha256(folder / name) for name in inputs}
    if inputs != after:
        raise ValueError('Prepared input files changed during calculation')
    result.update(converter_command=command, input_hashes=inputs,
                  inputs_unchanged=True)
    return result


def main():
    """Run the two synthetic fixtures and save a compatibility report."""
    if sys.prefix == sys.base_prefix:
        raise SystemExit('Activate ~/openquake before running this script')
    os.environ['OQ_DISTRIBUTE'] = 'no'
    from openquake.baselib import __version__
    from openquake.commonlib import oqvalidation
    expected_source = ROOT.parent / 'openquake/commonlib/oqvalidation.py'
    if Path(oqvalidation.__file__).resolve() != expected_source.resolve():
        raise SystemExit('Install this checkout editable in ~/openquake')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    stamp = datetime.now(SGT).strftime('%Y%m%d_%H%M%S_%f_SGT')
    folder = args.output_dir or ROOT / 'runs' / stamp
    if args.resume and not args.output_dir:
        parser.error('--resume requires --output-dir')
    folder.mkdir(parents=True, exist_ok=args.resume)
    report = dict(engine_version=__version__, python=platform.python_version(),
                  started_at=datetime.now(SGT).isoformat(),
                  scope='Synthetic imported-intensity compatibility only',
                  cases={}, passed=False)
    report.update(_provenance())
    report_path = folder / 'compatibility_report.json'
    try:
        for case in ('pga', 'jma'):
            report['cases'][case] = _run_case(case, folder / case, args.resume)
        report['passed'] = True
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        report['finished_at'] = datetime.now(SGT).isoformat()
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(f'Compatibility report: {report_path}')


if __name__ == '__main__':
    main()
