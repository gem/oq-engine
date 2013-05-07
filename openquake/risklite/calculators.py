import os
import itertools
import operator
import logging

from openquake.risklib import api, utils, scientific
from openquake.risklite import hazard_getters, writers

registry = utils.Register()

HG = hazard_getters.HazardGetter
log = logging.getLogger()

########################### classical ################################


@registry.add('classical')
def classical(ctxt, runner):
    raise NotImplementedError

######################### probabilistic_event_based #########################


@registry.add('probabilistic_event_based')
def probabilistic_event_based(ctxt, runner):
    raise NotImplementedError

########################### scenario_damage ###########################


def write(writer, tag, values):
    """
    Write mean and stddev of the values associated to the given tag
    by using the given writer.
    """
    mean, std = scientific.mean_std(values)
    writer.write(tag, mean, std)


def get_hazard(assets, hazard_getter):
    """
    :param assets:
      iterator over assets
    :param hazard_getter:
      callable returning the closest hazard for a site, if any
    :returns: three lists:
      the assets, the corresponding hazards and the missing assets,
      i.e. the one without a corresponding hazard.
    """
    alist = []
    hlist = []
    missing = []
    for asset in assets:
        try:
            hazard = hazard_getter(asset.site)
        except hazard_getters.MissingHazard:
            missing.append(asset)
            continue
        alist.append(asset)
        hlist.append(hazard)
    return alist, hlist, missing


@registry.add('scenario_damage')
def scenario_damage(ctxt, runner):
    fm = ctxt['fragility']
    outdir = ctxt['export_dir']
    by_asset_csv = os.path.join(outdir, 'dmg_dist_by_asset.csv')
    by_taxonomy_csv = os.path.join(outdir, 'dmg_dist_by_taxonomy.csv')
    total_csv = os.path.join(outdir, 'dmg_dist_total.csv')
    damage_states = ['no_damage'] + fm['limit_states']
    by_asset = writers.ScenarioDamageWriter(by_asset_csv, damage_states)
    by_taxonomy = writers.ScenarioDamageWriter(by_taxonomy_csv, damage_states)
    total = writers.ScenarioDamageWriter(total_csv, damage_states)
    exposure = ctxt['exposure']
    gmf = ctxt['gmf']
    hazard_getter = HG(gmf)
    ddpt = {}  # damage distribution per taxonomy dictionary

    for taxonomy, assets in itertools.groupby(
            exposure, operator.attrgetter("taxonomy")):
        alist, hlist, missing = get_hazard(assets, hazard_getter)
        log.info('Taxonomy %s, %d assets, %d missing', taxonomy,
                 len(alist), len(missing))
        calc = api.ScenarioDamage(fm['fragility_functions'][taxonomy]['fns'])
        fractions = [frac * asset.number_of_units for frac, asset in
                     zip(runner.run_in_order(calc, hlist), alist)]
        for asset, frac in zip(alist, fractions):
            write(by_asset, asset.asset_id, frac)
        if fractions:
            ddpt[taxonomy] = sum(fractions)
    for taxonomy, fractions in ddpt.iteritems():
        write(by_taxonomy, taxonomy, fractions)
    if ddpt:
        write(total, 'total', sum(ddpt.values()))


############################## scenario ################################


@registry.add('scenario')
def scenario(ctxt, runner):
    outdir = ctxt['export_dir']
    vm = ctxt['vulnerability']
    exposure = ctxt['exposure']
    gmf = ctxt['gmf']
    loss_map_csv = os.path.join(outdir, 'loss_map.csv')
    loss_map = writers.ScenarioWriter(loss_map_csv)
    hazard_getter = HG(gmf)
    for taxonomy, assets in itertools.groupby(
            exposure, operator.attrgetter("taxonomy")):
        calc = api.Scenario(vm[taxonomy])
        alist, hlist, missing = get_hazard(assets, hazard_getter)
        log.info('Taxonomy %s, %d assets, %d missing', taxonomy,
                 len(alist), len(missing))
        loss_ratios = runner.run_in_order(calc, hlist)
        for asset, loss_ratio in zip(alist, loss_ratios):
            write(loss_map, asset.asset_id, loss_ratio)
