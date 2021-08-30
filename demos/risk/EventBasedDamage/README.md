Stochastic Event-based Damage Demo
----------------------------------

This example computes average damage distributions, aggregate damage
distributions and damages at a return period of 500 years for an event
based damage calculation with 50 samples taken from 486 potential
realizations. There are 1047 buildings on 6 assets on 6 distinct sites.

By uncommenting the line

# sensitivity_analysis = {"random_seed": [100, 200, 300]}

it is possible study the sensitivity from the `random_seed`
parameter. The single command

$ oq engine --run job.ini

will generate three calculations, respectively with random_seed = 100, 200
and 300, each one with an effective investigation time of 100,000 years.
The damage distributions will have differences within 10%.

**Expected Runtimes and Outputs**

Expected runtime for event damage calculation: ~1 minute

Outputs:

- Aggregate Risk Curves
- Aggregated Risk By Event
- Asset Damage Distributions
- Earthquake Ruptures
- Ground Motion Fields
