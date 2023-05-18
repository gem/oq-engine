import pandas as pd


# function provided by Astha Poudel and Anirudh Rao
def analysis(dstore):
    """
    Performs a connectivity analysis. Assumes the datastore contains
    an exposure with `supply_or_demand` and all the needed stuff.

    :returns:  (functional_demand_nodes, avg_connectivity_loss)
    """
    import networkx as nx  # import only if needed

    oq = dstore["oqparam"]
    calculation_mode = oq.calculation_mode
    assert calculation_mode in ("event_based_damage", "scenario_damage")

    assetcol = dstore["assetcol"]
    tagnames = sorted(tn for tn in assetcol.tagnames if tn != "id")
    tags = {t: getattr(assetcol.tagcol, t) for t in tagnames}
    exposure_df = assetcol.to_dframe().replace(
        {
            tagname: {i: tag for i, tag in enumerate(tags[tagname])}
            for tagname in tagnames
        }
    ).set_index("id")

    source_nodes = exposure_df.loc[
        exposure_df.supply_or_demand == "source"].index.to_list()
    demand_nodes = exposure_df.loc[
        exposure_df.supply_or_demand == "demand"].index.to_list()

    # Create the graph and add edge and node attributes
    G_original = nx.from_pandas_edgelist(
        exposure_df.loc[exposure_df.type == "edge"],
        source="start_node",
        target="end_node",
        edge_attr=True,
    )
    nx.set_node_attributes(
        G_original,
        exposure_df.loc[exposure_df.type == "node"].to_dict("index"))

    agg_keys = pd.DataFrame(
        {"id": [key.decode() for key in dstore["agg_keys"][:]]})
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
    )[["type", "start_node", "end_node", "is_functional"]]
    full_damage_df = (
        pd.DataFrame(
            index=pd.MultiIndex.from_product(
                [damage_df.index.levels[0], exposure_df.index]
            ),
        )
        .join(exposure_df.supply_or_demand)
        .join(damage_df.is_functional)
        .fillna(True)
    )

    for event_id, event_damage_df in damage_df.groupby("event_id"):
        G = G_original.copy()
        nodes_damage_df = event_damage_df.loc[
            event_damage_df.type == "node"].droplevel(level=0)
        edges_damage_df = event_damage_df.loc[
            event_damage_df.type == "edge"].droplevel(level=0)

        # Updating the graph to remove damaged edges and nodes
        nonfunctional_edges_df = edges_damage_df.loc[
            edges_damage_df.is_functional == 0]
        nonfunctional_nodes_df = nodes_damage_df.loc[
            nodes_damage_df.is_functional == 0]
        nonfunctional_edge_tuples = list(
            zip(nonfunctional_edges_df.start_node,
                nonfunctional_edges_df.end_node))
        G.remove_edges_from(nonfunctional_edge_tuples)
        G.remove_nodes_from(nonfunctional_nodes_df.index.to_list())

        # Checking if there is a path between any souce to each demand node
        # Some demand nodes and source nodes may have been eliminated from
        # the network due to damage, so we do not need to check them
        extant_demand_nodes = sorted(set(demand_nodes) & set(G.nodes))
        extant_source_nodes = set(source_nodes) & set(G.nodes)
        full_damage_df.loc[
            (event_id, extant_demand_nodes), "is_functional"] = [
            any(
                [
                    nx.has_path(G, demand_node, source_node)
                    for source_node in extant_source_nodes
                ]
            )
            for demand_node in extant_demand_nodes
        ]

    demand_nodes_is_functional = (
        full_damage_df.loc[full_damage_df.supply_or_demand == "demand"]
        .groupby("id")
        .sum()
        .is_functional
    )  # a Series
    num_ok_nodes = pd.DataFrame(
        {'id': demand_nodes_is_functional.index,
         'number': list(demand_nodes_is_functional)}
    ).sort_values('id')
    sum_connectivity_loss = sum(
        1
        - full_damage_df.loc[full_damage_df.supply_or_demand == "demand"]
        .groupby("event_id")
        .sum()
        .is_functional
        / len(demand_nodes)
    )
    if calculation_mode == "event_based_damage":
        inv_time = oq.investigation_time
        ses_per_ltp = oq.ses_per_logic_tree_path
        num_lt_samples = oq.number_of_logic_tree_samples
        eff_inv_time = inv_time * ses_per_ltp * num_lt_samples
        avg_connectivity_loss = sum_connectivity_loss / eff_inv_time
    elif calculation_mode == "scenario_damage":
        num_events = len(damage_df.reset_index().event_id.unique())
        avg_connectivity_loss = sum_connectivity_loss / num_events
    return num_ok_nodes, avg_connectivity_loss
