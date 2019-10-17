How the hazard sites are determined
=====================================================

There are several ways to specify the hazard sites in an engine calculation.

1. The user can specify the sites directly in the job.ini
   (i.e. `sites = 0 0, 1 2`) This is the most direct way.
2. Otherwise the user can specify the sites in a .csv file
   (i.e. `sites_csv = sites.csv`).
3. Otherwise the user can specify a grid via the `region` and
   `region_grid_spacing` parameters
4. Otherwise the sites can be inferred from the exposure, if any,
   in two different ways:
   
   4a. if `region_grid_spacing` is specified a grid is implicitely
       generated from the convex hull of the exposure and used
   4b. otherwise the locations of the assets are used as hazard sites

5. Otherwise the sites can be inferred from the site model, if any.

Having determined the sites, a `SiteCollection` object is generated
by associating the closest parameters from the site model (if any)
or using the global site parameters, if any.
If the site model is specified, but the
closest site parameters are too distant from the sites, a warning
is logged for each site.

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

The relation between asset locations and hazard sites
=====================================================

This is one of the most frequently asked questions in the mailing list.
The answer is long and difficult and depends very much on the version
of the engine, since there are several corner cases and tricky points.


The case with explicit sites and no site model
----------------------------------------------

If the user specifies the hazard sites in a CSV file, such sites are
the ones used to compute the hazard.
