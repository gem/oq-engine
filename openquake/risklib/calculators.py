import os
import itertools
import operator
import logging

import numpy

from openquake.risklib import api, utils, scientific, hazard_getters, writers

registry = utils.Register()

HG = hazard_getters.HazardGetter
log = logging.getLogger()

########################### classical ################################


@registry.add('classical')
def classical(input):
    raise NotImplementedError

######################### probabilistic_event_based #########################


@registry.add('probabilistic_event_based')
def probabilistic_event_based(input):
    raise NotImplementedError

########################### scenario_damage ###########################


def write(writer, tag, values):
    """
    Write mean and stddev of the values associated to the given tag
    by using the given writer.
    """
    mean, std = scientific.mean_std(values)
    writer.write(tag, mean, std)


def array_sum(arraylist):
    try:
        shape = arraylist[0].shape
    except (IndexError, AttributeError):
        return
    result = numpy.zeros(shape)
    for a in arraylist:
        if a is not None:
            result += a
    return result


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
        except KeyError:
            missing.append(asset)
            continue
        alist.append(asset)
        hlist.append(hazard)
    return alist, hlist, missing


@registry.add('scenario_damage')
def scenario_damage(input, runner):
    fm = input['fragility']
    outdir = input['export_dir']
    by_asset_csv = os.path.join(outdir, 'dmg_dist_by_asset.csv')
    by_taxonomy_csv = os.path.join(outdir, 'dmg_dist_by_taxonomy.csv')
    total_csv = os.path.join(outdir, 'dmg_dist_total.csv')
    damage_states = ['no_damage'] + fm.limit_states
    by_asset = writers.ScenarioDamageWriter(by_asset_csv, damage_states)
    by_taxonomy = writers.ScenarioDamageWriter(by_taxonomy_csv, damage_states)
    total = writers.ScenarioDamageWriter(total_csv, damage_states)
    exposure = input['exposure']
    gmf = input['gmf']
    hazard_getter = HG(gmf)
    ddpt = {}
    for taxonomy, assets in itertools.groupby(
            exposure, operator.attrgetter("taxonomy")):
        alist, hlist, missing = get_hazard(assets, hazard_getter)
        log.info('Taxonomy %s, %d assets, %d missing', taxonomy,
                 len(alist), len(missing))
        calc = api.ScenarioDamage(fm[taxonomy])
        fractions = [frac * asset.number_of_units for frac, asset in
                     zip(runner.run(calc, hlist), alist)]
        for asset, frac in zip(alist, fractions):
            write(by_asset, asset.asset_id, frac)
        ddpt[taxonomy] = array_sum(fractions)
    for taxonomy, fractions in ddpt.iteritems():
        write(by_taxonomy, taxonomy, fractions)
    write(total, 'total', array_sum(ddpt.values()))


############################## scenario ################################


@registry.add('scenario')
def scenario(input, runner):
    outdir = input['export_dir']
    vm = input['vulnerability']
    exposure = input['exposure']
    gmf = input['gmf']
    loss_map_csv = os.path.join(outdir, 'loss_map.csv')
    loss_map = writers.ScenarioWriter(loss_map_csv)
    hazard_getter = HG(gmf)
    for taxonomy, assets in itertools.groupby(
            exposure, operator.attrgetter("taxonomy")):
        calc = api.Scenario(vm[taxonomy])
        alist, hlist, missing = get_hazard(assets, hazard_getter)
        log.info('Taxonomy %s, %d assets, %d missing', taxonomy,
                 len(alist), len(missing))
        loss_ratios = runner.run(calc, hlist)
        for asset, loss_ratio in zip(alist, loss_ratios):
            write(loss_map, asset.asset_id, loss_ratio)
