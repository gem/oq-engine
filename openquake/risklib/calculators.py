import os
import itertools
import operator
import numpy

from openquake.risklib import api, utils, scientific, hazard_getters, writers

registry = utils.Register()

########################### classical ################################


@registry.add('classical')
def classical(input):
    raise NotImplementedError

######################### probabilistic_event_based #########################


@registry.add('probabilistic_event_based')
def probabilistic_event_based(input):
    raise NotImplementedError

########################### scenario_damage ###########################


def write(writer, id_, fractions):
    mean, std = scientific.mean_std(fractions)
    writer.write(id_, mean, std)


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
    hazard_getter = hazard_getters.HazardGetter(gmf)
    ddpt = {}
    for taxonomy, assets in itertools.groupby(
            exposure, operator.attrgetter("taxonomy")):
        calc = api.ScenarioDamage(fm[taxonomy])
        alist = list(assets)
        hlist = map(hazard_getter, (a.site for a in alist))
        fractions = [frac * asset.number_of_units for frac, asset in
                     zip(runner.run(calc, hlist), alist)]
        for asset, frac in zip(alist, fractions):
            write(by_asset, asset.asset_id, frac)
        print taxonomy, len(hlist)
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
    hazard_getter = hazard_getters.HazardGetter(gmf)
    for taxonomy, assets in itertools.groupby(
            exposure, operator.attrgetter("taxonomy")):
        calc = api.Scenario(vm[taxonomy])
        alist = list(assets)
        hlist = map(hazard_getter, (a.site for a in alist))
        loss_ratio_list = runner.run(calc, hlist)
        for asset, loss_ratio in zip(alist, loss_ratio_list):
            write(loss_map, asset.asset_id, loss_ratio)
