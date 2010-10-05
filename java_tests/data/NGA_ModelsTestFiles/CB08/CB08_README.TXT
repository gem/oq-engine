TABLES FOR VERIFYING OPENSHA IMPLEMENTATION OF NGA MODELS

MODEL:	Campbell and Bozorgnia (2008)
	Earthquake Spectra, Vol. 24, March (Final)

FILES:
	CB08_MEDIAN_SS.TXT - Median estimates of geometric mean for strike-slip (SS) faulting
	CB08_MEDIAN_RV.TXT - Median estimates of geometric mean for reverse (RV) faulting
	CB08_MEDIAN_NM.TXT - Median estimates of geometric mean for normal (NM) faulting
	CB08_SIGMEAN_SS.TXT - Total standard deviation of geometric mean for SS faulting
	CB08_SIGARB_SS.TXT - Total standard deviation of arbitrary horizontal component for SS faulting

PARAMETERS IN OUTPUT FILES:
	Mw - Moment magnitude
	Rrup - Closest distance to coseismic rupture (km)
	Rjb - Closest distance to surface projection of coseismic rupture (km)
    Rx - Horizontal distance from top of rupture perpendicular to fault strike (not used; set to 0)
	Dip - Average dip of the rupture plane (degrees)
	W - Width of rupture plane (not used; set to 0)
	Ztor - Depth to the top of the rupture plane (km)
	Vs30 - Time-averaged shear-wave velocity in top 30 m of the soil profile (m/sec)
	Zsed - Sediment or basin depth (Z2.5 in CB08 model) (km)
	1.000E-02, etc. - Period representing value of PSA (g) or its standard deviation (ln)
	PGA - Value of peak ground acceleration (g) or its standard deviation (ln)
	PGV - Value of peak ground velocity (cm/sec) or its standard deviation (ln)
	PGD - Value of peak ground displacement (cm) or its standard deviation (ln)
