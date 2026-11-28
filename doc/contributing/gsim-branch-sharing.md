# Sharing GSIM computations across logic-tree branches

## The problem

A logic tree of a large model, such as the European model (EUR), contains
many branches. Some of them use the same GMPE, and differ only in an option
that shifts the median, like `sigma_mu_epsilon`. For instance, in EUR there
can be up to 19 GMPEs per tectonic region type, and the same GMPE can appear
in several branches, each with a different `sigma_mu_epsilon`.

Before this design, each branch computed the whole ground-motion model
from scratch, even though the expensive part of the computation (the
backbone, which depends on the rupture and the site, but not on the shift)
was the same for all of them.

## The idea

The computation of a GMPE is split in two parts:

1. the *central* part, which does not depend on the branch options and is
   computed once for all the branches that share it;
2. the *adjustment*, which applies the shift of a single branch and is cheap.

A GSIM class that can share its computation declares two methods:

- `compute_adj(self, ctx, imts, mean_stds)` computes the central part. It
  fills `mean_stds`, which holds the arrays `(mean, sig, tau, phi)` of shape
  `(M, N)`, in place, where `M` is the number of IMTs and `N` is the size of
  the context array `ctx`. It returns a dictionary mapping names to arrays,
  which is empty when there is nothing to share.
- `update_adj(self, ctx, imts, mean_stds, adj, sigma_mu_epsilon)` applies
  the adjustment of one branch. Its arguments after `mean_stds` and `adj`
  must be constructor options of the GSIM: `sigma_mu_epsilon` in the example.

The `compute` method of the GSIM is not written by hand: the metaclass
`MetaGSIM` generates it from the two methods, so that direct calls run
`compute_adj` followed by `update_adj`.

## Example: a GMPE with several sigma_mu_epsilon values

Consider a GMPE with the epistemic shift `sigma_mu_epsilon`, used in three
branches of the EUR model with values `-1`, `0` and `1`:

```python
import numpy as np

from openquake.hazardlib.gsim.base import GMPE


class MyGMPE(GMPE):
    def __init__(self, sigma_mu_epsilon=0.0):
        self.sigma_mu_epsilon = sigma_mu_epsilon

    def compute_adj(self, ctx, imts, mean_stds):
        mean, sig, tau, phi = mean_stds
        ...  # fill mean, sig, tau and phi, which do not depend on the shift
        # the precomputed arrays needed by update_adj, of shape (M, N)
        sigma_mu = np.array([get_sigma_mu(imt, ctx) for imt in imts])
        return {'sigma_mu': sigma_mu}

    def update_adj(self, ctx, imts, mean_stds, adj, sigma_mu_epsilon):
        mean = mean_stds[0]
        if sigma_mu_epsilon:
            mean += sigma_mu_epsilon * adj['sigma_mu']  # or any shift
```

The dictionary returned by `compute_adj` holds the arrays that `update_adj`
needs: here `sigma_mu`, computed once for the group rather than once per
branch. A GSIM that needs nothing else can return an empty dictionary.

The three branches have the same central options, so they share one central
key. When the ContextMaker computes the mean and standard deviations:

1. `compute_adj` runs once for the group, filling the arrays of the first
   branch;
2. the arrays are copied to the other branches;
3. `update_adj` runs once per branch, with that branch's `sigma_mu_epsilon`.

Without the sharing, `compute` would run three times, once per branch. With
the sharing it runs once, and the three branches only pay for the cheap
update.

The options of `update_adj` are excluded from the central key, which is the
part of the constructor options that decides whether two branches can share
the central computation. Branches with the same key are grouped together.
The key is computed once, when the GSIM is built, so the options must not
change after construction.

## Which GSIMs share

A class shares its computation when it defines, or inherits, both
`compute_adj` and `update_adj`:

- a class that defines `compute_adj` and `update_adj` (or inherits one of
  them, together with the other) gets a generated `compute`;
- a class that defines a plain `compute` opts out of the sharing: its
  branches are computed one by one, as before;
- a class for which `compute_adj` or `update_adj` is missing, both in the
  class and in its parent, is an error, and so is a class that defines
  `compute` in the same body as `compute_adj` or `update_adj`.

A subclass can override `compute_adj` or `update_adj` and call the parent's
method with `super()`. The generated `compute` of the parent applies only the
adjustment of the parent.

The first argument of `update_adj` is the GSIM, whatever its name, and
`self` is accepted as well.

## Existing GSIMs keep working

GSIMs written with a plain `compute` method, which is how all the GSIMs of
the engine were written so far, keep working without any change. They are
treated as before, and their results are the same. They just do not get the
performance improvement, because each of their branches still runs the full
computation.

Only the GSIMs that are converted to `compute_adj` and `update_adj` get the
speed-up. In the repository, the converted classes are the ones that have
a shift of the median as a branch option, such as the NSHM epistemic shift
(`sigma_mu_epsilon`) and the source-region scaling (`dl2l`), plus the
ModifiableGMPE modifiers and the grid-based adjustments.

## Schedule

The work is scheduled for the engine 3.28 release.
