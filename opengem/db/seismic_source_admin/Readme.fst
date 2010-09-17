Opengem Seismic Source Administration (Django/GeoDjango)
=======================================================
Aurea Moemke, 17 Sep 2010

This distribution arose from the user story: Basic Rest Interface (on
Datastores). This download provides a project called 'seismic_source_admin' 
with an application called 'seismicsources'. It is currently on test status
and far from complete. However, I believe it is enough to show the basic 
concepts that can be used to provide a complete solution.

The goal of this story is to illustrate how we can use the Django/GeoDjango
web framework with Opengem's spatially-enabled database to provide basic 
RESTful interfaces.  This test makes use of a portion of the Opengemdb Ver 1.4 
to illustrate the concept. This test borrows heavily from an opensource 
tutorial application available at http://code.google.com/geodjango-basic apps/
 
In particular, the Admin and Databrowse contrib applications with OpenLayers 
map interface and OpenStreetMap basedata were used to show the Source Geometry
Catalog area of interest and Seismic Source geometries.

The database table structures and data are recreated with the sql files that
come with this distribution.  Loading of data from other formats (i.e. ASCII
text, Shapefiles), if deemed necessary,  will be covered in the next 
distribution. 

This distribution is tested on PostgreSQL/Postgis, an opensource
relational dbms with geospatial extensions.

Here are the steps for installing this distribution:

(1) Check out the seismic_source_admin branch from the opengem github.
    The project is in opengem/db/seismic_source_admin/.
         $ git checkout seismic_source_admin

(2) Load all necessary dependencies:
    o Django 1.1 (see www.djangoproject.com for installation instructions)
    o PostgreSQL/PostGIS
    o Psycopg2
    o GEOS
    o Proj 4
    o GDAL

    To check if your system is set up correctly, start the python interpreter
    and enter the following:
    >>>import django
    >>>print django.VERSION
    (1, 1, 1, 'final', 0)
    >>> from django.contrib.gis.gdal import HAS_GDAL
    >>> HAS_GDAL
    True

(3) Create the database and load with data. 
    The following instructions are for postgresql.
    (a) If you have not yet done so, create a postgis template called 
        template_postgis.  For complete instructions, refer to:
             http://docs.djangoproject.com/en/dev/ref/contrib/gis/install/
                  #spatialdb-template  
    (b) Create the database.
            $ createdb -T template_postgis -U yourusername seismicsourcedb
    (c) Load sql files. This will create 2 tables (sourcegeometrycatalog and
        seismic source) and load them with data.
            $ psql seismicsourcedb postgres < ssdump.sql
   
(4) Modify the settings.py file. Set your postgres user name and password.
    DATABASE_ENGINE = 'postgresql_psycopg2' # setting for Postgresql
    DATABASE_NAME = 'seismicsourcedb'       # the database name
    DATABASE_USER = ''                      # add your user name
    DATABASE_PASSWORD = ''                  # add your password
    DATABASE_PORT = '5432'                  # port used by PostgreSQL    

(5) Start the server.
         $ python manage.py runserver

(6) Synchronize the database. Type yes when prompted for a superuser.
    This will be your login to the Admin panel.
         $ python manage.py syncdb

(7) View project in your browser. Go to to http://localhost:8080/admin/

References:
http://docs.djangoproject.com/
http://geodjango.org/
http://code.google.com/geodjango-basic-apps/
 
