Water Supply Demo
-----------------
In this example, we present a water supply system with 17 nodes and
23 edges. The exposure model is prepared for both node- and edge-like
components. The water supply system consists of pipelines, pumping stations,
tanks, treatment plants, and demand nodes. The information of the the `start_node`
and `end_node` of each edge indicated how components are
interlinked. With all the attributes from the exposure model, the network is
created. The graph considered is unweighted, undirected, and a simple one.

In the `expo_demo_edges`, the location is for the centroid of the edges.

As seen in the `expo_demo_nodes`, we have the nodes acting as demand and source.
Therefore, complete connectivity loss, partial connectivity loss, weighted
connectivity loss and efficiency loss are calculated. Even though all the four
metrics are calculated from the engine, since weights are not considered and
with the proper classification of demand and source node, complete connectivity
loss and partial connectivity loss are only of interest.

Note: this is an example for the demonstrative purpose and does not represent a
real network.

**Hazard**

Expected runtime: 4 seconds

Outputs:

- Events
- Ground Motion Fields

**Risk**

Expected runtime: 4 seconds

Outputs:

- Aggregate Risk
- Aggregated Risk By Event
- Asset Risk Distributions
- Average Infrastructure Loss
- Complete Connectivity Loss By Event
- Connectivity Loss Of Demand Nodes
- Efficiency Loss Of Nodes
- Efficiency Loss by Event
- Partial Connectivity Loss By Event
- Weighted Connectivity Loss By Event
