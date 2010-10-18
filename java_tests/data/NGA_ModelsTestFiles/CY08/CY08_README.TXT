TABLES FOR VERIFYING OPENSHA IMPLEMENTATION OF NGA MODELS

MODEL:	Chiou and Youngs (2008)
	Earthquake Spectra, February 2008, Vol. 24, p. 173-215

FILES:
	CY08_MODEL.FOR - FORTRAN subroutine to evaluate CY08 NGA model for a single period
	CY08_OPENSHA.FOR - FORTRAN program to evaluate CY08 NGA model for OpenSHA verification
	CY08_COEFS.TXT - ASCII table of CY08 model coefficients
	CY08_MEDIAN_AS_FW_SS.OUT - Median estimates of geometric mean for Aftershock (AS), Footwall (FW), Strike-slip (SS) faulting
	CY08_MEDIAN_MS_HW_NM.OUT - Median estimates of geometric mean for Mainshock (MS), Hanging-wall (HW), Normal (NM) faulting
	CY08_MEDIAN_MS_HW_RV.OUT - Median estimates of geometric mean for Mainshock (MS), Hanging-wall (HW), Reverse (RV) faulting
	CB08_MEDIAN_MS_HW_SS.OUT - Median estimates of geometric mean for Mainshock (MS), Hanging-wall (HW), Strike-slip (SS) faulting
	CY08_SIGINFER_AS_FW_SS.OUT - Total standard deviation of geometric mean (Inferred Vs30) for Aftershock (AS), Footwall (FW), Strike-slip (SS) faulting
	CY08_SIGINFER_MS_HW_SS.OUT - Total standard deviation of geometric mean (Inferred Vs30) for Mainshock (MS), Hanging-wall (HW), Strike-slip (SS) faulting
	CY08_SIGMEAS_AS_FW_SS.OUT - Total standard deviation of geometric mean (Measured Vs30) for Aftershock (AS), Footwall (FW), Strike-slip (SS) faulting
	CY08_SIGMEAS_MS_HW_SS.OUT - Total standard deviation of geometric mean (Measured Vs30) for Mainshock (MS), Hanging-wall (HW), Strike-slip (SS) faulting

PARAMETERS IN OUTPUT FILES:
	Mw - Moment magnitude
	Rrup - Closest distance to coseismic rupture (km)
	Rjb - Closest distance to surface projection of coseismic rupture (km)
        Rx - Horizontal distance from top of rupture perpendicular to fault strike (km)
	Dip - Average dip of the rupture plane (degrees)
	W - Width of rupture plane (not used; set to 0)
	Ztor - Depth to the top of the rupture plane8 (km)
	Vs30 - Time-averaged shear-wave velocity in top 30 m of the soil profile (m/sec)
	Zsed - Sediment or basin depth (Z1.0 in CY08 model) (km)
	1.000E-02, etc. - Period representing value of PSA (g) or its standard deviation (ln)
	PGA - Value of peak ground acceleration (g) or its standard deviation (ln)
        PGV - Value of peak ground velocity (cm/s) or its standard deviation (ln)
