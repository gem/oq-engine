Stochastic Event-based Damage Demo
----------------------------------

In this example, we study the sensitivity from the `random_seed` parameter
for an event based damage calculation with 50 samples taken from 486
potential realizations. The single command

$ oq engine --run job.ini

will generate three calculations, respectively with random_seed = 100, 200
and 300, each one with an effective investigation time of 100,000 years.
The damage distributions will have differences within 10%.

**Expected Runtimes and Outputs**

Expected runtime for event damage calculation: < 5 minutes

Outputs:

- Aggregate Risk Curves
- Aggregated Risk By Event
- Asset Damage Distributions
- Earthquake Ruptures
- Ground Motion Fields
