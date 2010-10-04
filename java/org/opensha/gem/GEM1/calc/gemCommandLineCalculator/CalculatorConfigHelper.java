package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import java.util.Arrays;
import java.util.Iterator;
import java.util.List;
import java.util.StringTokenizer;

import org.apache.commons.configuration.Configuration;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class CalculatorConfigHelper {
	// for internal use only
	private final static String INTENSITY_MEASURE_CODE_PGA = "pga";
	private final static String INTENSITY_MEASURE_CODE_MMI = "mmi";
	// There may be additional/customizable properties
	// -> does an enum type make sense? ...no.
	// ...and yes: For the programmer to know at least how to access the defaults.
	public enum ConfigItems {
		ERF_LOGIC_TREE_FILE,
		GMPE_LOGIC_TREE_FILE,
		OUTPUT_DIR,
		PROBABILITY_OF_EXCEEDANCE,
		SUBDUCTION_FAULT_SURFACE_DISCRETIZATION,
		MAXIMUM_DISTANCE,
		SUBDUCTION_FAULT_MAGNITUDE_SCALING_RELATIONSHIP,
		SUBDUCTION_RUPTURE_FLOATING_TYPE,
		INTENSITY_MEASURE_TYPE,
		FAULT_MAGNITUDE_SCALING_SIGMA,
		INCLUDE_GRID_SOURCES,
		PERIOD,
		INCLUDE_SUBDUCTION_FAULT_SOURCE,
		WIDTH_OF_MFD_BIN,
		MINIMUM_MAGNITUDE,
		MEAN_GROUND_MOTION_MAP,
		SUBDUCTION_FAULT_MAGNITUDE_SCALING_SIGMA,
		DAMPING,
		NUMBER_OF_HAZARD_CURVE_CALCULATIONS,
		AREA_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP,
		INVESTIGATION_TIME,
		TREAT_GRID_SOURCE_AS,
		INCLUDE_AREA_SOURCES,
		FAULT_MAGNITUDE_SCALING_RELATIONSHIP,
		SUBDUCTION_RUPTURE_ASPECT_RATIO,
		TREAT_AREA_SOURCE_AS,
		REFERENCE_VS30_VALUE,
		REGION_VERTEX,
		REGION_GRID_SPACING,
		CALCULATION_MODE,
		FAULT_SURFACE_DISCRETIZATION,
		COMPONENT,
		RUPTURE_ASPECT_RATIO,
		NUMBER_OF_PROCESSORS,
		INTENSITY_MEASURE_LEVELS,
		TRUNCATION_LEVEL,
		GMPE_TRUNCATION_TYPE,
		AREA_SOURCE_DISCRETIZATION,
		GRID_SOURCE_MAGNITUDE_SCALING_RELATIONSHIP,
		STANDARD_DEVIATION_TYPE,
		INCLUDE_FAULT_SOURCE,
		SUBDUCTION_FAULT_RUPTURE_OFFSET,
		FAULT_RUPTURE_OFFSET,
		INDIVIDUAL_GROUND_MOTION_MAP,
		MEAN_HAZARD_CURVES,
		INDIVIDUAL_HAZARD_CURVES,
		RUPTURE_FLOATING_TYPE
	}; // enum
	

	/**
	 * This helper method is necessary if the REGION property is saved like this:
	 * REGION_VERTEX = -78.0, 0.0, -77.0, 0.0, -77.0, 1.0, -78.0, 1.0
	 * -> comma separated list of doubles according to documentation of 
	 *    Apache commons configuration.
	 * -> implicitly they are pairs of coordinates,
	 * -> odd indexes mean latitude
	 * -> pair indexes mean longitude
	 * @param calcConfig
	 * @return
	 */
	public static LocationList makeRegionboundary(Configuration config) {
		List<String> vertices = config.getList(ConfigItems.REGION_VERTEX.name());
        LocationList regionBoundary = new LocationList();
        Location tmpLoc = null;
        Iterator<String> iterator = vertices.iterator();
        while(iterator.hasNext()) {
        	double lat = Double.parseDouble(iterator.next());
        	if(iterator.hasNext()) {
        		// if there is an odd number of coordinates, the last one is ignored
	            double lon = Double.parseDouble(iterator.next());
	            tmpLoc = new Location(lat, lon);
	            regionBoundary.add(tmpLoc);
            }
        } // while
        return regionBoundary;
	} // makeRegionBoundary()

	/**
	 * This method retrieves the configuration items</br>
	 * 1) INTENSITY_MEASURE_TYPE</br>
	 * 2) INTENSITY_MEASURE_LEVELS</br>
	 * 
	 * Valid values for INTENSITY_MEASURE_TYPE are "PGA" and "MMI".</br>
	 * 
	 * The value of INTENSITY_MEASURE_LEVLES is a comma separated list of
	 * doubles or a multiple value property of doubles according to 
	 * documentation of the org.apache.commons.configuration package.
	 * 
	 * From the Configuration object passed by as a parameter.
	 * This method is the same like "makeArbitrarilyDiscretizedFunc()".
	 * This method just exists to be consistent with terminology, i.e.
	 * the programmer can use "makeImlList()" instead of "makeArbitrarilyDiscretizedFunc()"
	 * which may the code make more understandable (to scientists).
	 * @param calcConfig A Configuration object, usually loaded from a config
	 * file.
	 * @return An arbitrarily discretized function.
	 */
	public static ArbitrarilyDiscretizedFunc makeImlList(Configuration config) {
		String intensityMeasureType = config.getString(ConfigItems.INTENSITY_MEASURE_TYPE.name());
		String[] imlArray = config.getStringArray(ConfigItems.INTENSITY_MEASURE_LEVELS.name());
		Double[] imls = StringArrToDoubleArr(imlArray);
		return makeArbitrarilyDiscretizedFunc(imls, intensityMeasureType);
	} // makeImlList()

	/**
	 * More direct access. Allows a more explicit call for the PGA case.
	 * @param config A Configuration object, usually loaded from a config
	 * file.
	 * @return An arbitrarily discretized function.
	 */
	public static ArbitrarilyDiscretizedFunc makeImlListForPGA(Configuration config) {
		String[] imlArray = config.getStringArray(ConfigItems.INTENSITY_MEASURE_LEVELS.name());
		Double[] imls = StringArrToDoubleArr(imlArray);
		return makeArbitrarilyDiscretizedFunc(imls, INTENSITY_MEASURE_CODE_PGA);
	} // makeImlListForPGA()

	/**
	 * More direct access. Allows a more explicit call for the MMI case.
	 * @param config A Configuration object, usually loaded from a config
	 * file.
	 * @return An arbitrarily discretized function.
	 */
	public static ArbitrarilyDiscretizedFunc makeImlListForMMI(Configuration config) {
		String[] imlArray = config.getStringArray(ConfigItems.INTENSITY_MEASURE_LEVELS.name());
		Double[] imls = StringArrToDoubleArr(imlArray);
		return makeArbitrarilyDiscretizedFunc(imls, INTENSITY_MEASURE_CODE_MMI);
	} // makeImlListForMMI()

	private static ArbitrarilyDiscretizedFunc makeArbitrarilyDiscretizedFunc(Double[] intensityMeasureLevels, String intensityMeasureCode) { 
		ArbitrarilyDiscretizedFunc adf = new ArbitrarilyDiscretizedFunc();
		for(double iml : intensityMeasureLevels) {
			if(intensityMeasureCode.equalsIgnoreCase(INTENSITY_MEASURE_CODE_PGA)) {
			adf.set(Math.log(iml), 1.0);
			} else if(intensityMeasureCode.equalsIgnoreCase(INTENSITY_MEASURE_CODE_MMI)) {
				adf.set(iml, 1.0);
			} else {
				throw new IllegalArgumentException("Unknown intensity measure type : \"" 
				                                   + intensityMeasureCode + "\"");
			}
		} // for
		return adf;
	} // makeArbitrarilyDiscretizedFunc()
	
	private static Double[] StringArrToDoubleArr(String[] strings) {
		Double[] doubles = new Double[strings.length];
		int index = 0;
		for(String s : strings) {
			doubles[index] = Double.parseDouble(s);
		}
		return doubles;
	} // StringArrToDoubleArr()

} // class
