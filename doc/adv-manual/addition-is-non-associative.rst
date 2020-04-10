Floating-point addition is non-associative
==========================================

Every practitioner of numeric calculations knows that the
addition is non-associative; for instance

>>>  (.1 + .2) + .3                                                          
0.6000000000000001

is not the same as

>>> .1 + (.2 + .3)                                                         
0.6

However, probably most people do not realize how dramatic the impact of
this fact is on OpenQuake calculations.

For instance, suppose that you are doing a risk calculation and that you want to
compute the total loss of your portfolio of assets: is the result reproducible?

The result is a decise NO!

The total loss is not reproducible even on the same machine, because
the engine works by parallelizing the calculation. Various strategies
can be used, for instance the assets could be split in blocks and then
each task would compute a partial loss, to be aggregated at the end;
alternatively, the asset could not be split, but still there would be
multiple tasks because the ruptures would be split instead; still, at
the end one has to aggregate partial losses. The order of the tasks is
random, because it is impossible to know how long a task will
take. For instance, suppose there are 3 tasks, the first one giving a
loss of 0.1 billions of euros, the second on of 0.2 billions of euros
and the third one of 0.3 billions of euros.  If we run the calculation
and the order in which the results are received is 1-2-3 (first the
result of the first task, second the result of the second task and
third the result of the third task) we will get a total loss of
0.6000000000000001 billion euros; but, if for some reason the order if
different, for instance the first core is particularly hot and the
operating system decide to enable some throttling on it, so that the
first task arrive later and the order of the results is 2-3-1, then the
aggregation will be (.2 + .3) + .1 = 0.6 billion euros, which is
different from the previous value by 1.11E-7 euros.

The difference seems to be totally negligible and insignificant, not to
be taken in consideration. But actually things get worse.

First of all, the engine does not use 64 bit floats to do the additions,
because for saving memory (both RAM and disk space) it stores 32 bit
floats, so the precision is a lot less. 64 bit floats have 53 bits
of precision, and this why the relative error in the previous calculation was
around 1.11 × 10−16 (i.e. 2^−53); 32 bit floats have only 24 bits of
precision, so we should expect a relative error around 6E-8 (2^-24) which means
60 euros.

It may not seem much, compared to 1 billion euros, but it gets
worse. Much worse. The error cumulates and the more tasks there are,
the worse the effect. You may wonder: how bad can it get, in real life
situations?

The answer is: sometimes VERY BAD.

This is why, starting from version 3.9, the engine logs a warning if it finds
out inconsistencies in the sums when computing loss curves.

For a real-life calculation that was run today, producing 196,830
aggregate loss curves, one for each possible combination of the tags
in the exposure, the engine found an inconsistency between the total
sum of the aggregate loss curves and the total loss curve computed
with a different ordering of the losses of 0.43362%: that means over
4 million euros over 1 billion!

So you can easily miss millions of euros on contry-level portfolios: worse
than that, every time you run the calculation you will get different
total losses, because the order of the tasks will be different.

You are warned now.


Mandatory readings:

https://en.wikipedia.org/wiki/Single-precision_floating-point_format
https://en.wikipedia.org/wiki/Double-precision_floating-point_format
