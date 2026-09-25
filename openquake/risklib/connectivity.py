# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

# This module was prepared by:

# @author 1 . Astha Poudel, Early Stage Researcher, PhD candidate
# Aristotle University of Thessaloniki/Université Grenoble Alpes

# @author 2 . Anirudh Rao

# @author 3 . Catarina Costa

# The present work has been done in the framework of grant agreement No. 813137
# funded by the European Commission ITN-Marie Sklodowska-Curie project
# “New Challenges for Urban Engineering Seismology (URBASIS-EU)”.
# @author 1 has been funded by this project

from dataclasses import dataclass
import pandas as pd
import numpy as np
try:
    import networkx as nx
except ImportError:
    nx = None
import logging

from openquake.baselib import parallel


@dataclass
class Inp:
    """
    Connectivity inputs
    """
    id: int
    CCL: float
    PCL: float
    WCL: float
    effloss: float


@dataclass
class Out:
    """
    Connectivity outputs
    """
    cl: pd.DataFrame
    node_el: pd.DataFrame
    ccl_table: pd.DataFrame
    pcl_table: pd.DataFrame
    wcl_table: pd.DataFrame
    eff_table: pd.DataFrame
    event_connectivity_loss_ccl: pd.DataFrame
    event_connectivity_loss_pcl: pd.DataFrame
    event_connectivity_loss_wcl: pd.DataFrame
    event_connectivity_loss_eff: pd.DataFrame
    avg_connectivity_loss_ccl = 0
    avg_connectivity_loss_pcl = 0
    avg_connectivity_loss_wcl = 0
    avg_connectivity_loss_eff = 0
        

    @classmethod
    def new(cls, expo_df, nodes, eff_nodes, kind):
        assert kind in ('taz', 'demand'), kind
        t0 = expo_df[expo_df['purpose'].str.lower() == kind].iloc[:, 0:1]
        t1 = expo_df[expo_df['type'].str.lower() == 'node'].iloc[:, 0:1]

        t2 = pd.DataFrame({'id': nodes})
        t2.set_index('id', inplace=True)
        t3 = pd.DataFrame({'id': nodes})
        t3.set_index('id', inplace=True)
        t4 = pd.DataFrame({'id': nodes})
        t4.set_index('id', inplace=True)
        t5 = pd.DataFrame({'id': eff_nodes})
        t5.set_index('id', inplace=True)

        # Create empty dataframes with columns "event_id" and
        # "CCL"/"PCL"/"WCL"/"EL"
        t6 = pd.DataFrame(
            {'event_id': pd.Series(dtype=int), 'CCL': pd.Series(dtype=float)})
        t7 = pd.DataFrame(
            {'event_id': pd.Series(dtype=int), 'PCL': pd.Series(dtype=float)})
        t8 = pd.DataFrame(
            {'event_id': pd.Series(dtype=int), 'WCL': pd.Series(dtype=float)})
        t9 = pd.DataFrame(
            {'event_id': pd.Series(dtype=int), 'EL': pd.Series(dtype=float)})
        return cls(t0, t1, t2, t3, t4, t5, t6, t7, t8, t9)


def get_exposure_df(dstore):
    assetcol = dstore["assetcol"]
    tagnames = sorted(tn for tn in assetcol.tagnames if tn != "id")
    tags = {t: getattr(assetcol.tagcol, t) for t in tagnames}
    exposure_df = (
        assetcol.to_dframe()
        .replace(
            {
                tagname: {i: tag for i, tag in enumerate(tags[tagname])}
                for tagname in tagnames
            }
        )
    ).set_index("id")

    if 'weight' in exposure_df.columns:
        exposure_df['weight'] = exposure_df['weight'].astype(float)

    return exposure_df


def classify_nodes(exposure_df):
    # Classifying the nodes accodingly to compute performance indicator in
    # global and local level

    # TAZ is the acronym of "Traffic Analysis Zone"
    # user can write both as well
    TAZ_nodes = exposure_df.loc[
        exposure_df.purpose.str.lower().isin(["taz", "both"])].index.to_list()

    source_nodes = exposure_df.loc[
        exposure_df.purpose.str.lower() == "source"].index.to_list()
    demand_nodes = exposure_df.loc[
        exposure_df.purpose.str.lower() == "demand"].index.to_list()
    eff_nodes = exposure_df.loc[
        exposure_df.type.str.lower() == "node"].index.to_list()

    # Raise an error if the exposure nodes contain at the same time
    # TAZ and demand/supply nodes
    if TAZ_nodes and demand_nodes:
        raise ValueError(
            'The exposure can contain either taz/both nodes or'
            ' demand/supply nodes, but not both kinds at the same time.')

    return TAZ_nodes, source_nodes, demand_nodes, eff_nodes


def get_graph_type(exposure_df):
    # This is to handle different type of graph. If nothing is provided, OQ
    # will assume as simple undirected graph
    # If there is a column name "graphtype" they can specify the type in any
    # row
    if 'graphtype' in exposure_df.columns and exposure_df[
            'graphtype'].isin(['directed']).any():
        g_type = "DiGraph"
    elif 'graphtype' in exposure_df.columns and exposure_df[
            'graphtype'].isin(['multi']).any():
        g_type = "MultiGraph"
    elif 'graphtype' in exposure_df.columns and exposure_df[
            'graphtype'].isin(['multidirected']).any():
        g_type = "MultiDiGraph"
    else:
        g_type = "Graph"

    return g_type


def create_original_graph(exposure_df, g_type):
    # Create the original graph and add edge and node attributes.
    G_original = nx.from_pandas_edgelist(
        exposure_df.loc[exposure_df.type.str.lower() == "edge"],
        source="start_node",
        target="end_node",
        edge_attr=True, create_using=getattr(nx, g_type)()
    )
    # This is done for the cases where there might be a disconnected node with
    # no edges and are not added in the G_original previously
    for _, row in exposure_df.loc[
            exposure_df.type.str.lower() == "node"].iterrows():
        if row["id"] not in G_original.nodes:
            G_original.add_node(row["id"], **row)
    # Adding the attribute of the nodes
    nx.set_node_attributes(
        G_original, exposure_df.loc[
            exposure_df.type.str.lower() == "node"].to_dict("index")
    )

    return G_original


def get_damage_df(dstore, exposure_df):
    # Extracting the damage data from component level analysis
    agg_keys = pd.DataFrame({"id": [key.decode()
                                    for key in dstore["agg_keys"][:]]})
    damage_df = (
        dstore.read_df("risk_by_event", "event_id")
        .join(agg_keys.id, on="agg_id")
        .dropna(subset=["id"])
        .set_index("id", append=True)
        .drop(columns=["agg_id", "loss_id"])
        .sort_index(level=["event_id", "id"])
        .astype(int)
        .join(exposure_df)
        .assign(is_functional=lambda x: x.non_operational == 0)
    )[["type", "start_node", "end_node", "is_functional", "taxonomy"]]

    return damage_df


def analyze_taz_nodes(dstore, exposure_df, G_original, TAZ_nodes, eff_nodes,
                      damage_df, g_type, N):
    oq = dstore["oqparam"]
    taz_nodes_analysis_results = {}
    o = ELWCLPCLloss_TAZ(
        exposure_df, G_original, TAZ_nodes, eff_nodes, damage_df, g_type,
        oq.max_nodes_network, oq.concurrent_tasks, dstore.hdf5)
    sum_connectivity_loss_pcl = o.event_connectivity_loss_pcl['PCL'].sum()
    sum_connectivity_loss_wcl = o.event_connectivity_loss_wcl['WCL'].sum()
    if N <= oq.max_nodes_network:
        sum_connectivity_loss_eff = o.event_connectivity_loss_eff['EL'].sum()
    else:
        sum_connectivity_loss_eff = np.nan

    if oq.calculation_mode == "event_based_damage":
        inv_time = oq.investigation_time
        ses_per_ltp = oq.ses_per_logic_tree_path
        num_lt_samples = oq.number_of_logic_tree_samples
        eff_inv_time = inv_time * ses_per_ltp * num_lt_samples
        o.avg_connectivity_loss_pcl = (
            sum_connectivity_loss_pcl / eff_inv_time)
        o.avg_connectivity_loss_wcl = sum_connectivity_loss_wcl/eff_inv_time
        o.avg_connectivity_loss_eff = sum_connectivity_loss_eff/eff_inv_time
        o.cl["PCL_node"] /= eff_inv_time
        o.cl["WCL_node"] /= eff_inv_time
        if N <= oq.max_nodes_network:
            o.node_el["EL"] /= eff_inv_time
        else:
            o.node_el["EL"] = np.nan

    elif oq.calculation_mode == "scenario_damage":
        num_events = len(damage_df.reset_index().event_id.unique())
        o.avg_connectivity_loss_pcl = sum_connectivity_loss_pcl / num_events
        o.avg_connectivity_loss_wcl = sum_connectivity_loss_wcl / num_events
        o.avg_connectivity_loss_eff = sum_connectivity_loss_eff / num_events
        o.cl["PCL_node"] /= num_events
        o.cl["WCL_node"] /= num_events

        if N <= oq.max_nodes_network:
            o.node_el["EL"] /= num_events
        else:
            o.node_el["EL"] = np.nan

    o.cl.drop(columns=['ordinal'], inplace=True)
    o.node_el.drop(columns=['ordinal'], inplace=True)

    for result in [
            'avg_connectivity_loss_pcl', 'avg_connectivity_loss_wcl',
            'avg_connectivity_loss_eff',
            'event_connectivity_loss_pcl', 'event_connectivity_loss_wcl',
            'event_connectivity_loss_eff',
            'cl', 'node_el']:
        key = 'taz_cl' if result == 'cl' else result
        taz_nodes_analysis_results[key] = getattr(o, result)

    return taz_nodes_analysis_results


def analyze_demand_nodes(dstore, exposure_df, G_original, eff_nodes,
                         demand_nodes, source_nodes, damage_df, g_type,
                         calculation_mode):
    oq = dstore["oqparam"]
    demand_nodes_analysis_results = {}
    N = len(G_original)
    o = ELWCLPCLCCL_demand(
        exposure_df, G_original, eff_nodes, demand_nodes, source_nodes,
        damage_df, g_type, oq.max_nodes_network, oq.concurrent_tasks,
        dstore.hdf5)

    sum_connectivity_loss_ccl = o.event_connectivity_loss_ccl['CCL'].sum()
    sum_connectivity_loss_pcl = o.event_connectivity_loss_pcl['PCL'].sum()
    sum_connectivity_loss_wcl = o.event_connectivity_loss_wcl['WCL'].sum()
    if N <= oq.max_nodes_network:
        sum_connectivity_loss_eff = o.event_connectivity_loss_eff['EL'].sum()
    else:
        sum_connectivity_loss_eff = np.nan

    if calculation_mode == "event_based_damage":
        inv_time = oq.investigation_time
        ses_per_ltp = oq.ses_per_logic_tree_path
        num_lt_samples = oq.number_of_logic_tree_samples
        eff_inv_time = inv_time * ses_per_ltp * num_lt_samples
        o.avg_connectivity_loss_ccl = (
            sum_connectivity_loss_ccl / eff_inv_time)
        o.avg_connectivity_loss_pcl = (
            sum_connectivity_loss_pcl / eff_inv_time)
        o.avg_connectivity_loss_wcl = (
            sum_connectivity_loss_wcl / eff_inv_time)
        o.avg_connectivity_loss_eff = (
            sum_connectivity_loss_eff / eff_inv_time)
        o.cl["Isolation_node"] /= eff_inv_time
        o.cl["PCL_node"] /= eff_inv_time
        o.cl["WCL_node"] /= eff_inv_time
        if N <= oq.max_nodes_network:
            o.node_el["EL"] /= eff_inv_time
        else:
            o.node_el["EL"] = np.nan

    elif calculation_mode == "scenario_damage":
        num_events = len(damage_df.reset_index().event_id.unique())
        o.avg_connectivity_loss_ccl = sum_connectivity_loss_ccl / num_events
        o.avg_connectivity_loss_pcl = sum_connectivity_loss_pcl / num_events
        o.avg_connectivity_loss_wcl = sum_connectivity_loss_wcl / num_events
        o.avg_connectivity_loss_eff = sum_connectivity_loss_eff/num_events
        o.cl["Isolation_node"] /= num_events
        o.cl["PCL_node"] /= num_events
        o.cl["WCL_node"] /= num_events
        if N <= oq.max_nodes_network:
            o.node_el["EL"] /= num_events
        else:
            o.node_el["EL"] = np.nan

    o.cl.drop(columns=['ordinal'], inplace=True)
    o.node_el.drop(columns=['ordinal'], inplace=True)

    for result in [
            'avg_connectivity_loss_ccl', 'avg_connectivity_loss_pcl',
            'avg_connectivity_loss_wcl', 'avg_connectivity_loss_eff',
            'event_connectivity_loss_ccl', 'event_connectivity_loss_pcl',
            'event_connectivity_loss_wcl', 'event_connectivity_loss_eff',
            'cl', 'node_el']:
        key = 'dem_cl' if result == 'cl' else result
        demand_nodes_analysis_results[key] = getattr(o, result)

    return demand_nodes_analysis_results


def analyze_generic_nodes(dstore, exposure_df, G_original, eff_nodes,
                          damage_df, g_type):
    oq = dstore["oqparam"]
    generic_nodes_analysis_results = {}
    N = len(G_original)
    node_el, event_connectivity_loss_eff = EL_node(
        exposure_df, G_original, eff_nodes, damage_df, g_type,
        oq.max_nodes_network, oq.concurrent_tasks, dstore.hdf5)

    if N <= oq.max_nodes_network:
        sum_connectivity_loss_eff = event_connectivity_loss_eff['EL'].sum()
    else:
        sum_connectivity_loss_eff = np.nan

    if oq.calculation_mode == "event_based_damage":
        inv_time = oq.investigation_time
        ses_per_ltp = oq.ses_per_logic_tree_path
        num_lt_samples = oq.number_of_logic_tree_samples
        eff_inv_time = inv_time * ses_per_ltp * num_lt_samples
        avg_connectivity_loss_eff = sum_connectivity_loss_eff/eff_inv_time
        if N <= oq.max_nodes_network:
            node_el["EL"] /= eff_inv_time
        else:
            node_el["EL"] = np.nan

    elif oq.calculation_mode == "scenario_damage":
        num_events = len(damage_df.reset_index().event_id.unique())
        avg_connectivity_loss_eff = sum_connectivity_loss_eff/num_events
        if N <= oq.max_nodes_network:
            node_el["EL"] /= num_events
        else:
            node_el["EL"] = np.nan

    node_el.drop(columns=['ordinal'], inplace=True)

    for result in [
            'avg_connectivity_loss_eff',
            'event_connectivity_loss_eff',
            'node_el']:
        generic_nodes_analysis_results[result] = locals()[result]

    return generic_nodes_analysis_results


def cleanup_graph(G_original, event_damage_df, g_type):
    # Making a copy of original graph for each event for the analysis
    G = G_original.copy()
    nodes_damage_df = event_damage_df.loc[
        event_damage_df.type.str.lower() == "node"].droplevel(level=0)
    edges_damage_df = event_damage_df.loc[
        event_damage_df.type.str.lower() == "edge"].droplevel(level=0)

    # Updating the graph to remove damaged edges and nodes
    nonfunctional_edges_df = edges_damage_df.loc[
        ~edges_damage_df.is_functional]
    nonfunctional_nodes_df = nodes_damage_df.loc[
        ~nodes_damage_df.is_functional]

    nonfunctional_edge_ids = set(nonfunctional_edges_df.index)
    nonfunctional_node_ids = list(nonfunctional_nodes_df.index)

    # This is done to handle multigraphs, where more than one edge can exist
    # between the same two nodes and each edge has a key value.
    if g_type in ["MultiGraph", "MultiDiGraph"]:
        edges_to_remove = [
            (u, v, key)
            for (u, v, key, data) in G.edges(keys=True, data=True)
            if data['id'] in nonfunctional_edge_ids]
    else:
        edges_to_remove = [
            (u, v)
            for (u, v, data) in G.edges(data=True)
            if data['id'] in nonfunctional_edge_ids]

    G.remove_edges_from(edges_to_remove)
    G.remove_nodes_from(nonfunctional_node_ids)
    return G


def calc_weighted_connectivity_loss(
        graph, att, nodes_from, nodes_to, wcl_table, pcl_table, ws, ns):
    # For calculating weighted connectivity loss
    nodes_to = list(nodes_to)
    _, reciprocal_distance_sum, _ = _source_target_metrics(
        graph, att, nodes_from, nodes_to)

    for target in nodes_to:
        wcl_table.at[target, ws] = (
            reciprocal_distance_sum[target] * pcl_table.at[target, ns])

    return wcl_table



def _efficiency_values(graph, N, att, max_nodes_network,
                       precomputed=None):
    """Return nodal efficiency values without calculating efficiency loss."""
    if N > max_nodes_network:
        return None

    if precomputed is None:
        precomputed = {}

    values = {}
    for node in graph:
        if node in precomputed:
            # Reuse the shortest-path traversal already performed while
            # calculating CCL/PCL/WCL for this source node.
            eff_node = precomputed[node]
        elif not att:
            lengths = nx.single_source_shortest_path_length(graph, node)
            inv = [1/x for x in lengths.values() if x != 0]
            eff_node = sum(inv) / (N - 1)
        else:
            lengths = nx.single_source_dijkstra_path_length(
                graph, node, weight='weight')
            inv = [1/x for x in lengths.values() if x != 0]
            eff_node = sum(inv) / (N - 1)

        values[node] = eff_node

    return values


def calc_efficiency(graph, N, att, eff_table, eff, max_nodes_network,
                    precomputed=None):
    # For calculating efficiency
    # Important: If the weight is not provided, then the weight of each edge
    # is considered to be one.
    if N > max_nodes_network:
        eff_table = pd.DataFrame([[np.nan, np.nan, np.nan]],
                                 columns=['Eff0', 'Eff', 'EL'])
        eff_table.index.names = ['id']
    else:
        values = _efficiency_values(
            graph, N, att, max_nodes_network, precomputed)
        for node, eff_node in values.items():
            eff_table.at[node, eff] = eff_node

        if eff == 'Eff':
            # This is done so that if the initial graph has a disconnected
            # node, the efficiency-loss calculation does not divide by zero.
            eff_table['EL'] = (eff_table.Eff0 - eff_table.Eff) / \
                eff_table.Eff0.replace({0: np.nan})
            eff_table['EL'] = eff_table['EL'].fillna(0)

    return eff_table


def analysis(dstore):
    """
    Postprocessor for the connectivity analysis
    """
    connectivity_results = {}
    oq = dstore["oqparam"]
    calculation_mode = oq.calculation_mode
    assert calculation_mode in ("event_based_damage", "scenario_damage")
    exposure_df = get_exposure_df(dstore)

    logging.info('Classifying nodes')
    (TAZ_nodes, source_nodes,
     demand_nodes, eff_nodes) = classify_nodes(exposure_df)

    g_type = get_graph_type(exposure_df)
    exposure_df['id'] = exposure_df.index
    G_original = create_original_graph(exposure_df, g_type)
    damage_df = get_damage_df(dstore, exposure_df)
    N = len(G_original)
    # Calling the function according to the specification of the node type
    if TAZ_nodes:
        # if the nodes acts as both supply or demand (for example: traffic
        # analysis zone in transportation network)
        logging.info('Analyzing TAZ nodes')
        taz_nodes_analysis_results = analyze_taz_nodes(
            dstore, exposure_df, G_original, TAZ_nodes, eff_nodes, damage_df,
            g_type, N)
        connectivity_results.update(taz_nodes_analysis_results)
    elif demand_nodes:
        # This is the classic and mostly used when supply/source and
        # demand/sink is explicity mentioned to the nodes of interest
        logging.info('Analyzing demand nodes')
        demand_nodes_analysis_results = analyze_demand_nodes(
            dstore, exposure_df, G_original, eff_nodes, demand_nodes,
            source_nodes, damage_df, g_type, calculation_mode)
        connectivity_results.update(demand_nodes_analysis_results)
    else:
        # if nothing is mentioned in case of scarce data or every node is
        # important and no distinction can be made
        logging.info('Analyzing generic nodes')
        generic_nodes_analysis_results = analyze_generic_nodes(
            dstore, exposure_df, G_original, eff_nodes, damage_df, g_type)
        connectivity_results.update(generic_nodes_analysis_results)

    return connectivity_results


def _mean_skipna(values):
    """Return the mean ignoring NaNs, matching pandas Series.mean()."""
    values = np.asarray(values, dtype=float)
    valid = ~np.isnan(values)
    if not valid.any():
        return np.nan
    return values[valid].mean()


def _loss_ratio(current, original):
    """Return ``1 - current / original`` without raising on zero values."""
    with np.errstate(divide='ignore', invalid='ignore'):
        return 1 - np.divide(current, original)


def _add_skipna(total, values):
    """Accumulate values as pandas groupby(...).sum() would for NaNs."""
    total += np.where(np.isnan(values), 0.0, values)


def _efficiency_baseline(eff_table, enabled):
    """Return the small immutable efficiency baseline sent to workers."""
    if not enabled:
        return {
            'eff_ids': None,
            'eff0': None,
            'eff0_mean': np.nan,
        }

    eff_ids = eff_table.index.to_numpy(copy=True)
    eff0 = eff_table['Eff0'].to_numpy(dtype=float, copy=True)
    return {
        'eff_ids': eff_ids,
        'eff0': eff0,
        'eff0_mean': _mean_skipna(eff0),
    }


def _efficiency_loss_arrays(eff_values, baseline, eff_index):
    """Return event-level and nodal efficiency loss from raw efficiencies."""
    eff0 = baseline['eff0']
    if eff0 is None:
        return np.nan, None

    eff = np.zeros(len(eff0), dtype=float)
    for node, value in eff_values.items():
        idx = eff_index.get(node)
        if idx is not None:
            eff[idx] = value

    el_node = np.zeros(len(eff0), dtype=float)
    nonzero = eff0 != 0
    el_node[nonzero] = (
        (eff0[nonzero] - eff[nonzero]) / eff0[nonzero])

    glo_eff = _mean_skipna(eff)
    with np.errstate(divide='ignore', invalid='ignore'):
        glo_el = np.divide(
            baseline['eff0_mean'] - glo_eff,
            baseline['eff0_mean'])
    return float(glo_el), el_node


def _ordered_blocks(block_results, event_order):
    """Order task results by their first event in the original OQ sequence."""
    event_index = pd.Index(event_order)
    ranked = []
    for result in block_results:
        positions = event_index.get_indexer(result['event_id'])
        if (positions < 0).any():
            raise RuntimeError('Unexpected connectivity event result')
        first = positions.min() if len(positions) else len(event_order)
        ranked.append((first, result))
    ranked.sort(key=lambda item: item[0])
    return [result for _, result in ranked]


def _ordered_event_metrics(block_results, event_order, metric_names):
    """Concatenate block results and restore the original event ordering."""
    event_ids = np.concatenate(
        [result['event_id'] for result in block_results])
    expected = np.asarray(event_order)
    event_index = pd.Index(expected)
    positions = event_index.get_indexer(event_ids)

    if (len(event_ids) != len(expected) or (positions < 0).any() or
            len(np.unique(positions)) != len(expected)):
        raise RuntimeError('Missing or duplicated connectivity event results')

    order = np.argsort(positions, kind='stable')
    if not np.array_equal(positions[order], np.arange(len(expected))):
        raise RuntimeError('Connectivity event results are out of sequence')

    metrics = {}
    for name in metric_names:
        values = np.concatenate(
            [result[name] for result in block_results])
        metrics[name] = values[order]
    return expected, metrics


def _sum_block_metric(block_results, key, size):
    """Sum block-level nodal arrays in deterministic block order."""
    total = np.zeros(size, dtype=float)
    for result in block_results:
        values = result.get(key)
        if values is not None:
            total += values
    return total


def _sort_node_output(df):
    """Preserve the node ordering produced by the previous implementation."""
    return df.sort_values('id', kind='stable').reset_index(drop=True)


def _validate_baseline_connectivity(ns0, nodes, mode):
    """Ensure every analysed node has a valid connectivity baseline."""
    disconnected = [node for node in nodes if ns0[node] == 0]
    if not disconnected:
        return

    preview = disconnected[:10]
    suffix = '' if len(disconnected) <= 10 else ' ...'
    if mode == 'demand':
        relation = 'to any source node'
        node_kind = 'demand'
    elif mode == 'taz':
        relation = 'to any other TAZ node'
        node_kind = 'TAZ'
    else:
        raise ValueError(f'Unknown connectivity validation mode: {mode}')

    raise ValueError(
        f'{len(disconnected)} {node_kind} node(s) are not connected {relation} '
        'in the undamaged network. PCL and WCL require a positive NS0 '
        f'baseline for every analysed node. Node IDs: {preview}{suffix}')


def ELWCLPCLCCL_demand(expo_df, G_original, eff_nodes, demand_nodes,
                       source_nodes, damage_df, g_type, max_nodes_network,
                       concurrent_tasks=None, h5=None):
    # Classic case where particular nodes are divided as supply or demand.
    o = Out.new(expo_df, demand_nodes, eff_nodes, 'demand')

    att = nx.get_edge_attributes(G_original, 'weight')
    weighted = bool(att)
    N = len(G_original)

    # One shortest-path tree per source supplies CNO, NS0 and WS0 together.
    # When efficiency is enabled, also reuse those same trees for Eff0.
    eff_N = N if N <= max_nodes_network else None
    ns0, invdist0, source_eff0 = _source_target_metrics(
        G_original, att, source_nodes, demand_nodes, N=eff_N)
    _validate_baseline_connectivity(ns0, demand_nodes, 'demand')

    for node in demand_nodes:
        o.ccl_table.at[node, 'CNO'] = 1 if ns0[node] else 0
        o.pcl_table.at[node, 'NS0'] = ns0[node]
        o.wcl_table.at[node, 'WS0'] = invdist0[node] * ns0[node]

    o.eff_table = calc_efficiency(
        G_original, N, att, o.eff_table, 'Eff0', max_nodes_network,
        precomputed=source_eff0)

    efficiency_enabled = N <= max_nodes_network
    baseline = {
        'cno_sum': float(o.ccl_table['CNO'].sum()),
        'ns0': o.pcl_table['NS0'].to_numpy(dtype=float, copy=True),
        'ws0': o.wcl_table['WS0'].to_numpy(dtype=float, copy=True),
    }
    baseline.update(_efficiency_baseline(o.eff_table, efficiency_enabled))

    logging.info('Checking for every event after earthquake')
    events = damage_df.groupby('event_id', sort=False)
    event_order = damage_df.index.get_level_values(
        'event_id').unique().to_numpy()
    num_events = events.ngroups

    # For the serial/nested-worker path process all events as a single block.
    if concurrent_tasks == 0 or parallel.Starmap.on or num_events <= 1:
        block_results = [_process_demand_block(
            events, G_original, g_type, source_nodes, demand_nodes, N,
            weighted, max_nodes_network, baseline)]
    else:
        smap = parallel.Starmap.apply(
            process_demand_events,
            (events, G_original, g_type, source_nodes, demand_nodes, N,
             weighted, max_nodes_network, baseline),
            concurrent_tasks=concurrent_tasks, h5=h5)
        # Drain Starmap before doing the final pandas formatting/reduction.
        block_results = list(smap)

    return _merge_demand_blocks(
        o, block_results, event_order, demand_nodes, baseline,
        efficiency_enabled)


def _process_demand_block(
        event_block, G_original, g_type, source_nodes, demand_nodes, N,
        weighted, max_nodes_network, baseline):
    """Calculate event losses and block nodal sums for demand/source mode."""
    event_ids = []
    event_ccl = []
    event_pcl = []
    event_wcl = []
    event_el = []

    isolation_sum = np.zeros(len(demand_nodes), dtype=float)
    pcl_sum = np.zeros(len(demand_nodes), dtype=float)
    wcl_sum = np.zeros(len(demand_nodes), dtype=float)

    eff_ids = baseline['eff_ids']
    eff_index = ({node: idx for idx, node in enumerate(eff_ids)}
                 if eff_ids is not None else {})
    el_sum = (np.zeros(len(eff_ids), dtype=float)
              if eff_ids is not None else None)
    eff_N = N if baseline['eff0'] is not None else None

    for event_id, event_damage_df in event_block:
        G = cleanup_graph(G_original, event_damage_df, g_type)
        graph_nodes = set(G.nodes)
        extant_source_nodes = set(source_nodes) & graph_nodes
        extant_demand_nodes = sorted(set(demand_nodes) & graph_nodes)

        ns_values, invdist, source_eff = _source_target_metrics(
            G, weighted, extant_source_nodes, extant_demand_nodes, N=eff_N)

        ns = np.array(
            [ns_values.get(node, 0) for node in demand_nodes], dtype=float)
        ws = np.array(
            [invdist.get(node, 0.0) * ns_values.get(node, 0)
             for node in demand_nodes], dtype=float)
        cns = (ns > 0).astype(float)

        pcl_node = _loss_ratio(ns, baseline['ns0'])
        wcl_node = _loss_ratio(ws, baseline['ws0'])
        isolation_node = 1 - cns

        ccl = _loss_ratio(cns.sum(), baseline['cno_sum'])
        pcl = _mean_skipna(pcl_node)
        wcl = _mean_skipna(wcl_node)

        if eff_N is None:
            glo_el, el_node = np.nan, None
        else:
            eff_values = _efficiency_values(
                G, N, weighted, max_nodes_network,
                precomputed=source_eff)
            glo_el, el_node = _efficiency_loss_arrays(
                eff_values, baseline, eff_index)

        event_ids.append(event_id)
        event_ccl.append(ccl)
        event_pcl.append(pcl)
        event_wcl.append(wcl)
        event_el.append(glo_el)

        isolation_sum += isolation_node
        _add_skipna(pcl_sum, pcl_node)
        _add_skipna(wcl_sum, wcl_node)
        if el_sum is not None:
            el_sum += el_node

    return {
        'event_id': np.asarray(event_ids),
        'CCL': np.asarray(event_ccl, dtype=float),
        'PCL': np.asarray(event_pcl, dtype=float),
        'WCL': np.asarray(event_wcl, dtype=float),
        'EL': np.asarray(event_el, dtype=float),
        'Isolation_node': isolation_sum,
        'PCL_node': pcl_sum,
        'WCL_node': wcl_sum,
        'EL_node': el_sum,
    }


def process_demand_events(
        event_block, G_original, g_type, source_nodes, demand_nodes, N,
        weighted, max_nodes_network, baseline, monitor):
    """Process one Starmap block for demand/source connectivity."""
    return _process_demand_block(
        event_block, G_original, g_type, source_nodes, demand_nodes, N,
        weighted, max_nodes_network, baseline)


def _merge_demand_blocks(
        o, block_results, event_order, demand_nodes, baseline,
        efficiency_enabled):
    """Merge compact demand/source block results in the master process."""
    block_results = _ordered_blocks(block_results, event_order)
    event_ids, metrics = _ordered_event_metrics(
        block_results, event_order, ('CCL', 'PCL', 'WCL', 'EL'))

    o.event_connectivity_loss_ccl = pd.DataFrame({
        'event_id': event_ids, 'CCL': metrics['CCL']})
    o.event_connectivity_loss_pcl = pd.DataFrame({
        'event_id': event_ids, 'PCL': metrics['PCL']})
    o.event_connectivity_loss_wcl = pd.DataFrame({
        'event_id': event_ids, 'WCL': metrics['WCL']})
    o.event_connectivity_loss_eff = pd.DataFrame({
        'event_id': event_ids, 'EL': metrics['EL']})

    o.cl = _sort_node_output(pd.DataFrame({
        'id': demand_nodes,
        'ordinal': np.zeros(len(demand_nodes), dtype=int),
        'Isolation_node': _sum_block_metric(
            block_results, 'Isolation_node', len(demand_nodes)),
        'PCL_node': _sum_block_metric(
            block_results, 'PCL_node', len(demand_nodes)),
        'WCL_node': _sum_block_metric(
            block_results, 'WCL_node', len(demand_nodes)),
    }))

    if efficiency_enabled:
        eff_ids = baseline['eff_ids']
        o.node_el = _sort_node_output(pd.DataFrame({
            'id': eff_ids,
            'ordinal': np.zeros(len(eff_ids), dtype=int),
            'EL': _sum_block_metric(
                block_results, 'EL_node', len(eff_ids)),
        }))
    return o


def ELWCLPCLloss_TAZ(expo_df, G_original, TAZ_nodes,
                     eff_nodes, damage_df, g_type, max_nodes_network,
                     concurrent_tasks=None, h5=None):
    # When the nodes act as both demand and supply, for example traffic
    # analysis zones in a transportation network.
    o = Out.new(expo_df, TAZ_nodes, eff_nodes, 'taz')

    att = nx.get_edge_attributes(G_original, 'weight')
    weighted = bool(att)
    N = len(G_original)

    eff_N = N if N <= max_nodes_network else None
    ns0, invdist0, source_eff0 = _source_target_metrics(
        G_original, att, TAZ_nodes, TAZ_nodes,
        exclude_self=True, N=eff_N)
    _validate_baseline_connectivity(ns0, TAZ_nodes, 'taz')

    for node in TAZ_nodes:
        o.pcl_table.at[node, 'NS0'] = ns0[node]
        o.wcl_table.at[node, 'WS0'] = invdist0[node] * ns0[node]

    o.eff_table = calc_efficiency(
        G_original, N, att, o.eff_table, 'Eff0', max_nodes_network,
        precomputed=source_eff0)

    efficiency_enabled = N <= max_nodes_network
    baseline = {
        'ns0': o.pcl_table['NS0'].to_numpy(dtype=float, copy=True),
        'ws0': o.wcl_table['WS0'].to_numpy(dtype=float, copy=True),
    }
    baseline.update(_efficiency_baseline(o.eff_table, efficiency_enabled))

    logging.info('Checking for every event after earthquake')
    events = damage_df.groupby('event_id', sort=False)
    event_order = damage_df.index.get_level_values(
        'event_id').unique().to_numpy()
    num_events = events.ngroups

    if concurrent_tasks == 0 or parallel.Starmap.on or num_events <= 1:
        block_results = [_process_taz_block(
            events, G_original, g_type, TAZ_nodes, N, weighted,
            max_nodes_network, baseline)]
    else:
        smap = parallel.Starmap.apply(
            process_taz_events,
            (events, G_original, g_type, TAZ_nodes, N, weighted,
             max_nodes_network, baseline),
            concurrent_tasks=concurrent_tasks, h5=h5)
        block_results = list(smap)

    return _merge_taz_blocks(
        o, block_results, event_order, TAZ_nodes, baseline,
        efficiency_enabled)


def _process_taz_block(
        event_block, G_original, g_type, TAZ_nodes, N, weighted,
        max_nodes_network, baseline):
    """Calculate event losses and block nodal sums for TAZ mode."""
    event_ids = []
    event_pcl = []
    event_wcl = []
    event_el = []

    pcl_sum = np.zeros(len(TAZ_nodes), dtype=float)
    wcl_sum = np.zeros(len(TAZ_nodes), dtype=float)

    eff_ids = baseline['eff_ids']
    eff_index = ({node: idx for idx, node in enumerate(eff_ids)}
                 if eff_ids is not None else {})
    el_sum = (np.zeros(len(eff_ids), dtype=float)
              if eff_ids is not None else None)
    eff_N = N if baseline['eff0'] is not None else None

    for event_id, event_damage_df in event_block:
        G = cleanup_graph(G_original, event_damage_df, g_type)
        graph_nodes = set(G.nodes)
        extant_TAZ_nodes = sorted(set(TAZ_nodes) & graph_nodes)

        ns_values, invdist, source_eff = _source_target_metrics(
            G, weighted, extant_TAZ_nodes, extant_TAZ_nodes,
            exclude_self=True, N=eff_N)

        ns = np.array(
            [ns_values.get(node, 0) for node in TAZ_nodes], dtype=float)
        ws = np.array(
            [invdist.get(node, 0.0) * ns_values.get(node, 0)
             for node in TAZ_nodes], dtype=float)

        pcl_node = _loss_ratio(ns, baseline['ns0'])
        wcl_node = _loss_ratio(ws, baseline['ws0'])
        pcl = _mean_skipna(pcl_node)
        wcl = _mean_skipna(wcl_node)

        if eff_N is None:
            glo_el, el_node = np.nan, None
        else:
            eff_values = _efficiency_values(
                G, N, weighted, max_nodes_network,
                precomputed=source_eff)
            glo_el, el_node = _efficiency_loss_arrays(
                eff_values, baseline, eff_index)

        event_ids.append(event_id)
        event_pcl.append(pcl)
        event_wcl.append(wcl)
        event_el.append(glo_el)

        _add_skipna(pcl_sum, pcl_node)
        _add_skipna(wcl_sum, wcl_node)
        if el_sum is not None:
            el_sum += el_node

    return {
        'event_id': np.asarray(event_ids),
        'PCL': np.asarray(event_pcl, dtype=float),
        'WCL': np.asarray(event_wcl, dtype=float),
        'EL': np.asarray(event_el, dtype=float),
        'PCL_node': pcl_sum,
        'WCL_node': wcl_sum,
        'EL_node': el_sum,
    }


def process_taz_events(
        event_block, G_original, g_type, TAZ_nodes, N, weighted,
        max_nodes_network, baseline, monitor):
    """Process one Starmap block for TAZ connectivity."""
    return _process_taz_block(
        event_block, G_original, g_type, TAZ_nodes, N, weighted,
        max_nodes_network, baseline)


def _merge_taz_blocks(
        o, block_results, event_order, TAZ_nodes, baseline,
        efficiency_enabled):
    """Merge compact TAZ block results in the master process."""
    block_results = _ordered_blocks(block_results, event_order)
    event_ids, metrics = _ordered_event_metrics(
        block_results, event_order, ('PCL', 'WCL', 'EL'))

    o.event_connectivity_loss_pcl = pd.DataFrame({
        'event_id': event_ids, 'PCL': metrics['PCL']})
    o.event_connectivity_loss_wcl = pd.DataFrame({
        'event_id': event_ids, 'WCL': metrics['WCL']})
    o.event_connectivity_loss_eff = pd.DataFrame({
        'event_id': event_ids, 'EL': metrics['EL']})

    o.cl = _sort_node_output(pd.DataFrame({
        'id': TAZ_nodes,
        'ordinal': np.zeros(len(TAZ_nodes), dtype=int),
        'PCL_node': _sum_block_metric(
            block_results, 'PCL_node', len(TAZ_nodes)),
        'WCL_node': _sum_block_metric(
            block_results, 'WCL_node', len(TAZ_nodes)),
    }))

    if efficiency_enabled:
        eff_ids = baseline['eff_ids']
        o.node_el = _sort_node_output(pd.DataFrame({
            'id': eff_ids,
            'ordinal': np.zeros(len(eff_ids), dtype=int),
            'EL': _sum_block_metric(
                block_results, 'EL_node', len(eff_ids)),
        }))
    return o


def EL_node(expo_df, G_original, eff_nodes, damage_df, g_type,
            max_nodes_network, concurrent_tasks=None, h5=None):
    # When no information about supply or demand is given or known,
    # only efficiency loss is calculated for all nodes.
    node_el = expo_df[expo_df['type'].str.lower() == 'node'].iloc[:, 0:1]

    eff_table = pd.DataFrame({'id': eff_nodes})
    eff_table.set_index('id', inplace=True)

    N = len(G_original)
    att = nx.get_edge_attributes(G_original, 'weight')
    weighted = bool(att)
    eff_table = calc_efficiency(
        G_original, N, att, eff_table, 'Eff0', max_nodes_network)

    efficiency_enabled = N <= max_nodes_network
    baseline = _efficiency_baseline(eff_table, efficiency_enabled)

    logging.info('Checking for every event after earthquake')
    events = damage_df.groupby('event_id', sort=False)
    event_order = damage_df.index.get_level_values(
        'event_id').unique().to_numpy()
    num_events = events.ngroups

    if concurrent_tasks == 0 or parallel.Starmap.on or num_events <= 1:
        block_results = [_process_generic_block(
            events, G_original, g_type, N, weighted,
            max_nodes_network, baseline)]
    else:
        smap = parallel.Starmap.apply(
            process_generic_events,
            (events, G_original, g_type, N, weighted,
             max_nodes_network, baseline),
            concurrent_tasks=concurrent_tasks, h5=h5)
        block_results = list(smap)

    block_results = _ordered_blocks(block_results, event_order)
    event_ids, metrics = _ordered_event_metrics(
        block_results, event_order, ('EL',))
    event_eff = pd.DataFrame({
        'event_id': event_ids, 'EL': metrics['EL']})

    if efficiency_enabled:
        eff_ids = baseline['eff_ids']
        node_el = _sort_node_output(pd.DataFrame({
            'id': eff_ids,
            'ordinal': np.zeros(len(eff_ids), dtype=int),
            'EL': _sum_block_metric(
                block_results, 'EL_node', len(eff_ids)),
        }))

    return node_el, event_eff


def _process_generic_block(
        event_block, G_original, g_type, N, weighted,
        max_nodes_network, baseline):
    """Calculate per-event EL and block nodal EL sums for generic mode."""
    event_ids = []
    event_el = []

    eff_ids = baseline['eff_ids']
    eff_index = ({node: idx for idx, node in enumerate(eff_ids)}
                 if eff_ids is not None else {})
    el_sum = (np.zeros(len(eff_ids), dtype=float)
              if eff_ids is not None else None)

    for event_id, event_damage_df in event_block:
        G = cleanup_graph(G_original, event_damage_df, g_type)
        if baseline['eff0'] is None:
            glo_el, el_node = np.nan, None
        else:
            eff_values = _efficiency_values(
                G, N, weighted, max_nodes_network)
            glo_el, el_node = _efficiency_loss_arrays(
                eff_values, baseline, eff_index)

        event_ids.append(event_id)
        event_el.append(glo_el)
        if el_sum is not None:
            el_sum += el_node

    return {
        'event_id': np.asarray(event_ids),
        'EL': np.asarray(event_el, dtype=float),
        'EL_node': el_sum,
    }


def process_generic_events(
        event_block, G_original, g_type, N, weighted, max_nodes_network,
        baseline, monitor):
    """Process one Starmap block for generic-node efficiency analysis."""
    return _process_generic_block(
        event_block, G_original, g_type, N, weighted,
        max_nodes_network, baseline)


def _source_target_metrics(graph, att, nodes_from, nodes_to,
                           exclude_self=False, N=None):
    """
    Compute all source-to-target quantities with one shortest-path traversal
    per source node.

    :param graph:
        NetworkX graph.
    :param att:
        Edge-weight attribute dictionary. An empty
        dictionary means an unweighted analysis; otherwise ``weight`` is used.
    :param nodes_from:
        Source nodes.
    :param nodes_to:
        Target nodes.
    :param exclude_self:
        If True, do not count source == target in the reachable-source count.
        This preserves the existing TAZ definition of NS/NS0.
    :param N:
        If provided, also calculate nodal efficiency for each source using the
        same shortest-path tree. This lets calc_efficiency reuse work already
        done here.
    :returns:
        ``(reachable_count, reciprocal_distance_sum, source_efficiency)``.

    ``reachable_count[target]`` is the number of source nodes that can reach
    the target.

    ``reciprocal_distance_sum[target]`` is the sum of 1 / shortest-path length
    from every reachable source to the target, excluding zero-length paths.

    ``source_efficiency[source]`` is calculated only when N is provided.
    """
    nodes_to = list(nodes_to)
    reachable_count = {node: 0 for node in nodes_to}
    reciprocal_distance_sum = {node: 0.0 for node in nodes_to}
    source_efficiency = {}

    weighted = bool(att)

    for source in nodes_from:
        if weighted:
            lengths = nx.single_source_dijkstra_path_length(
                graph, source, weight='weight')
        else:
            lengths = nx.single_source_shortest_path_length(graph, source)

        # calc_efficiency needs exactly the same single-source shortest-path
        # tree, so reuse it instead of traversing the graph again later.
        if N is not None:
            inv = [1 / distance for distance in lengths.values()
                   if distance != 0]
            source_efficiency[source] = sum(inv) / (N - 1)

        for target in nodes_to:
            if target not in lengths:
                continue

            if not (exclude_self and source == target):
                reachable_count[target] += 1

            distance = lengths[target]
            if distance != 0:
                reciprocal_distance_sum[target] += 1 / distance

    return reachable_count, reciprocal_distance_sum, source_efficiency

