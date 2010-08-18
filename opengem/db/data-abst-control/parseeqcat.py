#!/usr/bin/env python2
"""Parser for Earthquake Catalog and Event Data

@author: Aurea Moemke

Writes earthquake catalaog and event data into the opengemdb based on an
ASCII text file specified in a given format

This program parses earthquake catalog event data from an ascii file in a 
specific format and writes it into the opengemdb.
Visit the opengem github site for the latest version.
"""

__author__ = "Aurea Moemke (aurea.moemke@sed.ethz.ch)"
__version__ = "$Revision: 1.0 $"
__date__ = "$Date: 2010/08/12 10:43 $"
__copyright__ = "Copyright (c) 2010 Aurea Moemke"
__license__ = "Python"

import sys

from sqlalchemy.ext import declarative
from sqlalchemy import MetaData
from sqlalchemy.orm import session

from geoalchemy import postgis
from geoalchemy import base
from geoalchemy import geometry

import dbconnect
import eventdata

_debug = 0

conn_str = "postgresql://<user>:<password>@<host>/<dbname>"
engine = dbconnect.dbconnect(conn_str)
metadata = MetaData(engine)
Base = declarative.declarative_base(metadata = metadata)
    
# Define the model classes
class EarthquakeCatalog(Base):
    __tablename__ = 'earthquakecatalog'
    __table_args__ = {'autoload': True}
    ecpgareapolygon = geometry.GeometryColumn(geometry.Polygon(2), 
                        comparator = postgis.PGComparator)
    ecpgareamultipolygon = geometry.GeometryColumn(geometry.MultiPolygon(2),
                        comparator = postgis.PGComparator)

class Event(Base):
    __tablename__ = 'event'
    __table_args__ = {'autoload': True}
    evpgpoint = geometry.GeometryColumn(geometry.Point(1), 
                        comparator = postgis.PGComparator)
 
class NoSourceError(Exception): pass

class EqCatParser:
    """generates earthquake catalog and event data from an ASCII text file"""
    
    def __init__(self,inputfile,ecid, formatdefn):
        self.inputfile = inputfile;
        self.ecid = ecid;
        self.formatdefn = formatdefn;
        
    def loadEqcatfile(self):
        """load ASCII file

        """
        f = open(self.inputfile,'r')
        return f

    def loadEventData(self, line):
        
        if self.formatdefn == 1:
            eventData = eventdata.EventData()
            eventData.parse_gshapea_event_data(line)
       
        return eventData
   
def usage():
    print __doc__

def main(argv):

    inputfile = "gshapeacat.txt"
    # Default is 1 = GSHAPEA format
    formatdefn = 1  
    catalogname = 'GSHAPEA'
    catalogshortname = 'GSHAPEA'
    catalogpolygon = "POLYGON((40 0,160 0,160 60, 40 60,40 0))"

    Session = session.sessionmaker(bind = engine)
    sess = Session()
            
    # Create Earthquake Catalog in Earthquakecatalog file
    # For Ver140:
 
    eqcat = EarthquakeCatalog(ecprivatetag = False,
                    ecshortname = catalogshortname, 
                    ecname = catalogname, 
                    ecareapolygon = catalogpolygon, 
                    ecpgareapolygon = base.WKTSpatialElement(catalogpolygon))
    
    sess.add(eqcat)
    sess.commit()
    
    eqcatid = eqcat.ecid
    
    # To display all earthquake catalogs in database
    # 
    # results=session.query(EarthquakeCatalog).all()
    # for row in results:
    #    print row.ecname, session.scalar(row.ecpgareapolygon.wkt)
    
    # Show values of current earthquake catalog
    results = sess.query(EarthquakeCatalog).\
            filter(EarthquakeCatalog.ecshortname == catalogname)
    for row in results:
        print row.ecid, row.ecshortname, sess.scalar(row.ecpgareapolygon.wkt)
    
    f = EqCatParser(inputfile,eqcatid,formatdefn)
    
    contents = f.loadEqcatfile()
    
    # Read each line in Earthquakecatalog file and parse
    i = 0
    for line in contents:
        if i == 0:
            i = i + 1
            continue
        print i, ": ", line
        i = i + 1
        eventData = f.loadEventData(line)
        event = Event(ecid = eqcatid, evtimestamp = eventData.timestamp,
                    evyear = eventData.year, 
                    evmonth = eventData.month,
                    evday = eventData.day, 
                    evmin = eventData.mins, 
                    evsec = eventData.secs, 
                    evnanosec = eventData.nanosecs,
                    evlat = eventData.lat, 
                    evlong = eventData.lon,
                    evmagnitude = eventData.magnitude, 
                    evdepth = eventData.depth, 
                    evremarks = eventData.remarks,
                    evpoint = eventData.point, 
                    evpgpoint = base.WKTSpatialElement(eventData.point))
        
        sess.add(event)
        sess.commit()

if __name__ == "__main__":
    main(sys.argv[1:])
