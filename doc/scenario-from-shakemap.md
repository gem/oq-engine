Scenario calculations starting from USGS ShakeMaps
==================================================

Since version 3.1 the engine is able to perform `scenario_risk`
and `scenario_damage` calculations starting from the shakemaps provided
by the United States Geological Survey (USGS) service.

In order to enable this functionality one has to prepare a parent
calculation containing the full exposure and risk functions for the
region of interest, say South America. To that aim the user will need
to write a `prepare_job.ini` file like this one:

```
   [general]
   description = Full South America
   calculation_mode = scenario
   exposure_file = exposure_model.xml
   structural_vulnerability_file = structural_vulnerability_model.xml
```
By running the calculation

```bash
$ oq engine --run prepare_job.ini
```

the exposure and the risk functions will be imported in the datastore.

In this example there are only vulnerability functions for the loss type
`structural`, but there could be more, and even fragility functions.

It is essential that you have the right risk functions.
The ShakeMaps contains data for the intensity measure types PGA, SA(0.3),
SA(1.0) and SA(3.0). If your vulnerability functions involves an intensity
measure type which is not in the ShakeMap (for instance SA(0.6)) you will
get an error and it will be impossible to perform the analysis.

The hazard has to be prepared only once.

Let's suppose that the calculation ID of this hazard calculation is 1000.
We can now run the risk on a given ShakeMap.
For that, one need a `job.ini` file like the following::

```
   [general]
   calculation_mode = scenario_risk
   number_of_ground_motion_fields = 10
   truncation_level = 3
   shakemap_id = usp000fjta
   hazard_calculation_id = 1000  # ID of the prepared calculation
```

This example refers to an Earthquake happened in Pisco in Peru in 2007
(see https://earthquake.usgs.gov/earthquakes/eventpage/usp000fjta#shakemap).
The risk can be computed by running the risk file against the prepared
hazard calculation:

```bash
$ oq engine --run job.ini
```

The engine will perform the following operations:

1. dowload the shakemap from the USGS web site and convert it into a format
   suitable for further processing, i.e. a shakemap array with lon, lat fields
2. the shakemap array will be associated to the hazard sites in the region
   covered by the shakemap
3. by using the parameters `truncation_level` and
   `number_of_ground_motion_field` a set of ground motion fields following the
   truncated gaussian distribution will be generated and stored in the datastore
4. a regular risk calculation will be performed by using such GMFs and the
   assets within the region covered by the shakemap.
   
The performance of the calculation will be crucially determined by the number
of involved hazard sites. For instance in the case of the Pisco earthquake
the shakemap has 506,142 sites, which seems a huge number. However,
the extent of the shakemap in longitude and latitude is about 6 degrees,
with a step of 10 km the grid contains around 65 x 65 sites;
most of the sites are without assets because most of the
grid is on the sea or on high montains, so actually there are
around ~500 effective sites. Computing a correlation matrix of size
500 x 500 is actually possible, so the risk computation can be performed.
Clearly in situations in which the number of hazard sites is too large,
approximations will have to be made, like neglecting the correlation
effects.

By default the engine tries to compute both the spatial correlation and the
cross correlation between different intensity measure types. For each kind
of correlation you have three choices, that you can set in the `job.ini`,
for a total of nine combinations:

```
spatial_correlation = yes, cross_correlation = yes  # the default
spatial_correlation = no, cross_correlation = no   # disable everything
spatial_correlation = yes, cross_correlation = no
spatial_correlation = no, cross_correlation = yes
spatial_correlation = full, cross_correlation = full
spatial_correlation = yes, cross_correlation = full
spatial_correlation = no, cross_correlation = full
spatial_correlation = full, cross_correlation = no
spatial_correlation = full, cross_correlation = yes
```

`yes` means using the correlation matrix of the Silva-Horspool paper;
'no' mean using a unity correlation matrix; `full` means using a correlation
matrix full of 1s in all positions.

Disabling some kind of correlation is useful to see how big the effect
of the correlation is; sometimes it is also necessary because the
calculation cannot be performed otherwise.

In particular, due to numeric errors, the spatial correlation matrix - that
by construction contains only positive numbers - can still produce small
negative eigenvalues (of the order of -1E-15) and the calculation fails
with an error message saying that the correlation matrix is not positive
defined. Welcome to the world of floating point approximation!
Rather than magically discarding negative eigenvalues the engine raises
an error and the user has two choices: either disable the spatial correlation
or reduce the number of sites because that can make the numerical instability
go away. The easiest way to reduce the number of sites is setting a
`region_grid_spacing` parameter in the `prepare_job.ini` file, then the
engine will automatically put the assets on a grid. The larger the grid
spacing, the smaller the number of points, until the calculation can be done.

If the ground motion values or the standard deviations are particularly
large the user will get a warning about suspicious GMFs.

Moreover, especially for old ShakeMaps, the USGS can provide them in a
format that the engine cannot read.

So you should not expect the functionality to work 100% of the times.
