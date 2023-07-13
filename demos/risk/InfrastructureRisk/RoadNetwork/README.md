Road Network Demo
-----------------

In this example, we present a grid-like road network with 29 nodes and 38
edges. The exposure model is prepared for both node- and edge-like components.
The road network consists of road segments, bridges, connections and TAZ
(Traffic Analysis Zone) nodes. The information of the `start_node` and
`end_node` of each edge indicated how components are interlinked. With all the
attributes from the exposure model, the network is created.

In the `expo_demo_edges`, the location is for the centroid of the edges. The
weights refer to the lengths and thus the graph is weighted.

As seen in the `expo_demo_nodes`, we have the nodes acting as TAZ. Therefore,
partial connectivity loss, weighted connectivity loss and efficiency loss are
calculated.

Note: this is an example for the demonstrative purpose and does not represent a
real network.

**Hazard**

Expected runtime: 4 seconds

Outputs:

- Events
- Ground Motion Fields

**Risk**

Expected runtime: 3 seconds

Outputs:

- Aggregate Risk
- Aggregated Risk By Event
- Asset Risk Distributions
- Average Infrastructure Loss
- Connectivity Loss Of TAZ Nodes
- Efficiency Loss Of Nodes
- Efficiency Loss by Event
- Partial Connectivity Loss By Event
- Weighted Connectivity Loss By Event
