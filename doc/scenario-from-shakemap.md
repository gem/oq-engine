Scenario calculations starting from USGS shakemaps
==================================================

Since version 3.1 the engine is able to perform `scenario_risk`
and `scenario_damage` calculations starting from the shakemaps provided
by the United States Geological Survey (USGS) service.

First of all, one has to prepare a parent calculation containing the
full exposure and risk functions for the region of interest, say South
America. To that aim the user will need to write a `job_hazard.ini` file
like this one:

```
   [general]
   description = Full South America
   calculation_mode = scenario
   exposure_file = full_exposure_model.xml
   structural_vulnerability_file = structural_vulnerability_model.xml
```
By running the calculation

```bash
$ oq engine --run job_hazard.ini
```

the exposure and the risk functions will be imported in the datastore.

In this example there are only vulnerability functions for the loss type
`structural`, but there could be more, and even fragility functions.

The hazard has to be prepared only once.

Let's suppose that the calculation ID of this hazard calculation is 1000.
We can now run the risk on a given shakemap.
For that, one need a `job_risk.ini` file like the following::

```
   [general]
   calculation_mode = scenario_risk
   number_of_ground_motion_fields = 10
   truncation_level = 3
   shakemap_id = usp000fjta
```

This example refers to an Earthquake happened in Pisco in Peru in 2007
(see https://earthquake.usgs.gov/earthquakes/eventpage/usp000fjta#shakemap).
The risk can be computed by running the risk file against the prepared
hazard calculation:

```bash
$ oq run job_risk.ini --hc 1000
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
