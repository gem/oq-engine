'''
Created on Aug 12, 2010

@author: Aurea Moemke
'''
from datetime import datetime

class EventData:
    """This class takes event data information from an earthquake catalog in a 
    specific ascii text file format and parses out the event data (for later 
    write to the opengemdb)
    """
    
    def __init__(self):
        self.timestamp = None
        self.year = 0
        self.month = 0
        self.day = 0
        self.hour = 0
        self.mins = 0
        self.secs = 0
        self.nanosecs = 0
        self.lat = 0.0
        self.lon = 0.0
        self.depth = 0.0
        self.magnitude = 0.0
        self.remarks = ""
        self.errorcode = None
        self.point = None
        
    def parse_gshapea_event_data(self, line):
        if len(line[4:9].strip()) == 0:
            self.year = 0
        else:
            self.year = int(line[4:9].strip())
        
        if len(line[9:11].strip()) == 0:
            # Empty, thus set to January, i.e. 1
            self.month = 1 
            # Errorcode 1: no month set
            self.errorcode = 1 
        else:
            self.month = int(line[9:11].strip())
            
        if len(line[11:13].strip()) == 0:
            # Empty, thus set to 1
            self.day = 1
            # Errorcode 2: no day is set
            self.errorcode = 2 
        else:
            self.day = int(line[11:13].strip())
            if self.day == 0:
                self.day = 1
        
        if len(line[13:15].strip()) == 0:
            self.hour = 0
        else:
            self.hour = int(line[13:15].strip())
       
        if len(line[15:17].strip()) == 0:
            self.mins = 0
        else:
            self.mins = int(line[15:17].strip())
            
        if len(line[17:19].strip()) == 0:
            self.secs = 0
        else:
            self.secs = int(line[17:19].strip())
            
        if len(line[20:21].strip()) == 0:
            self.nanosecs = 0
        else:
            self.nanosecs = int(line[20:21].strip())
       
        # Catch errors in input, i.e. neg values in time fields, hr, min, sec
        if self.hour < 0:
            self.hour = self.hour * -1
        
        if self.mins < 0:
            self.mins = self.mins * -1
        
        if self.secs < 0:
            self.secs = self.secs * -1
        
        self.lon = float(line[27:34].strip())
        self.lat = float(line[21:27].strip())
        self.depth = float(line[39:43].strip())
        self.magnitude = float(line[49:53].strip())
        self.remarks = line[64:74].strip()
        
        self.point = "POINT(" + str(self.lon) + " " + str(self.lat) + ")"
        
        if self.year < 0 or self.month < 1 or self.month > 12 :
            if self.year < -4713:
                # Errorcode 3: year is out of range
                self.errorcode = 3 
            else:
                # Errorcode 4: year is negative
                self.errorcode = 4
        else:
            self.timestamp = datetime(self.year, self.month, self.day, 
                            self.hour, self.mins, self.secs, self.nanosecs)
            