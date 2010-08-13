'''
Created on Aug 11, 2010

@author: Aurea Moemke
'''
#!/usr/bin/env python2
"""Parser for Earthquake Catalog and Event Data

Writes earthquake catalaog and event data into the opengemdb based on an
ASCII text file specified in a given format

This program parses earthquake catalog event data from an ascii file in a 
specific format and writes it into the opengemdb.
Visit the opengem github site for the latest version.
"""

__author__ = "Aurea Moemke (aurea.moemke@yahoo.com, aurea.moemke@sed.ethz.ch)"
__version__ = "$Revision: 1.0 $"
__date__ = "$Date: 2010/08/12 10:43 $"
__copyright__ = "Copyright (c) 2010 Aurea Moemke"
__license__ = "Python"

import sys
import getopt
import eventdata

from dbconnect import dbconnect

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from geoalchemy import *
from geoalchemy.postgis import PGComparator
import binascii

from geoalchemy.functions import functions
from geoalchemy.postgis import pg_functions

_debug = 0

class NoSourceError(Exception): pass


class EqCatParser:
    """generates earthquake catalog and event data from an ASCII text file"""
    
    def __init__(self,inputfile,ecid, formatdefn):
        self.inputfile=inputfile;
        self.ecid=ecid;
        self.formatdefn=formatdefn;
        
    def loadEqcatfile(self):
        """load ASCII file

        """
        f = open(self.inputfile,'r')
        return f

    def loadEventData(self, line):
        
        if self.formatdefn == 1:
            eventData = eventdata.EventData()
            eventData.parseGshapeaEventData(line)
       
        return eventData
   
def usage():
    print __doc__

def main(argv):
    
    conn_str = "postgresql://gemdev:gem4321@gemsun01.ethz.ch/opengemdbpython"
    inputfile = "gshapeacat.txt"
    formatdefn = 1  #default: 1=GSHAPEA format
    catalogname = 'GSHAPEA'
    catalogshortname='GSHAPEA'
    catalogpolygon="POLYGON((40 0,160 0,160 60, 40 60,40 0))"
    
    engine = dbconnect(conn_str)
    metadata = MetaData(engine)
    Base = declarative_base(metadata=metadata)
    connection = engine.connect()
    
    # Define the model classes
    class EarthquakeCatalog(Base):
        __tablename__ = 'earthquakecatalog'
        __table_args__ = {'autoload': True}
        ecpgareapolygon = GeometryColumn(Polygon(2), comparator=PGComparator)
        ecpgareamultipolygon = GeometryColumn(MultiPolygon(2), comparator=PGComparator)
    
    class Event(Base):
        __tablename__ = 'event'
        __table_args__ = {'autoload': True}
        evpgpoint = GeometryColumn(Point(1), comparator=PGComparator)
 
    Session=sessionmaker(bind=engine)
    session=Session()
            
    #CREATE Earthquake Catalog in Earthquakecatalog file
    #FOR VER140 in gemsun01:
 
    eqcat = EarthquakeCatalog(ecprivatetag=False, ecshortname=catalogshortname, ecname=catalogname,\
                              ecareapolygon=catalogpolygon, ecpgareapolygon=WKTSpatialElement(catalogpolygon))
    
    session.add(eqcat)
    session.commit()
    
    eqcatid = eqcat.ecid
    
    #Display all earthquake catalogs in database
    #results=session.query(EarthquakeCatalog).all()
    
    #for row in results:
    #    print row.ecname, session.scalar(row.ecpgareapolygon.wkt)
    
    #Show values of current earthquake catalog
    results = session.query(EarthquakeCatalog).filter(EarthquakeCatalog.ecshortname==catalogname)
    for row in results:
        print row.ecid, row.ecshortname, session.scalar(row.ecpgareapolygon.wkt)
    
    f = EqCatParser(inputfile,eqcatid,formatdefn)
    
    contents = f.loadEqcatfile()
    
    #CREATE EVENTS For EarthquakeCatalog GSHAPEA4
    i = 0
    
    #READ EACH LINE IN EqCat File and parse
    for line in contents:
        if i==0:
            i = i + 1
            continue
        print i, ": ", line
        i = i + 1
        eventData = f.loadEventData(line)
        event = Event(ecid=eqcatid,evtimestamp=eventData.eventtimestamp,evyear=eventData.eventyear,evmonth=eventData.eventmonth,\
                      evday=eventData.eventday, evmin=eventData.eventmins,evsec=eventData.eventsecs,evnanosec=eventData.eventnanosecs,\
                      evlat=eventData.eventlat,evlong=eventData.eventlon,evmagnitude=eventData.eventmagnitude,evdepth=eventData.eventdepth,\
                      evremarks=eventData.eventremarks,evpoint=eventData.eventpoint,evpgpoint=WKTSpatialElement(eventData.eventpoint))
        session.add(event)
        session.commit()

if __name__ == "__main__":
    main(sys.argv[1:])
