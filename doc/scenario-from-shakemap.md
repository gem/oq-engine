# Scenario calculations starting from USGS ShakeMaps

Beginning with version 3.1, the engine is able to perform `scenario_risk`
and `scenario_damage` calculations starting from the GeoJSON feed for
[ShakeMaps](https://earthquake.usgs.gov/data/shakemap/) 
provided by the United States Geological Survey (USGS).

In order to enable this functionality one has to prepare a parent
calculation containing the exposure and risk functions for the
region of interest, say Peru. To that aim the user will need
to write a `prepare_job.ini` file like this one:

```
   [general]
   description = Peru - Preloading exposure and vulnerability
   calculation_mode = scenario
   exposure_file = exposure_model.xml
   structural_vulnerability_file = structural_vulnerability_model.xml
```
By running the calculation

```bash
$ oq engine --run prepare_job.ini
```

The exposure and the risk functions will be imported in the datastore.

This example only includes vulnerability functions for the loss type
`structural`, but one could also have in this preparatory job file the 
functions for nonstructural components and contents, and occupants, 
or fragility functions if damage calculations are of interest.

It is essential that each fragility/vulnerability function in the risk
model should be conditioned on one of the intensity measure types that 
are supported by the ShakeMap service – PGV, PGA, SA(0.3), SA(1.0), and SA(3.0).
If your fragility/vulnerability functions involves an intensity
measure type which is not supported by the ShakeMap system
(for instance SA(0.6)) the calculation will terminate with an error.

Let's suppose that the calculation ID of this 'pre' calculation is 1000.
We can now run the risk calculation starting from a ShakeMap.
For that, one need a `job.ini` file like the following::

```
   [general]
   description = Peru - 2007 M8.0 Pisco earthquake losses
   calculation_mode = scenario_risk
   number_of_ground_motion_fields = 10
   truncation_level = 3
   shakemap_id = usp000fjta
   hazard_calculation_id = 1000  # ID of the pre-calculation
   spatial_correlation = yes
   cross_correlation = yes
```

This example refers to the 2007 Mw8.0 Pisco earthquake in Peru
(see https://earthquake.usgs.gov/earthquakes/eventpage/usp000fjta#shakemap).
The risk can be computed by running the risk job file against the prepared calculation:

```bash
$ oq engine --run job.ini
```

The engine will perform the following operations:

1. download the ShakeMap from the USGS web service and convert it into a format
   suitable for further processing, i.e. a ShakeMaps array with lon, lat fields
2. the ShakeMap array will be associated to the hazard sites in the region
   covered by the ShakeMap
3. by using the parameters `truncation_level` and
   `number_of_ground_motion_fields` a set of ground motion fields (GMFs) following the
   truncated Gaussian distribution will be generated and stored in the datastore
4. a regular risk calculation will be performed by using such GMFs and the
   assets within the region covered by the shakemap.
   
The performance of the calculation will be crucially determined by the number
of hazard sites. For instance, in the case of the Pisco earthquake
the ShakeMap has 506,142 sites, which is a significantly large number of sites.
However, the extent of the ShakeMap in longitude and latitude is about 6 degrees,
with a step of 10 km the grid contains around 65 x 65 sites;
most of the sites are without assets because most of the
grid is on the sea or on high mountains, so actually there are
around ~500 effective sites. Computing a correlation matrix of size
500 x 500 is feasible, so the risk computation can be performed.
Clearly in situations in which the number of hazard sites is too large,
approximations will have to be made, such as neglecting the spatial or cross
correlation effects, or using a larger `region_grid_spacing`.

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
`no` mean using a unity correlation matrix; `full` means using an 
all-ones correlation matrix.

Disabling either the spatial correlation or the cross correlation (or both)
might be useful to see how significant the effect of the correlation is on the
damage/loss estimates; sometimes it is also made necessary because the
calculation simply cannot be performed otherwise due to the large size of the
resulting correlation matrices.

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

So you should not expect the functionality to work in 100% of the cases.

### Notes

On macOS make sure to run the script located under
`/Applications/Python 3.6/Install Certificates.command`,
after Python has been installed, to update the SSL certificates and to avoid
SSL errors when dowbnloading the shakemaps from the USGS website
[see FAQ](faq.md#Certificate-verification-on-macOS).

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
