What's new in engine-1.4
========================

Here are the new features of the OpenQuake Engine, version 1.4.

1. The main novelty is the full support for Ubuntu 14.04.  Not only the
engine works on Ubuntu 14.04 (that was already the case with OpenQuake 1.3)
but we are also providing official packages for it. As of now, Ubuntu
14.04 is the recommended platform to run the engine. Ubuntu 12.04 is still
supported and we will continue to support it for the near future.

2. The biggest new feature is the introduction of a Web interface integrated
in the engine code base. Users who do not like the command-line interface
or users that want to manage engine calculations remotely using a Web
interface can do so. The Web interface also supports authentication which 
can be used in multiple users situations.
The documentation is still lacking, but we will add it shortly.

3. A lot of minor improvements have been implemented, the engine has
more validation checks and better error messages. In particular
exposures containing assets with an attribute `number` are valid only
if the number is a positive integer larger than zero. If you have an
exposure with `number="0"` you must remove the `number` attribute in
the XML. For compatibility with the past the engine does not reject such
exposures yet, but it will in the next release.

3. There is a new ``--run`` command to run hazard and risk together:

  `$ oq-engine --run job_haz.ini,job_risk.ini`

  Notice that there are no spaces around the comma.

4. The procedure to associate hazard sites to the closest site parameters has
been replaced with an equivalent one which does not rely on the existence
of a geospatial database. If you have a site which is exactly at the same distance
from two different site parameter locations, it could be that the new procedure
associates different parameters than before. However the new approach is more
consistent since it is using the same distance algorithm which is used in the rest
of engine, specifically the routine `openquake.hazardlib.geo.geodetic.min_distance`.

5. The parameter `maximum_distance` in the risk configuration files has been
renamed to `asset_hazard_distance`, to avoid any possible confusion with the
parameter `maximum_distance` in the hazard configuration files. If you have an
old job_risk.ini file using the name  `maximum_distance` you will get an error.
The error message will clearly say that you must rename the parameter to
`asset_hazard_distance`. Just to refresh your memory, here is the meaning of the two
parameters. `maximum_distance`: if a site is outside this range from the sources, the hazard
on that site is considered zero. `asset_hazard_distance`: if an asset is outside this range
from the hazard sites, it is discarded in the risk computation and a warning is printed.

5. The engine now supports GSIMs with a backarc param, i.e. Abrahamson et al. (2015).

8. A few new CSV exporters have been added, in particular one for the aggregated loss curves.

10. A lot of progress and bug fixing on the lite version of the engine has been
made, which is now nearly feature-complete, but it is still marked as experimental.
In particular the `oq-lite info` command has been extended and can give
information about the logic tree of a computation without running the
computation. The scenario calculators are able to manage multiple GSIMs
at the same time, by producing an output file for each GSIM. The
documentation is still lacking.

11. Several new features have been implemented in hazardlib, see the corresponding
[changelog](https://github.com/gem/oq-hazardlib/releases/tag/v0.14.0). In particular now hazardlib returns hazard curves and ground motion fields as 
arrays of records and not as dictionaries of arrays. This is of interest only to
people using directly hazardlib, the change is invisible for people using the engine.

12. Overall in this release more than 160 bugs/feature requests were fixed/implemented.