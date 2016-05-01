The OpenQuake 1.2 release is a major change with respect to the OpenQuake 1.0 release.
You can find a detailed list of the improvements [on this page](What's-new.md).

A few new features were added and the performance of all calculators has been improved significatively. In some cases even of several orders of magnitude! Moreover the database name and schema have changed, the underlying dependencies have changed and a lot of bugs were fixed. Most of the changes have been backward compatible though.

You should not expect the numbers of an OpenQuake 1.2 computation to be exactly identical to the numbers
of an OpenQuake 1.0 computation, because the algorithms or the underlying implementation may have changed,
or because bugs may have been fixed. Moreover, you cannot use the hazard computed with OpenQuake 1.0
to run a risk calculation with OpenQuake 1.2: instead, you must recompute the hazard by using the original
files.

OpenQuake 1.2 internally uses a new database called `openquake2` and has no access to the
old database `openquake` used by OpenQuake 1.0. The upgrade procedure will not
touch the old database at all and you can safely remove it, assuming you are not interested in
the old data.

Whereas the internal changes have been *huge*, the changes visible to the final users are few.
I am listing them here:

0. The `openquake` command has been renamed to `oq-engine`, and it has different options.
   You can see them with

   `$ oq-engine --help`

1. In particular the command-line options for export have
   been reduced. Before we had `--export-hazard-output`, `--export-hazard-outputs`,
   `--export-risk-output`, `--export-risk-outputs`, `--list-hazard-outputs`, `--list-risk-outputs`;
   now we have `--export-output`, `--export-outputs`, `--list-outputs`. The ``--export-type`` option
   has been removed since it was somewhat redundant with the ``--exports`` option.

2. There is now a command-line option

  `$ oq-engine --make-html-report today`

   which generates a HTML file with performance information about the computations ran today;
   you can generate the report even for past days by giving an ISO date in the format YYYY-MM-DD.
 
0. We found a couples of errors in the XML source model files. Old files are now rejected if
   they contain duplicated IDs or if they contain invalid geometries.

1. The configuration file `openquake.cfg` has changed. There are some new parameters, some have been
   dropped and the name of the database has changed. If you upgrade to OpenQuake 1.2 you must
   manually change the file `openquake.cfg`. You can see the format of the [latest configuration file on GitHub](https://github.com/gem/oq-engine/blob/master/openquake.cfg). You may also need to change the
   PostgreSQL permissions in the file pg_hba.conf so that the database openquake2 can be accessed.

3. The acceptable values of the parameter `calculation_mode` in the risk configuration files have
   changed; in particular whereas before the values were `classical`, `event_based` and
   `scenario`, now you must write `classical_risk`, `event_based_risk` and `scenario_risk` instead.
   The names  `classical`, `event_based` and `scenario` are now reserved to the hazard calculators.

4. In the past, when doing a GMF calculation with correlation the syntax `ground_motion_correlation_params = {"vs30_clustering": false}` was accepted; now you must write `ground_motion_correlation_params = {"vs30_clustering": False}` with capital `F`; the same for `true`, now it must be written `True`;
`0` and `1` are accepted flags, as they were before.

5. Now you cannot specify both `intensity_measure_types` and `intensity_measure_types_and_levels`; if
   the `intensity_measure_types_and_levels`are known (explicitly or by reading them from the risk models)
   you must remove the line `intensity_measure_types = ` from the `job.ini` file, if it is there.

6. The format to export the GMFs from a scenario computation has changed: now it is the same as
   for event based computations.
