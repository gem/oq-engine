"""Checks for scientific quantity preservation and fail-closed preparation."""
import csv
import json
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from tokyo_compatibility.prepare_inputs import NRML, parser, prepare


def _csv(path, fields, rows):
    # Write source fixtures with the same user-facing CSV format as the CLI.
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)


def _inputs(tmp_path, imt='PGA', units='g'):
    # Two sites and two sparse event IDs exercise remapping and site order.
    metadata = {'scenario_name': 'Synthetic compatibility check',
                'source_url': 'https://example.org/synthetic',
                'source_version': 'test', 'imt': imt, 'units': units,
                'ground_level': 'surface', 'component': 'horizontal'}
    fragility = {'imt': imt, 'units': units, 'ground_level': 'surface',
                 'component': 'horizontal',
                 'source_url': 'https://example.org/synthetic-fragility',
                 'limit_states': ['slight', 'complete'],
                 'functions': [{'id': 'Wood', 'imls': [0, 1, 2],
                                'no_damage_limit': 0,
                                'poes': {'slight': [0, 0.5, 0.9],
                                         'complete': [0, 0.1, 0.4]}}]}
    shaking = tmp_path / 'shaking.csv'
    exposure = tmp_path / 'source_exposure.csv'
    meta_path = tmp_path / 'metadata.json'
    frag_path = tmp_path / 'fragility.json'
    _csv(shaking, ['lon', 'lat', 'event_id', 'value'],
         [[139.71, 35.68, 9, 0.4], [139.70, 35.68, 5, 0.2],
          [139.71, 35.68, 5, 0.3], [139.70, 35.68, 9, 0.5]])
    _csv(exposure, ['id', 'lon', 'lat', 'number', 'taxonomy'],
         [['asset_1', 139.70, 35.68, 2, 'Wood'],
          ['asset_2', 139.71, 35.68, 3, 'Wood']])
    meta_path.write_text(json.dumps(metadata), encoding='utf-8')
    frag_path.write_text(json.dumps(fragility), encoding='utf-8')
    args = parser().parse_args([
        '--shaking-csv', str(shaking), '--exposure-csv', str(exposure),
        '--metadata-json', str(meta_path), '--fragility-json', str(frag_path),
        '--output-dir', str(tmp_path / 'prepared')])
    return args


def _update_json(path, updates):
    # Update fixture source data before conversion, never generated files.
    data = json.loads(path.read_text(encoding='utf-8'))
    updates(data)
    path.write_text(json.dumps(data), encoding='utf-8')


def _read_csv(path):
    # Return records for assertions on the actual prepared interchange files.
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


@pytest.mark.parametrize('imt, units, expected', [
    ('PGA', 'g', 0.2), ('PGA', 'm/s2', 0.2 / 9.80665),
    ('PGA', 'gal', 0.002 / 9.80665), ('PGA', 'percent_g', 0.002),
    ('PGV', 'cm/s', 0.2), ('PGV', 'm/s', 20.0)])
def test_shaking_and_fragility_unit_conversion(tmp_path, imt, units, expected):
    args = _inputs(tmp_path, imt, units)
    result = prepare(args)
    gmfs = _read_csv(args.output_dir / 'gmfs.csv')
    assert float(gmfs[0]['gmv_' + imt]) == pytest.approx(expected)
    tree = ET.parse(args.output_dir / 'fragility.xml')
    imls = tree.find(f'.//{{{NRML}}}imls').text.split()
    assert float(imls[1]) == pytest.approx(expected / 0.2)
    assert result['event_id_mapping'] == {'5': 0, '9': 1}
    assert result['building_count'] == 5


def test_jma_remains_jma(tmp_path):
    args = _inputs(tmp_path, 'JMA', 'instrumental')
    _csv(args.shaking_csv, ['lon', 'lat', 'value'],
         [[139.70, 35.68, 5.3], [139.71, 35.68, 5.8]])
    _update_json(args.fragility_json, lambda d: d['functions'][0].update(
        {'imls': [0, 5, 7]}))
    report = prepare(args)
    gmfs = _read_csv(args.output_dir / 'gmfs.csv')
    assert set(gmfs[0]) == {'site_id', 'event_id', 'gmv_JMA'}
    assert float(gmfs[0]['gmv_JMA']) == 5.3
    assert report['canonical_imt'] == 'JMA'
    assert 'intensity_measure_types = JMA' in (
        args.output_dir / 'job_damage.ini').read_text(encoding='utf-8')


@pytest.mark.parametrize('units', ['jma_category', 'MMI', 'g'])
def test_jma_category_and_relabel_units_rejected(tmp_path, units):
    args = _inputs(tmp_path, 'JMA', units)
    with pytest.raises(ValueError, match='Unsupported units'):
        prepare(args)
    assert not args.output_dir.exists()


def test_different_intensity_measures_rejected(tmp_path):
    args = _inputs(tmp_path)
    _update_json(args.fragility_json, lambda d: d.update({'imt': 'JMA'}))
    with pytest.raises(ValueError, match='IMTs do not match'):
        prepare(args)


@pytest.mark.parametrize('field, value', [
    ('ground_level', 'engineering_bedrock'), ('component', 'vertical')])
def test_ground_level_and_component_mismatch(tmp_path, field, value):
    args = _inputs(tmp_path)
    _update_json(args.metadata_json, lambda d: d.update({field: value}))
    with pytest.raises(ValueError, match=field):
        prepare(args)


def test_complete_bedrock_inputs_still_require_site_response(tmp_path):
    args = _inputs(tmp_path)
    for path in (args.metadata_json, args.fragility_json):
        _update_json(path, lambda d: d.update({'ground_level': 'bedrock'}))
    with pytest.raises(ValueError, match='site-response'):
        prepare(args)


def test_missing_site_in_one_case_rejected(tmp_path):
    args = _inputs(tmp_path)
    _csv(args.shaking_csv, ['lon', 'lat', 'event_id', 'value'],
         [[139.70, 35.68, 0, 0.2], [139.71, 35.68, 0, 0.3],
          [139.70, 35.68, 1, 0.4]])
    with pytest.raises(ValueError, match='Every event'):
        prepare(args)


def test_duplicate_site_case_rejected(tmp_path):
    args = _inputs(tmp_path)
    _csv(args.shaking_csv, ['lon', 'lat', 'event_id', 'value'],
         [[139.70, 35.68, 0, 0.2], [139.70, 35.68, 0, 0.3]])
    with pytest.raises(ValueError, match='Duplicate event'):
        prepare(args)


def test_rounded_coordinate_collision_rejected(tmp_path):
    args = _inputs(tmp_path)
    _csv(args.shaking_csv, ['lon', 'lat', 'value'],
         [[139.700001, 35.68, 0.2], [139.700002, 35.68, 0.3]])
    with pytest.raises(ValueError, match='five decimal'):
        prepare(args)


def test_missing_building_class_rejected(tmp_path):
    args = _inputs(tmp_path)
    _csv(args.exposure_csv, ['id', 'lon', 'lat', 'number', 'taxonomy'],
         [['asset_1', 139.70, 35.68, 2, 'Unknown']])
    with pytest.raises(ValueError, match='Missing fragility'):
        prepare(args)


def test_unmatched_asset_is_not_silently_dropped(tmp_path):
    args = _inputs(tmp_path)
    _csv(args.exposure_csv, ['id', 'lon', 'lat', 'number', 'taxonomy'],
         [['asset_1', 139.90, 35.68, 2, 'Wood']])
    with pytest.raises(ValueError, match='nearest site'):
        prepare(args)


def test_nearest_site_assignment_is_reported(tmp_path):
    args = _inputs(tmp_path)
    _csv(args.exposure_csv, ['id', 'lon', 'lat', 'number', 'taxonomy'],
         [['near_right', 139.7099, 35.68, 2, 'Wood']])
    prepare(args)
    assignment = _read_csv(args.output_dir / 'asset_site_assignments.csv')[0]
    assert assignment['site_id'] == '1'
    assert 0 < float(assignment['distance_km']) < 0.1


@pytest.mark.parametrize('numbers', [[0], [-1], [float('nan')], [1.5]])
def test_invalid_counts_rejected(tmp_path, numbers):
    args = _inputs(tmp_path)
    _csv(args.exposure_csv, ['id', 'lon', 'lat', 'number', 'taxonomy'],
         [['asset_1', 139.70, 35.68, numbers[0], 'Wood']])
    with pytest.raises(ValueError):
        prepare(args)


def test_estimated_counts_require_explicit_declaration(tmp_path):
    args = _inputs(tmp_path)
    _update_json(args.metadata_json, lambda d: d.update(
        {'exposure_count_type': 'estimated'}))
    _csv(args.exposure_csv, ['id', 'lon', 'lat', 'number', 'taxonomy'],
         [['asset_1', 139.70, 35.68, 1.5, 'Wood']])
    assert prepare(args)['building_count'] == 1.5


@pytest.mark.parametrize('poes, message', [
    ({'slight': [0, 0.8, 0.7], 'complete': [0, 0.1, 0.4]}, 'intensity'),
    ({'slight': [0, 0.5, 0.9], 'complete': [0, 0.6, 0.8]}, 'severity'),
    ({'slight': [0, 0.5, 1.1], 'complete': [0, 0.1, 0.4]}, 'in \\[0, 1\\]')])
def test_invalid_exceedance_probabilities(tmp_path, poes, message):
    args = _inputs(tmp_path)
    _update_json(args.fragility_json, lambda d: d['functions'][0].update(
        {'poes': poes}))
    with pytest.raises(ValueError, match=message):
        prepare(args)


def test_shaking_above_curve_range_rejected(tmp_path):
    args = _inputs(tmp_path)
    _csv(args.shaking_csv, ['lon', 'lat', 'value'],
         [[139.70, 35.68, 2.1], [139.71, 35.68, 0.3]])
    with pytest.raises(ValueError, match='outside supported fragility range'):
        prepare(args)


def test_shaking_below_declared_no_damage_limit_is_allowed(tmp_path):
    args = _inputs(tmp_path)
    _update_json(args.fragility_json, lambda d: d['functions'][0].update(
        {'imls': [0.3, 1, 2], 'no_damage_limit': 0.25}))
    assert prepare(args)['event_count'] == 2


def test_no_damage_boundary_below_curve_range_rejected(tmp_path):
    args = _inputs(tmp_path)
    _update_json(args.fragility_json, lambda d: d['functions'][0].update(
        {'imls': [0.3, 1, 2], 'no_damage_limit': 0.25}))
    _csv(args.shaking_csv, ['lon', 'lat', 'value'],
         [[139.70, 35.68, 0.25], [139.71, 35.68, 0.3]])
    with pytest.raises(ValueError, match='outside supported fragility range'):
        prepare(args)
    assert not args.output_dir.exists()
    _csv(args.shaking_csv, ['lon', 'lat', 'value'],
         [[139.70, 35.68, 0.2], [139.71, 35.68, 0.3]])
    assert prepare(args)['event_count'] == 1


def test_jma_zero_below_curve_range_is_not_zero_acceleration(tmp_path):
    args = _inputs(tmp_path, 'JMA', 'instrumental')
    _update_json(args.fragility_json, lambda d: d['functions'][0].update(
        {'imls': [1, 5, 7], 'no_damage_limit': 0}))
    _csv(args.shaking_csv, ['lon', 'lat', 'value'],
         [[139.70, 35.68, 0], [139.71, 35.68, 5]])
    with pytest.raises(ValueError, match='outside supported fragility range'):
        prepare(args)


@pytest.mark.parametrize('value', ['nan', 'inf', '-0.1'])
def test_invalid_shaking_values_rejected(tmp_path, value):
    args = _inputs(tmp_path)
    _csv(args.shaking_csv, ['lon', 'lat', 'value'],
         [[139.70, 35.68, value]])
    with pytest.raises(ValueError):
        prepare(args)


def test_sa_requires_matching_five_percent_damping(tmp_path):
    args = _inputs(tmp_path, 'SA(0.5)')
    with pytest.raises(ValueError, match='damping_percent'):
        prepare(args)
    for path in (args.metadata_json, args.fragility_json):
        _update_json(path, lambda d: d.update({'damping_percent': 5}))
    assert prepare(args)['canonical_imt'] == 'SA(0.5)'


def test_existing_output_never_overwritten(tmp_path):
    args = _inputs(tmp_path)
    prepare(args)
    manifest = (args.output_dir / 'manifest.json').read_bytes()
    with pytest.raises(ValueError, match='already exists'):
        prepare(args)
    assert (args.output_dir / 'manifest.json').read_bytes() == manifest


def test_prepared_files_pass_installed_nrml_readers(tmp_path):
    from openquake.hazardlib import nrml
    from openquake.risklib.asset import read_exp_df

    args = _inputs(tmp_path)
    prepare(args)
    model = nrml.to_python(str(args.output_dir / 'fragility.xml'))
    assert set(model) == {('PGA', 'Wood')}
    _, exposure = read_exp_df(str(args.output_dir / 'exposure.xml'))
    np.testing.assert_array_equal(exposure['value-number'], [2.0, 3.0])
