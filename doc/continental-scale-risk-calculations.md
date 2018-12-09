Continental Scale Risk Calculations
=========================================

Since version 3.3 the OpenQuake engine is able to handle continental
scale (event based) risk calculations, a feat previously impossible due
to memory limitations. Here I will document the new feature.

First of all, *the recommended way to run large event based risk calculation
is to use a single job.ini file*. This is the opposite of the previous
recommendation of using two job.ini files, one for hazard `job_hazard.ini`
and one for risk `job_risk.ini`. In the past using a single file was
discourage since a single computation was performed and the engine had to
transfer the generated ground motion fields causing RabbitMQ to run out
of memory if the calculation was large enough. Instead, with two files
two separated calculations were performed, and the GMFs could be read
from the hazard datastore without passing via RabbitMQ, provided the
hazard was stored on a shared file system. In a non-cluster situation
the data transfer does not use RabbitMQ, however it is still slow,
inefficient and memory consuming, so the recommendation was to use
two files even in that situation.

Starting from engine 3.3 the engine automatically splits a single file job.ini
for an `event_based_risk` calculation in two jobs, one for hazard and one for
risk. It basically does the splitting of the `job.ini` for you, so that the
GMFs are never transferred, just read, which is a lot more efficient.
Having a single `job.ini` is more convenient and less error-prone, so
you should always do that, even if the old approach of using two files
will still work and will work forever to keep compatibility with the past.

Continental scale calculations use typically multiple exposure files, one
per country. Since version 3.3 the OpenQuake engine is able to manage
multiple exposures, it is enough to list the files in the `exposure_file`
parameter of the `job.ini`, as in this example for South America, in
which all the exposures are in a folder called Exposure one level above
the job.ini file:
```
[exposure]
exposure_file =
  ../Exposure/Exposure_Argentina.xml
  ../Exposure/Exposure_Colombia.xml
  ../Exposure/Exposure_Paraguay.xml
  ../Exposure/Exposure_Venezuela.xml
  ../Exposure/Exposure_Bolivia.xml
  ../Exposure/Exposure_Ecuador.xml
  ../Exposure/Exposure_Peru.xml
  ../Exposure/Exposure_Brazil.xml
  ../Exposure/Exposure_French_Guiana.xml
  ../Exposure/Exposure_Suriname.xml
  ../Exposure/Exposure_Chile.xml
  ../Exposure/Exposure_Guyana.xml
  ../Exposure/Exposure_Uruguay.xml
```
Continental scale calculations also typically use multiple site model files,
one per country. Since version 3.3 the OpenQuake engine is able to manage
multiple site models, it is enough to list the files in the `site_model_file`
parameter, as in this example were all the site models are stored in a folder
called Vs30 one level above the job.ini file:
```
[site_params]
site_model_file =
 ../Vs30/Site_model_Argentina.csv
 ../Vs30/Site_model_Colombia.csv
 ../Vs30/Site_model_Paraguay.csv
 ../Vs30/Site_model_Venezuela.csv
 ../Vs30/Site_model_Bolivia.csv
 ../Vs30/Site_model_Ecuador.csv
 ../Vs30/Site_model_Peru.csv
 ../Vs30/Site_model_Brazil.csv
 ../Vs30/Site_model_French_Guiana.csv
 ../Vs30/Site_model_Suriname.csv
 ../Vs30/Site_model_Chile.csv
 ../Vs30/Site_model_Guyana.csv
 ../Vs30/Site_model_Uruguay.csv
```
The .csv format for the site model files is new and is the preferred
format to use, but the old .xml format is still accepted and will work
forever to keep compatibility with the past. There is also a new command
`oq prepare_site_model` to generate the `site_model.csv` files starting
from the exposures and CSV files containing lon, lat and vs30 values,
such as the ones provided by the USGS.

Notice that it is very possible to use a single big exposure for all of
the continent, as well as a single big site model file; however using
multiple files has the advantage that you can comment out in the `job.ini`
the countries that you are not interested in, in the case one wanted
to discard some regions, possibly because they have been already computed.

When running continental scale calculations one is typically interested
in aggregated results, such as the average losses by country and the
loss curves by country. The engine can automatically calculate and export
such results if you say so in the `job.ini`, i.e. if you set
```
aggregate_by = country
```
It is also possible to compute what we call multi-tag aggregations;
for instance, if you want results aggregated by country, occupancy
and taxonomy you can just set in the job.ini
```
aggregate_by = country, occupancy, taxonomy
```
Any valid tag can be used. In order to be valid the tag has to be listed
in the `tagNames` attribute of each .xml exposure and there must be a
field with the name of the tag in the .csv exposures, if any.
The `country` tag is currently a bit special and automatically inferred
from the name of the exposure file, which must contain a valid country
name. We may change this behaviour in the future and make the country tag
mandatory in the exposure, but it will require to change all of the exposures
we have, so it is still undecided.

For the rest, the `job.ini` file is the same as always, except for a
new parameter `split_sources`, added in version 3.3 of the OpenQuake
engine.  By default it is `true`, which means that the sources are
split before performing the sampling of the ruptures. This has been
the traditional logic used by the engine for several years. However,
it is possible to set `split_sources=false` and use a different and a
lot more efficient logic for the sampling of the ruptures. The
difference in the case of South America is of more than an order of
magnitude, so the new logic is to be preferred for large calculations
and will probably become the default in the future.  It is not the
default yet for reasons of backward compatibility.

The reason for the performance improvement is in the number of calls
to the random number generator. Suppose there is a large area source
with 1 million ruptures: with `split_source=true` a million calls to
the random generator are performed, one for each rupture, while with
`split_source=false` only one call per source is performed.  Clearly
the two approaches produce different ruptures, but if your effective
investigation time is large enough they will produce statically
convergent results. Be warned that the effective investigation
time to get convergent results (i.e. independent from the random seed
choice) can be rather long, depending on the level of precision
required.
