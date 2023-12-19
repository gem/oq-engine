.. _infrastructure:

Infrastructure
==============

Critical infrastructures are represented as graph-like components consisting of nodes/vertices connected by edges/links. 
The graph can be simple undirected, directed, multi or multidirected type. To each of these types, the graph can be 
weighted or unweighted. If not specified, the default is simple unweighted undirected graph. In order to generate the 
graphs, the adjustment should be made in the **exposure.csv** file. Additional to the usual information, it should also 
include the columns **type**, **start_node**, **end_node**, **demand_or_supply**.

A snippet of exposure model for nodes and edges for a simple unweighted graph is shown in the next two figures.

.. figure:: _images/infrastructure-nodes.png

Example of the exposure model of nodes of the infrastructure

.. figure:: _images/infrastructure-edges.png

Example of the exposure model of edges of the infrastructure

If the weights are to be added, there should be a column name **weights**, and weights can be travel time, distance, 
importance factor, etc., according to the user requirement.

*Note: If weight is not present, it assigns 1 as weight to every edge while calculating Weighted Connectivity Loss(WCL) and Efficiency Loss(EL)*

If the user wants to specify the graph type, another column **graphtype** must be added. It can be either "directed", 
"multi", "multidirected" or "simple".

Hazard model and fragility model are similar to other comuptations. In order to do the network analysis, it is important 
to define if each component is functional/operational or not, which is defined by the damage states. For this, an 
additional consequence model is necessary (see next figure). As of now, only the 
binary state is considered i.e "functional/operational" or "non-functional/non-operational".

.. figure:: _images/infrastructure-consequence-model.png

Example of the consequence model (Note: 0 implies still operational and 1 implies non-operational)