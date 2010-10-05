TABLES FOR VERIFYING OPENSHA IMPLEMENTATION OF NGA MODELS

MODEL:	Boore and Atkinson (2008)
	Earthquake Spectra, Vol. 24, March (Final)

FILES:
	BA08_MODEL.FOR - FORTRAN subroutine of BA08 NGA model for a single period
	BA08_OPENSHA.FOR - FORTRAN program to evaluate BA08 NGA model
	BA08_COEFS.TXT - ASCII table of BA08 model coefficients (Revised 01/04/08)
	BA08_MEDIAN_SS.OUT - Median estimates of geometric mean for Strike-slip (SS) faulting
	BA08_MEDIAN_RV.OUT - Median estimates of geometric mean for Reverse (RV) faulting
	BA08_MEDIAN_NM.OUT - Median estimates of geometric mean for Normal (NM) faulting
	BA08_MEDIAN_U.OUT - Median estimates of geometric mean for Unspecified (U) faulting
	BA08_SIGTM_SS.OUT - Standard deviation of geometric mean for known faulting (evaluated for SS)
	BA08_SIGTU_SS.OUT - Standard deviation of geometric mean for unspecified faulting (evaluated for SS)

PARAMETERS IN OUTPUT FILES:
	Mw - Moment magnitude
	Rrup - Closest distance to coseismic rupture (not used; set to 0)
	Rjb - Closest distance to surface projection of coseismic rupture (km)
	Rx - Horizontal distance from top of rupture perpendicular to fault strike (not used; set to 0)
	Dip - Average dip of the rupture plane (not used; set to 0)
	W - Width of rupture plane (not used; set to 0)
	Ztor - Depth to the top of the rupture plane (not used; set to 0)
	Vs30 - Time-averaged shear-wave velocity in top 30 m of the soil profile (m/sec)
	Zsed - Sediment or basin depth (not used; set to 0)
	1.000E-02, etc. - Period representing value of PSA (g) or its standard deviation (ln)
	PGA - Value of peak ground acceleration (g) or its standard deviation (ln)
	PGV - Value of peak ground velocity (cm/sec) or its standard deviation (ln)
	PGA4NL - Value of rock PGA (g) used for nonlinear soil term
