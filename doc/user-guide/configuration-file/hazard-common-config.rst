.. _hazard-common-params:

Common hazard parameters
------------------------

*******
general
*******

In a section conventionally called ``[general]``, the user specifies the parameters
to specify the calculation type and description::

	[general]
	description = A demo OpenQuake-engine .ini file for classical PSHA
	calculation_mode = classical

- ``description``: a parameter that can be used to designate the model
- ``calculation_mode``: used to set the kind of calculation. In this
  example it corresponds to ``classical``. Alternative options for the
  calculation_mode are described later in this manual.


********
geometry
********

A section conventionally called ``[geometry]`` is used to specify
where the hazard will be computed. Two options are available.

The first option is to define a polygon (usually a rectangle) and a
distance (in km) to be used to discretize the polygon area. The
polygon is defined by a list of longitude-latitude tuples, and the 
coordinates must be provided in either a clockwise or counterclockwise order.

An example is provided below::

	[geometry]
	region = 10.0 43.0, 12.0 43.0, 12.0 46.0, 10.0 46.0
	region_grid_spacing = 10.0

The second option allows the definition of a number of sites where the hazardwill be computed. Each site is specified 
in terms of a longitude, latitude tuple. Optionally, if the user wants to consider the elevation of the sites, a value 
of depth [km] can also be specified, where positive values indicate below sea level, and negative values indicate above 
sea level (i.e. the topographic surface). If no value of depth is given for a site, it is assumed to be zero. 

An example is provided below::

	[geometry]
	sites = 10.0 43.0, 12.0 43.0, 12.0 46.0, 10.0 46.0

If the list of sites is too long the user can specify the name of a CSV file as shown below::

	[geometry]
	sites_csv = <name_of_the_csv_file>

The format of the CSV file containing the list of sites is a sequence of points (one per row) specified in terms of the 
longitude, latitude tuple. Depth values are again optional. An example is provided below::

    site_id,lon,lat
	0,179.0,90.0
	1,178.0,89.0
	2,177.0,88.0

For reasons of backward compatibility, it is also possible to skip the header and to omit the ``site_id`` column, however
we recommend to avoid that format, since it is error prone given that many users tend to use the lat,lon convention
instead of the lon,lat convention that the engine honors::

	179.0,90.0
	178.0,89.0
	177.0,88.0

***************
site conditions
***************

Such parameters are used to specify local soil conditions and are normally listed in a section of the ``job.ini``
file called ``[site_params]``. The simplest possibility is to define uniform site conditions 
(i.e. all the sites have the same characteristics), as in this example::

	[site_params]
	reference_vs30_type = measured
	reference_vs30_value = 760.0
	reference_depth_to_2pt5km_per_sec = 5.0
	reference_depth_to_1pt0km_per_sec = 100.0

Alternatively it is possible to define spatially variable soil properties in a separate file; the engine will then 
assign to each investigation location the values of the closest point used to specify site conditions::

	[site_params]
	site_model_file = site_model.csv

The file containing the site model has the following structure::

	lon,lat,vs30,z1pt0,z2pt5,vs30measured,backarc
	10.0,40.0,800.0,19.367196734,0.588625072259,0,0
	10.1,40.0,800.0,19.367196734,0.588625072259,0,0
	10.2,40.0,800.0,19.367196734,0.588625072259,0,0
	10.3,40.0,800.0,19.367196734,0.588625072259,0,0
	10.4,40.0,800.0,19.367196734,0.588625072259,0,0

Notice that the 0 for the field ``vs30measured`` means that the ``vs30`` field is inferred, not measured. Most of the 
GMPEs are not sensitive to it, so you can usually skip it. For the ``backarc`` parameter 0 means false and this is the 
default, so you can skip such column. All columns that have defaults or are not needed by the GMPEs you are using can 
be skipped, while you will get an error if a relevant column is missing.

If the closest available site with soil conditions is at a distance greater than 5 km from the investigation location, a 
warning is generated.

**Note**: For backward-compatibility reasons, the site model file can also be given in XML format. That old format is 
deprecated but there are no plans to remove it any soon.

There are a lot more site parameters than the one listed above. You can get the full list with the command
`oq info`::
  
 $ oq info site_params # full list as of engine-3.20
             D50_15              F_15                Fs               PHV
                THV              T_15              T_eq           ampcode
         amplfactor           backarc               bas         ch_ampl03
          ch_ampl06       ch_phis2s03       ch_phis2s06        ch_phiss03
         ch_phiss06      cohesion_mid        crit_accel               cti
     custom_site_id                dc             depth                dr
        dry_density                dw               dwb               ec8
            ec8_p18                f0    freeface_ratio      friction_mid
            geohash           geology               gwd              h800
             hwater           in_cshm            kappa0               lat
       liq_susc_cat               lon            precip            region
             relief        saturation              sids           site_id
          siteclass             slope          soiltype               tri
               unit              vs30      vs30measured               xvf
 yield_acceleration             z1pt0             z1pt4             z2pt5
                zwb

Most parameters are very specific to particular GMPEs and particular
calculations, so you need to study the implementation of the specific
feature you are interested in to know what they mean and how they
work.
