"""Prepare audited OpenQuake inputs from externally supplied shaking."""
import argparse
import csv
import hashlib
import json
import math
import re
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np


NRML = 'http://openquake.org/xmlns/nrml/0.5'
GRAVITY = 9.80665
ET.register_namespace('', NRML)


def _text(data, field):
    # Require meaningful text, rather than accepting implicit assumptions.
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'Missing or empty {field}')
    return value.strip()


def _imt(value):
    # Keep JMA as its own IMT; no intensity-scale conversion is performed.
    if value in ('PGA', 'PGV', 'JMA'):
        return value
    match = re.fullmatch(r'SA\(([0-9]+(?:\.[0-9]+)?)\)', value)
    period = float(match[1]) if match else 0
    if math.isfinite(period) and period > 0:
        return f'SA({period:g})'
    raise ValueError('IMT must be PGA, PGV, SA(positive period), or JMA')


def _unit_factor(imt, units):
    # Canonical OpenQuake units are g, cm/s, or instrumental JMA intensity.
    if imt == 'JMA':
        factors = {'instrumental': 1.0}
    elif imt == 'PGV':
        factors = {'cm/s': 1.0, 'm/s': 100.0}
    else:
        factors = {'g': 1.0, 'm/s2': 1 / GRAVITY,
                   'gal': 0.01 / GRAVITY, 'percent_g': 0.01}
    if units not in factors:
        raise ValueError(f'Unsupported units {units!r} for {imt}; '
                         f'choose {", ".join(factors)}')
    return factors[units]


def _array(values, label, nonnegative=True):
    # Reject missing, nonnumeric, nonfinite, or negative numerical inputs.
    try:
        array = np.asarray(values, dtype=float)
    except (ValueError, TypeError) as exc:
        raise ValueError(f'{label} must contain numbers') from exc
    if array.ndim != 1 or not array.size or not np.isfinite(array).all():
        raise ValueError(f'{label} must be a finite, nonempty list')
    if nonnegative and (array < 0).any():
        raise ValueError(f'{label} must be nonnegative')
    return array


def _coordinates(lon, lat, label):
    # Check geographic longitude/latitude rather than projected coordinates.
    coords = _array([lon, lat], label, nonnegative=False)
    if abs(coords[0]) > 180 or abs(coords[1]) > 90:
        raise ValueError(f'{label} requires WGS84 degrees within world bounds')
    return tuple(coords)


def _identity(value, label):
    # OpenQuake risk IDs forbid quotes and hashes; whitespace is ambiguous.
    if any(c.isspace() or c in '#\"\'' for c in value):
        raise ValueError(f'Invalid {label} {value!r}')
    return value


def _json(path):
    # Duplicate JSON keys are errors: otherwise later keys silently win.
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key {key}')
            result[key] = value
        return result

    with Path(path).open(encoding='utf-8-sig') as stream:
        result = json.load(stream, object_pairs_hook=unique_keys)
    if not isinstance(result, dict):
        raise ValueError(f'{path} must contain a JSON object')
    return result


def _csv(path, fields):
    # Validate the CSV structure before interpreting any values.
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        names = reader.fieldnames or []
        if len(names) != len(set(names)):
            raise ValueError(f'Duplicate CSV columns in {path}')
        if set(fields) - set(names):
            raise ValueError(f'{path} is missing columns '
                             f'{sorted(set(fields) - set(names))}')
        rows = list(reader)
    if not rows:
        raise ValueError(f'Empty CSV: {path}')
    malformed = [None in row or any(v is None for v in row.values())
                 for row in rows]
    if any(malformed):
        raise ValueError(f'CSV row length does not match header in {path}')
    return rows


def _metadata(metadata, fragility):
    # The shaking and curves must describe the same quantity and ground level.
    for field in ('scenario_name', 'source_url', 'source_version'):
        _text(metadata, field)
    _text(fragility, 'source_url')
    imt = _imt(_text(metadata, 'imt'))
    if imt != _imt(_text(fragility, 'imt')):
        raise ValueError('Shaking and fragility IMTs do not match')
    for field in ('ground_level', 'component'):
        if _text(metadata, field) != _text(fragility, field):
            raise ValueError(f'Shaking and fragility {field} do not match')
    if metadata['ground_level'] != 'surface':
        raise ValueError('Only surface shaking is supported; bedrock shaking '
                         'needs a justified site-response step first')
    if imt.startswith('SA('):
        for data in (metadata, fragility):
            if data.get('damping_percent') != 5:
                raise ValueError('SA requires explicit damping_percent = 5')
    count_type = metadata.get('exposure_count_type', 'integer')
    if count_type not in ('integer', 'estimated'):
        raise ValueError('exposure_count_type must be integer or estimated')
    return (imt, _unit_factor(imt, _text(metadata, 'units')),
            _unit_factor(imt, _text(fragility, 'units')))


def _curves(fragility, factor):
    # Enforce valid discrete exceedance curves without fitting or relabelling.
    states = fragility.get('limit_states')
    if (not isinstance(states, list) or not states
            or any(not isinstance(state, str) for state in states)
            or len(set(states)) != len(states)):
        raise ValueError('limit_states must be an ordered unique list')
    for state in states:
        if (not isinstance(state, str)
                or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', state)
                or state == 'no_damage'):
            raise ValueError(f'Invalid limit state {state!r}')
    functions = fragility.get('functions')
    if not isinstance(functions, list) or not functions:
        raise ValueError('functions must be a nonempty list')
    curves = {}
    for function in functions:
        identity = _identity(_text(function, 'id'), 'function id')
        if identity in curves:
            raise ValueError(f'Invalid or duplicate function id {identity!r}')
        imls = _array(function.get('imls'), f'{identity} imls') * factor
        if (not np.isfinite(imls).all() or len(imls) < 2
                or (np.diff(imls) <= 0).any()):
            raise ValueError(f'{identity} imls must strictly increase')
        poe_map = function.get('poes', {})
        if set(poe_map) != set(states):
            raise ValueError(f'{identity} poes must match limit_states')
        poes = np.vstack([_array(poe_map[s], f'{identity} {s}')
                          for s in states])
        if poes.shape != (len(states), len(imls)) or (poes > 1).any():
            raise ValueError(f'{identity} poes need matching lengths '
                             'in [0, 1]')
        if (np.diff(poes, axis=1) < 0).any():
            raise ValueError(f'{identity} poes must increase with intensity')
        if (np.diff(poes, axis=0) > 0).any():
            raise ValueError(f'{identity} poes must decrease with severity')
        limit = _array([function.get('no_damage_limit')],
                       f'{identity} no_damage_limit')[0] * factor
        if (not math.isfinite(limit) or limit > imls[-1]
                or (poes[:, imls <= limit] > 0).any()):
            raise ValueError(f'{identity} no_damage_limit contradicts curves')
        curves[identity] = {'imls': imls, 'poes': poes, 'limit': limit}
    return states, curves


def _shaking(args, factor):
    # Preserve all cases, assign stable sites, and remap sparse integer IDs.
    fields = [args.lon_column, args.lat_column, args.value_column]
    rows = _csv(args.shaking_csv, fields)
    shaking = {}
    for row in rows:
        coords = _coordinates(row[args.lon_column], row[args.lat_column],
                              'Shaking coordinates')
        event = row.get(args.event_column, '0').strip()
        if not re.fullmatch(r'[0-9]+', event):
            raise ValueError('event_id must be a nonnegative integer')
        key = (int(event), coords)
        if key in shaking:
            raise ValueError('Duplicate event and coordinate pair')
        shaking[key] = _array([row[args.value_column]], 'Shaking value')[0]
    sites = sorted({coords for _, coords in shaking})
    rounded = [tuple(np.round(coords, 5)) for coords in sites]
    if len(rounded) != len(set(rounded)):
        raise ValueError('Shaking coordinates collide at five decimal places')
    events = sorted({event for event, _ in shaking})
    if len(shaking) != len(sites) * len(events):
        raise ValueError('Every event must provide shaking at every site')
    if len(events) >= 2 ** 32 or len(sites) >= 2 ** 32:
        raise ValueError('OpenQuake site and event IDs must fit uint32')
    values = np.array([[shaking[event, coords] for coords in sites]
                       for event in events]) * factor
    if not np.isfinite(values).all() or (values > np.finfo('f4').max).any():
        raise ValueError('Converted shaking values must fit finite float32')
    return rounded, events, values


def _exposure(path, curves, count_type):
    # Exact taxonomy IDs connect assets to the corresponding fragility curves.
    rows = _csv(path, ['id', 'lon', 'lat', 'number', 'taxonomy'])
    assets = []
    identities = set()
    for row in rows:
        identity = _identity(_text(row, 'id'), 'asset id')
        if identity in identities:
            raise ValueError(f'Invalid or duplicate asset id {identity!r}')
        if len(identity.encode('utf-8')) > 100:
            raise ValueError(f'Asset id exceeds 100 UTF-8 bytes: {identity}')
        identities.add(identity)
        taxonomy = _text(row, 'taxonomy')
        if taxonomy not in curves:
            raise ValueError(f'Missing fragility for taxonomy {taxonomy!r}')
        lon, lat = _coordinates(row['lon'], row['lat'], identity)
        number = _array([row['number']], f'{identity} number')[0]
        fractional = count_type == 'integer' and not number.is_integer()
        if number <= 0 or number > np.finfo('f4').max or fractional:
            raise ValueError('Counts must be positive integers unless '
                             'exposure_count_type = estimated')
        assets.append({'id': identity, 'lon': lon, 'lat': lat,
                       'number': number, 'taxonomy': taxonomy})
    return assets


def _assignments(assets, sites, maximum):
    # Match in bounded numpy batches using great-circle distance in kilometres.
    if not math.isfinite(maximum) or maximum <= 0:
        raise ValueError('max-asset-distance-km must be finite and positive')
    coords = np.radians(sites)
    batch_size = max(1, 1000000 // len(sites))
    assignments = []
    for start in range(0, len(assets), batch_size):
        batch = assets[start:start + batch_size]
        locs = np.radians([[a['lon'], a['lat']] for a in batch])
        delta = locs[:, None, :] - coords[None, :, :]
        sin2 = np.sin(delta[:, :, 1] / 2) ** 2
        sin2 += (np.cos(locs[:, None, 1]) * np.cos(coords[None, :, 1])
                 * np.sin(delta[:, :, 0] / 2) ** 2)
        distance = 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(sin2, 0, 1)))
        nearest = distance.argmin(axis=1)
        for i, asset in enumerate(batch):
            sid = int(nearest[i])
            km = float(distance[i, sid])
            if km > maximum:
                raise ValueError(f'Asset {asset["id"]} is {km:.6g} km from '
                                 f'nearest site; threshold is {maximum} km')
            assignments.append({'asset_id': asset['id'], 'site_id': sid,
                                'distance_km': km, 'lon': asset['lon'],
                                'lat': asset['lat'], 'site_lon': sites[sid][0],
                                'site_lat': sites[sid][1]})
    return assignments


def _coverage(assets, assignments, values, curves):
    # Prevent OpenQuake's upper-end extrapolation from becoming an assumption.
    checked = set()
    for asset, match in zip(assets, assignments):
        key = (asset['taxonomy'], match['site_id'])
        if key in checked:
            continue
        checked.add(key)
        curve = curves[key[0]]
        site_values = values[:, key[1]]
        no_damage = site_values < curve['limit']
        below = (site_values < curve['imls'][0]) & ~no_damage
        if below.any() or (site_values > curve['imls'][-1]).any():
            raise ValueError(f'Shaking outside supported fragility range for '
                             f'{key[0]} at site {key[1]}')


def _write_csv(path, fields, rows):
    # Use UTF-8 without a BOM and enough digits for numerical fidelity.
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)


def _xml(path, model):
    # Namespace all elements explicitly so the NRML reader accepts the file.
    root = ET.Element(f'{{{NRML}}}nrml')
    root.append(model)
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def _element(parent, tag, text=None, **attributes):
    # Escape user text and attribute values through ElementTree.
    element = ET.SubElement(parent, f'{{{NRML}}}{tag}', attributes)
    element.text = text
    return element


def _exposure_files(output, assets):
    # A counts-only exposure supports physical damage, without economic costs.
    _write_csv(output / 'exposure.csv',
               ['id', 'lon', 'lat', 'number', 'taxonomy'],
               [[a[f] for f in ('id', 'lon', 'lat', 'number', 'taxonomy')]
                for a in assets])
    model = ET.Element(f'{{{NRML}}}exposureModel', {
        'id': 'tokyo_exposure', 'category': 'buildings',
        'taxonomySource': 'Exact supplied fragility function IDs'})
    _element(model, 'description', 'Externally supplied building counts')
    _element(_element(model, 'conversions'), 'costTypes')
    _element(model, 'assets', 'exposure.csv')
    _xml(output / 'exposure.xml', model)


def _fragility_file(output, imt, states, curves):
    # The curve probabilities and canonical IMT are preserved without fitting.
    model = ET.Element(f'{{{NRML}}}fragilityModel', {
        'id': 'tokyo_fragility', 'assetCategory': 'building',
        'lossCategory': 'structural'})
    _element(model, 'description', 'Supplied discrete exceedance curves')
    _element(model, 'limitStates', ' '.join(states))
    for identity, curve in curves.items():
        function = _element(model, 'fragilityFunction', id=identity,
                            format='discrete')
        _element(function, 'imls', ' '.join(map(str, curve['imls'])),
                 imt=imt, noDamageLimit=str(curve['limit']))
        for state, poes in zip(states, curve['poes']):
            _element(function, 'poes', ' '.join(map(str, poes)), ls=state)
    _xml(output / 'fragility.xml', model)


def _job_file(output, imt, maximum):
    # Imported surface GMFs need no Vs30, rupture, GSIM, or waveform input.
    text = ('[general]\n'
            'description = External scenario shaking damage calculation\n'
            'calculation_mode = scenario_damage\n'
            'concurrent_tasks = 0\n'
            '\n[inputs]\n'
            'sites_csv = sites.csv\n'
            'gmfs_file = gmfs.csv\n'
            'exposure_file = exposure.xml\n'
            'structural_fragility_file = fragility.xml\n'
            f'intensity_measure_types = {imt}\n'
            '\n[damage]\n'
            f'asset_hazard_distance = {maximum:.15g}\n'
            'discrete_damage_distribution = false\n'
            'aggregate_by = taxonomy\n'
            'exports = csv\n')
    (output / 'job_damage.ini').write_text(text, encoding='utf-8')


def _hash(path):
    # Stream checksums so large external shaking CSVs do not fill RAM again.
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _manifest(args, output, metadata, fragility, sites, events, assets, imt):
    # Capture provenance, conversions, event mapping, and output integrity.
    inputs = {name: getattr(args, name) for name in (
        'shaking_csv', 'exposure_csv', 'fragility_json', 'metadata_json')}
    result = {
        'schema_version': 1, 'shaking_metadata': metadata,
        'fragility_metadata': {k: v for k, v in fragility.items()
                               if k != 'functions'},
        'canonical_imt': imt,
        'canonical_units': ('instrumental' if imt == 'JMA' else
                            'cm/s' if imt == 'PGV' else 'g'),
        'site_count': len(sites), 'event_count': len(events),
        'asset_count': len(assets),
        'building_count': float(sum(a['number'] for a in assets)),
        'max_asset_distance_km': args.max_asset_distance_km,
        'source_event_ids': events,
        'event_id_mapping': {str(e): i for i, e in enumerate(events)},
        'input_sha256': {name: _hash(path) for name, path in inputs.items()},
        'output_sha256': {p.name: _hash(p) for p in sorted(output.iterdir())},
        'limitations': [
            'Imported cases are equally weighted within one realization.',
            'A mean map is deterministic input, not shaking uncertainty.',
            'Counts-only damage; economic losses are not configured.',
            'Nearest-site assignment; no interpolation or site amplification.',
            'JMA is never converted to PGA or MMI.',
            'Scientific applicability still needs source-study review.']}
    path = output / 'manifest.json'
    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def prepare(args):
    """Validate source inputs and write a new OpenQuake scenario package."""
    output = Path(args.output_dir)
    if output.exists():
        raise ValueError(f'Output directory already exists: {output}')
    metadata = _json(args.metadata_json)
    fragility = _json(args.fragility_json)
    imt, shake_factor, curve_factor = _metadata(metadata, fragility)
    states, curves = _curves(fragility, curve_factor)
    sites, events, values = _shaking(args, shake_factor)
    assets = _exposure(args.exposure_csv, curves,
                       metadata.get('exposure_count_type', 'integer'))
    matches = _assignments(assets, sites, args.max_asset_distance_km)
    _coverage(assets, matches, values, curves)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent,
                                     prefix='oq_prepare_') as location:
        temp = Path(location)
        _write_csv(temp / 'sites.csv', ['site_id', 'lon', 'lat'],
                   [[i, f'{lon:.5f}', f'{lat:.5f}']
                    for i, (lon, lat) in enumerate(sites)])
        _write_csv(temp / 'gmfs.csv', ['site_id', 'event_id', f'gmv_{imt}'],
                   [[sid, eid, value] for eid, row in enumerate(values)
                    for sid, value in enumerate(row)])
        _write_csv(temp / 'asset_site_assignments.csv', list(matches[0]),
                   [list(match.values()) for match in matches])
        _exposure_files(temp, assets)
        _fragility_file(temp, imt, states, curves)
        _job_file(temp, imt, args.max_asset_distance_km)
        result = _manifest(args, temp, metadata, fragility, sites, events,
                           assets, imt)
        temp.rename(output)
    return result


def parser():
    """Return the command-line parser for external scenario preparation."""
    command = argparse.ArgumentParser(description=__doc__)
    for name in ('shaking-csv', 'exposure-csv', 'fragility-json',
                 'metadata-json', 'output-dir'):
        command.add_argument('--' + name, required=True, type=Path)
    for name, default in (('lon-column', 'lon'), ('lat-column', 'lat'),
                          ('value-column', 'value'),
                          ('event-column', 'event_id')):
        command.add_argument('--' + name, default=default)
    command.add_argument('--max-asset-distance-km', type=float, default=0.1)
    return command


def main():
    """Prepare inputs or print a concise validation error and exit nonzero."""
    command = parser()
    try:
        result = prepare(command.parse_args())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        command.exit(2, f'Input preparation failed: {exc}\n')
    print(f'Prepared {result["canonical_imt"]}: {result["site_count"]} sites, '
          f'{result["event_count"]} cases, {result["asset_count"]} asset rows')


if __name__ == '__main__':
    main()
