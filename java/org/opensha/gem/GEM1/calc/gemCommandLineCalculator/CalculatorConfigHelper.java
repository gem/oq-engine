package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import java.util.Properties;
import java.util.StringTokenizer;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class CalculatorConfigHelper {
	
	// There may be additional/customizable properties
	// -> does an enum type make sense? ...no.
	// ...and yes: For the programmer to know at least how to access the defaults.
	public enum defaultConfigItems {
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
		RESULT_TYPE,
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
		REGION,
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
		RUPTURE_FLOATING_TYPE
	}; // enum
	

	/**
	 * This helper method is necessary if the REGION property is saved like this:
	 * REGION = -78.0 0.0 -77.0 0.0 -77.0 1.0 -78.0 1.0
	 * -> pair number of doubles
	 * -> implicitly they are pairs of coordinates,
	 * -> odd indexes mean latitude
	 * -> pair indexes mean longitude
	 * @param calcConfig
	 * @return
	 */
	public static LocationList makeRegionboundary(Properties calcConfig) {
		String region = calcConfig.getProperty(defaultConfigItems.REGION.name());
		StringTokenizer st = new StringTokenizer(region);
        LocationList regionBoundary = new LocationList();
        Location tmpLoc = null;
        while(st.hasMoreTokens()) {
        	double lat = Double.parseDouble(st.nextToken());
        	if (st.hasMoreTokens()) {
        		// if there is an odd number of coordinates, the last one is ignored
	            double lon = Double.parseDouble(st.nextToken());
	            tmpLoc = new Location(lat, lon);
	            regionBoundary.add(tmpLoc);
            }
        } // while
        return regionBoundary;
	} // makeRegionBoundary()
	
	/**
	 * This method is the same like "makeArbitrarilyDiscretizedFunc()".
	 * This method just exists to be consistent with terminology.
	 * @param calcConfig
	 * @return
	 */
	public static ArbitrarilyDiscretizedFunc makeImlList(Properties calcConfig) {
		return makeArbitrarilyDiscretizedFunc(calcConfig);
	}

	/**
	 * The result or this method is also called "iml List" where "iml" means
	 * "intensity measure levels"
	 * @param calcConfig
	 * @return
	 */
	public static ArbitrarilyDiscretizedFunc makeArbitrarilyDiscretizedFunc(Properties calcConfig) { 
		// read intensity measure levels
		String imlProp = calcConfig.getProperty(defaultConfigItems.INTENSITY_MEASURE_LEVELS.name());
		StringTokenizer st = new StringTokenizer(imlProp);
		int numGMV = st.countTokens();
		ArbitrarilyDiscretizedFunc adf = new ArbitrarilyDiscretizedFunc();
		while(st.hasMoreTokens()) {
			adf.set(Math.log(Double.parseDouble(st.nextToken())), 1.0);
		}
		return adf;
	} // makeArbitrarilyDiscretizedFunc()

} // class
