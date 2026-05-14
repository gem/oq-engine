# Test case for mutually exclusive sources

This test uses the functionalities implemented in the OpenQuake-engine to compute ruptures using mutually exclusive sources.

1. `source_model.xml` contains 10 non-parametric seismic sources (IDs sag:01 through sag:10), each representing a distinct rupture scenario ("CASE 1" through "CASE 10") for the Sagami Trough, near the Tokyo/Kanto region of Japan. Occurrence probabilities for all the sources are 0.984 (no rupture) and 0.016 (rupture) for the 50-year investigation period.

2. `ssm.xml` contais one group with 3 non-parametric seismic sources that are mutually exclusive. The probability of occurrence of the group in the investigation time is 0.01. All the sources have an occurrence probability equal to 1.

The source model 1 has a weight of 0.2 and the source model 2 has a weight of 0.8.

For 10000 hypothetical simulations we expect
- 2000 realisations on model 1 
- 8000 realizations of model 2 

This means on average:
- 32 ruptures from model 1 
- 80 ruptures from model 2 
totalling 112 events.

By setting in the `job.ini` 100 stochastic event set per logic tree sample and 10000 realizations (10.000.000 years) we obtain 11_226. This number is quite consistent with the figures provided above.
