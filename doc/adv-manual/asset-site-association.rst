How the hazard sites are determined
=====================================================

There are several ways to specify the hazard sites in an engine calculation.
There are listed here, in order of precedence.

1. The user can specify the sites directly in the job.ini
   (i.e. `sites = 0 0, 1 2`) This is the most direct way.
2. The user can specify the sites in a .csv file
   (i.e. `sites_csv = sites.csv`).
3. The user can specify a grid via the `region` and
   `region_grid_spacing` parameters
4. If the `region` parameter is
   missing but `region_grid_spacing` is specified and there is an exposure,
   a grid is implicitely generated from the convex hull of the exposure
5. Otherwise the sites can be inferred from the site model, if any.
6. Finally, if the user is running a `classical_risk` or
   `classical_damage` calculation starting from a set of hazard curves
   in CSV format, then the sites are read from such file.

Moreover, it should be noticed that the engine rounds longitudes and latitudes
to 5 digits (1 meter resolution) so sites that differs at the 6 digit or so
end up as being duplicated for the engine, and they may give issues.
   
Having determined the sites, a `SiteCollection` object is generated
by associating to each site the closest parameters from the site model (if any)
or using the global site parameters, if any.

If the site model is specified, but the closest site parameters are
too distant from the sites, a warning is logged for each site.

There are a number of error situations:

1. If both site model and global site parameters are missing the engine
   raises an error.
2. If both site model and global site parameters are specified the
   engine raises an error.
3. Specifying both the sites.csv and a grid is an error.
4. Specifying both the sites.csv and a site_model.csv is an error.
   If you are in such situation you should use the command
   `oq prepare_site_model`
   to manually prepare a site model on the location of the sites.
5. Having duplicates (i.e. rows with identical lon, lat) in the site model
   is an error.
