Limitations of Floating-point Arithmetic
========================================

Most practitioners of numeric calculations are aware that addition 
of floating-point numbers is non-associative; for instance

>>>  (.1 + .2) + .3                                                          
0.6000000000000001

is not identical to

>>> .1 + (.2 + .3)                                                         
0.6

Other floating-point operations, such as multiplication,
are also non-associative. The order in which operations are performed plays 
a role in the results of a calculation.

Single-precision floating-point variables are able to represent integers
between [-16777216, 16777216] exactly, but start losing precision 
beyond that range; for instance:

>>> numpy.float32(16777216)
16777216.0

>>> numpy.float32(16777217)
16777216.0

This loss of precision is even more apparent for larger values:

>>> numpy.float32(123456786432)
123456780000.0

>>> numpy.float32(123456786433)
123456790000.0

These properties of floating-point numbers have critical implications
for numerical reproducibility of scientific computations, particularly
in a parallel or distributed computing environment.

For the purposes of this discussion, let us define numerical reproducibility
as obtaining bit-wise identical results for different runs of the 
same computation on either the same machine or different machines.

Given that the OpenQuake engine works by parallelizing calculations, 
numerical reproducibility cannot be fully guaranteed, even for 
different runs on the same machine (unless the computation is run
using the --no-distribute or --nd flag).

Consider the following strategies for distributing the
calculation of the asset losses for a set of events, followed by
aggregation of the results for the portfolio due to all of the events. 
The assets could be split into blocks with each task computing the
losses for a particular block of assets and for all events, and the partial
losses coming in from each task is aggregated at the end.
Alternatively, the assets could be kept as a single block, splitting
the set of events/ruptures into blocks instead; once again the engine has to 
aggregate partial losses coming in from each of the tasks. 
The order of the tasks is arbitrary, because it is impossible to know 
how long each task will take before the computation actually begins.

For instance, suppose there are 3 tasks, the first one producing a partial
loss of 0.1 billion, the second one of 0.2 billion, and the third one of 0.3 billion.
If we run the calculation and the order in which the results are received 
is 1-2-3, we will compute a total loss of (.1 + .2) + .3 = 0.6000000000000001 billion.
On the other hand, if for some reason the order in which the results arrive is
2-3-1, say for instance, if the first core is particularly hot and the
operating system decides to enable some throttling on it, then the
aggregation will be (.2 + .3) + .1 = 0.6 billion, which is different 
from the previous value by 1.11E-7 units. This example assumes the use of 
Python's IEEE-754 “double precision” 64-bit floats.

However, the engine uses single-precision 32-bit floats rather than
double-precision 64-bit floats in a tradeoff necessary for reducing the
memory demand (both RAM and disk space) for large computations, 
so the precision of results is less than in the above example. 
64-bit floats have 53 bits of precision, and this why the relative error 
in the example above was around 1.11E-16 (i.e. 2^-53). 32-bit floats 
have only 24 bits of precision, so we should expect a relative error of 
around 6E-8 (i.e. 2^-24), which for the example above would be around 60 units. 
Loss of precision in representing and storing large numbers is a factor
that *must* be considered when running large computations.

By itself, such differences may be negligible for most computations. However,
small differences may accumulate when there are hundreds or even thousands
of tasks handling different parts of the overall computation and sending
back results for aggregation.

Anticipating these issues, some adjustments can be made to the input models 
in order to circumvent or at least minimize surprises arising from floating-point
arithmetic. Representing asset values in the exposure using thousands of dollars 
as the unit instead of dollars could be one such defensive measure. 

This is why, as an aid to the interested user, 
starting from version 3.9, the engine logs a warning if it finds
inconsistencies beyond a tolerance level in the aggregated loss results.

Recommended readings:

- Goldberg, D. (1991). What every computer scientist should know about floating-point arithmetic. *ACM Computing Surveys (CSUR)*, 23(1), 5-48. Reprinted at https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html
- https://docs.python.org/3/tutorial/floatingpoint.html
- https://en.wikipedia.org/wiki/Single-precision_floating-point_format
- https://en.wikipedia.org/wiki/Double-precision_floating-point_format
