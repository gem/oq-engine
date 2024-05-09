# FAQ about running risk calculations

### What implications do `random_seed`, `ses_seed`, and `master_seed` have on my calculation?

The OpenQuake engine uses (Monte Carlo) sampling strategies for
propagating epistemic uncertainty at various stages in a calculation.
The sampling is based on numpy's pseudo-random number generator.
Setting a 'seed' is useful for controlling the initialization of the 
random number generator, and repeating a calculation using the same
seed should result in identical random numbers being generated each time.

Three different seeds are currently recognized and used by the OpenQuake
engine.

1. `random_seed` is the seed that controls the sampling of branches 
from both the source model logic tree and the ground motion model logic tree,
when the parameter `number_of_logic_tree_samples` is non-zero.
It affects both classical calculations and event based calculations.

2. `ses_seed` is the seed that controls the sampling of the ruptures
in an event based calculation (but notice that the generation of
ruptures is also affected by the `random_seed`, unless full
enumeration of the logic tree is used, due to the reasons mentioned in
the previous paragraph). It is also used to generate rupture seeds for
both event based and scenario calculations, which are in turn used
for sampling ground motion values / intensities from a Ground Motion Model,
when the parameter `truncation_level` is non-zero. NB: before engine
3.11, sampling ground motion values / intensities from a GMM in
a scenario calculation was incorrectly controlled by the `random_seed`
and not the `ses_seed`.

3. `master_seed` is used when generating the epsilons in a calculation 
involving vulnerability functions with non-zero coefficients of 
variations. This is a purely risk-related seed, while the previous 
two are hazard-related seeds.

### What values should I use for `investigation_time`, `ses_per_logic_tree_path`, and `number_of_logic_tree_samples` in my calculation? And what does the `risk_investigation_time` parameter for risk calculations do?

Setting the `number_of_logic_tree_samples` is relatively straightforward. This
parameter controls the method used for propagation of epistemic uncertainty
represented in the logic-tree structure and calculation of statistics such as
the mean, median, and quantiles of key results.

`number_of_logic_tree_samples = 0` implies that the engine will perform a
so-called 'full-enumeration' of the logic-tree, i.e., it will compute the
requested results for every end-branch, or 'path' in the logic-tree. Statistics
are then computed with consideration of the relative weights assigned to each
end-branch.

For models that have complex logic-trees containing thousands, or even millions
of end-branches, a full-enumeration calculation will be computationally
infeasible. In such cases, a sampling strategy might be more preferable and much
more tractable. Setting, for instance, `number_of_logic_tree_samples = 100`
implies that the engine will randomly choose (i.e., 'sample') 100 end-branches
from the complete logic-tree based on the weight assignments. The requested
results will be computed for each of these 100 sampled end-branches. Statistics
are then computed using the results from the 100 sampled end-branches, where the
100 sampled end-branches are considered to be equi-weighted (1/100 weight for
each sampled end-branch). Note that once the end-branches have been chosen for
the calculation, the initial weights assigned in the logic-tree files have no
further role to play in the computation of the statistics of the requested
results. As mentioned in the previous section, changing the `random_seed` will
result in a different set of paths or end-branches being sampled.

The `risk_investigation_time` parameter is also fairly straightforward. It
affects only the risk part of the computation and does not affect the hazard
calculations or results. Two of the most common risk metrics are (1) the
time-averaged risk value (damages, losses, fatalities) for a specified
time-window, and (2) the risk values (damages, losses, fatalities) corresponding
to a set of return periods. The `risk_investigation_time` parameter controls the
time-window used for computing the former category of risk metrics.
Specifically, setting `risk_investigation_time = 1` will produce _average
annual_ risk values; such as average annual collapses, average annual losses,
and average annual fatalities. This parameter does not affect the computation of
the latter category of risk metrics. For example, the loss exceedance curves
will remain the same irrespective of the value set for
`risk_investigation_time`, provided all other parameters are kept the same.

Next, we come to the two parameters `investigation_time` and
`ses_per_logic_tree_path`.

If the hazard model includes time-dependent sources, the choice of the
`investigation_time` will most likely be dictated by the source model(s), and
the engine will raise an error unless you set the value to that required by the
source model(s). In this case, the `ses_per_logic_tree_path` parameter can be
used to control the effective length of the stochastic event-set (or event
catalog) for each end-branch, or 'path', for both full-enumeration and
sampling-based calculations. As an example, suppose that the hazard model
requires you to set `investigation_time = 1`, because the source model defines
1-year occurrence probabilities for the seismic sources. Further, suppose you
have decided to sample 100 branches from the complete logic-tree as your
strategy to propagate epistemic uncertainty. Now, setting
`ses_per_logic_tree_path = 10000` will imply that the engine will generate
10,000 'event-sets' for each of the 100 sampled branches, where each 'event-set'
spans 1 year. Note that some of these 1-year event-sets could be empty, implying
that no events were generated in those particular 1-year intervals.

On the other hand, if the hazard model contains only time-independent sources,
there is no hard constraint on the `investigation_time` parameter. In this case,
the `ses_per_logic_tree_path` parameter can be used in conjunction with the
`investigation_time` to control the effective length of the stochastic event-set
(or event catalog) for each end-branch, or 'path', for both full-enumeration and
sampling-based calculations. For instance, the following three calculation
settings would produce statistically equivalent risk results:

**Calculation 1**
```ini
number_of_logic_tree_samples = 0
investigation_time = 1
ses_per_logic_tree_path = 10000
risk_investigation_time = 1
```

**Calculation 2**
```ini
number_of_logic_tree_samples = 0
investigation_time = 50
ses_per_logic_tree_path = 200
risk_investigation_time = 1
```

**Calculation 3**
```ini
number_of_logic_tree_samples = 0
investigation_time = 10000
ses_per_logic_tree_path = 1
risk_investigation_time = 1
```

The effective catalog length per branch in such cases is `investigation_time ×
ses_per_logic_tree_path`. The choice of how to split the effective catalog
length amongst the two parameters is up to the modeller/analyst's preferrence,
and there are no performance implications for perferring particular choices.

Note that if you were also computing hazard curves and maps in the above
example calculations, the hazard curves output in the first calculation would
provide probabilities of exceedance in 1 year, whereas the hazard curves
output in the second calculation would provide probabilities of exceedance in
50 years. All _**risk**_ results for the three calculations will be
statistically identical.


### Can I disaggregate my losses by source?

Starting from engine 3.10 you can get a summary of the total losses across your
portfolio of assets arising from each seismic source, over the effective
investigation time. 
For instance run the event based risk demo as follows:
```bash
$ oq engine --run job.ini
```
and export the output "Source Loss Table".
You should see a table like the one below:

| source | loss_type     | loss_value  |
|--------|---------------|-------------|
| 231    | nonstructural | 1.07658E+10 |
| 231    | structural    | 1.63773E+10 |
| 386    | nonstructural | 3.82246E+07 |
| 386    | structural    | 6.18172E+07 |
| 238    | nonstructural | 2.75016E+08 |
| 238    | structural    | 4.58682E+08 |
| 239    | nonstructural | 4.51321E+05 |
| 239    | structural    | 7.62048E+05 |
| 240    | nonstructural | 9.49753E+04 |
| 240    | structural    | 1.58884E+05 |
| 280    | nonstructural | 6.44677E+03 |
| 280    | structural    | 1.14898E+04 |
| 374    | nonstructural | 8.14875E+07 |
| 374    | structural    | 1.35158E+08 |
| ⋮      | ⋮             | ⋮           |

from which one can infer the sources causing the highest total losses for
the portfolio of assets within the specified effective investigation time.


### How does the engine compute loss curves (a.k.a. Probable Maximum Losses)?

The PML for a given return period is built from the losses in the event loss
table. The algorithm used is documented in detail in the [advanced
manual](https://docs.openquake.org/oq-engine/advanced/latest/event_based.html#the-probable-maximum-loss-pml-and-the-loss-curves) at
the end of the section about risk calculations. The section also explains
why sometimes the PML or the loss curves contain NaN values (the
effective investigation time is too short compared to the return period).
Finally, it also explains why the PML is not additive.
