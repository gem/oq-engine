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

``openquake.hazardlib.random_sample(items, num_samples, seed, sampling_method)``

You are invited to play with it; in general the latin sampling produces
samples very close to the expected weights even with few samples:

    >>> items = random_sample(
    ...         [('A', .2), ('B', .3), ('C', .5)], 10, 42, 'early_weights')
    >>> collections.Counter(it.object for it in items)
    Counter({'C': 6, 'A': 3, 'B': 1})

    >>> items = random_sample(
    ...         [('A', .2), ('B', .3), ('C', .5)], 10, 42, 'late_weights')
    >>> collections.Counter(it.object for it in items)
    Counter({'C': 4, 'B': 3, 'A': 3})

    >>> items = random_sample(
    ...         [('A', .2), ('B', .3), ('C', .5)], 10, 42, 'early_latin')
    >>> collections.Counter(it.object for it in items)
    Counter({'C': 5, 'B': 3, 'A': 2})

    >>> items = random_sample(
    ...         [('A', .2), ('B', .3), ('C', .5)], 10, 42, 'late_latin')
    >>> collections.Counter(it.object for it in items)
    Counter({'A': 4, 'B': 3, 'C': 3})
