Infrastructure Results
======================

- For the classic generic case where "demand" and "supply" are explicity mentioned in the column **demand_or_supply**, all four metrics are computed for overall network. Also, at nodal level, all the four metrics are calculated.
- If some nodes behave as both supply and demand, and are assigned as "both" or "TAZ" (traffic analysis zone) in the column **demand_or_supply**, PCL, WCL and EL are computed for both nodal level and overall network.
- If there is no assignment of "demand" or "supply" to the column **demand_or_supply**, only EL is computed for overall network. Also, at nodal level, for all the nodes, EL only is computed.

For the simplification, the next figure has been added to understand what can be obtained by various specifications.

.. figure:: _images/infrastructure-output-by-nodes-func.png

Output computed from the implementation according to the specification of the function of the nodes

Mainly, the library, NetworkX (Aric et al. 2008) has been used during the implementation. Further details can be found 
in Poudel et al. 2023. Also, much concept during the implementation has been drawn from Pitilakis et al. 2014.