
**Infrastructure Multi-Peril Demo**

This demo showcases a Multi-Peril risk calculator using a small infrastructure
 network with four nodes and four edges. The model evaluates the combined 
 effects of ground shaking, landslides, and liquefaction to generate risk outputs.

Each peril is associated with a specific fragility model. The mapping file 
(`mapping_multiple_loss_types.csv`) links building classes to their respective
 fragility function IDs for each peril. The consequence file 
 (`consequence_multiple_loss_types.csv`) defines the consequences of each 
 damage state across all building classes and perils.

Expected runtime: ~ 10 seconds

Outputs: 
- Events
- Ground Motion Fields
- Aggregate Risk Statistics
- Aggregated Risk by Event
- Average Asset Risk Distributions
- Average Asset Risk Statistics
- Average Infrastructure Loss
- Efficiency Loss of Nodes
- Efficiency Loss by Event

