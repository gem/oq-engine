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
          {purge,show_attrs,export,extract,restore,db,info,reset,to_hdf5,help,run_tiles,plot,checksum,run_server,tidy,dbserver,engine,dump,plot_uhs,plot_ac,reduce,to_shapefile,show,upgrade_nrml,run,plot_sites,from_shapefile,webui,plot_lc}
          ...

positional arguments:
  {purge,show_attrs,export,restore,db,info,reset,to_hdf5,help,run_tiles,plot,checksum,run_server,tidy,dbserver,engine,dump,plot_uhs,plot_ac,reduce,to_shapefile,show,upgrade_nrml,run,plot_sites,from_shapefile,webui,plot_lc}
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
$ oq extract hazard/rlzs
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
usage: oq zip [-h] [-r RISK_INI] job_ini archive_zip

Zip the given job.ini file into the given archive, together with all related
files.

positional arguments:
  job_ini               path to a job.ini file
  archive_zip           path to a non-existing .zip file

optional arguments:
  -h, --help            show this help message and exit
  -r RISK_INI, --risk-ini RISK_INI
                        optional .ini file for risk
```

A typical example of usage for a risk calculation would be
```bash
$ oq zip job_hazard.ini job.zip -r job_risk.ini
```

plotting commands
------------------

The engine provides several plotting commands. They are all experimental
and subject to change. The official away to plot the engine results is
by using the QGIS plugin. Still, the `oq plot` commands are useful for
debugging purpose. Here I will describe only the `plot_assets` command,
which allows to plot the exposure used in a calculation together with
the hazard sites:

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
usage: oq prepare_site_model [-h] [-g 0] [-s 5] [-o sites.csv]
                             exposure_xml vs30_csv [vs30_csv ...]

Prepare a sites.csv file from an exposure xml file, a vs30 csv file and a
grid spacing which can be 0 (meaning no grid). For each asset site or grid
site the closest vs30 parameter is used. The command can also generate
(on demand) the additional fields z1pt0, z2pt5 and vs30measured which may
be needed by your hazard model, depending on the required GSIMs.

positional arguments:
  exposure_xml          exposure in XML format
  vs30_csv              files with lon,lat,vs30 and no header

optional arguments:
  -h, --help            show this help message and exit
  -1, --z1pt0           build the z1pt0
  -2, --z2pt5           build the z2pt5
  -3, --vs30measured    build the vs30measured
  -g 0, --grid-spacing 0
                        grid spacing in km (the default 0 means no grid)
  -s 5, --site-param-distance 5
                        sites over this distance are discarded
  -o sites.csv, --output sites.csv
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
$ oq prepare_site_model Exposure/Exposure_Res_Ecuador.csv,Exposure/Exposure_Res_Bolivia.csv Vs30/Ecuador.csv Vs30/Bolivia.csv --grid-spacing=10
```
