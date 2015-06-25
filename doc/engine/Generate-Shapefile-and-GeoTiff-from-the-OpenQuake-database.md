Some of the OpenQuake calculators write their output to the OpenQuake database.

This is a quick and dirty guide to visualize the output of your calculation in a shapefile or a Geotif.

When you run your calculation you will need to make note of the job number that is reported by OpenQuake.

log into your OpenQuake server, and navigate to your home directory and make an empty directory:
<pre>
mkdir my_calc_dir
</pre>
navigate into your new directory with:
<pre>
cd my_calc_dir
</pre>
then generate a shapefile of the whole table that contains your calculation by running: 
<pre>
pgsql2shp -u oq_admin -P openquake openquake hzrdr.gmf_data OQ_GMF_data.shp
</pre>
check out your new shapefile with:
<pre>
ls
</pre>
note that a shapefile is comprised of four or five files ending in .shp .shx .dbf .prj etc. 
now navigate out of the folder you created above with:
<pre>
cd ..
</pre>
Now you need to copy the file out of the OpenQuake server and onto your computer. First we need zip the file:
<pre>
tar -cvf my_calc.tgz my_calc_dir/
</pre>

then pull the file onto your computer, open a terminal session on your computer, navigate to an appropriate working directory and pull the file over with:
<pre>
scp myuser@myserver:my_calc.tgz .
</pre>
extract the file by running:
<pre>
tar -xf my_calc.tgz
</pre>

then open the shapefile in QGIS and clean it up so that you only have the one calculation you want (the bump above will give you the whole DB table). You will now need to know the Job number and the corresponding calculation output ID for the calculation you ran. See the database documentation here: https://github.com/gem/oq-engine/wiki/OpenQuake-database-schema-diagrams

Once your shapefile is limited to the calculation you are interested in, in QGIS or in terminal convert the shapefile to a geotiff. In QGIS from the top menu select: Raster - Conversion - Rasterize. Or in the terminal you can run the gdal_rasterize with:
<pre>
gdal_rasterize -a <the meaningful shape file attribute>  -ts 90 90 -l <layer name> <shapefile name> <output file name> </pre>