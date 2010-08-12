'''
Created on Aug 11, 2010

@author: apm
'''
#!/usr/bin/env python2
"""Parser for Earthquake Catalog and Event Data

Writes earthquake catalaog and event data into the opengemdb based on an
ASCII text file specified in a given format


Usage: python parseeqcat.py [options] [source]

Options:
  -n                    specify catalog name string
  -i                    specify input file name including path
  -o                    specify input file format
  -h, --help            show this help
  -d                    show debugging information while parsing

Examples:
  parseeqcat.py                                writes Earthquake catalog and event data to opengemdb
  parseeqcat -n gshapea -i gshapcatalog.txt    writes Earthquake catalog gshapea 

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
            eventData.parseEventData(line)
       
        return eventData
    
def usage():
    print __doc__

def main(argv):
    conn_str = "postgresql://user:password@gemsun01.ethz.ch/opengemdbpython"
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
    
    inputfile = "/home/apm/GEM1/hazard/earthquakeCatalogs/GSHAPEA/final-cata.txt"
    formatdefn = 1  #default: 1=GSHAPEA format
        
    try:
        opts, args = getopt.getopt(argv, "hg:d", ["help", "inputfile=", "formatdefn="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt == '-d':
            global _debug
            _debug = 1
        elif opt in ("-i", "--inputfile"):
            inputfile = arg
        elif opt in ("-f", "--formatdefn"):
            formatdefn = arg
    
    
    Session=sessionmaker(bind=engine)
    session=Session()
            
    #CREATE Earthquake Catalog in Earthquakecatalog file
    #FOR VER140 in gemsun01:
    
    catalogshortname='GSHAPEA5'
    catalogname='GSHAPEA Test Catalog 5'
    catalogpolygon="POLYGON((40 0,160 0,160 60, 40 60,40 0))"
    
    eqcat = EarthquakeCatalog(ecprivatetag=False, ecshortname=catalogshortname, ecname=catalogname,\
                              ecareapolygon=catalogpolygon, ecpgareapolygon=WKTSpatialElement(catalogpolygon))
    
    session.add(eqcat)
    session.commit()
    eqcatid = eqcat.ecid
    
    results=session.query(EarthquakeCatalog).all()
    
    for row in results:
        print row.ecname, session.scalar(row.ecpgareapolygon.wkt)
    
    results = session.query(EarthquakeCatalog).filter(EarthquakeCatalog.ecshortname=='GSHAPEA3')
    for row in results:
        print row.ecid, row.ecshortname, session.scalar(row.ecpgareapolygon.wkt)
    
    catecid = row.ecid
    
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
        event = Event(ecid=eqcatid,evtimestamp=eventData.eventtimestamp,evlat=eventData.eventlat,evlong=eventData.eventlon,\
                          evmagnitude=eventData.eventmagnitude,evdepth=eventData.eventdepth,evremarks=eventData.eventremarks,\
                          evpoint=eventData.eventpoint,evpgpoint=WKTSpatialElement(eventData.eventpoint))
        session.add(event)
        session.commit()

if __name__ == "__main__":
    main(sys.argv[1:])
