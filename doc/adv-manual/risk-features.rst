New risk features
======================

Here we document some new risk features which have not yet made it
into the engine manual. These are new features and cannot be
considered fully-tested and stable yet.


Taxonomy mapping
---------------------------------

In an ideal world, for every building type represented in the 
exposure model, there would be a unique matching function
in the vulnerability or fragility models. However, often it may
not be possible to have a one-to-one mapping of the taxonomy strings
in the exposure and those in the vulnerability or fragility models.
For cases where the exposure model has richer detail, many taxonomy
strings in the exposure would need to be mapped onto a single 
vulnerability or fragility function. In other cases where building
classes in the exposure are more generic and the fragility or vulnerability
functions are available for more specific building types, a modeller
may wish to assign more than one vulnerability or fragility function
to the same building type in the exposure with different weights.

We may encode such information into a `taxonomy_mapping.csv`
file like the following:

=========== ===========
taxonomy     conversion
----------- -----------
Wood Type A  Wood
Wood Type B  Wood
Wood Type C  Wood
=========== ===========

Using an external file is convenient, because we can avoid changing the
original exposure. If in the future we will be able to get specific
risk functions, then we will just remove the taxonomy mapping.
This usage of the taxonomy mapping (use proxies for missing risk
functions) is pretty useful, but there is also another usage which
is even more interesting.

Consider a situation where there are doubts about the precise
composition of the exposure. For instance we may know than in a given
geographic region 20% of the building of type "Wood" are of "Wood Type
A", 30% of "Wood Type B" and 50% of "Wood Type C", corresponding to
different risk functions, but do not know building per building
what it its precise taxonomy, so we just use a generic "Wood"
taxonomy in the exposure. We may encode the weight information into a
`taxonomy_mapping.csv` file like the following:

========= ============ =======
taxonomy   conversion   weight
--------- ------------ -------
Wood       Wood Type A  0.2
Wood       Wood Type B  0.3
Wood       Wood Type C  0.5
========= ============ =======

The engine will read this mapping file and when performing the risk calculation
will use all three kinds of risk functions to compute a single result
with a weighted mean algorithm. The sums of the weights must be 1
for each exposure taxonomy, otherwise the engine will raise an error.
In this case the taxonomy mapping file works like a risk logic tree.

Internally both the first usage and the second usage are treated in
the same way, since the first usage is a special case of the second
when all the weights are equal to 1.

Currently, this taxonomy mapping feature has been tested only for the scenario
and event based risk calculators.


Extended consequences
----------------------------------------------

Scenario damage calculations produce the so called *asset damage table*,
i.e. a set of damage distributions (the probability of being in each
damage state listed in the fragility functions) per each asset, event
and loss type. From the asset damage table it is possible to compute
generic consequences by multiplying for known coefficients specified in
what are called *consequence model*. For instance, from the probability
of being in the collapsed damage state, one might estimate the number of
fatalities, given the right multiplicative coefficient.

By default the engine allows to compute economic losses; in that case the
coefficients depends on the taxonomy and the consequence model can be
represented as a CSV file like the following:

===================	============	============	========	==========	===========	==========	
 taxonomy          	 consequence  	 loss_type  	 slight 	 moderate 	 extensive 	 complete 	
-------------------	------------	------------	--------	----------	-----------	----------	
 CR_LFINF-DUH_H2   	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 CR_LFINF-DUH_H4   	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 MCF_LWAL-DNO_H3   	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 MR_LWAL-DNO_H1    	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 MR_LWAL-DNO_H2    	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 MUR_LWAL-DNO_H1   	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 W-WS_LPB-DNO_H1   	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 W-WWD_LWAL-DNO_H1 	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
 MR_LWAL-DNO_H3    	 losses 	 structural 	 0.05   	 0.25     	 0.6       	 1        	
===================	============	============	========	==========	===========	==========	

The first field in the header is the name of a tag in the exposure; in
this case it is the taxonomy but it could be any other tag — for instance,
for volcanic ash-fall consequences, the roof-type might be more relevant,
and for recovery time estimates, the occupancy class might be more relevant.
The framework is meant to be used for generic consequences,
not necessarily limited to earthquakes, because since version 3.6 the engine
provides a multi-hazard risk calculator.

The second field of the header, the ``consequence``, is a string
identifying the kind of consequence we are considering. It is
important because it is associated to the name of the plugin function
to use to compute the consequence.

The other fields in the header are the loss_type and the damage states.
For instance the coefficient 0.25 for "moderate" means that the cost to
bring a structure in "moderate damage" back to its undamaged state is
25% of the total replacement value of the asset.


Scenarios from ShakeMaps
--------------------------

Beginning with version 3.1, the engine is able to perform `scenario_risk`
and `scenario_damage` calculations starting from the GeoJSON feed for
ShakeMaps_ provided by the United States Geological Survey (USGS). 
Furthermore, starting from version 3.12 it is possible to use 
ShakeMaps from other sources like the local filesystem or a custom URL.

.. _ShakeMaps: https://earthquake.usgs.gov/data/shakemap/

Running the Calculation
.......................

In order to enable this functionality one has to prepare a parent
calculation containing the exposure and risk functions for the
region of interest, say Peru. To that aim the user will need
to write a `prepare_job.ini` file like this one::

   [general]
   description = Peru - Preloading exposure and vulnerability
   calculation_mode = scenario
   exposure_file = exposure_model.xml
   structural_vulnerability_file = structural_vulnerability_model.xml

By running the calculation

  ``$ oq engine --run prepare_job.ini``

The exposure and the risk functions will be imported in the datastore.

This example only includes vulnerability functions for the loss type
``structural``, but one could also have in this preparatory job file the 
functions for nonstructural components and contents, and occupants, 
or fragility functions if damage calculations are of interest.

It is essential that each fragility/vulnerability function in the risk
model should be conditioned on one of the intensity measure types that 
are supported by the ShakeMap service – MMI, PGV, PGA, SA(0.3), SA(1.0), 
and SA(3.0). If your fragility/vulnerability functions involves an intensity
measure type which is not supported by the ShakeMap system
(for instance SA(0.6)) the calculation will terminate with an error.

Let's suppose that the calculation ID of this 'pre' calculation is 1000.
We can now run the risk calculation starting from a ShakeMap.
For that, one need a `job.ini` file like the following::

   [general]
   description = Peru - 2007 M8.0 Pisco earthquake losses
   calculation_mode = scenario_risk
   number_of_ground_motion_fields = 10
   truncation_level = 3
   shakemap_id = usp000fjta
   spatial_correlation = yes
   cross_correlation = yes

This example refers to the 2007 Mw8.0 Pisco earthquake in Peru
(see https://earthquake.usgs.gov/earthquakes/eventpage/usp000fjta#shakemap).
The risk can be computed by running the risk job file against the prepared
calculation::

  $ oq engine --run job.ini --hc 1000

Starting from version 3.12 it is also possible to specify the following sources
instead of a `shakemap_id`::

   # (1) from local files:
   shakemap_uri = {
         "kind": "usgs_xml",
         "grid_url": "relative/path/file.xml",
         "uncertainty_url": "relative/path/file.xml"
         }

   # (2) from remote files:
   shakemap_uri = {
         "kind": "usgs_xml",
         "grid_url": "https://url.to/grid.xml",
         "uncertainty_url": "https://url.to/uncertainty.zip"
         }
   
   # (3) both files in a single archive
   # containing grid.xml, uncertainty.xml:
   shakemap_uri = {
         "kind": "usgs_xml",
         "grid_url": "relative/path/grid.zip" 
         }

While it is also possible to define absolute paths, it is advised not to do
so since using absolute paths will make your calculation not portable
across different machines.

The files must be valid `.xml` USGS ShakeMaps `(1)`. One or both files can
also be passed as `.zip` archives containing a single valid xml ShakeMap
`(2)`. If both files are in the same `.zip`, the archived files `must` be
named ``grid.xml`` and ``uncertainty.xml``.

Also starting from version 3.12 it is possible to use ESRI Shapefiles
in the same manner as ShakeMaps. Polygons define areas with the same
intensity levels and assets/sites will be associated to a polygon if
contained by the latter. Sites outside of a polygon will be
discarded. Shapefile inputs can be specified similar to ShakeMaps::

   shakemap_uri = {
      "kind": "shapefile",
      "fname": "path_to/file.shp"
   }

It is only necessary to specify one of the available files, and the rest of the files
will be expected to be in the same location. It is also possible to have them
contained together in a `*.zip` file.
There are at least a `*.shp`-main file and a `*.dbf`-dBASE file required. The 
record field names, intensity measure types and units all need to be the same 
as with regular USGS ShakeMaps.

Irrespective of the input, the engine will perform the following operations:

1. download the ShakeMap and convert it into a format
   suitable for further processing, i.e. a ShakeMaps array with lon, lat fields
2. the ShakeMap array will be associated to the hazard sites in the region
   covered by the ShakeMap
3. by using the parameters ``truncation_level`` and
   ``number_of_ground_motion_fields`` a set of ground motion fields (GMFs)
   following the truncated Gaussian distribution will be generated and stored
   in the datastore
4. a regular risk calculation will be performed by using such GMFs and the
   assets within the region covered by the shakemap.

Correlation
...........

By default the engine tries to compute both the spatial correlation and the
cross correlation between different intensity measure types. Please note that 
if you are using MMI as intensity measure type in your vulnerability model,
it is not possible to apply correlations since those are based on physical measures.

For each kind of correlation you have three choices, that you can set in the 
`job.ini`, for a total of nine combinations::

- spatial_correlation = yes, cross_correlation = yes  # the default
- spatial_correlation = no, cross_correlation = no   # disable everything
- spatial_correlation = yes, cross_correlation = no
- spatial_correlation = no, cross_correlation = yes
- spatial_correlation = full, cross_correlation = full
- spatial_correlation = yes, cross_correlation = full
- spatial_correlation = no, cross_correlation = full
- spatial_correlation = full, cross_correlation = no
- spatial_correlation = full, cross_correlation = yes

`yes` means using the correlation matrix of the Silva-Horspool_ paper;
`no` mean using no correlation; `full` means using an 
all-ones correlation matrix.

.. _Silva-Horspool: https://onlinelibrary.wiley.com/doi/abs/10.1002/eqe.3154

Apart from performance considerations, disabling either the spatial correlation 
or the cross correlation (or both) might be useful to see how significant the 
effect of the correlation is on the damage/loss estimates.

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
spacing, the fewer the number of points, and the closer the calculation
will be to tractability.

Performance Considerations
..........................

The performance of the calculation will be crucially determined by the number
of hazard sites. For instance, in the case of the Pisco earthquake
the ShakeMap has 506,142 sites, which is a significantly large number of sites.
However, the extent of the ShakeMap in longitude and latitude is about 6
degrees, with a step of 10 km the grid contains around 65 x 65 sites;
most of the sites are without assets because most of the
grid is on the sea or on high mountains, so actually there are
around ~500 effective sites. Computing a correlation matrix of size
500 x 500 is feasible, so the risk computation can be performed.

Clearly in situations in which the number of hazard sites is too
large, approximations will have to be made such as using a larger
`region_grid_spacing`.  Disabling spatial AND cross correlation makes
it possible run much larger calculations. The performance can be
further increased by not using a ``truncation_level``.

When applying correlation, a soft cap on the size of the calculations
is defined. This is done and modifiable through the parameter
``cholesky_limit`` which refers to the number of sites multiplied by
the number of intensity measure types used in the vulnerability
model. Raising that limit is at your own peril, as you might run out
of memory during calculation or may encounter instabilities in the
calculations as described above.

If the ground motion values or the standard deviations are particularly
large, the user will get a warning about suspicious GMFs.

Moreover, especially for old ShakeMaps, the USGS can provide them in a
format that the engine cannot read.

Thus, this feature is not expected to work in 100% of the cases.

Note: on macOS make sure to run the script located under
``/Applications/Python 3.6/Install Certificates.command``,
after Python has been installed, to update the SSL certificates and to avoid
SSL errors when downloading the ShakeMaps from the USGS website
(see the FAQ_)

.. _FAQ: faq.md#Certificate-verification-on-macOS
