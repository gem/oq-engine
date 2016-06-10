New features of the OpenQuake Engine, version 2.0
-------------------------------------------------

There are several major improvements in OpenQuake 2.0.

1. We have removed the dependency from PostgreSQL and celery and made
the engine installable with zero configuration effort on non-cluster
platforms. As a consequence, now the engine runs natively on Windows,
Mac and Linux. We provide official packages for Ubuntu (14.04, 16.04),
Red Had (7.0) and a Windows installer (from XP to Windows 10). There
is a guide to install the engine on Mac OS X.

2. We have improved tremendously the performance of the event based
calculators, both hazard and risk. In large calculations the
engine can be over an order of magnitude faster and use two orders of
magnitudes less memory. Now it is possible to run event based calculations
with half million assets and several realizations.

3. We have reduced significantly the data transfer in classical PSHA
calculations, reduced the memory footprint and speed up the calculator.
The net effect is a lot less visible than for the event based, but
still positive. Also, now it is possible to set different integration
distances for different tectonic region types: this may have a very positive
effect on the performance.

4. We have introduced a command `oq` with a lot of new functionalities;
we deprecated the old command `oq-engine`, which has been replaced by `oq engine`.
We added a command `oq engine --show-log <job_id>`

5. As usual there were a lot of bug fixes, including a very
significant one in the event based risk calculator in presence of a
complex logic tree. We removed some deprecated functionality.
We improved the serialization of Python objects into HDF5 objects.
We fixed some issues in the WebUI and made sure it works on Windows.
Internally a lot of refactoring has been done, and the HDF5
structure has changed.

6. There was a lot of work on the exporters and several bugs were fixed.
Now virtually all of them export floats in exponential notation with 5
decimal digits.

7. In the event based calculator the user can specificy a minimum intensity
for each Intensity Measure Type to ignore any ground motion value below
the threshold. The saving of the asset loss table has been optimized,
with a measured speedup of three orders of magnitude. Moreover, we
optimized the case when the epsilons are not required, i.e. all the
covariance coefficients are zero in the vulnerability functions.

8. We revisited the weighting of the tasks to have a better task distribution.

9. Several new views of the datastore. were added and the reports improved.

10. In hazardlib we fixed Z1.0 units bug in Abrahamson, Silva and Kamai (2014)
We added modifications to Zhao (2006) inslab GMPE and implemented
Atkinson (2008), needed for 2014 US NSHMP.

11. We backported `libhdf5` and `h5py` from Ubuntu 14.04 to the Ubuntu
12.04 series, thus the engine still works on Ubuntu 12.04 even if
this platform is officially deprecated and it has been deprecated for
a long time.

12. A lot more was done and interested people should look at the
changelogs: https://github.com/gem/oq-hazardlib/blob/engine-2.0/debian/changelog and https://github.com/gem/oq engine/blob/engine-2.0/debian/changelog
