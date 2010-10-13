import fileinput

def defaultConfig() :
    d = {"MINIMUM_MAGNITUDE" : "5.0",
         "INVESTIGATION_TIME" : "50.0",
         "MAXIMUM_DISTANCE" : "200.0",
         "COMPONENT" : "Average Horizontal (GMRotI50)",
         "INTENSITY_MEASURE_TYPE" : "PGA",
         "PERIOD" : "0.0",
         "DAMPING" : "5.0",
         "INTENSITY_MEASURE_LEVELS" : "0.005 0.007 0.098 0.0137 0.0192 0.0269 0.0376 0.0527 0.0738 0.103 0.145 0.203 0.284 0.397 0.556 0.778 1.09 1.52 2.13",
         "GMPE_TRUNCATION_TYPE" : "2 Sided",
         "TRUNCATION_LEVEL" : "3",
         "STANDARD_DEVIATION_TYPE" : "Total",
         "REFERENCE_VS30_VALUE" : "760.0",
         "INCLUDE_AREA_SOURCES" : "yes",
         "TREAT_AREA_SOURCE_AS" : "Point Sources",
         "AREA_SOURCE_DISCRETIZATION" : "0.1",
         "AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP" : "W&C 1994 Mag-Length Rel.",
         "INCLUDE_GRID_SOURCES" : "yes",
         "TREAT_GRID_SOURCE_AS" : "Point Sources",
         "GRID_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP" : "W&C 1994 Mag-Length Rel.",
         "INCLUDE_FAULT_SOURCE" : "yes",
         "FAULT_RUPTURE_OFFSET" : "5.0",
         "FAULT_SURFACE_DISCRETIZATION" : "1.0",
         "FAULT_MAGNITUDE_SCALING_RELATIONSHIP" : "W&C 1994 Mag-Length Rel.",
         "FAULT_MAGNITUDE_SCALING_SIGMA" : "0.0",
         "RUPTURE_ASPECT_RATIO" : "1.5",
         "RUPTURE_FLOATING_TYPE" : "Along strike and down dip",
         "INCLUDE_SUBDUCTION_FAULT_SOURCE" : "yes",
         "SUBDUCTION_FAULT_RUPTURE_OFFSET" : "10.0",
         "SUBDUCTION_FAULT_SURFACE_DISCRETIZATION" : "10.0",
         "SUBDUCTION_FAULT_MAGNITUDE_SCALING_RELATIONSHIP" : "W&C 1994 Mag-Length Rel.",
         "SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA" : "0.0",
         "SUBDUCTION_RUPTURE_ASPECT_RATIO" : "1.5",
         "SUBDUCTION_RUPTURE_FLOATING_TYPE" : "Along strike and down dip",
         "WIDTH_OF_MFD_BIN" : "0.1",
         "NUMBER_OF_PROCESSORS" : "1",
         "RESULT_TYPE" : "Hazard map",
         "PROBABILITY_OF_EXCEEDANCE" : "0.1",
         "REGION": "-78.0 0.0 -77.0 0.0 -77.0 1.0 -78.0 1.0 1.0",
         "NUMBER_OF_HAZARD_CURVE_CALCULATIONS":"100"}
    return d
    
def defaultConfigReverseOrder() :
    d = {"REGION": "-78.0 0.0 -77.0 0.0 -77.0 1.0 -78.0 1.0 1.0",
         "NUMBER_OF_HAZARD_CURVE_CALCULATIONS":"100",
	 "PROBABILITY_OF_EXCEEDANCE" : "0.1",
	 "RESULT_TYPE" : "Hazard map",
	 "NUMBER_OF_PROCESSORS" : "1",
	 "WIDTH_OF_MFD_BIN" : "0.1",
	 "SUBDUCTION_RUPTURE_FLOATING_TYPE" : "Along strike and down dip",
	 "SUBDUCTION_RUPTURE_ASPECT_RATIO" : "1.5",
	 "SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA" : "0.0",
	 "SUBDUCTION_FAULT_MAGNITUDE_SCALING_RELATIONSHIP" : "W&C 1994 Mag-Length Rel.",
	 "SUBDUCTION_FAULT_SURFACE_DISCRETIZATION" : "10.0",
	 "SUBDUCTION_FAULT_RUPTURE_OFFSET" : "10.0",
	 "INCLUDE_SUBDUCTION_FAULT_SOURCE" : "yes",
	 "RUPTURE_FLOATING_TYPE" : "Along strike and down dip",
	 "RUPTURE_ASPECT_RATIO" : "1.5",
	 "FAULT_MAGNITUDE_SCALING_SIGMA" : "0.0",
	 "FAULT_MAGNITUDE_SCALING_RELATIONSHIP" : "W&C 1994 Mag-Length Rel.",
	 "FAULT_SURFACE_DISCRETIZATION" : "1.0",
	 "FAULT_RUPTURE_OFFSET" : "5.0",
	 "INCLUDE_FAULT_SOURCE" : "yes",
	 "GRID_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP" : "W&C 1994 Mag-Length Rel.",
	 "TREAT_GRID_SOURCE_AS" : "Point Sources",
	 "INCLUDE_GRID_SOURCES" : "yes",
	 "AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP" : "W&C 1994 Mag-Length Rel.",
	 "AREA_SOURCE_DISCRETIZATION" : "0.1",
	 "TREAT_AREA_SOURCE_AS" : "Point Sources",
	 "INCLUDE_AREA_SOURCES" : "yes",
	 "REFERENCE_VS30_VALUE" : "760.0",
	 "STANDARD_DEVIATION_TYPE" : "Total",
	 "TRUNCATION_LEVEL" : "3",
	 "GMPE_TRUNCATION_TYPE" : "2 Sided",
	 "INTENSITY_MEASURE_LEVELS" : "0.005 0.007 0.098 0.0137 0.0192 0.0269 0.0376 0.0527 0.0738 0.103 0.145 0.203 0.284 0.397 0.556 0.778 1.09 1.52 2.13",
	 "DAMPING" : "5.0",
	 "PERIOD" : "0.0",
	 "INTENSITY_MEASURE_TYPE" : "PGA",
	 "COMPONENT" : "Average Horizontal (GMRotI50)",
	 "MAXIMUM_DISTANCE" : "200.0",
	 "INVESTIGATION_TIME" : "50.0",
	 "MINIMUM_MAGNITUDE" : "5.0"}
    return d

def printLinesOfFile(path, begin=0, end=-1) :
    try :
	f = open(path)
	# if end - begin <= 0 just print the first line
	i = 0
	while i < begin : 
	    f.readline()
	    i = i + 1
	while i < end :
	    line = f.readline()
	    if line == '' : break
	    print(str(line).strip())
	    i = i + 1
    except IOError : pass
    finally : f.close()

def saveFile(configs, configFile) :
    for k, v in configs.iteritems():
        configFile.write(k + " = " + v + "\n")
    configFile.close()

def loadConfig(dictionary, configFile) :
    commentTokens = ( "#", "!", "//" )
    keys = dictionary.keys()
    try:
	configList = configFile.readlines()
	for configLine in configList :
	    strippedLine = configLine.strip()
	    if strippedLine.startswith(commentTokens) :
		continue
	    keyValuePair = configLine.split("=", 1)
	    if len(keyValuePair) == 2 :
	        key = keyValuePair[0].strip()
	        value = keyValuePair[1].strip()
		# set the key to the specified value
		# if the key exists, its value will be overwritten
		# if the key does not yet exist, it will be added
		dictionary[key] = value
	        # if key in keys :
		# print "xxr key \"" + key + "\" = \"" + dictionary[key]
	    else :
	    	print "xxr illegal keyValuePair = " + str(keyValuePair)
    except IOError :
        pass
    
def read_calculator_config(path):
    """Reads the file at the specified path.
    Stores the config parameters internally."""
    try:
        f = open(path)
        print "file mode: " + f.mode
        print "file name: " + f.name
	#
	d = defaultConfig()
	loadConfig(d, f);
	#
    except IOError:
        pass
    return path
    
if __name__ == "__main__":
    path = "/home/roland/CalculatorConfig_new.inp"

    # d = defaultConfig()
    # keys = d.keys()
    
    # this works:
    # newFile = open("/home/roland/CalculatorConfig_new.inp", "w")
    # saveFile(d, newFile)
    
    # this works:
    # for k in keys : print(k)
    
    # this also works:
    # for k in d : print d[k]
    
    # ... and this also works:
    # for k, v in d.iteritems():
    #     print k, v
    printLinesOfFile(path, 2, 5)
    # print "return value of method read_calculator_config(): " + read_calculator_config(path)

