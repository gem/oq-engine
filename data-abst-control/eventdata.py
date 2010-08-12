'''
Created on Aug 12, 2010

@author: apm
'''
from datetime import datetime

class EventData:
    
    def __init__(self):
        self.eventtimestamp = None
        self.eventyear = 0
        self.eventmonth = 0
        self.eventday = 0
        self.eventhour = 0
        self.eventmins = 0
        self.eventsecs = 0
        self.eventnanosecs = 0
        self.eventlat=0.0
        self.eventlon=0.0
        self.eventdepth=0.0
        self.eventmagnitude=0.0
        self.eventremarks=""
        self.eventerrorcode=None
        self.eventpoint=None
        print "Now inside init of EventData!!!"
        
    def parseEventData(self, line):
        if len(line[4:9].strip()) == 0: #empty string
            self.eventyear=0
        else:
            self.eventyear = int(line[4:9].strip()) #strip removes trailing space on both sides, rstrip on right, lstrip on left
        
        if len(line[9:11].strip())==0:
            self.eventmonth=1 #empty, thus set to January
            self.eventerrorcode = 1 # no month set
        else:
            self.eventmonth = int(line[9:11].strip())
            
        if len(line[11:13].strip())==0:
            self.eventday=1 #empty, thus set to 1
            self.eventerrorcode = 2 # no day
        else:
            self.eventday = int(line[11:13].strip())
            if self.eventday==0:
                self.eventday=1
        
        if len(line[13:15].strip())==0:
            self.eventhour=0
        else:
            self.eventhour = int(line[13:15].strip())
       
        if len(line[15:17].strip())==0:
            self.eventmins=0
        else:
            self.eventmins = int(line[15:17].strip())
            
        if len(line[17:19].strip())==0:
            self.eventsecs=0
        else:
            print "eventsecs", line[17:19].strip()
            self.eventsecs = int(line[17:19].strip())
            
        if len(line[20:21].strip())==0:
            self.eventnanosecs=0
        else:
            self.eventnanosecs = int(line[20:21].strip())
       
        # catch errors in input, i.e. -values in time fields, hr,min,sec
        if self.eventhour < 0:
            self.eventhour = self.eventhour * -1
        
        if self.eventmins < 0:
            self.eventmins = self.eventmins * -1
        
        if self.eventsecs < 0:
            self.eventsecs = self.eventsecs * -1
        
        self.eventlon = float(line[27:34].strip())
        self.eventlat = float(line[21:27].strip())
        self.eventdepth= float(line[39:43].strip())
        self.eventmagnitude= float(line[49:53].strip())
        self.eventremarks= line[64:74].strip()
        
        self.eventpoint="POINT("+str(self.eventlon)+" "+str(self.eventlat)+")"
        
        if self.eventyear < 0 or self.eventmonth <1 or self.eventmonth > 12 :
            if self.eventyear <-4713:
                self.eventerrorcode = 3 #out of range
            else:
                self.eventerrorcode = 4 #year is negative

        else:
            self.eventtimestamp = datetime(self.eventyear,self.eventmonth,self.eventday,self.eventhour,self.eventmins,self.eventsecs,self.eventnanosecs)
            