"""Export and map weighted arithmetic mean PGA from a scenario datastore.

Run with the activated ~/openquake environment. The map summarizes sampled
ground-motion fields; it is not an individual event or a JMA/MMI intensity map.
"""

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib
import numpy
import pandas

from openquake.commonlib import datastore

matplotlib.use('Agg')
from matplotlib import pyplot  # noqa: E402


def _rupture_geometry(path):
    # Read the input trace and the hypocentre projection, without a basemap.
    root = ET.parse(path).getroot()
    for element in root.iter():
        element.tag = element.tag.rsplit('}', 1)[-1]
    hypocentre = root.find('.//hypocenter')
    if hypocentre is None:
        raise ValueError('Rupture XML must contain a hypocenter')
    epicentre = numpy.array([float(hypocentre.get(name))
                            for name in ('lon', 'lat')])
    poslist = root.find('.//simpleFaultGeometry//posList')
    if poslist is not None:
        trace = numpy.fromstring(poslist.text, sep=' ')
        if len(trace) < 4 or len(trace) % 2:
            raise ValueError('Simple fault trace must contain lon/lat pairs')
        trace = trace.reshape(-1, 2)
    else:
        surface = root.find('.//planarSurface')
        if surface is None:
            raise ValueError('Expected a simple fault or planar rupture XML')
        trace = numpy.array([[float(surface.find(corner).get(name))
                              for name in ('lon', 'lat')]
                             for corner in ('topLeft', 'topRight')])
    if not numpy.isfinite(trace).all() or not numpy.isfinite(epicentre).all():
        raise ValueError('Rupture coordinates must be finite')
    magnitude = root.find('.//magnitude')
    info = {'magnitude': float(magnitude.text),
            'rake_degrees': float(root.find('.//rake').text),
            'hypocentre_depth_km': float(hypocentre.get('depth')),
            'epicentre_lon': float(epicentre[0]),
            'epicentre_lat': float(epicentre[1]),
            'trace_lon_lat': trace.tolist()}
    return trace, epicentre, info


def _effective_rupture(dstore):
    # The engine can move an invalid supplied hypocentre onto the rupture.
    ruptures = dstore['ruptures'][()]
    if len(ruptures) != 1:
        raise ValueError('This map expects exactly one scenario rupture')
    rupture = ruptures[0]
    hypo = numpy.asarray(rupture['hypo'], dtype=float)
    if not numpy.isfinite(hypo).all():
        raise ValueError('Effective engine hypocentre must be finite')
    return {'magnitude': float(rupture['mag']),
            'rake_degrees': float(rupture['rake']),
            'hypocentre_depth_km': float(hypo[2]),
            'epicentre_lon': float(hypo[0]),
            'epicentre_lat': float(hypo[1])}


def _branch_models(dstore):
    # Derive model labels from realization objects, without named assumptions.
    full_lt = dstore['full_lt']
    return {int(rlz.ordinal): ', '.join(
        sorted({type(gsim).__name__
                for gsim in full_lt.gsim_by_trt(rlz).values()}))
            for rlz in full_lt.get_realizations()}


def _rupture_details(supplied, effective):
    # Ignore float32 storage rounding when deciding whether the centre moved.
    fields = ['epicentre_lon', 'epicentre_lat', 'hypocentre_depth_km']
    moved = not numpy.allclose([supplied[key] for key in fields],
                               [effective[key] for key in fields],
                               rtol=0, atol=1e-4)
    note = ('Engine adjusted supplied hypocentre; the star marks the '
            'effective position.') if moved else 'No hypocentre adjustment.'
    return {'supplied_xml': supplied, 'effective_engine': effective,
            'hypocentre_moved': moved, 'hypocentre_adjustment_note': note}


def _read_hazard(path):
    # Use the full precision datastore, rather than the rounded GMF CSV.
    with datastore.read(str(path), read_parent=False) as dstore:
        oq = dstore['oqparam']
        if oq.calculation_mode != 'scenario':
            raise ValueError('Expected a hazard-only scenario calculation')
        sitecol = dstore['sitecol']
        sites = pandas.DataFrame({'site_id': sitecol.sids,
                                  'lon': sitecol.lons,
                                  'lat': sitecol.lats})
        events = dstore['events'][()]
        mapping = pandas.DataFrame({'event_id': events['id'],
                                    'rlz_id': events['rlz_id']})
        weights = numpy.asarray(dstore['weights'][()], dtype=float)
        gmfs = dstore.read_df('gmf_data')
        version = dstore.hdf5.attrs.get('engine_version', 'unknown')
        if isinstance(version, bytes):
            version = version.decode('utf-8')
        metadata = {'engine_version': str(version),
                    'effective_rupture': _effective_rupture(dstore),
                    'branch_models': _branch_models(dstore)}
    return sites, mapping, weights, gmfs, metadata


def _validate_inputs(sites, events, weights, gmfs):
    # Reject invalid IDs, weights, values, or duplicated site/event pairs.
    if not len(sites) or not len(events) or not len(gmfs):
        raise ValueError('Sites, events, and ground-motion fields must exist')
    if sites.site_id.duplicated().any() or events.event_id.duplicated().any():
        raise ValueError('Site IDs and event IDs must be unique')
    if not numpy.isfinite(sites[['lon', 'lat']].to_numpy()).all():
        raise ValueError('Site coordinates must be finite')
    if not sites.lon.between(-180, 180).all():
        raise ValueError('Site longitudes must be between -180 and 180')
    if not sites.lat.between(-90, 90).all():
        raise ValueError('Site latitudes must be between -90 and 90')
    if weights.ndim != 1 or not len(weights):
        raise ValueError('Expected one scalar weight per realization')
    if not numpy.isfinite(weights).all() or (weights < 0).any():
        raise ValueError('Realization weights must be finite and nonnegative')
    if not numpy.isclose(weights.sum(), 1.0, rtol=0, atol=1e-6):
        raise ValueError('Stored realization weights must sum to one')
    branches = numpy.arange(len(weights))
    if not numpy.array_equal(numpy.unique(events.rlz_id), branches):
        raise ValueError('Event realization IDs must match stored weights')
    if not {'sid', 'eid', 'PGA'}.issubset(gmfs.columns):
        raise ValueError('gmf_data must contain sid, eid, and PGA columns')
    if gmfs[['sid', 'eid', 'PGA']].isna().any().any():
        raise ValueError('GMF identifiers and PGA cannot be missing')
    pga = gmfs.PGA.to_numpy(dtype=float)
    if not numpy.isfinite(pga).all() or (pga < 0).any():
        raise ValueError('PGA must be finite and nonnegative, in g')
    if gmfs.duplicated(['sid', 'eid']).any():
        raise ValueError('Repeated site/event GMF pairs')
    if not gmfs.sid.isin(sites.site_id).all():
        raise ValueError('GMFs refer to site IDs absent from sitecol')
    if not gmfs.eid.isin(events.event_id).all():
        raise ValueError('GMFs refer to event IDs absent from events')


def _site_means(sites, events, weights, gmfs):
    # Average within branches before weighting; event counts are not weights.
    rows = gmfs[['sid', 'eid', 'PGA']].copy()
    rows['PGA'] = rows.PGA.astype(float)
    rows = rows.merge(
        events, left_on='eid', right_on='event_id', validate='many_to_one')
    branch_counts = events.groupby('rlz_id').size()
    grouped = rows.groupby(['sid', 'rlz_id']).PGA.agg(['mean', 'count'])
    active_ids = numpy.sort(rows.sid.unique())
    counts = grouped['count'].unstack('rlz_id').reindex(
        index=active_ids, columns=numpy.arange(len(weights)), fill_value=0)
    expected = branch_counts.reindex(numpy.arange(len(weights))).to_numpy()
    if not numpy.equal(counts.fillna(0).to_numpy(), expected).all():
        raise ValueError('Incomplete GMFs for a site/realization. Sparse or '
                         'threshold-filtered GMFs need explicit treatment; '
                         'this script will not assume absent values are zero.')
    means = grouped['mean'].unstack('rlz_id').reindex(
        index=sites.site_id, columns=numpy.arange(len(weights)))
    out = sites.copy()
    missing = ~sites.site_id.isin(active_ids)
    out['gmf_status'] = numpy.where(missing, 'no_gmfs', 'complete')
    for branch in range(len(weights)):
        out[f'pga_mean_rlz_{branch}_g'] = means[branch].to_numpy()
        out[f'gmf_count_rlz_{branch}'] = numpy.where(
            missing, 0, expected[branch])
    out['pga_weighted_mean_g'] = means.to_numpy().dot(weights)
    return out, branch_counts


def _plot_map(sites, weights, branch_counts, trace, rupture, models,
              output_dir):
    # Preserve geographic coordinates and correct longitude scale locally.
    fig, ax = pyplot.subplots(figsize=(9, 6.7), layout='constrained')
    complete = sites.gmf_status == 'complete'
    shown = sites[complete]
    pga = ax.scatter(shown.lon, shown.lat, c=shown.pga_weighted_mean_g,
                     cmap='viridis', s=65, edgecolors='black', linewidths=0.3,
                     zorder=3)
    fig.colorbar(pga, ax=ax, label='Weighted arithmetic mean PGA (g)')
    missing = sites[~complete]
    if len(missing):
        ax.scatter(missing.lon, missing.lat, marker='x', color='gray',
                   label='Sites without GMFs (excluded)', zorder=4)
    ax.plot(trace[:, 0], trace[:, 1], color='firebrick', linewidth=2,
            label='Fault trace from rupture XML', zorder=5)
    effective = rupture['effective_engine']
    epicentre = [effective['epicentre_lon'], effective['epicentre_lat']]
    ax.scatter(*epicentre, marker='*', s=200, color='red',
               edgecolors='black', label='Effective engine epicentre',
               zorder=6)
    if rupture['hypocentre_moved']:
        supplied = rupture['supplied_xml']
        ax.scatter(supplied['epicentre_lon'], supplied['epicentre_lat'],
                   marker='o', s=90, facecolors='none', edgecolors='red',
                   linewidths=1.5, label='Supplied hypocentre projection',
                   zorder=6)
    mean_lat = float(sites.lat.mean())
    ax.set_aspect(1.0 / numpy.cos(numpy.radians(mean_lat)))
    branches = '; '.join(f'{models[i]}: {weight:g}'
                         for i, weight in enumerate(weights))
    counts = sorted(set(branch_counts.to_list()))
    count_text = (f'{counts[0]} GMFs per branch' if len(counts) == 1
                  else f'{len(sites)} sites; unequal GMF counts per branch')
    ax.set_title('Scenario shaking: weighted mean PGA\n'
                 f'Weights {branches}\n{count_text}',
                 fontsize=11)
    ax.set_xlabel('Longitude (degrees east)')
    ax.set_ylabel('Latitude (degrees north)')
    ax.grid(alpha=0.25)
    ax.margins(0.08)
    ax.legend(loc='best', fontsize=8)
    note = 'PGA is not a JMA/MMI intensity classification. No basemap.'
    if rupture['hypocentre_moved']:
        note += '\n' + rupture['hypocentre_adjustment_note']
    fig.supxlabel(note, fontsize=8)
    paths = [output_dir / f'shaking_pga.{extension}'
             for extension in ('png', 'pdf')]
    for path in paths:
        fig.savefig(path, dpi=200)
    pyplot.close(fig)
    return paths


def _summary(sites, events, weights, gmfs, counts, metadata, rupture):
    # Include all omitted sites and branch statistics for an auditable handoff.
    complete = sites.gmf_status == 'complete'
    pga = sites.loc[complete, 'pga_weighted_mean_g']
    branches = []
    for branch, weight in enumerate(weights):
        values = sites.loc[complete, f'pga_mean_rlz_{branch}_g']
        branches.append({'rlz_id': branch, 'weight': float(weight),
                         'gsim': metadata['branch_models'][branch],
                         'event_count': int(counts[branch]),
                         'mean_pga_min_g': float(values.min()),
                         'mean_pga_max_g': float(values.max())})
    return {'engine_version': metadata['engine_version'],
            'imt': 'PGA', 'units': 'g',
            'aggregation': 'Arithmetic mean of all sampled GMFs within '
                           'each realization, then stored-weight mean of '
                           'those branch means; not JMA or MMI intensity.',
            'site_count': len(sites), 'event_count': len(events),
            'gmf_row_count': len(gmfs),
            'expected_complete_gmf_row_count': len(sites) * len(events),
            'mapped_site_count': int(complete.sum()),
            'missing_site_count': int((~complete).sum()),
            'missing_site_ids': sites.loc[~complete, 'site_id'].tolist(),
            'missing_site_handling': 'Sites with no GMFs have blank means '
                                     'in CSV and are excluded from averaging. '
                                     'Partial event coverage is rejected.',
            'weighted_mean_pga_min_g': float(pga.min()),
            'weighted_mean_pga_max_g': float(pga.max()),
            'sampled_pga_min_g': float(gmfs.PGA.min()),
            'sampled_pga_max_g': float(gmfs.PGA.max()),
            'branches': branches, 'rupture': rupture}


def main():
    """Write a shaking map and inspectable statistics from hazard outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('datastore', type=Path,
                        help='Full hazard calculation HDF5 path')
    parser.add_argument('--rupture', type=Path, required=True,
                        help='Input rupture XML path')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    sites, events, weights, gmfs, metadata = _read_hazard(args.datastore)
    _validate_inputs(sites, events, weights, gmfs)
    means, counts = _site_means(sites, events, weights, gmfs)
    trace, _, supplied = _rupture_geometry(args.rupture)
    rupture = _rupture_details(supplied, metadata['effective_rupture'])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sites_path = args.output_dir / 'site_pga_means.csv'
    events_path = args.output_dir / 'event_realizations.csv'
    means.to_csv(sites_path, index=False, float_format='%.17g')
    events.sort_values('event_id').to_csv(events_path, index=False)
    plots = _plot_map(means, weights, counts, trace, rupture,
                      metadata['branch_models'], args.output_dir)
    summary = _summary(means, events, weights, gmfs, counts, metadata, rupture)
    summary['source_datastore'] = str(args.datastore.resolve())
    summary['source_rupture_xml'] = str(args.rupture.resolve())
    summary_path = args.output_dir / 'plot_summary.json'
    summary_path.write_text(json.dumps(summary, indent=2) + '\n',
                            encoding='utf-8')
    for path in [sites_path, events_path, *plots, summary_path]:
        print(path.resolve())


if __name__ == '__main__':
    main()
