Logic tree sampling strategies
==============================

Stating from version 3.10, the OpenQuake engine suppports 4 different
strategies for sampling the logic tree. They are called, respectively,
``early_weights``, ``late_weights``, ``early_latin``, ``late_latin``.
Here we will discuss how they work.

First of all, we must point out that logic tree sampling is controlled
by three parameters in the job.ini:

- number_of_logic_tree_samples (default 0, no sampling)
- sampling_method (default ``early_weights``)
- random_seed (default 42)

When sampling is enabled ``number_of_logic_tree_samples`` is a positive
number, equal to the number of branches to be randomly extracted from
full logic tree of the calculation. The precise why the random extraction
works depends on the sampling method.

early_weights
  We this sampling method, the engine randomly choose branches depending
  on the weights in the logic tree; having done that, the hazard curve
  statistics (mean and quantiles) are computed with equal weights.

late_weights
  We this sampling method, the engine randomly choose branches ignoring
  the weights in the logic tree; however, the hazard curve
  statistics are computed by taking into account the weights.

early_latin
  We this sampling method, the engine randomly choose branches depending
  on the weights in the logic tree by using an hypercube latin sampling;
  having done that, the hazard curve statistics are computed with equal weights.

late_latin
  We this sampling method, the engine randomly choose branches ignoring
  the weights in the logic tree, but still using an hypercube sampling;
  then, the hazard curve statistics are computed by taking into account
  the weights.

More precisely, the engine calls something like the function

``openquake.hazardlib.lt.random_sample(
    branchsets, num_samples, seed, sampling_method)``

You are invited to play with it; in general the latin sampling produces
samples much closer to the expected weights even with few samples.
Here in an example with two branchsets with weights [.4, .6] and
[.2, .3, .5] respectively.

    >>> bsets = [[('X', .4), ('Y', .6)], [('A', .2), ('B', .3), ('C', .5)]]

With 100 samples one would expect to get the path XA 8 times, XB 12
times, XC 20 times, YA 12 times, YB 18 times, YC 30 times. Instead we get:

    >>> paths = random_sample(bsets, 100, 42, 'early_weights')
    >>> collections.Counter(paths)
    Counter({'YC': 26, 'XC': 24, 'YB': 17, 'XA': 13, 'YA': 10, 'XB': 10})

    >>> paths = random_sample(bsets, 100, 42, 'late_weights')
    >>> collections.Counter(paths)
    Counter({'XA': 20, 'YA': 18, 'XB': 17, 'XC': 15, 'YB': 15, 'YC': 15})

    >>> paths = random_sample(bsets, 100, 42, 'early_latin')
    >>> collections.Counter(paths)
    Counter({'YC': 31, 'XC': 19, 'YB': 17, 'XB': 13, 'YA': 12, 'XA': 8})

    >>> paths = random_sample(bsets, 100, 45, 'late_latin')
    >>> collections.Counter(paths)
    Counter({'YC': 18, 'XA': 18, 'XC': 16, 'YA': 16, 'XB': 16, 'YB': 16})
