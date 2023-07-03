
# Code prepared by:

# @author 1 . Astha Poudel, Early Stage Researcher, PhD candidate
# Aristotle University of Thessaloniki/Université Grenoble Alpes

# @author 2 . Anirudh Rao

# The present work has been done in the framework of grant agreement No. 813137
# funded by the European Commission ITN-Marie Sklodowska-Curie project
# “New Challenges for Urban Engineering Seismology (URBASIS-EU)”.
# @author 1 has been funded by this project

import pandas as pd
import numpy as np
import networkx as nx


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

    # FIXME: Needs to be checked. It gives an error if this is not done.
    if 'weights' in exposure_df.columns:
        exposure_df['weights'] = exposure_df['weights'].astype(float)

    return exposure_df


def classify_nodes(exposure_df):
    # Classifying the nodes accodingly to compute performance indicator in
    # global and local scale

    # TAZ is the acronym of "Traffic Analysis Zone"
    # user can write both as well
    TAZ_nodes = exposure_df.loc[(exposure_df.supply_or_demand == "TAZ") | (
        exposure_df.supply_or_demand == "both")].index.to_list()

    # ## Maybe we can write supply or source and demand or sink so that user
    #    can use whatever they want to
    # source_nodes = exposure_df.loc[exposure_df[
    #     'supply_or_demand'].isin(['source', 'supply'])].index.to_list()
    source_nodes = exposure_df.loc[
        exposure_df.supply_or_demand == "source"].index.to_list()
    demand_nodes = exposure_df.loc[
        exposure_df.supply_or_demand == "demand"].index.to_list()
    eff_nodes = exposure_df.loc[exposure_df.type == "node"].index.to_list()

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
        exposure_df.loc[exposure_df.type == "edge"],
        source="start_node",
        target="end_node",
        edge_attr=True, create_using=getattr(nx, g_type)()
    )
    # This is done for the cases where there might be a disconnected node with
    # no edges and are not added in the G_original previously
    for _, row in exposure_df.loc[exposure_df.type == "node"].iterrows():
        if row["id"] not in G_original.nodes:
            G_original.add_node(row["id"], **row)
    # Adding the attribute of the nodes
    nx.set_node_attributes(
        G_original, exposure_df.loc[
            exposure_df.type == "node"].to_dict("index")
    )

    return G_original


def get_damage_df(dstore, exposure_df):
    # Extractung the damage data from component level analysis
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
        .assign(is_functional=lambda x: x.collapsed == 0)
    )[["type", "start_node", "end_node", "is_functional", "taxonomy"]]

    return damage_df


def analyze_taz_nodes(dstore, exposure_df, G_original, TAZ_nodes, eff_nodes,
                      damage_df, g_type, calculation_mode):
    (taz_cl, node_el,
        event_connectivity_loss_pcl,
        event_connectivity_loss_wcl,
        event_connectivity_loss_eff) = EFLWCLPCLloss_TAZ(
        exposure_df, G_original, TAZ_nodes, eff_nodes, damage_df, g_type)
    sum_connectivity_loss_pcl = event_connectivity_loss_pcl['PCL'].sum()
    sum_connectivity_loss_wcl = event_connectivity_loss_wcl['WCL'].sum()
    sum_connectivity_loss_eff = event_connectivity_loss_eff[
        'EFFLoss'].sum()

    if calculation_mode == "event_based_damage":
        inv_time = dstore["oqparam"].investigation_time
        ses_per_ltp = dstore["oqparam"].ses_per_logic_tree_path
        num_lt_samples = dstore["oqparam"].number_of_logic_tree_samples
        eff_inv_time = inv_time * ses_per_ltp * num_lt_samples
        avg_connectivity_loss_pcl = (
            sum_connectivity_loss_pcl / eff_inv_time)
        avg_connectivity_loss_wcl = sum_connectivity_loss_wcl/eff_inv_time
        avg_connectivity_loss_eff = sum_connectivity_loss_eff/eff_inv_time

    elif calculation_mode == "scenario_damage":
        num_events = len(damage_df.reset_index().event_id.unique())
        avg_connectivity_loss_pcl = sum_connectivity_loss_pcl / num_events
        avg_connectivity_loss_wcl = sum_connectivity_loss_wcl / num_events
        avg_connectivity_loss_eff = sum_connectivity_loss_eff / num_events
        taz_cl.loc[:, "PCL_node"] = taz_cl["PCL_node"].apply(
            lambda x: x/num_events)
        taz_cl.loc[:, "WCL_node"] = taz_cl["WCL_node"].apply(
            lambda x: x/num_events)
        node_el.loc[:, "Eff_loss"] = node_el["Eff_loss"].apply(
            lambda x: x/num_events)

    print("The mean of the Partial Connectivity Loss: {}".format(
        avg_connectivity_loss_pcl))
    print("The mean of the Weighted Connectivity Loss: {}".format(
        avg_connectivity_loss_wcl))
    print("The mean of the Global Efficiency Loss: {}".format(
        avg_connectivity_loss_eff))
    dstore['avg_connectivity_loss_pcl'] = avg_connectivity_loss_pcl
    dstore['avg_connectivity_loss_wcl'] = avg_connectivity_loss_wcl
    dstore['avg_connectivity_loss_eff'] = avg_connectivity_loss_eff

    # Storing the connectivity loss at global level for each event
    # TODO: Save performance metrics for each event in datastore and make
    #       it exportable
    # event_connectivity_loss_pcl.to_csv("pcl_event.csv")
    # event_connectivity_loss_wcl.to_csv("wcl_event.csv")
    # event_connectivity_loss_eff.to_csv("efl_event.csv")
    dstore['event_connectivity_loss_pcl'] = event_connectivity_loss_pcl
    dstore['event_connectivity_loss_wcl'] = event_connectivity_loss_wcl
    dstore['event_connectivity_loss_eff'] = event_connectivity_loss_eff
    # Storing the connectivity loss at nodal level
    # TODO: Save taz_cl in datastore and make it exportable
    # taz_cl.to_csv("taz.csv")
    dstore.create_df('taz_cl', taz_cl)
    # TODO: Save node_el in datastore and make it exportable
    # node_el.to_csv("node_el.csv")
    dstore.create_df('node_el', node_el)

    return node_el, avg_connectivity_loss_eff


def analyze_demand_nodes(dstore, exposure_df, G_original, eff_nodes,
                         demand_nodes, source_nodes, damage_df, g_type,
                         calculation_mode):
    (dem_cl, node_el, event_connectivity_loss_ccl,
        event_connectivity_loss_pcl, event_connectivity_loss_wcl,
        event_connectivity_loss_eff) = EFLWCLPCLCCL_demand(
        exposure_df, G_original, eff_nodes, demand_nodes, source_nodes,
        damage_df, g_type)
    sum_connectivity_loss_ccl = event_connectivity_loss_ccl['CCL'].sum()
    sum_connectivity_loss_pcl = event_connectivity_loss_pcl['PCL'].sum()
    sum_connectivity_loss_wcl = event_connectivity_loss_wcl['WCL'].sum()
    sum_connectivity_loss_eff = event_connectivity_loss_eff[
        'EFFLoss'].sum()

    if calculation_mode == "event_based_damage":
        inv_time = dstore["oqparam"].investigation_time
        ses_per_ltp = dstore["oqparam"].ses_per_logic_tree_path
        num_lt_samples = dstore["oqparam"].number_of_logic_tree_samples
        eff_inv_time = inv_time * ses_per_ltp * num_lt_samples
        avg_connectivity_loss_ccl = (
            sum_connectivity_loss_ccl / eff_inv_time)
        avg_connectivity_loss_pcl = (
            sum_connectivity_loss_pcl / eff_inv_time)
        avg_connectivity_loss_wcl = (
            sum_connectivity_loss_wcl / eff_inv_time)
        avg_connectivity_loss_eff = (
            sum_connectivity_loss_eff / eff_inv_time)

    elif calculation_mode == "scenario_damage":
        num_events = len(damage_df.reset_index().event_id.unique())
        avg_connectivity_loss_ccl = sum_connectivity_loss_ccl / num_events
        avg_connectivity_loss_pcl = sum_connectivity_loss_pcl / num_events
        avg_connectivity_loss_wcl = sum_connectivity_loss_wcl / num_events
        avg_connectivity_loss_eff = sum_connectivity_loss_eff/num_events
        dem_cl.loc[:, "CCL_node"] = dem_cl["CCL_node"].apply(
            lambda x: x/num_events)
        dem_cl.loc[:, "PCL_node"] = dem_cl["PCL_node"].apply(
            lambda x: x/num_events)
        dem_cl.loc[:, "WCL_node"] = dem_cl["WCL_node"].apply(
            lambda x: x/num_events)
        node_el.loc[:, "Eff_loss"] = node_el["Eff_loss"].apply(
            lambda x: x/num_events)

    print("The mean of the Complete Connectivity Loss: {}".format(
        avg_connectivity_loss_ccl))
    print("The mean of the Partial Connectivity Loss: {}".format(
        avg_connectivity_loss_pcl))
    print("The mean of the Weighted Connectivity Loss: {}".format(
        avg_connectivity_loss_wcl))
    print("The mean of the Global Efficiency Loss: {}".format(
        avg_connectivity_loss_eff))
    dstore['avg_connectivity_loss_ccl'] = avg_connectivity_loss_ccl
    dstore['avg_connectivity_loss_pcl'] = avg_connectivity_loss_pcl
    dstore['avg_connectivity_loss_wcl'] = avg_connectivity_loss_wcl
    dstore['avg_connectivity_loss_eff'] = avg_connectivity_loss_eff

    # Storing the connectivity loss at global level for each event
    # TODO: Save performance metrics in datastore and make it exportable
    # event_connectivity_loss_ccl.to_csv("ccl_event.csv")
    # event_connectivity_loss_pcl.to_csv("pcl_event.csv")
    # event_connectivity_loss_wcl.to_csv("wcl_event.csv")
    # event_connectivity_loss_eff.to_csv("efl_event.csv")
    dstore['event_connectivity_loss_ccl'] = event_connectivity_loss_ccl
    dstore['event_connectivity_loss_pcl'] = event_connectivity_loss_pcl
    dstore['event_connectivity_loss_wcl'] = event_connectivity_loss_wcl
    dstore['event_connectivity_loss_eff'] = event_connectivity_loss_eff

    # Storing the connectivity loss at nodal level
    # TODO: Save dem_cl in datastore and make it exportable
    # dem_cl.to_csv("dem_cl.csv")
    dstore.create_df('dem_cl', dem_cl)
    # TODO: Save node_el in datastore and make it exportable
    # node_el.to_csv("node_el.csv")
    dstore.create_df('node_el', node_el)

    return node_el, avg_connectivity_loss_eff


def analyze_generic_nodes(dstore, exposure_df, G_original, eff_nodes,
                          damage_df, g_type, calculation_mode):
    node_el, event_connectivity_loss_eff = EFL_node(
        exposure_df, G_original, eff_nodes, damage_df, g_type)
    sum_connectivity_loss_eff = event_connectivity_loss_eff[
        'EFFLoss'].sum()

    if calculation_mode == "event_based_damage":
        inv_time = dstore["oqparam"].investigation_time
        ses_per_ltp = dstore["oqparam"].ses_per_logic_tree_path
        num_lt_samples = dstore["oqparam"].number_of_logic_tree_samples
        eff_inv_time = inv_time * ses_per_ltp * num_lt_samples
        avg_connectivity_loss_eff = sum_connectivity_loss_eff/eff_inv_time

    elif calculation_mode == "scenario_damage":
        num_events = len(damage_df.reset_index().event_id.unique())
        avg_connectivity_loss_eff = sum_connectivity_loss_eff/num_events
        node_el.loc[:, "Eff_loss"] = node_el["Eff_loss"].apply(
            lambda x: x/num_events)

    print("The mean of the Global Efficiency Loss: {}".format(
        avg_connectivity_loss_eff))
    dstore['avg_connectivity_loss_eff'] = avg_connectivity_loss_eff

    # Storing the connectivity loss at global level for each event
    # TODO: Save event_connectivity_loss_eff in datastore and make it
    #       exportable
    # event_connectivity_loss_eff.to_csv("efl_event.csv")
    dstore['event_connectivity_loss_eff'] = event_connectivity_loss_eff
    # Storing the connectivity loss at nodal level
    # TODO: Save node_el in datastore and make it exportable
    # node_el.to_csv("node_el.csv")
    dstore.create_df('node_el', node_el)

    return node_el, avg_connectivity_loss_eff


def analysis(dstore):
    oq = dstore["oqparam"]
    calculation_mode = oq.calculation_mode
    assert calculation_mode in ("event_based_damage", "scenario_damage")

    exposure_df = get_exposure_df(dstore)

    (TAZ_nodes, source_nodes,
     demand_nodes, eff_nodes) = classify_nodes(exposure_df)

    g_type = get_graph_type(exposure_df)

    exposure_df['id'] = exposure_df.index

    G_original = create_original_graph(exposure_df, g_type)

    damage_df = get_damage_df(dstore, exposure_df)

    # Calling the function according to the specification of the node type
    # if the nodes acts as both supply or demand (for example: traffic analysis
    # zone in transportation network)

    # FIXME: what happens if we have more than one node class? Shouldn't we
    # consider all separate groups instead of e.g. just TAZ_nodes, when
    # present?

    if TAZ_nodes:
        node_el, avg_connectivity_loss_eff = analyze_taz_nodes(
            dstore, exposure_df, G_original, TAZ_nodes, eff_nodes, damage_df,
            g_type, calculation_mode)

    # This is the classic and mostly used when supply/source and demand/sink is
    # explicity mentioned to the nodes of interest
    elif demand_nodes:
        node_el, avg_connectivity_loss_eff = analyze_demand_nodes(
            dstore, exposure_df, G_original, eff_nodes, demand_nodes,
            source_nodes, damage_df, g_type, calculation_mode)

    # if nothing is mentioned in case of scarce data or every node is important
    # and no distinction can be made
    else:
        node_el, avg_connectivity_loss_eff = analyze_generic_nodes(
            dstore, exposure_df, G_original, eff_nodes, damage_df, g_type,
            calculation_mode)

    # FIXME
    # The output gives efficiency loss even if it say average connectivity loss
    # in the output. It has to be modified in
    # openquake/calculators/event_based_damage.py
    # from line number 290 -293.
    # node_el and avg_connectivity_loss_eff has been retuned now to avoid the
    # error since this is calculated in every scenario.

    return node_el, avg_connectivity_loss_eff


def EFLWCLPCLCCL_demand(exposure_df, G_original, eff_nodes, demand_nodes,
                        source_nodes, damage_df, g_type):
    # Classic one where particular nodes are divided as supply or demand and
    # the main interest is to check the serviceability of supply to demand
    # nodes. This calculates, complete connectivity loss (CCL), weighted
    # connectivity loss (WCL), partial connectivity loss(PCL) considering the
    # demand and supply nodes provided at nodal and global level. Additionly,
    # efficiency loss globally and for each node is also calculated

    # To store the information of the performance indicators at connectivity
    # level
    dem_cl = exposure_df[
        exposure_df['supply_or_demand'] == 'demand'].iloc[:, 0:1]
    node_el = exposure_df[exposure_df['type'] == 'node'].iloc[:, 0:1]

    ccl_table = pd.DataFrame({'id': demand_nodes})
    pcl_table = pd.DataFrame({'id': demand_nodes})
    wcl_table = pd.DataFrame({'id': demand_nodes})
    eff_table = pd.DataFrame({'id': eff_nodes})

    ccl_table.set_index('id', inplace=True)
    pcl_table.set_index('id', inplace=True)
    wcl_table.set_index('id', inplace=True)
    eff_table.set_index("id", inplace=True)

    # Create an empty dataframe with columns "event_id" and
    # "CCL"/"PCL"/"WCL"/"EFFLoss"

    event_connectivity_loss_ccl = pd.DataFrame(columns=['event_id', 'CCL'])
    event_connectivity_loss_pcl = pd.DataFrame(columns=['event_id', 'PCL'])
    event_connectivity_loss_wcl = pd.DataFrame(columns=['event_id', 'WCL'])
    event_connectivity_loss_eff = pd.DataFrame(columns=['event_id', 'EFFLoss'])

    # To check the the values for each node before the earthquake event
    # For calculating complete connectivity Loss

    ccl_table['CNO'] = [1 if any(nx.has_path(G_original, j, i)
                        for j in source_nodes) else 0 for i in demand_nodes]

    # For calculating partialy connectivity loss
    pcl_table['NS0'] = [sum(nx.has_path(G_original, j, i)
                        for j in source_nodes) for i in demand_nodes]

    # For calculating weighted connectivity loss
    # Important: If the weights is not provided, then the weights of each edges
    # is considered to be one
    att = nx.get_edge_attributes(G_original, 'weights')

    for i in demand_nodes:
        if not att:
            path_lengths = [nx.shortest_path_length(G_original, j, i)
                            for j in source_nodes
                            if nx.has_path(G_original, j, i)]
            countw = sum([1/path_length for path_length in path_lengths
                          if path_length != 0])
        else:
            path_lengths = [
                nx.shortest_path_length(G_original, j, i, weight='weights')
                for j in source_nodes if nx.has_path(G_original, j, i)]
            countw = sum([1/path_length for path_length in path_lengths
                         if path_length != 0])
        wcl_table.at[i, 'WS0'] = countw * pcl_table.at[i, 'NS0']

    # For calculating efficiency
    # Important: If the weights is not provided, then the weights of each edges
    # is considered to be one.

    N = len(G_original)
    att = nx.get_edge_attributes(G_original, 'weights')
    for node in G_original:
        if not att:
            lengths = nx.single_source_shortest_path_length(G_original, node)
            inv = [1/x for x in lengths.values() if x != 0]
            eff_node = (sum(inv))/(N-1)
        else:
            lengths = nx.single_source_dijkstra_path_length(
                G_original, node, weight="weights")
            inv = [1/x for x in lengths.values() if x != 0]
            eff_node = (sum(inv))/(N-1)
        eff_table.at[node, 'Eff0'] = eff_node

    # Now we check for every event after earthquake
    for event_id, event_damage_df in damage_df.groupby("event_id"):
        # Making a copy of original graph for each event for the analysis
        G = G_original.copy()

        nodes_damage_df = event_damage_df.loc[
            event_damage_df.type == "node"].droplevel(level=0)
        edges_damage_df = event_damage_df.loc[
            event_damage_df.type == "edge"].droplevel(level=0)

        # Updating the graph to remove damaged edges and nodes
        nonfunctional_edges_df = edges_damage_df.loc[
            ~edges_damage_df.is_functional]
        nonfunctional_nodes_df = nodes_damage_df.loc[
            ~nodes_damage_df.is_functional]

        # This is done to handle the the multi graph where more that one edge
        # is possible between two nodes.
        # If it is a multi graph then every edge has a key value

        if g_type == "MultiGraph" or g_type == "MultiDiGraph":
            edges_to_remove = [
                (u, v, key)
                for (u, v, key, data) in G.edges(keys=True, data=True)
                if data['id'] in nonfunctional_edges_df.index.to_list()]
        else:
            edges_to_remove = [
                (u, v) for (u, v, data) in G.edges(data=True)
                if data['id'] in nonfunctional_edges_df.index.to_list()]

        # nonfunctional_edge_tuples = list(
        #     zip(nonfunctional_edges_df.start_node,
        #         nonfunctional_edges_df.end_node)
        # )

        G.remove_edges_from(edges_to_remove)
        G.remove_nodes_from(nonfunctional_nodes_df.index.to_list())

        # Now we start to check if there is a path between any souce to each
        # demand node

        # Some demand nodes and source nodes may have been eliminated from
        # the network due to damage, so we do not need to check their
        # functionalities

        extant_source_nodes = set(source_nodes) & set(G.nodes)
        extant_demand_nodes = sorted(set(demand_nodes) & set(G.nodes))
        extant_eff_nodes = sorted(set(eff_nodes) & set(G.nodes))

        # If demand nodes are damaged itself (Example, building collapsed where
        # demand node is considered)

        ccl_table.loc[~ccl_table.index.isin(extant_demand_nodes), 'CN'] = 0
        pcl_table.loc[~pcl_table.index.isin(extant_demand_nodes), 'NS'] = 0
        wcl_table.loc[~wcl_table.index.isin(extant_demand_nodes), 'WS'] = 0
        eff_table.loc[~eff_table.index.isin(extant_eff_nodes), 'Eff'] = 0

        # To check the the values for each node after the earthquake event
        # Complete connectivity loss
        ccl_table['CNS'] = [
            1 if any(nx.has_path(G, j, i) for j in extant_source_nodes) else 0
            for i in extant_demand_nodes]

        # Partial Connectivity Loss
        pcl_table.loc[extant_demand_nodes, 'NS'] = [
            sum(nx.has_path(G, j, i) for j in extant_source_nodes)
            for i in extant_demand_nodes]

        # Weighted Connectivity Loss
        for i in extant_demand_nodes:
            if not att:
                path_lengths = [
                    nx.shortest_path_length(G, j, i)
                    for j in extant_source_nodes if nx.has_path(G, j, i)]
                countw1 = sum([
                    1/path_length for path_length in path_lengths
                    if path_length != 0])
            else:
                path_lengths = [
                    nx.shortest_path_length(G, j, i, weight='weights')
                    for j in extant_source_nodes if nx.has_path(G, j, i)]
                countw1 = sum([
                    1/path_length for path_length in path_lengths
                    if path_length != 0])
            wcl_table.at[i, 'WS'] = countw1 * pcl_table.at[i, 'NS']

        # Calculation of efficieny
        for node in G:
            if not att:
                lengths = nx.single_source_shortest_path_length(G, node)
                inv = [1/x for x in lengths.values() if x != 0]
                eff_node = (sum(inv))/(N-1)
            else:
                lengths = nx.single_source_dijkstra_path_length(
                    G, node, weight="weights")
                inv = [1/x for x in lengths.values() if x != 0]
                eff_node = (sum(inv))/(N-1)
            eff_table.at[node, 'Eff'] = eff_node

        # Connectivity Loss for each node
        pcl_table['PCL_node'] = 1 - (pcl_table['NS']/pcl_table['NS0'])
        wcl_table['WCL_node'] = 1 - (wcl_table['WS']/wcl_table['WS0'])

        # This is done so that if the initial graph has a node disconnected,
        # will raise an error when calculating the efficiency loss
        eff_table['Eff_loss'] = (
            eff_table.Eff0 - eff_table.Eff)/eff_table.Eff0.replace({0: np.nan})
        eff_table['Eff_loss'] = eff_table['Eff_loss'].fillna(0)

        # Computing the mean of the connectivity loss to consider the overall
        # performance of the area (at global level)
        CCL_per_event = 1 - ((ccl_table['CNS'].sum())/ccl_table['CNO'].sum())
        PCL_mean_per_event = pcl_table['PCL_node'].mean()
        WCL_mean_per_event = wcl_table['WCL_node'].mean()
        Glo_eff0_per_event = eff_table['Eff0'].mean()
        Glo_eff_per_event = eff_table['Eff'].mean()
        # Calculation of Efficiency loss
        Glo_effloss_per_event = (
            Glo_eff0_per_event - Glo_eff_per_event)/Glo_eff0_per_event

        # Storing the value of performance indicators for each event
        event_connectivity_loss_ccl = event_connectivity_loss_ccl.append(
            {'event_id': event_id, 'CCL': CCL_per_event}, ignore_index=True)
        event_connectivity_loss_pcl = event_connectivity_loss_pcl.append(
            {'event_id': event_id, 'PCL': PCL_mean_per_event},
            ignore_index=True)
        event_connectivity_loss_wcl = event_connectivity_loss_wcl.append(
            {'event_id': event_id, 'WCL': WCL_mean_per_event},
            ignore_index=True)
        event_connectivity_loss_eff = event_connectivity_loss_eff.append(
            {'event_id': event_id, 'EFFLoss': Glo_effloss_per_event},
            ignore_index=True)

        # To store the sum of performance indicator at nodal level to calulate
        # the average afterwards
        ccl_table['CCL_node'] = 1 - ccl_table['CNS']
        ccl_table1 = ccl_table.drop(columns=['CNO', 'CNS'])
        ccl_table1 = ccl_table1.reset_index()
        dem_cl = pd.concat((dem_cl, ccl_table1)).groupby(
            'id', as_index=False).sum()

        pcl_table1 = pcl_table.drop(columns=['NS0', 'NS'])
        pcl_table1 = pcl_table1.reset_index()
        dem_cl = pd.concat((dem_cl, pcl_table1)).groupby(
            'id', as_index=False).sum()

        wcl_table1 = wcl_table.drop(columns=['WS0', 'WS'])
        wcl_table1 = wcl_table1.reset_index()
        dem_cl = pd.concat((dem_cl, wcl_table1)).groupby(
            'id', as_index=False).sum()

        eff_table1 = eff_table.drop(columns=['Eff0', 'Eff'])
        eff_table1 = eff_table1.reset_index()
        node_el = pd.concat((node_el, eff_table1)).groupby(
            'id', as_index=False).sum()

    return (dem_cl, node_el, event_connectivity_loss_ccl,
            event_connectivity_loss_pcl, event_connectivity_loss_wcl,
            event_connectivity_loss_eff)


def EFLWCLPCLloss_TAZ(exposure_df, G_original, TAZ_nodes,
                      eff_nodes, damage_df, g_type):
    # When the nodes acts as both demand and supply.
    # For example, traffic analysis zone in transportation network. This
    # calculates, efficiency loss (EFL),
    # weighted connectivity loss (WCL),partial connectivity loss(PCL).
    # Simple connectivity loss (SCL) doesnt make any sense in this case.

    # To store the information of the performance indicators at connectivity
    # level
    taz_cl = exposure_df[exposure_df['supply_or_demand'] == 'TAZ'].iloc[:, 0:1]
    node_el = exposure_df[exposure_df['type'] == 'node'].iloc[:, 0:1]

    pcl_table = pd.DataFrame({'id': TAZ_nodes})
    wcl_table = pd.DataFrame({'id': TAZ_nodes})
    eff_table = pd.DataFrame({'id': eff_nodes})
    eff_table.set_index("id", inplace=True)
    pcl_table.set_index('id', inplace=True)
    wcl_table.set_index('id', inplace=True)

    # Create an empty dataframe with columns "event_id" and
    # "CCL"/"PCL"/"WCL"/"EFFLoss"
    event_connectivity_loss_pcl = pd.DataFrame(columns=['event_id', 'PCL'])
    event_connectivity_loss_wcl = pd.DataFrame(columns=['event_id', 'WCL'])
    event_connectivity_loss_eff = pd.DataFrame(columns=['event_id', 'EFFLoss'])

    # To check the the values for each node before the earthquake event
    # For calculating partialy connectivity loss
    for i in TAZ_nodes:
        count = 0
        for j in TAZ_nodes:
            if i != j:
                if nx.has_path(G_original, j, i):
                    count = count + 1
        pcl_table.at[i, 'NS0'] = count

    # Code below is not giving correct answer because the path is checked from
    # a TAZ to every other TAZ
    # but this will include itself as well. in the above code it is done by
    # specifying (if i !=j)
    # pcl_table['NS0'] = [sum(nx.has_path(G_original, j, i) for j in TAZ_nodes)
    # for i in TAZ_nodes]

    # For calculating weighted connectivity loss
    # If the weights is not provided, then the weights of each edges is
    # considered to be one.
    att = nx.get_edge_attributes(G_original, 'weights')
    for i in TAZ_nodes:
        if not att:
            path_lengths = [
                nx.shortest_path_length(G_original, j, i)
                for j in TAZ_nodes if nx.has_path(G_original, j, i)]
            countw = sum(
                [1/path_length for path_length in path_lengths
                 if path_length != 0])
        else:
            path_lengths = [
                nx.shortest_path_length(G_original, j, i, weight='weights')
                for j in TAZ_nodes if nx.has_path(G_original, j, i)]
            countw = sum(
                [1/path_length for path_length in path_lengths
                 if path_length != 0])
        wcl_table.at[i, 'WS0'] = countw * pcl_table.at[i, 'NS0']
    # For calculating efficiency loss
    N = len(G_original)
    att = nx.get_edge_attributes(G_original, 'weights')
    for node in G_original:
        if not att:
            lengths = nx.single_source_shortest_path_length(G_original, node)
            inv = [1/x for x in lengths.values() if x != 0]
            eff_node = (sum(inv))/(N-1)
        else:
            lengths = nx.single_source_dijkstra_path_length(
                G_original, node, weight="weights")
            inv = [1/x for x in lengths.values() if x != 0]
            eff_node = (sum(inv))/(N-1)
        eff_table.at[node, 'Eff0'] = eff_node

    for event_id, event_damage_df in damage_df.groupby("event_id"):
        G = G_original.copy()
        nodes_damage_df = event_damage_df.loc[
            event_damage_df.type == "node"].droplevel(level=0)
        edges_damage_df = event_damage_df.loc[
            event_damage_df.type == "edge"].droplevel(level=0)

        # Updating the graph to remove damaged edges and nodes
        nonfunctional_edges_df = edges_damage_df.loc[
            ~edges_damage_df.is_functional]
        nonfunctional_nodes_df = nodes_damage_df.loc[
            ~nodes_damage_df.is_functional]

        # This is done to handle the the multi graph where more that one edge
        # is possible between two nodes.
        # If it is a multi graph then every edge has a key value
        if g_type == "MultiGraph" or g_type == "MultiDiGraph":
            edges_to_remove = [
                (u, v, key)
                for (u, v, key, data) in G.edges(keys=True, data=True)
                if data['id'] in nonfunctional_edges_df.index.to_list()]
        else:
            edges_to_remove = [
                (u, v) for (u, v, data) in G.edges(data=True)
                if data['id'] in nonfunctional_edges_df.index.to_list()]

        G.remove_edges_from(edges_to_remove)
        G.remove_nodes_from(nonfunctional_nodes_df.index.to_list())

        # Checking if there is a path between any souce to each demand node
        # Some demand nodes and source nodes may have been eliminated from
        # the network due to damage, so we do not need to check their
        # functionalities
        extant_TAZ_nodes = sorted(set(TAZ_nodes) & set(G.nodes))
        extant_eff_nodes = sorted(set(eff_nodes) & set(G.nodes))

        # If demand nodes are damaged itself (Example, building collapsed where
        # demand node is considered)
        pcl_table.loc[~pcl_table.index.isin(extant_TAZ_nodes), 'NS'] = 0
        wcl_table.loc[~wcl_table.index.isin(extant_TAZ_nodes), 'WS'] = 0
        eff_table.loc[~eff_table.index.isin(extant_eff_nodes), 'Eff'] = 0

        for i in extant_TAZ_nodes:
            count = 0
            for j in extant_TAZ_nodes:
                if i != j:
                    if nx.has_path(G, j, i):
                        count = count + 1
            pcl_table.at[i, 'NS'] = count

        for i in extant_TAZ_nodes:
            if not att:
                path_lengths = [
                    nx.shortest_path_length(G, j, i)
                    for j in extant_TAZ_nodes if nx.has_path(G, j, i)]
                countw1 = sum(
                    [1/path_length for path_length in path_lengths
                     if path_length != 0])
            else:
                path_lengths = [
                    nx.shortest_path_length(G, j, i, weight='weights')
                    for j in extant_TAZ_nodes if nx.has_path(G, j, i)]
                countw1 = sum(
                    [1/path_length for path_length in path_lengths
                     if path_length != 0])

            wcl_table.at[i, 'WS'] = countw1 * pcl_table.at[i, 'NS']

        for node in G:
            if not att:
                lengths = nx.single_source_shortest_path_length(G, node)
                inv = [1/x for x in lengths.values() if x != 0]
                eff_node = (sum(inv))/(N-1)
            else:
                lengths = nx.single_source_dijkstra_path_length(
                    G, node, weight="weights")
                inv = [1/x for x in lengths.values() if x != 0]
                eff_node = (sum(inv))/(N-1)
            eff_table.at[node, 'Eff'] = eff_node

        # Connectivity Loss for each node
        pcl_table['PCL_node'] = 1 - (pcl_table['NS']/pcl_table['NS0'])
        wcl_table['WCL_node'] = 1 - (wcl_table['WS']/wcl_table['WS0'])
        # This is done so that if the initial graph has a node disconnected,
        # will raise an error when calculating the efficiency loss
        eff_table['Eff_loss'] = (
            eff_table.Eff0 - eff_table.Eff)/eff_table.Eff0.replace({0: np.nan})
        eff_table['Eff_loss'] = eff_table['Eff_loss'].fillna(0)

        # Computing the mean of the connectivity loss to consider the overall
        # performance of the area (at global level)
        PCL_mean_per_event = pcl_table['PCL_node'].mean()
        WCL_mean_per_event = wcl_table['WCL_node'].mean()
        Glo_eff0_per_event = eff_table['Eff0'].mean()
        Glo_eff_per_event = eff_table['Eff'].mean()
        Glo_effloss_per_event = (
            Glo_eff0_per_event - Glo_eff_per_event)/Glo_eff0_per_event

        # Storing the value of performance indicators for each event
        event_connectivity_loss_pcl = event_connectivity_loss_pcl.append(
            {'event_id': event_id, 'PCL': PCL_mean_per_event},
            ignore_index=True)
        event_connectivity_loss_wcl = event_connectivity_loss_wcl.append(
            {'event_id': event_id, 'WCL': WCL_mean_per_event},
            ignore_index=True)
        event_connectivity_loss_eff = event_connectivity_loss_eff.append(
            {'event_id': event_id, 'EFFLoss': Glo_effloss_per_event},
            ignore_index=True)

        # To store the sum of performance indicator at nodal level to calulate
        # the average afterwards
        pcl_table1 = pcl_table.drop(columns=['NS0', 'NS'])
        pcl_table1 = pcl_table1.reset_index()
        taz_cl = pd.concat(
            (taz_cl, pcl_table1)).groupby('id', as_index=False).sum()

        wcl_table1 = wcl_table.drop(columns=['WS0', 'WS'])
        wcl_table1 = wcl_table1.reset_index()
        taz_cl = pd.concat(
            (taz_cl, wcl_table1)).groupby('id', as_index=False).sum()

        eff_table1 = eff_table.drop(columns=['Eff0', 'Eff'])
        eff_table1 = eff_table1.reset_index()
        node_el = pd.concat(
            (node_el, eff_table1)).groupby('id', as_index=False).sum()

    return (taz_cl, node_el, event_connectivity_loss_pcl,
            event_connectivity_loss_wcl, event_connectivity_loss_eff)


def EFL_node(exposure_df, G_original, eff_nodes, damage_df, g_type):
    # when no information about supply or demand is given or known,
    # only efficiency loss is calculated for all nodes

    # To store the information of the performance indicators at connectivity
    # level
    node_el = exposure_df[exposure_df['type'] == 'node'].iloc[:, 0:1]

    eff_table = pd.DataFrame({'id': eff_nodes})
    eff_table.set_index("id", inplace=True)

    # Create an empty dataframe with columns "event_id" and "EFFLoss"
    event_connectivity_loss_eff = pd.DataFrame(columns=['event_id', 'EFFLoss'])

    # To check the the values for each node before the earthquake event
    # For calculating efficiency
    N = len(G_original)
    att = nx.get_edge_attributes(G_original, 'weights')
    for node in G_original:
        if not att:
            lengths = nx.single_source_shortest_path_length(G_original, node)
            inv = [1/x for x in lengths.values() if x != 0]
            eff_node = (sum(inv))/(N-1)
        else:
            lengths = nx.single_source_dijkstra_path_length(
                G_original, node, weight="weights")
            inv = [1/x for x in lengths.values() if x != 0]
            eff_node = (sum(inv))/(N-1)
        eff_table.at[node, 'Eff0'] = eff_node

    # After eathquake
    for event_id, event_damage_df in damage_df.groupby("event_id"):
        G = G_original.copy()
        nodes_damage_df = event_damage_df.loc[
            event_damage_df.type == "node"].droplevel(level=0)
        edges_damage_df = event_damage_df.loc[
            event_damage_df.type == "edge"].droplevel(level=0)

        # Updating the graph to remove damaged edges and nodes
        nonfunctional_edges_df = edges_damage_df.loc[
            ~edges_damage_df.is_functional]
        nonfunctional_nodes_df = nodes_damage_df.loc[
            ~nodes_damage_df.is_functional]
        # nonfunctional_edge_tuples = list(
        #     zip(nonfunctional_edges_df.start_node,
        #         nonfunctional_edges_df.end_node)
        # )
        if g_type == "MultiGraph" or g_type == "MultiDiGraph":
            edges_to_remove = [
                (u, v, key)
                for (u, v, key, data) in G.edges(keys=True, data=True)
                if data['id'] in nonfunctional_edges_df.index.to_list()]
        else:
            edges_to_remove = [
                (u, v) for (u, v, data) in G.edges(data=True)
                if data['id'] in nonfunctional_edges_df.index.to_list()]

        G.remove_edges_from(edges_to_remove)
        # G.remove_edges_from(nonfunctional_edge_tuples)
        G.remove_nodes_from(nonfunctional_nodes_df.index.to_list())

        # Checking if there is a path between any souce to each demand node
        # Some demand nodes and source nodes may have been eliminated from
        # the network due to damage, so we do not need to check their
        # functionalities
        extant_eff_nodes = sorted(set(eff_nodes) & set(G.nodes))

        # If demand nodes are damaged itself (Example, building collapsed where
        # demand node is considered)
        eff_table.loc[~eff_table.index.isin(extant_eff_nodes), 'Eff'] = 0

        # To check the the values for each node after the earthquake event
        for node in G:
            if not att:
                lengths = nx.single_source_shortest_path_length(G, node)
                inv = [1/x for x in lengths.values() if x != 0]
                eff_node = (sum(inv))/(N-1)
            else:
                lengths = nx.single_source_dijkstra_path_length(
                    G, node, weight="weights")
                inv = [1/x for x in lengths.values() if x != 0]
                eff_node = (sum(inv))/(N-1)
            eff_table.at[node, 'Eff'] = eff_node

        # Efficiency Loss for each node
        # This is done so that if the initial graph has a node disconnected,
        # will raise an error when calculating the efficiency loss
        eff_table['Eff_loss'] = (
            eff_table.Eff0 - eff_table.Eff)/eff_table.Eff0.replace({0: np.nan})
        eff_table['Eff_loss'] = eff_table['Eff_loss'].fillna(0)

        # Computing the mean of the connectivity loss to consider the overall
        # performance of the area (at global level)
        Glo_eff0_per_event = eff_table['Eff0'].mean()
        Glo_eff_per_event = eff_table['Eff'].mean()
        Glo_effloss_per_event = (
            Glo_eff0_per_event - Glo_eff_per_event)/Glo_eff0_per_event

        # Storing the value of performance indicators for each event
        event_connectivity_loss_eff = event_connectivity_loss_eff.append(
            {'event_id': event_id, 'EFFLoss': Glo_effloss_per_event},
            ignore_index=True)

        # To store the sum of performance indicator at nodal level to calulate
        # the average afterwards
        eff_table1 = eff_table.drop(columns=['Eff0', 'Eff'])
        eff_table1 = eff_table1.reset_index()
        node_el = pd.concat(
            (node_el, eff_table1)).groupby('id', as_index=False).sum()

    return node_el, event_connectivity_loss_eff
