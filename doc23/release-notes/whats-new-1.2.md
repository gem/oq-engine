What's new in engine-1.2
========================

The difference in OpenQuake 1.2 is mostly in the performance of the hazard calculators.
They are *much* faster, sometimes several order of magnitudes faster. 

The changes which are not compatible with the past [are listed here](Incompatible-changes-with-previous-version.md).
Moreover a few new features have been added.

1. it is possible to avoid saving the individual hazard curves. This is useful for people working
   with large logic trees and interested only in the mean curves and/or on the quantile curves.
   Such users should set the configuration parameter `individual_curves=false` in the `job.ini`
   configuration file.

2. If you computed the hazard at the points specified by an exposure file, later risk calculations
   do not need to reimport the exposure. This is a significant improvement for large exposures.
   In practice, if the parameter `exposure_file` is specified in the `job_hazard.ini` file, you
   should removed it from the `job_risk.ini` file, otherwise it will be reimported.

3. An optimization has been added for the case where the hazard is known at the sites of the exposure.
   In that case the hazard data can be extracted directly without geospatial queries and the risk
   calculation is faster.

4. The validation system has been rewritten and now it is much more effective and accurate than before,
   i.e. the user gets better error messages for invalid input. Several bugs in this area have been
   closed, even if certainly there will be more work to do on this front.

5. The procedure to import the source models has been improved: it is now faster and more memory efficient.

6. The risk calculators are now more memory efficient and faster than before; moreover the robustness of
   the results has improved, bugs have been fixed and several new correcteness tests have been added.

7. The task distribution in the hazard calculators has improved substantially: now the tasks are more
   homogeneous in size and it is less likely to have a single slow tasks slowing down the
   entire computation. Also, there is in place a mechanism to split large sources into small sources,
   to make the tasks more regular in source size.

8. The logic tree mechanism for GSIMs has been rewritten and an optimization has been put in place,
   so that the engine does not perform needless computations for non-relevant tectonic region types
   (a tectonic region type is not relevant if, even if it is in the logic tree file, there are no
   sources for that tectonic region type in the source model within the integration distance).

9. There is now a way to get an HTML report with the performance of the engine:

   ```bash
   $ oq-engine --make-html-report today
   ```

   This will list all the computations of the day. You can also specify the date using the ISO format
   YYYY-MM-DD.

10. A lot of the logic of the engine has been moved into a different repository, [oq-risklib]
   (https://github.com/gem/oq-risklib): that means that now it is much easier for hazard and risk
   scientists to use the libraries underlying the engine programmatically.
 
On top of that, there is perhaps the most important improvement of them all:

- *it is possible to perform post-1.2 upgrades without destroying the database*.

That means that the users can keep updated their system with the OpenQuake nightly builds without 
having too worry too much. We added a page [describing how to upgrade from OpenQuake 1.2 up to higher versions](How-to-upgrade-an-OpenQuake-1.2-database.md).
