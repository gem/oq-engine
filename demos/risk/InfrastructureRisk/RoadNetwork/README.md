Road Network Demo
-----------------
In this example, we present a road network with 29 nodes and 38 edges which is more grid-like. Exposure model is prepared for both node and edge-like components. The road network consists of road segment, bridges, connection and TAZ nodes. The information of the start_node and end_node of each edge gives the information about how components are interlinked. With all the attributes from the exposure model, the network is created. 

In the expo_demo_edges, the location is for the centroid of the edges. The weights refer to the lengths and thus the graph is weighted. 

As seen in the expo_demo_nodes, we have the nodes acting as TAZ (traffic analysis zone). Therefore, partial connectivity loss , weighted connectivity loss and efficiency loss are calculated. 

Note:This is an example for the demonstrative purpose and doesn't represent a real network. 

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
