"""Validate damage consumers of the original and portable hazard results."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SGT = timezone(timedelta(hours=8))


def _check_environment():
    # Require the project environment before importing scientific packages.
    expected = (Path.home() / 'openquake').resolve()
    active = Path(os.environ.get('VIRTUAL_ENV', '.')).resolve()
    if active != expected:
        raise RuntimeError('Activate ~/openquake before validation')
    for package in ('ruff', 'pytest-xdist', 'pytest-django'):
        version(package)


def _sha256(path):
    # Hash complete files so consumer calculations cannot modify the hazard.
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _read_snapshot(path, consumer=False):
    # Follow the consumer's own parent reference rather than opening it alone.
    from openquake.commonlib import datastore
    with datastore.read(str(path)) as store:
        oq = store['oqparam']
        assets = store['assetcol']
        snapshot = dict(mode=oq.calculation_mode,
                        parent=oq.hazard_calculation_id,
                        gmfs={name: store[f'gmf_data/{name}'][()]
                              for name in store['gmf_data']},
                        events=store['events'][()],
                        weights=store['weights'][()],
                        asset_ids=assets['id'].copy(),
                        asset_sites=assets['site_id'].copy(),
                        asset_numbers=assets['value-number'].copy())
        snapshot['calculator_runs'] = [
            dict(operation=row['operation'].decode(),
                 runtime_seconds=float(row['time_sec']))
            for row in store['performance_data'][()]
            if row['operation'].decode().endswith('.run')]
        if consumer:
            snapshot['damages'] = store['damages-rlzs'][()]
            snapshot['damage_stats'] = store['damages-stats'][()]
            states = store.getitem('crm').attrs['limit_states']
            snapshot['states'] = ['no_damage'] + [
                state.decode() if isinstance(state, bytes) else str(state)
                for state in states]
    return snapshot


def _compare_hazard(expected, actual):
    # Compare every GMF column and all event, weight, and asset associations.
    import numpy
    if set(expected['gmfs']) != set(actual['gmfs']):
        raise ValueError('The consumer GMF column set differs from hazard')
    for name, array in expected['gmfs'].items():
        numpy.testing.assert_array_equal(
            actual['gmfs'][name], array, err_msg=f'GMF column {name}')
    for name in ('events', 'weights', 'asset_ids', 'asset_sites',
                 'asset_numbers'):
        numpy.testing.assert_array_equal(
            actual[name], expected[name], err_msg=name)


def _check_damage(snapshot):
    # Check asset conservation and the stored weighted mean of each field.
    import numpy
    damages = snapshot['damages']
    stats = snapshot['damage_stats']
    weights = snapshot['weights'].astype(float)
    states = snapshot['states']
    if damages.shape != (len(snapshot['asset_ids']), len(weights)):
        raise ValueError('Unexpected asset/realization damage dimensions')
    if stats.shape != (len(damages), 1):
        raise ValueError('Expected one mean damage statistic per asset')
    total = numpy.zeros(damages.shape, dtype=float)
    portfolio = {}
    for state in states:
        field = f'structural-{state}'
        values = damages[field].astype(float)
        if not numpy.isfinite(values).all() or (values < 0).any():
            raise ValueError(f'Invalid damage counts in {field}')
        total += values
        portfolio[state] = float(stats[field][:, 0].sum(dtype=float))
    numbers = snapshot['asset_numbers'][:, None]
    error = float(numpy.abs(total - numbers).max())
    numpy.testing.assert_allclose(
        total, numpy.broadcast_to(numbers, total.shape),
        rtol=1e-6, atol=1e-6,
        err_msg='Damage states must conserve asset numbers')
    relative = numpy.divide(
        numpy.abs(total - numbers), numbers, out=numpy.zeros_like(total),
        where=numbers != 0)
    mean_errors = {}
    for field in damages.dtype.names:
        mean = damages[field].astype(float).dot(weights)
        actual = stats[field][:, 0].astype(float)
        numpy.testing.assert_allclose(
            actual, mean, rtol=5e-6, atol=5e-6,
            err_msg=f'Stored weighted mean of {field}')
        mean_errors[field] = float(numpy.abs(actual - mean).max())
    return dict(damage_states=states, damage_shape=list(damages.shape),
                asset_count=len(damages),
                total_asset_number=float(numbers.sum()),
                portfolio_mean_damage_counts=portfolio,
                conservation_max_absolute_error=error,
                conservation_max_relative_error=float(relative.max()),
                conservation_relative_tolerance=1e-6,
                weighted_mean_max_absolute_errors=mean_errors,
                conservation_absolute_tolerance=1e-6,
                weighted_mean_relative_tolerance=5e-6,
                weighted_mean_absolute_tolerance=5e-6)


def _run_consumer(job_ini, parent, output_dir):
    # Use a distinct log to identify this calculation without latest-job races.
    from openquake.commonlib import logs
    output_dir.mkdir(parents=True, exist_ok=False)
    log_file = output_dir / 'engine.log'
    exports = output_dir / 'exports'
    exports.mkdir()
    command = [sys.executable, '-m', 'openquake.commands', 'engine',
               '--run', str(job_ini), '--hc', str(parent), '--exports', 'csv',
               '--param', 'export_dir=' + str(exports),
               '--log-file', str(log_file), '--no-distribute']
    environment = os.environ.copy()
    environment.update(OQ_DISTRIBUTE='no', PYTHONUTF8='1')
    started = datetime.now(SGT).isoformat()
    tick = time.perf_counter()
    result = subprocess.run(command, cwd=ROOT, env=environment,
                            capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    elapsed = time.perf_counter() - tick
    (output_dir / 'stdout.txt').write_text(result.stdout, encoding='utf-8')
    (output_dir / 'stderr.txt').write_text(result.stderr, encoding='utf-8')
    result.check_returncode()
    contents = log_file.read_text(encoding='utf-8')
    ids = set(re.findall(r'#(\d+)\s', contents))
    if len(ids) != 1:
        raise RuntimeError(f'Expected one calculation ID in {log_file}')
    calc_id = int(ids.pop())
    job = logs.dbcmd('get_job', calc_id)
    if job.status != 'complete' or job.calculation_mode != 'scenario_damage':
        raise RuntimeError(f'Damage calculation {calc_id} did not complete')
    return dict(calculation_id=calc_id, status=job.status,
                datastore=job.ds_calc_dir + '.hdf5', parent=str(parent),
                command=command, wall_runtime_seconds=elapsed,
                started_at_singapore=started,
                finished_at_singapore=datetime.now(SGT).isoformat(),
                log_file=str(log_file), exports=str(exports))


def _validate_consumer(result, expected):
    # Verify exact shaking reuse before checking the resulting damage counts.
    snapshot = _read_snapshot(result['datastore'], consumer=True)
    if snapshot['mode'] != 'scenario_damage':
        raise ValueError('Expected a scenario_damage consumer')
    if str(snapshot['parent']) != result['parent']:
        raise ValueError('Consumer references a different hazard parent')
    _compare_hazard(expected, snapshot)
    result['exact_hazard_arrays_and_asset_associations'] = True
    result['damage_checks'] = _check_damage(snapshot)
    result['calculator_performance_records'] = snapshot['calculator_runs']
    result['calculator_runtime_seconds'] = sum(
        row['runtime_seconds'] for row in snapshot['calculator_runs'])
    result['calculator_runtime_scope'] = (
        'Stored calculator .run performance records; excludes CLI startup '
        'and the engine memory wait before calculator creation')
    return snapshot


def _check_baseline(original, portable):
    # The two source datastores must represent the unchanged two-branch demo.
    import numpy
    if original['mode'] != 'scenario' or portable['mode'] != 'scenario':
        raise ValueError('Both hazards must be scenario calculations')
    _compare_hazard(original, portable)
    numpy.testing.assert_array_equal(original['weights'], [0.75, 0.25])
    counts = numpy.bincount(original['events']['rlz_id'], minlength=2)
    numpy.testing.assert_array_equal(counts, [100, 100])
    return dict(event_count=len(original['events']),
                events_per_realization=counts.tolist(),
                weights=original['weights'].tolist(),
                asset_count=len(original['asset_ids']),
                gmf_columns=sorted(original['gmfs']),
                gmf_row_count=len(original['gmfs']['sid']),
                exact_original_and_portable_hazard_arrays=True)


def _perform_validation(handoff, hazard_id, folder, report, previous):
    # Run the original-ID and portable-file workflows sequentially.
    import numpy
    from openquake.commonlib import logs
    original_job = logs.dbcmd('get_job', hazard_id)
    if original_job.status != 'complete':
        raise ValueError('The original hazard calculation is incomplete')
    source = Path(original_job.ds_calc_dir + '.hdf5')
    portable = handoff / f'calc_{hazard_id}.hdf5'
    report['hazard_paths'] = dict(original=str(source), portable=str(portable))
    report['hazard_sha256_before'] = {
        label: _sha256(Path(path))
        for label, path in report['hazard_paths'].items()}
    hashes = report['hazard_sha256_before']
    if hashes['original'] != hashes['portable']:
        raise ValueError('The portable datastore differs from the original')
    original = _read_snapshot(source)
    report['hazard_checks'] = _check_baseline(
        original, _read_snapshot(portable))
    configs = [('same_installation',
                ROOT / 'demos/risk/ScenarioDamage/job_risk.ini', hazard_id),
               ('portable_hdf5', handoff / 'inputs/job_risk.ini', portable)]
    snapshots = []
    for label, config, parent in configs:
        if label in previous:
            result = previous[label].copy()
            job = logs.dbcmd('get_job', result['calculation_id'])
            if job.status != 'complete':
                raise ValueError('The resumed damage job is incomplete')
            result['revalidated_existing_calculation'] = True
        else:
            print(f'Running {label} damage consumer...', flush=True)
            result = _run_consumer(config, parent, folder / label)
        result['workflow'] = label
        report['consumers'].append(result)
        snapshots.append(_validate_consumer(result, original))
        print(f"Completed calculation {result['calculation_id']} in "
              f"{result['wall_runtime_seconds']:.3f} s", flush=True)
    for name in ('damages', 'damage_stats'):
        numpy.testing.assert_array_equal(
            snapshots[0][name], snapshots[1][name], err_msg=name)
    report['damage_outputs_identical'] = True
    report['status'] = 'passed'


def _resume_results(path, hazard_id):
    # Resume validation without rerunning a previously completed consumer.
    if path is None:
        return {}
    previous = json.loads(path.read_text(encoding='utf-8'))
    if previous['hazard_calculation_id'] != hazard_id:
        raise ValueError('The previous report used a different hazard')
    return {consumer['workflow']: consumer
            for consumer in previous['consumers']}


def main():
    """Run both consumer workflows and persist an auditable JSON report."""
    _check_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('handoff', type=Path,
                        help='Completed handoff directory')
    parser.add_argument('hazard_id', type=int,
                        help='Original installation hazard calculation ID')
    parser.add_argument('--output-dir', type=Path,
                        help='Validation root; default is beside handoff')
    parser.add_argument('--resume-report', type=Path,
                        help='Revalidate completed consumers from a report')
    args = parser.parse_args()
    handoff = args.handoff.resolve(strict=True)
    stamp = datetime.now(SGT).strftime('%Y%m%d_%H%M%S_%f_SGT')
    validation_root = args.output_dir or handoff.parent / 'validation'
    folder = validation_root.resolve() / stamp
    folder.mkdir(parents=True, exist_ok=False)
    report_path = folder / 'validation_report.json'
    report = dict(status='running', hazard_calculation_id=args.hazard_id,
                  started_at_singapore=datetime.now(SGT).isoformat(),
                  runtime_scope='Damage CLI startup, memory wait, calculation '
                                'and CSV exports',
                  validation_scope='Both consumer paths on this installation; '
                                   'a separate machine has not been exercised',
                  consumers=[])
    if args.resume_report:
        report['resumed_from_report'] = str(args.resume_report.resolve())
    try:
        previous = _resume_results(args.resume_report, args.hazard_id)
        _perform_validation(handoff, args.hazard_id, folder, report, previous)
    except Exception as error:
        message = f'{type(error).__name__}: {error}'
        report.update(status='failed', error=message)
        raise
    finally:
        paths = report.get('hazard_paths', {})
        after = {label: _sha256(Path(path)) if Path(path).is_file() else None
                 for label, path in paths.items()}
        report['hazard_sha256_after'] = after
        report['hazard_files_unchanged'] = (
            bool(after) and after == report.get('hazard_sha256_before'))
        if not report['hazard_files_unchanged']:
            report['status'] = 'failed'
        report['finished_at_singapore'] = datetime.now(SGT).isoformat()
        report_path.write_text(json.dumps(report, indent=2) + '\n',
                               encoding='utf-8')
        print(f'Validation report: {report_path}', flush=True)
    if report['status'] != 'passed':
        raise RuntimeError('Validation failed; inspect the JSON report')


if __name__ == '__main__':
    main()
