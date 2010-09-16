Opengem Seismic Source Administration (Django/GeoDjango)
=======================================================
Aurea Moemke, 16 Sep 2010

This distribution arose from the user story: Basic Rest Interface (on
Datastores). It is basically a test on how to integrate the current Opengemdb
Postgis backend and provide this data via RESTful interfaces.  The web
framework of choice is the Django/GeoDjango using Python code. 
For projects where you need to get a robust database driven application online in a timely manner, Django can be an exceptional tool.  

This download provides a project called 'seismic_source_admin' with an 
application called 'seismicsources'. It is currently on test status.
It is based on the geographic admin application at 
http://code.google.com/p/geodjango-basic-apps/


The dataset covered by the project is a portion of the Opengemdb Ver 1.4
covering source geometry catalogs and seismic sources.  These database 
table structures and data may be recreated with the sql files that come 
with this distribution.  Loading of data from various sources (i.e. ASCII
text, Shapefiles) will be covered in the next distribution. 

This distribution is tested on a PostgreSQL/Postgis database.  It is necessary
to use a relational database with geospatial extensions.

The seismicsourcedb consists of two tables: the SourceGeometryCatalog table
and the SeismicSource table.  Each Source Geometry Catalog can have one or more
seismic sources (either Simple Fault, Complex/Subduction Fault, Area Source or
Gridded Seismicity Point. They may have any of the following geometry types: 
(multi)point, (multi)linestring, (multi)polygon.

This project code uses the Admin and Databrowse contrib applications
with an OpenLayers map interface and OpenStreetMap basedata.  

This distribution is testedbased on the 

(1) Check out the seismic_source_admin branch from the opengem github.
The project is in opengem/db/seismic_source_admin/

(2) Load all necessary dependencies:
o Django 1.1 (see www.djangoproject.com for installation instructions)
o PostgreSQL/PostGIS
o Psycopg2
o GEOS
o Proj 4
o GDAL
o OpenLayers
For installing 

Test if you have what you need:
To check if your system is setup correctly with above dependencies, start the
python interpreter and type:
>>>import django
>>>print django.VERSION
(1, 1, 1, 'final', 0)
>>> from django.contrib.gis.gdal import HAS_GDAL
>>> HAS_GDAL
True

(3) Create the database. The following instructions are for postgresql:
(a) If you have not yet done so, create a postgis template called 
    template_postgis.  For instructions, refer to:
    http://docs.djangoproject.com/en/dev/ref/contrib/gis/install/
         #spatialdb-template  
    (under the GeoDjango Installation, Post Installation, Creating a Spatial
    Database Template for PostGIS)
(b) Create the database.
        createdb -T template_postgis -U postgres seismicsourcedb
        python manage.py syncdb  
   

(4) Modify the following settings.py in the project:
    DATABASE_ENGINE = 'postgresql_psycopg2' #This is the setting for postgresql
    DATABASE_NAME = 'seismicsourcedb'
    DATABASE_USER = ''
    DATABASE_PASSWORD = ''
    DATABASE_PORT = ''

This project is based on the application code found at:
http://code.google.com/p/geodjango-basic-apps/wiki/GeographicAdminQuickStart
 
