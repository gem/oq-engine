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

# The present work has been done in the framework of grant agreement No. 813137
# funded by the European Commission ITN-Marie Sklodowska-Curie project
# “New Challenges for Urban Engineering Seismology (URBASIS-EU)”.
# @author 1 has been funded by this project

from dataclasses import dataclass
import copy
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

    # We should raise an error if the exposure nodes contain at the same time
    # taz/both and demand/supply
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
        if precomputed is None:
            precomputed = {}

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


def ELWCLPCLCCL_demand(expo_df, G_original, eff_nodes, demand_nodes,
                       source_nodes, damage_df, g_type, max_nodes_network,
                       concurrent_tasks=None, h5=None):
    # Classic case where particular nodes are divided as supply or demand.
    o = Out.new(expo_df, demand_nodes, eff_nodes, 'demand')

    att = nx.get_edge_attributes(G_original, 'weight')
    N = len(G_original)

    # One shortest-path tree per source supplies CNO, NS0 and WS0 together.
    # When efficiency is enabled, also reuse those same trees for Eff0.
    eff_N = N if N <= max_nodes_network else None
    ns0, invdist0, source_eff0 = _source_target_metrics(
        G_original, att, source_nodes, demand_nodes, N=eff_N)

    for node in demand_nodes:
        o.ccl_table.at[node, 'CNO'] = 1 if ns0[node] else 0
        o.pcl_table.at[node, 'NS0'] = ns0[node]
        o.wcl_table.at[node, 'WS0'] = invdist0[node] * ns0[node]

    o.eff_table = calc_efficiency(
        G_original, N, att, o.eff_table, 'Eff0', max_nodes_network,
        precomputed=source_eff0)

    logging.info('Checking for every event after earthquake')
    events = list(damage_df.groupby('event_id'))

    # concurrent_tasks=0 to disable parallelism.
    # Also avoid creating a nested Starmap if this code is already executing
    # inside an OQ worker.
    if concurrent_tasks == 0 or parallel.Starmap.on or len(events) <= 1:
        for event_id, event_damage_df in events:
            update_demand(
                o, event_id, event_damage_df, G_original, g_type,
                source_nodes, demand_nodes, eff_nodes, N, att,
                max_nodes_network)
        return o

    weighted = bool(att)
    smap = parallel.Starmap.apply(
        process_demand_events,
        (events, o, G_original, g_type, source_nodes, demand_nodes,
         eff_nodes, N, weighted, max_nodes_network),
        concurrent_tasks=concurrent_tasks, h5=h5)
    return _merge_demand_results(o, list(smap), N <= max_nodes_network)


def update_demand(o, event_id, event_damage_df, G_original, g_type,
                  source_nodes, demand_nodes, eff_nodes, N, att,
                  max_nodes_network):
    G = cleanup_graph(G_original, event_damage_df, g_type)

    # Some demand/source nodes may have been removed by the damage state.
    graph_nodes = set(G.nodes)
    extant_source_nodes = set(source_nodes) & graph_nodes
    extant_demand_nodes = sorted(set(demand_nodes) & graph_nodes)
    extant_eff_nodes = sorted(set(eff_nodes) & graph_nodes)

    # Nodes removed from the damaged graph have zero post-event connectivity.
    o.ccl_table.loc[
        ~o.ccl_table.index.isin(extant_demand_nodes), 'CNS'] = 0
    o.pcl_table.loc[
        ~o.pcl_table.index.isin(extant_demand_nodes), 'NS'] = 0
    o.wcl_table.loc[
        ~o.wcl_table.index.isin(extant_demand_nodes), 'WS'] = 0
    o.eff_table.loc[
        ~o.eff_table.index.isin(extant_eff_nodes), 'Eff'] = 0

    # Calculate CNS, NS and WS from the same set of single-source shortest
    # paths. Reuse source efficiencies in calc_efficiency when applicable.
    eff_N = N if N <= max_nodes_network else None
    ns_values, invdist, source_eff = _source_target_metrics(
        G, att, extant_source_nodes, extant_demand_nodes, N=eff_N)

    for node in extant_demand_nodes:
        ns = ns_values[node]
        o.ccl_table.at[node, 'CNS'] = 1 if ns else 0
        o.pcl_table.at[node, 'NS'] = ns
        o.wcl_table.at[node, 'WS'] = invdist[node] * ns

    o.eff_table = calc_efficiency(
        G, N, att, o.eff_table, 'Eff', max_nodes_network,
        precomputed=source_eff)

    # Connectivity Loss for each node
    o.pcl_table['PCL_node'] = 1 - (o.pcl_table['NS'] / o.pcl_table['NS0'])
    o.wcl_table['WCL_node'] = 1 - (o.wcl_table['WS'] / o.wcl_table['WS0'])

    # Computing the mean of the connectivity loss to consider the overall
    # performance of the area (at global level)
    CCL_per_event = 1 - (
        o.ccl_table['CNS'].sum() / o.ccl_table['CNO'].sum())
    PCL_mean_per_event = o.pcl_table['PCL_node'].mean()
    WCL_mean_per_event = o.wcl_table['WCL_node'].mean()

    if N > max_nodes_network:
        Glo_eff0_per_event = np.nan
        Glo_eff_per_event = np.nan
        Glo_effloss_per_event = np.nan
    else:
        Glo_eff0_per_event = o.eff_table['Eff0'].mean()
        Glo_eff_per_event = o.eff_table['Eff'].mean()
        Glo_effloss_per_event = (
            Glo_eff0_per_event - Glo_eff_per_event) / Glo_eff0_per_event

    event = Inp(
        event_id, CCL_per_event, PCL_mean_per_event,
        WCL_mean_per_event, Glo_effloss_per_event)
    _update_demand(o, event)

    if N <= max_nodes_network:
        eff_table1 = o.eff_table.drop(columns=['Eff0', 'Eff'])
        o.node_el = pd.concat(
            (o.node_el, eff_table1.reset_index())
        ).groupby('id', as_index=False).sum()



def _update_demand(o, event):
    # Storing the value of performance indicators for each event
    o.event_connectivity_loss_ccl = pd.concat(
        [o.event_connectivity_loss_ccl, pd.DataFrame.from_records(
            [{'event_id': event.id, 'CCL': event.CCL}])],
        ignore_index=True)
    o.event_connectivity_loss_pcl = pd.concat(
        [o.event_connectivity_loss_pcl, pd.DataFrame.from_records(
            [{'event_id': event.id, 'PCL': event.PCL}])],
        ignore_index=True)
    o.event_connectivity_loss_wcl = pd.concat(
        [o.event_connectivity_loss_wcl, pd.DataFrame.from_records(
            [{'event_id': event.id, 'WCL': event.WCL}])],
        ignore_index=True)
    o.event_connectivity_loss_eff = pd.concat(
        [o.event_connectivity_loss_eff, pd.DataFrame.from_records(
            [{'event_id': event.id, 'EL': event.effloss}])],
        ignore_index=True)
    # To store the sum of performance indicator at nodal level to calulate
    # the average afterwards
    o.ccl_table['Isolation_node'] = 1 - o.ccl_table['CNS']
    ccl_table1 = o.ccl_table.drop(columns=['CNO', 'CNS'])
    o.cl = pd.concat((o.cl, ccl_table1.reset_index())).groupby(
        'id', as_index=False).sum()

    pcl_table1 = o.pcl_table.drop(columns=['NS0', 'NS'])
    o.cl = pd.concat((o.cl, pcl_table1.reset_index())).groupby(
        'id', as_index=False).sum()

    wcl_table1 = o.wcl_table.drop(columns=['WS0', 'WS'])
    o.cl = pd.concat((o.cl, wcl_table1.reset_index())).groupby(
        'id', as_index=False).sum()


def update_taz(o, event_id, event_damage_df, G_original, g_type,
               TAZ_nodes, eff_nodes, N, att, max_nodes_network):
    G = cleanup_graph(G_original, event_damage_df, g_type)

    # Checking if there is a path between any source to each demand node.
    # Some demand nodes and source nodes may have been eliminated from
    # the network due to damage, so we do not need to check their
    # functionalities
    graph_nodes = set(G.nodes)
    extant_TAZ_nodes = sorted(set(TAZ_nodes) & graph_nodes)
    extant_eff_nodes = sorted(set(eff_nodes) & graph_nodes)

    # If demand nodes are damaged itself (Example, building collapsed where
    # demand node is considered)
    o.pcl_table.loc[~o.pcl_table.index.isin(extant_TAZ_nodes), 'NS'] = 0
    o.wcl_table.loc[~o.wcl_table.index.isin(extant_TAZ_nodes), 'WS'] = 0
    o.eff_table.loc[~o.eff_table.index.isin(extant_eff_nodes), 'Eff'] = 0

    # In TAZ mode a node is not counted as connected to itself in NS/NS0.
    eff_N = N if N <= max_nodes_network else None
    ns_values, invdist, source_eff = _source_target_metrics(
        G, att, extant_TAZ_nodes, extant_TAZ_nodes,
        exclude_self=True, N=eff_N)

    for node in extant_TAZ_nodes:
        ns = ns_values[node]
        o.pcl_table.at[node, 'NS'] = ns
        o.wcl_table.at[node, 'WS'] = invdist[node] * ns

    o.eff_table = calc_efficiency(
        G, N, att, o.eff_table, 'Eff', max_nodes_network,
        precomputed=source_eff)

    # Connectivity Loss for each node
    o.pcl_table['PCL_node'] = 1 - (o.pcl_table['NS'] / o.pcl_table['NS0'])
    o.wcl_table['WCL_node'] = 1 - (o.wcl_table['WS'] / o.wcl_table['WS0'])

    # Computing the mean of the connectivity loss to consider the overall
    # performance of the area (at global level)
    PCL_mean_per_event = o.pcl_table['PCL_node'].mean()
    WCL_mean_per_event = o.wcl_table['WCL_node'].mean()

    if N > max_nodes_network:
        Glo_eff0_per_event = np.nan
        Glo_eff_per_event = np.nan
        Glo_effloss_per_event = np.nan
    else:
        Glo_eff0_per_event = o.eff_table['Eff0'].mean()
        Glo_eff_per_event = o.eff_table['Eff'].mean()
        Glo_effloss_per_event = (
            Glo_eff0_per_event - Glo_eff_per_event) / Glo_eff0_per_event

    # Storing the value of performance indicators for each event
    o.event_connectivity_loss_pcl = pd.concat(
        [o.event_connectivity_loss_pcl, pd.DataFrame.from_records(
            [{'event_id': event_id, 'PCL': PCL_mean_per_event}])],
        ignore_index=True)
    o.event_connectivity_loss_wcl = pd.concat(
        [o.event_connectivity_loss_wcl, pd.DataFrame.from_records(
            [{'event_id': event_id, 'WCL': WCL_mean_per_event}])],
        ignore_index=True)
    o.event_connectivity_loss_eff = pd.concat(
        [o.event_connectivity_loss_eff, pd.DataFrame.from_records(
            [{'event_id': event_id, 'EL': Glo_effloss_per_event}])],
        ignore_index=True)

    # To store the sum of performance indicator at nodal level to calculate
    # the average afterwards
    pcl_table1 = o.pcl_table.drop(columns=['NS0', 'NS'])
    o.cl = pd.concat((o.cl, pcl_table1.reset_index())).groupby(
        'id', as_index=False).sum()
    wcl_table1 = o.wcl_table.drop(columns=['WS0', 'WS'])
    o.cl = pd.concat((o.cl, wcl_table1.reset_index())).groupby(
        'id', as_index=False).sum()

    if N <= max_nodes_network:
        eff_table1 = o.eff_table.drop(columns=['Eff0', 'Eff'])
        o.node_el = pd.concat(
            (o.node_el, eff_table1.reset_index())
        ).groupby('id', as_index=False).sum()
    

def ELWCLPCLloss_TAZ(expo_df, G_original, TAZ_nodes,
                     eff_nodes, damage_df, g_type, max_nodes_network,
                     concurrent_tasks=None, h5=None):
    # When the nodes act as both demand and supply, for example traffic
    # analysis zones in a transportation network.

    # To store the information of the performance indicators at connectivity
    # level
    o = Out.new(expo_df, TAZ_nodes, eff_nodes, 'taz')

    att = nx.get_edge_attributes(G_original, 'weight')
    N = len(G_original)

    eff_N = N if N <= max_nodes_network else None
    ns0, invdist0, source_eff0 = _source_target_metrics(
        G_original, att, TAZ_nodes, TAZ_nodes,
        exclude_self=True, N=eff_N)

    for node in TAZ_nodes:
        o.pcl_table.at[node, 'NS0'] = ns0[node]
        o.wcl_table.at[node, 'WS0'] = invdist0[node] * ns0[node]

    o.eff_table = calc_efficiency(
        G_original, N, att, o.eff_table, 'Eff0', max_nodes_network,
        precomputed=source_eff0)

    logging.info('Checking for every event after earthquake')
    events = list(damage_df.groupby('event_id'))
    if concurrent_tasks == 0 or parallel.Starmap.on or len(events) <= 1:
        for event_id, event_damage_df in events:
            update_taz(
                o, event_id, event_damage_df, G_original, g_type,
                TAZ_nodes, eff_nodes, N, att, max_nodes_network)
        return o

    weighted = bool(att)
    smap = parallel.Starmap.apply(
        process_taz_events,
        (events, o, G_original, g_type, TAZ_nodes, eff_nodes, N,
         weighted, max_nodes_network),
        concurrent_tasks=concurrent_tasks, h5=h5)
    return _merge_taz_results(o, list(smap), N <= max_nodes_network)

def EL_node(expo_df, G_original, eff_nodes, damage_df, g_type,
            max_nodes_network, concurrent_tasks=None, h5=None):
    # when no information about supply or demand is given or known,
    # only efficiency loss is calculated for all nodes

    node_el = expo_df[expo_df['type'].str.lower() == 'node'].iloc[:, 0:1]

    eff_table = pd.DataFrame({'id': eff_nodes})
    eff_table.set_index("id", inplace=True)

    event_connectivity_loss_eff = pd.DataFrame(
        {'event_id': pd.Series(dtype=int), 'EL': pd.Series(dtype=float)})

    N = len(G_original)
    att = nx.get_edge_attributes(G_original, 'weight')
    eff_table = calc_efficiency(
        G_original, N, att, eff_table, 'Eff0', max_nodes_network)

    logging.info('Checking for every event after earthquake')
    events = list(damage_df.groupby('event_id'))
    if concurrent_tasks == 0 or parallel.Starmap.on or len(events) <= 1:
        for event_id, event_damage_df in events:
            node_el, event_connectivity_loss_eff, eff_table = update_generic(
                node_el, event_connectivity_loss_eff, eff_table,
                event_id, event_damage_df, G_original, g_type, eff_nodes,
                N, att, max_nodes_network)
        return node_el, event_connectivity_loss_eff

    weighted = bool(att)
    smap = parallel.Starmap.apply(
        process_generic_events,
        (events, eff_table, node_el, G_original, g_type, eff_nodes, N,
         weighted, max_nodes_network),
        concurrent_tasks=concurrent_tasks, h5=h5)
    return _merge_generic_results(
        node_el, list(smap), N <= max_nodes_network)



def _event_frames(results, key, columns):
    """Concatenate and order per-event results returned by Starmap tasks."""
    frames = [res[key] for res in results if len(res[key])]
    if not frames:
        return pd.DataFrame({
            col: pd.Series(dtype=int if col == 'event_id' else float)
            for col in columns})
    return (pd.concat(frames, ignore_index=True)[columns]
            .sort_values('event_id', kind='stable')
            .reset_index(drop=True))


def _sum_node_frames(results, key):
    """Sum nodal event losses produced independently by each task."""
    frames = [res[key] for res in results
              if res.get(key) is not None and len(res[key])]
    if not frames:
        return None
    frame = pd.concat(frames, ignore_index=True)
    value_cols = [col for col in frame.columns
                  if col not in ('id', 'ordinal')]
    if not value_cols:
        return None
    return frame[['id'] + value_cols].groupby('id', as_index=False).sum()


def process_demand_events(
        event_block, o_template, G_original, g_type, source_nodes,
        demand_nodes, eff_nodes, N, weighted, max_nodes_network, monitor):
    """Process one Starmap block of damage events for demand/source mode."""
    o = copy.deepcopy(o_template)
    for event_id, event_damage_df in event_block:
        update_demand(
            o, event_id, event_damage_df, G_original, g_type,
            source_nodes, demand_nodes, eff_nodes, N, weighted,
            max_nodes_network)

    node_el = None
    if N <= max_nodes_network:
        node_el = o.node_el.drop(columns=['ordinal'], errors='ignore')

    return {
        'event_ccl': o.event_connectivity_loss_ccl,
        'event_pcl': o.event_connectivity_loss_pcl,
        'event_wcl': o.event_connectivity_loss_wcl,
        'event_eff': o.event_connectivity_loss_eff,
        'cl': o.cl.drop(columns=['ordinal'], errors='ignore'),
        'node_el': node_el,
    }


def _merge_demand_results(o, results, efficiency_enabled):
    """Merge independent demand/source task outputs in the master process."""
    o.event_connectivity_loss_ccl = _event_frames(
        results, 'event_ccl', ['event_id', 'CCL'])
    o.event_connectivity_loss_pcl = _event_frames(
        results, 'event_pcl', ['event_id', 'PCL'])
    o.event_connectivity_loss_wcl = _event_frames(
        results, 'event_wcl', ['event_id', 'WCL'])
    o.event_connectivity_loss_eff = _event_frames(
        results, 'event_eff', ['event_id', 'EL'])

    cl = _sum_node_frames(results, 'cl')
    if cl is not None:
        cl['ordinal'] = 0
        o.cl = cl

    if efficiency_enabled:
        node_el = _sum_node_frames(results, 'node_el')
        if node_el is not None:
            node_el['ordinal'] = 0
            o.node_el = node_el
    return o


def process_taz_events(
        event_block, o_template, G_original, g_type, TAZ_nodes, eff_nodes,
        N, weighted, max_nodes_network, monitor):
    """Process one Starmap block of damage events for TAZ mode."""
    o = copy.deepcopy(o_template)
    for event_id, event_damage_df in event_block:
        update_taz(
            o, event_id, event_damage_df, G_original, g_type,
            TAZ_nodes, eff_nodes, N, weighted, max_nodes_network)

    node_el = None
    if N <= max_nodes_network:
        node_el = o.node_el.drop(columns=['ordinal'], errors='ignore')

    return {
        'event_pcl': o.event_connectivity_loss_pcl,
        'event_wcl': o.event_connectivity_loss_wcl,
        'event_eff': o.event_connectivity_loss_eff,
        'cl': o.cl.drop(columns=['ordinal'], errors='ignore'),
        'node_el': node_el,
    }


def _merge_taz_results(o, results, efficiency_enabled):
    """Merge independent TAZ task outputs in the master process."""
    o.event_connectivity_loss_pcl = _event_frames(
        results, 'event_pcl', ['event_id', 'PCL'])
    o.event_connectivity_loss_wcl = _event_frames(
        results, 'event_wcl', ['event_id', 'WCL'])
    o.event_connectivity_loss_eff = _event_frames(
        results, 'event_eff', ['event_id', 'EL'])

    cl = _sum_node_frames(results, 'cl')
    if cl is not None:
        cl['ordinal'] = 0
        o.cl = cl

    if efficiency_enabled:
        node_el = _sum_node_frames(results, 'node_el')
        if node_el is not None:
            node_el['ordinal'] = 0
            o.node_el = node_el
    return o


def update_generic(node_el, event_connectivity_loss_eff, eff_table,
                   event_id, event_damage_df, G_original, g_type, eff_nodes,
                   N, att, max_nodes_network):
    """Calculate generic-node efficiency loss for a single damage event."""
    G = cleanup_graph(G_original, event_damage_df, g_type)
    extant_eff_nodes = sorted(set(eff_nodes) & set(G.nodes))

    eff_table.loc[~eff_table.index.isin(extant_eff_nodes), 'Eff'] = 0
    eff_table = calc_efficiency(
        G, N, att, eff_table, 'Eff', max_nodes_network)

    if N > max_nodes_network:
        Glo_effloss_per_event = np.nan
    else:
        Glo_eff0_per_event = eff_table['Eff0'].mean()
        Glo_eff_per_event = eff_table['Eff'].mean()
        Glo_effloss_per_event = (
            Glo_eff0_per_event - Glo_eff_per_event) / Glo_eff0_per_event

    event_connectivity_loss_eff = pd.concat(
        [event_connectivity_loss_eff, pd.DataFrame.from_records(
            [{'event_id': event_id, 'EL': Glo_effloss_per_event}])],
        ignore_index=True)

    if N <= max_nodes_network:
        eff_table1 = eff_table.drop(columns=['Eff0', 'Eff']).reset_index()
        node_el = pd.concat((node_el, eff_table1)).groupby(
            'id', as_index=False).sum()

    return node_el, event_connectivity_loss_eff, eff_table


def process_generic_events(
        event_block, eff_table_template, node_el_template, G_original,
        g_type, eff_nodes, N, weighted, max_nodes_network, monitor):
    """Process one Starmap block for generic-node efficiency analysis."""
    eff_table = copy.deepcopy(eff_table_template)
    node_el = copy.deepcopy(node_el_template)
    event_eff = pd.DataFrame(
        {'event_id': pd.Series(dtype=int), 'EL': pd.Series(dtype=float)})

    for event_id, event_damage_df in event_block:
        node_el, event_eff, eff_table = update_generic(
            node_el, event_eff, eff_table, event_id, event_damage_df,
            G_original, g_type, eff_nodes, N, weighted, max_nodes_network)

    node_result = None
    if N <= max_nodes_network:
        node_result = node_el.drop(columns=['ordinal'], errors='ignore')
    return {'event_eff': event_eff, 'node_el': node_result}


def _merge_generic_results(node_el, results, efficiency_enabled):
    """Merge generic-node task outputs in the master process."""
    event_eff = _event_frames(results, 'event_eff', ['event_id', 'EL'])
    if efficiency_enabled:
        merged = _sum_node_frames(results, 'node_el')
        if merged is not None:
            merged['ordinal'] = 0
            node_el = merged
    return node_el, event_eff

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