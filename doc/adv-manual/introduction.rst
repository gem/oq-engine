Introduction
=======================================

If you have just started using the OpenQuake engine, and the only thing
you have tried are the OpenQuake demos, this manual is NOT for you. Beginners
should study the [official manual](https://www.globalquakemodel.org/single-post/OpenQuake-Engine-Manual). This manual is for advanced users, i.e.
people that already know how to use the engine, but are running *large*
calculations and have trouble performing them.

For the purposes of this manual a calculation is large if it cannot be run,
i.e. if it runs out of memory, it fails with strange errors (rabbitmq
errors, pickling errors, ...) or it just takes too long to complete.

There are various reasons way a calculation can be too large. 99% of the
times it is because the user is making some mistakes and he is trying to
run a calculation larger than he really needs. In the remaining 1% of the
times the calculation is genuinely large and the only solution is to
buy a larger machine, or to ask the OpenQuake developers to optimize the
engine for the specific calculation that is giving issues.



