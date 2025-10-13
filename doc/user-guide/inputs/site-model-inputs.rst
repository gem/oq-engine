Site Models
===========

This section is used to specify where the hazard will be computed. Two options are available:

The first option is to define a polygon (usually a rectangle) and a distance (in km) to be used to discretize the 
polygon area. The polygon is defined by a list of longitude-latitude tuples.

An example is provided below::

	[geometry]
	region = 10.0 43.0, 12.0 43.0, 12.0 46.0, 10.0 46.0
	region_grid_spacing = 10.0

The second option allows the definition of a number of sites where the hazard will be computed. Each site is specified 
in terms of a longitude, latitude tuple. Optionally, if the user wants to consider the elevation of the sites, a value 
of depth [km] can also be specified, where positive values indicate below sea level, and negative values indicate above 
sea level (i.e. the topographic surface). If no value of depth is given for a site, it is assumed to be zero. An example 
is provided below::

	[geometry]
	sites = 10.0 43.0, 12.0 43.0, 12.0 46.0, 10.0 46.0

If the list of sites is too long the user can specify the name of a csv file as shown below::

	[geometry]
	site_model_csv = <name_of_the_csv_file>

The format of the csv file containing the list of sites is a sequence of points (one per row) specified in terms of the 
longitude, latitude tuple. Depth values are again optional. An example is provided below::

     site_id,lon,lat
	0,179.0,90.0
	1,178.0,89.0
	2,177.0,88.0

The complete list of valid site parameters that can go into a site model .csv file are listed here. Currently, the work
in documentation to describe this input parameters more explicitly, and to provide short descriptions of each valid site 
parameter and where they are needed is in progress::

	# dtype of each valid site parameter
	site_param_dt = {
	    'sids': numpy.uint32,
	    'site_id': numpy.uint32,
	    'lon': numpy.float64,
	    'lat': numpy.float64,
	    'depth': numpy.float64,
	    'vs30': numpy.float64,
	    'kappa0': numpy.float64,
	    'vs30measured': bool,
	    'z1pt0': numpy.float64,
	    'z2pt5': numpy.float64,
	    'siteclass': (numpy.string_, 1),
	    'geohash': (numpy.string_, 6),
	    'z1pt4': numpy.float64,
	    'backarc': numpy.uint8,  # 0=forearc,1=backarc,2=alongarc
	    'xvf': numpy.float64,
	    'soiltype': numpy.uint32,
	    'bas': bool,
	
	    # Parameters for site amplification
	    'ampcode': ampcode_dt,
	    'ec8': (numpy.string_, 1),
	    'ec8_p18': (numpy.string_, 2),
	    'h800': numpy.float64,
	    'geology': (numpy.string_, 20),
	    'amplfactor': numpy.float64,
	    'ch_ampl03': numpy.float64,
	    'ch_ampl06': numpy.float64,
	    'ch_phis2s03': numpy.float64,
	    'ch_phis2s06': numpy.float64,
	    'ch_phiss03': numpy.float64,
	    'ch_phiss06': numpy.float64,
	    'fpeak': numpy.float64,
	    # Fundamental period and and amplitude of HVRSR spectra
	    'THV': numpy.float64,
	    'PHV': numpy.float64,
	
	    # parameters for secondary perils
	    'friction_mid': numpy.float64,
	    'cohesion_mid': numpy.float64,
	    'saturation': numpy.float64,
	    'dry_density': numpy.float64,
	    'Fs': numpy.float64,
	    'crit_accel': numpy.float64,
	    'unit': (numpy.string_, 5),
	    'liq_susc_cat': (numpy.string_, 2),
	    'dw': numpy.float64,
	    'yield_acceleration': numpy.float64,
	    'slope': numpy.float64,
	    'relief': numpy.float64,
	    'gwd': numpy.float64,
	    'cti': numpy.float64,
	    'dc': numpy.float64,
	    'dr': numpy.float64,
	    'dwb': numpy.float64,
	    'zwb': numpy.float64,
	    'tri': numpy.float64,
	    'hwater': numpy.float64,
	    'precip': numpy.float64,
	
	    # parameters for YoudEtAl2002
	    'freeface_ratio': numpy.float64,
	    'T_15': numpy.float64,
	    'D50_15': numpy.float64,
	    'F_15': numpy.float64,
	    'T_eq': numpy.float64,
	
	    # other parameters
	    'custom_site_id': (numpy.string_, 8),
	    'region': numpy.uint32,
	    'in_cshm': bool  # used in mcverry
	}

The ``custom_site_id``
----------------------

Since engine v3.13, it is possible to assign 6-character ASCII strings as unique identifiers for the sites (8-characters 
since engine v3.15). This can be convenient in various situations, especially when splitting a calculation in geographic 
regions. The way to enable it is to add a field called ``custom_site_id`` to the site model file, which must be unique 
for each site.

The hazard curve and ground motion field exporters have been modified to export the ``custom_site_id`` instead of the 
``site_id`` (if present).

We used this feature to split the ESHM20 model in two parts (Northern Europe and Southern Europe). Then creating the 
full hazard map was as trivial as joining the generated CSV files. Without the ``custom_site_id`` the site IDs would 
overlap, thus making impossible to join the outputs.

A geohash string (see https://en.wikipedia.org/wiki/Geohash) makes a good ``custom_site_id`` since it can enable the 
unique identification of all potential sites across the globe.
