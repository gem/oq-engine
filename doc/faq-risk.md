# FAQ about running risk calculations

### What effective investigation time should I use in my calculation?

In an event based calculation the effective investigation time is the number

```
  eff_inv_time = investigation_time * ses_per_logic_tree_path * (
      number_of_logic_tre_samples or 1)
```

Setting the investigation time is relatively easy. For instance, the
hazard model could use time-dependent sources (this happens for
South America, the Caribbeans, Japan ...). In that case the
investigation time is fixed by the hazard and the engine will
raise an error unless you set the right one. If the hazard model
contains only time-independent sources you can set whatever
investigation time you want. For instance, if you want to compare
with the hazard curves generated for an investigation time of 50
years (a common value) you should use that. If you have no particular
constraints a common choice is `investigation_time = 10000`.

The problem is to decide how to set `ses_per_logic_tree_path` and
`number_of_logic_tre_samples`. Most hazard model have thousands
of realizations, so using full enumeration is a no go, performance-wise.
Right now (engine 3.3) it is more efficient to use a relatively small
number of samples (say < 100) while the number of SES can be larger.

For instance in the case of the SHARE model for Europe there are 3200
realizations and you could use 50 samples, a reasonable number. Assuming
an investigation time of 1 year, how big should be the parameter
`ses_per_logic_tree_path`?

The answer is: as big as it takes to get statistically significant results.
Statistically significant means that by changing the seed used in the
Montecarlo simulation the results change little. If by changing the seed
your total portfolio loss changes by one order of magnitude then your
choice of `ses_per_logic_tree_path` was incorrect; if it changes by 10%
it is reasonable; if it changes by 1% it is very good.

I did some experiments on Slovenia (a small country that can be run on a laptop)
and the total portfolio loss with
```
investigation_time = 1
number_of_logic_tre_samples = 50
ses_per_logic_tree_path = 200
```
i.e. with an effective investigation time of 10,000 years changes by
of 10%s by changing the `ses_seed` parameter.

If we use `ses_per_logic_tree_path = 2000` i.e. 100,000 years
the change is only 0.3%; if we use `ses_per_logic_tree_path = 20000`
i.e. 1 million years the change is less than 0.2%.

If you want a good convergency in the loss curves
you typically need a very long effective investigation time.
