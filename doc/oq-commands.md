Some useful `oq` commands
=================================

The `oq` command-line script is the entry point for several commands,
the most important one being `oq engine`, which is documented in the
manual.

The commands documented here are not in the manual because they have
not reached the same level of maturity and stability. Still, some of
them are quite stable and quite useful for the final users, so feel free
to use them.

You can see the full list of commands by running `oq help`:

```bash
$ oq help
usage: oq [--version]
          {purge,show_attrs,export,extract,restore,db,info,reset,to_hdf5,help,run_tiles,plot,checksum,run_server,tidy,dbserver,engine,dump,plot_ac,reduce,reduce_sm,to_shapefile,show,upgrade_nrml,run,plot_sites,from_shapefile,webui,plot_lc}
          ...

positional arguments:
  {purge,show_attrs,export,restore,db,info,reset,to_hdf5,help,run_tiles,plot,checksum,run_server,tidy,dbserver,engine,dump,plot_ac,reduce,reduce_sm,to_shapefile,show,upgrade_nrml,run,plot_sites,from_shapefile,webui,plot_lc}
                        available subcommands; use oq help <subcmd>

optional arguments:
  --version, -v         show program's version number and exit
```

This is the output that you get at the present time (engine 2.6); depending
on your version of the engine you may get a different output. As you see, there
are several commands, like `purge`, `show_attrs`, `export`, `restore`, ...
You can get information about each command with `oq help <command>`;
for instance, here is the help for `purge`:

```bash
$ oq help purge
usage: oq purge [-h] calc_id

Remove the given calculation. If you want to remove all calculations, use oq
reset.

positional arguments:
  calc_id     calculation ID

optional arguments:
  -h, --help  show this help message and exit
```

Some of this commands are highly experimental and may disappear; others are
meant for debugging and should not be used by final users. Here I will
document only the commands that are useful for the general public and
have reached some level of stability.

Probably the most important command is `oq info`. It has several
features.

1. It can invoked over a `job.ini` file to extract information about the
logic tree of a calculation.

2. When invoked with the `--report` option produces a `.rst` report with
several important informations about the computation. It is ESSENTIAL in
case of large calculations, since it will give you an idea of the feasibility
of the computation without running it. Here is an example of usage:

```bash
$ oq info --report job.ini
...
Generated /tmp/report_1644.rst
<Monitor info, duration=10.910529613494873s, memory=60.16 MB>
```
You can open `/tmp/report_1644.rst` and read the informations listed there
(`1644` is the calculation ID, the number will be different each time).

3. It can be invoked without a `job.ini` file and it that case it provides
global information about the engine and its libraries. Try for instance

```
$ oq info --calculators # list available calculators
$ oq info --gsims       # list available GSIMs
$ oq info --views       # list available views
$ oq info --exports     # list available exports
$ oq info --parameters  # list all job.ini parameters
```

The second most important command is `oq export`. It allows to customize
the exports from the datastore a lot more than the `oq engine` exports
commands. In the future the  `oq engine` exports commands might be
deprecated and `oq export` might become the official export command, but
we are not there yet.

Here is the usage message:

```bash
$ oq help export
usage: oq export [-h] [-e csv] [-d .] datastore_key [calc_id]

Export an output from the datastore.

positional arguments:
  datastore_key         datastore key
  calc_id               number of the calculation [default: -1]

optional arguments:
  -h, --help            show this help message and exit
  -e csv, --exports csv
                        export formats (comma separated)
  -d ., --export-dir .  export directory
```

The list of available exports (i.e. the datastore keys and the available export
formats) can be extracted with the `oq info --exports`
command; at the moment (engine 3.2) there are 48 exporters defined, but
this number changes at each version:

```bash
$ oq info --exports
agg_curve-rlzs ['csv']
agg_curve-stats ['csv']
agg_loss_table ['csv']
agg_losses-rlzs ['csv']
agglosses-rlzs ['csv']
all_losses-rlzs ['npz']
avg_losses-rlzs ['csv']
avg_losses-stats ['csv']
bcr-rlzs ['csv']
bcr-stats ['csv']
damages-rlzs ['csv']
damages-stats ['csv']
disagg ['xml', 'csv']
dmg_by_asset ['csv', 'npz']
dmg_by_taxon ['csv']
dmg_total ['csv']
fullreport ['rst']
gmf_data ['xml', 'csv', 'npz']
gmf_scenario ['csv']
hcurves ['csv', 'xml', 'geojson', 'npz']
hcurves-rlzs ['hdf5']
hmaps ['csv', 'xml', 'geojson', 'npz']
loss_curves ['csv']
loss_maps-rlzs ['csv', 'npz']
loss_maps-stats ['csv', 'npz']
losses_by_asset ['csv', 'npz']
losses_by_event ['csv']
losses_by_taxon ['csv']
losses_by_taxon-rlzs ['csv']
losses_by_taxon-stats ['csv']
losses_total ['csv']
realizations ['csv']
ruptures ['xml', 'csv']
sourcegroups ['csv']
uhs ['csv', 'xml', 'npz']
There are 52 exporters defined.
```

At the present the supported export types are `xml`, `csv`, `rst`,
`geojson`, `npz` and `hdf5`. `geojson` will likely disappear soon;
`xml` will not disappear, but it is not recommended for large
exports. For large exports the recommended formats are `npz` (which is
a binary format for numpy arrays) and `hdf5`. If you want the data for
a specific realization (say the first one), you can use

```
$ oq export hcurves/rlz-0 --exports csv
$ oq export hmaps/rlz-0 --exports csv
$ oq export uhs/rlz-0 --exports csv
```

but currently this only works for `csv` and `xml`. The exporters are one of
the most time-consuming parts on the engine, mostly for the sheer number
of them; the are more than fifty exporters and they are always increasing.
If you need new exports, please [add an issue on GitHub](https://github.com/gem/oq-engine/issues).

There is a command similar to `export`, called `extract`, which is able to
export in HDF5 format. For instance if you want to extract the full bulk
of hazard curves, hazard maps and uniform hazard spectra
for all realizations the command to use is

```
$ oq extract hazard/rlzs <calc_id> local
```

Be warned that for large calculations the extraction will likely be slower
than the entire calculation. In this case you should extract only the
sites you are interested in, while this command extracts everything.
The extract/export system will be extended in the near future.

oq zip
------

An extremely useful command if you need to copy the files associated
to a computation from a machine to another is `oq zip`:

```bash
$ oq help zip
usage: oq zip [-h] [-r] what [archive_zip]

positional arguments:
  what               path to a job.ini, a ssmLT.xml file, or an exposure.xml
  archive_zip        path to a non-existing .zip file [default: '']

optional arguments:
  -h, --help         show this help message and exit
  -r , --risk-file   optional file for risk
```
For instance, if you have two configuration files `job_hazard.ini` and
`job_risk.ini`, you can zip all the files they refer to with the command
```bash
$ oq zip job_hazard.ini -r job_risk.ini
```
`oq zip` is actually more powerful than that; other than job.ini files,
it can also zip source models
```bash
$ oq zip ssmLT.xml
```
and exposures

```bash
$ oq zip my_exposure.xml
```

Importing a remote calculation
--------------------------------

```bash
$ oq importcalc --help
usage: oq importcalc [-h] calc_id

Import a remote calculation into the local database. server, username and
password must be specified in an openquake.cfg file.
NB: calc_id can be a local pathname to a datastore not already present in
the database: in that case it is imported in the db.

positional arguments:
  calc_id     calculation ID or pathname

optional arguments:
  -h, --help  show this help message and exit
```

plotting commands
------------------

The engine provides several plotting commands. They are all
experimental and subject to change. They will always be. The official
away to plot the engine results is by using the QGIS plugin. Still,
the `oq` plotting commands are useful for debugging purpose. Here I will
describe only the `plot_assets` command, which allows to plot the
exposure used in a calculation together with the hazard sites:

```bash
$ oq help plot_assets
usage: oq plot_assets [-h] [calc_id]

Plot the sites and the assets

positional arguments:
  calc_id     a computation id [default: -1]

optional arguments:
  -h, --help  show this help message and exit
```

This is particularly interesting when the hazard sites do not coincide
with the asset locations, which is normal when gridding the exposure.

prepare_site_model
------------------

The command `oq prepare_site_model`, new in engine 3.3, is quite useful
if you have a vs30 file with fields lon, lat, vs30 - the USGS provides such
files for the whole world - and you want to generate a site model from it.
Normally this feature is used for risk calculations: given an exposure,
one wants to generate a collection of hazard sites covering the exposure
and with vs30 values extracted from the vs30 file with a nearest neighbour
algorithm.

```bash
$ oq help prepare_site_model
usage: oq prepare_site_model [-h] [-e EXPOSURE_XML [EXPOSURE_XML ...]] [-1]
                             [-2] [-3] [-g 0] [-s 5] [-o site_model.csv]
                             vs30_csv [vs30_csv ...]

Prepare a site_model.csv file from an exposure xml file, a vs30 csv file and a
grid spacing which can be 0 (meaning no grid). For each asset site or grid site
the closest vs30 parameter is used. The command can also generate (on demand)
the additional fields z1pt0, z2pt5 and vs30measured which may be needed by your
hazard model, depending on the required GSIMs.

positional arguments:
  vs30_csv              files with lon,lat,vs30 and no header

optional arguments:
  -h, --help            show this help message and exit
  -e EXPOSURE_XML [EXPOSURE_XML ...], --exposure-xml EXPOSURE_XML [EXPOSURE_XML ...]
                        exposure(s) in XML format
  -1, --z1pt0           build the z1pt0
  -2, --z2pt5           build the z2pt5
  -3, --vs30measured    build the vs30measured
  -g 0, --grid-spacing 0
                        grid spacing in km (the default 0 means no grid)
  -s 5, --site-param-distance 5
                        sites over this distance are discarded
  -o site_model.csv, --output site_model.csv
                        output file
```

The command work in two modes: with non-gridded exposures (the
default) and with gridded exposures. In the first case the assets are
aggregated in unique locations and for each location the vs30 coming
from the closest vs30 record is taken. In the second case, when a
`grid_spacing` parameter is passed, a grid containing all of the
exposure is built and the points with assets are associated to the
vs30 records. In both cases if the closest vs30 record is
over the `site_param_distance` - which by default is 5 km - a warning
is printed. 

In large risk calculations one wants to *use the gridded mode always* because:

1) the results are the nearly the same than without the grid and
2) the calculation is a lot faster and uses a lot less memory.

Basically by using a grid you can turn an impossible calculation into a possible
one.
The command is able to manage multiple Vs30 files at once. Here is an example
of usage:

```bash
$ oq prepare_site_model Vs30/Ecuador.csv Vs30/Bolivia.csv -e Exposure/Exposure_Res_Ecuador.csv Exposure/Exposure_Res_Bolivia.csv --grid-spacing=10
```

Reducing the source model
-------------------------

Source models are usually large, at the continental scale. If you are
interested in a city or in a small region, it makes sense to reduce the
model to only the sources close to the region, within the integration
distance. To fullfill this purpose there is the `oq reduce_sm` command.
The suggestion is run a preclassical calculation (i.e. set
`calculation_mode=preclassical` in the job.ini) with the full model
in the region of interest, keep track of the calculation ID and then
run
```bash
$ oq reduce_sm <calc_id>
```
The command will reduce the source model files and add an extension `.bak`
to the original ones.
```bash
$ oq reduce_sm -h
usage: oq reduce_sm [-h] calc_id

Reduce the source model of the given (pre)calculation by discarding all
sources that do not contribute to the hazard.

positional arguments:
  calc_id     calculation ID

optional arguments:
  -h, --help  show this help message and exit
```

Comparing hazard results
------------------------------

If you are interested in sensitivity analysis, i.e. in how much the
results of the engine change by tuning a parameter, the `oq compare`
command is useful. For the moment it is able to compare hazard curves
and hazard maps. Here is the help message:
```bash
$ oq compare --help
usage: oq compare [-h] [-f] [-s 100] [-r 0.1] [-a 0.0001]
                  {hmaps,hcurves} imt calc_ids [calc_ids ...]

Compare the hazard curves or maps of two or more calculations

positional arguments:
  {hmaps,hcurves}       hmaps or hcurves
  imt                   intensity measure type to compare
  calc_ids              calculation IDs

optional arguments:
  -h, --help            show this help message and exit
  -f, --files           write the results in multiple files
  -s 100, --samplesites 100
                        number of sites to sample
  -r 0.1, --rtol 0.1    relative tolerance
  -a 0.0001, --atol 0.0001
                        absolute tolerance
```
