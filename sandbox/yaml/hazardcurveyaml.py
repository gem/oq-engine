import yaml
import math
hc = yaml.load(open('HC_input.yml'))

for lat in hc['Points'].keys():
  for long in hc['Points'][lat].keys():
	for idx, val in enumerate(hc['Points'][lat][long]):
   	  print "%s , %s" % (hc['Abcissa Values'][idx], val)
 


def point_within(pointlat, pointlong, offset):
  for lat in hc['Points'].keys():
    print math.fabs(pointlat - lat)
    if math.fabs(pointlat - lat) <= offset:
      for long in hc['Points'][lat].keys():
        print math.fabs(pointlong - long)
        if math.fabs(pointlong - long) <= offset:
          for idx, val in enumerate(hc['Points'][lat][long]):
            yield (hc['Abcissa Values'][idx], val)
	  
	
# tests
# point_within(41, 27, 1)