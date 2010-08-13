package org.opensha.sha.earthquake.rupForecastImpl.GEM1;

import java.util.ArrayList;
import java.util.HashMap;

import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.MagScalingRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.PEER_testsMagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagLengthRelationship;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.SourceType;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultSource;
import org.opensha.sha.earthquake.rupForecastImpl.PointEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.PointToLineSource;
import org.opensha.sha.earthquake.rupForecastImpl.PoissonAreaSource;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.faultSurface.ApproxEvenlyGriddedSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <p>Title: GEM1ERF </p>
 *
 *@TODO
	1) test and verify all the options contained herein
	2) fix problem that lowerSeisDepth for point sources can be inconsistent with given aveRupTomDepthVersusMag.
	   For example, if both shallow and very deep sources exist, then rupture-length estimates are bogus if computed 
	   from a mag-area relationship (e.g., if lowerSeisDepth = 14km and aveRuptTopDepthVersusMag = 115 km, as happens
	   for the S. American ERF)
	3) mk calcSettings contain only GEM1ERF values (not all GEM1 calc values)
	4) move all dependencies (parsers and data files) into subdirs here (and streamline thing if possible)
	5) move each adjustable parameter to a separate class (as is done for IMRs); this will clean things a lot
	6) Add spinning, dipping faults for point-sources option. 
	7) Review all documentation and add more (including to glossary?)

 * @author : Edward Field
 * @Date : 
 * @version 1.0
 */

public class GEM1ERF extends EqkRupForecast {

	// name of this ERF
	public final static String NAME = new String("GEM1 Eqk Rup Forecast");

	//for Debug purposes
	private static String  C = new String("GEM1ERF");
	private boolean D = false;
	
	protected ArrayList<GEMSourceData> gemSourceDataList;
	
	protected ArrayList<GEMSourceData> areaSourceDataList;
	protected ArrayList<GEMSourceData> griddedSeisSourceDataList;
	protected ArrayList<GEMSourceData> faultSourceDataList;
	protected ArrayList<GEMSourceData> subductionSourceDataList;
	
	// some fixed parameters
	final static double MINMAG = 0;   // this sets the minimum mag considered in the forecast (overriding that implied in the source data)
	
	// calculation settings (primitive versions of the adj parameters)
	// for area sources
	String areaSrcRupTypeValue;
	double areaSrcLowerSeisDepthValue;
	double areaSrcDiscrValue;
	MagScalingRelationship areaSrcMagScalingRel;
	// for gridded seis sources
	String griddedSeisRupTypeValue;
	double griddedSeisLowerSeisDepthValue;
	MagScalingRelationship griddedSeisMagScalingRel;
	// for fault sources
	double faultRupOffsetValue;
	double faultDiscrValue;
	MagScalingRelationship faultMagScalingRel;
	double faultScalingSigmaValue;
	double faultRupAspectRatioValue;
	int faultFloaterTypeValue;
	// for subduction fault
	double subductionRupOffsetValue;
	double subductionDiscrValue;
	MagScalingRelationship subductionMagScalingRel;
	double subductionScalingSigmaValue;
	double subductionRupAspectRatioValue;
	int subductionFloaterTypeValue;
	// from the timeSpan
	double duration;		


	// THE REST IS FOR ALL THE ADJUSTABLE PARAMERS:
	
	//-------------------------------------------------------------------------------- AREA SOURCES
	
	// Whether or not to include these sources
	public final static String INCLUDE_AREA_SRC_PARAM_NAME = "Include Area Sources?";
	public final static String INCLUDE_SRC_PARAM_INFO = "These sources will be excluded if this is unchecked";
	public final static Boolean INCLUDE_SRC_PARAM_DEFAULT = true;
	private BooleanParameter includeAreaSourceParam;

	// Treat background seismogenic as point of finite ruptures parameter
	public final static String AREA_SRC_RUP_TYPE_NAME = new String ("Treat Area Sources As");
	public final static String AREA_SRC_RUP_TYPE_POINT = new String ("Point Sources");
	public final static String AREA_SRC_RUP_TYPE_LINE = new String ("Line Sources (random or given strike)");
	public final static String AREA_SRC_RUP_TYPE_CROSS_HAIR = new String ("Cross Hair Line Sources");
	public final static String AREA_SRC_RUP_TYPE_SPOKED = new String ("16 Spoked Line Sources");
	public final static String AREA_SRC_RUP_TYPE_FINITE_SURF = new String ("Finite Dipping Sources");
	StringParameter areaSrcRupTypeParam;

	// Default lower seismogenic depth of area sources
	public final static String AREA_SRC_LOWER_SEIS_DEPTH_PARAM_NAME = "Area Source Lower Seis Depth";
	public final static Double AREA_SRC_LOWER_SEIS_DEPTH_PARAM_MIN = new Double(5.0);
	public final static Double AREA_SRC_LOWER_SEIS_DEPTH_PARAM_MAX = new Double(50);
	public final static Double AREA_SRC_LOWER_SEIS_DEPTH_PARAM_DEFAULT = new Double(14);
	public final static String AREA_SRC_LOWER_SEIS_DEPTH_PARAM_UNITS = "km";
	private final static String AREA_SRC_LOWER_SEIS_DEPTH_PARAM_INFO = "The default lower-seimogenic " +
			"depth for area sources";
	private DoubleParameter areaSrcLowerSeisDepthParam;

	// For area discretization
	public final static String AREA_SRC_DISCR_PARAM_NAME ="Area Source Discretization";
	private final static Double AREA_SRC_DISCR_PARAM_DEFAULT = new Double(0.1);
	private final static String AREA_SRC_DISCR_PARAM_UNITS = "deg";
	private final static String AREA_SRC_DISCR_PARAM_INFO = "The discretization of area sources";
	public final static double AREA_SRC_DISCR_PARAM_MIN = new Double(0.01);
	public final static double AREA_SRC_DISCR_PARAM_MAX = new Double(1.0);
	DoubleParameter areaSrcDiscrParam;
	
	// Mag-scaling relationship for turning grip points into finite ruptures
	public final static String AREA_SRC_MAG_SCALING_REL_PARAM_NAME = "Area Source Mag-Scaling";
	private final static String AREA_SRC_MAG_SCALING_REL_PARAM_INFO = " Mag-scaling relationship " +
			"for computing size of area source events";
	StringParameter areaSrcMagScalingRelParam;

	//--------------------------------------------------------------------------- GRIDDED SEISMCITY

	// Whether or not to include these sources
	public final static String INCLUDE_GRIDDED_SEIS_PARAM_NAME = "Include Gridded Seis Sources?";
	private BooleanParameter includeGriddedSeisParam;

	// Treat background seis as point of finite ruptures parameter
	public final static String GRIDDED_SEIS_RUP_TYPE_NAME = new String ("Treat Gridded Seis As");
	public final static String GRIDDED_SEIS_RUP_TYPE_POINT = new String ("Point Sources");
	public final static String GRIDDED_SEIS_RUP_TYPE_LINE = new String ("Line Sources (random or given strike)");
	public final static String GRIDDED_SEIS_RUP_TYPE_CROSS_HAIR = new String ("Cross Hair Line Sources");
	public final static String GRIDDED_SEIS_RUP_TYPE_SPOKED = new String ("16 Spoked Line Sources");
	public final static String GRIDDED_SEIS_RUP_TYPE_FINITE_SURF = new String ("Finite Dipping Sources");
	StringParameter griddedSeisRupTypeParam;

	// default lower seis depth of gridded/background source
	public final static String GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_NAME = "Gridded Seis Lower Seis Depth";
	public final static Double GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_MIN = new Double(5.0);
	public final static Double GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_MAX = new Double(50);
	public final static Double GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_DEFAULT = new Double(14);
	public final static String GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_UNITS = "km";
	private final static String GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_INFO = "The default lower-seimogenic depth for gridded seismicity=";
	private DoubleParameter griddedSeisLowerSeisDepthParam;

	// Mag-scaling relationship for turning grip points into finite ruptures
	public final static String GRIDDED_SEIS_MAG_SCALING_REL_PARAM_NAME = "Gridded Seis Mag-Scaling";
	private final static String GRIDDED_SEIS_MAG_SCALING_REL_PARAM_INFO = " Mag-scaling relationship for computing size of background events";
	StringParameter griddedSeisMagScalingRelParam;

	//------------------------------------------------------------------------------- FAULT SOURCES

	// Whether or not to include these sources
	public final static String INCLUDE_FAULT_SOURCES_PARAM_NAME = "Include Fault Sources?";
	private BooleanParameter includeFaultSourcesParam;

	// For rupture offset length along fault parameter
	public final static String FAULT_RUP_OFFSET_PARAM_NAME ="Fault Rupture Offset";
	private final static Double RUP_OFFSET_DEFAULT = new Double(5);
	private final static String FAULT_RUP_OFFSET_PARAM_UNITS = "km";
	private final static String FAULT_RUP_OFFSET_PARAM_INFO = "The amount floating ruptures are offset along the fault";
	public final static double FAULT_RUP_OFFSET_PARAM_MIN = 1;
	public final static double FAULT_RUP_OFFSET_PARAM_MAX = 100;
	DoubleParameter faultRupOffsetParam;

	// For fault discretization
	public final static String FAULT_DISCR_PARAM_NAME ="Fault Discretization";
	private final static Double FAULT_DISCR_PARAM_DEFAULT = new Double(1.0);
	private final static String FAULT_DISCR_PARAM_UNITS = "km";
	private final static String FAULT_DISCR_PARAM_INFO = "The discretization of faults";
	public final static double FAULT_DISCR_PARAM_MIN = 1;
	public final static double FAULT_DISCR_PARAM_MAX = 10;
	DoubleParameter faultDiscrParam;

	// Mag-scaling relationship parameter stuff
	public final static String FAULT_MAG_SCALING_REL_PARAM_NAME = "Fault Rupture Scaling";
	private final static String FAULT_MAG_SCALING_REL_PARAM_INFO = " Mag-scaling relationship for computing size of floaters";
	StringParameter faultMagScalingRelParam;

	// Mag-scaling sigma parameter stuff
	public final static String FAULT_SCALING_SIGMA_PARAM_NAME =  "Fault Scaling Sigma";
	private final static String FAULT_SCALING_SIGMA_PARAM_INFO =  "The standard deviation of the Area(mag) or Length(M) relationship";
	private Double FAULT_SCALING_SIGMA_PARAM_MIN = new Double(0);
	private Double FAULT_SCALING_SIGMA_PARAM_MAX = new Double(1);
	private Double FAULT_SCALING_SIGMA_PARAM_DEFAULT = new Double(0.0);
	DoubleParameter faultScalingSigmaParam;

	// rupture aspect ratio parameter stuff
	public final static String FAULT_RUP_ASPECT_RATIO_PARAM_NAME = "Fault Rupture Aspect Ratio";
	private final static String FAULT_RUP_ASPECT_RATIO_PARAM_INFO = "The ratio of rupture length to rupture width for floaters";
	private Double FAULT_RUP_ASPECT_RATIO_PARAM_MIN = new Double(Double.MIN_VALUE);
	private Double FAULT_RUP_ASPECT_RATIO_PARAM_MAX = new Double(Double.MAX_VALUE);
	private Double FAULT_RUP_ASPECT_RATIO_PARAM_DEFAULT = new Double(1.0);
	DoubleParameter faultRupAspectRatioParam;

	// Floater Type
	public final static String FAULT_FLOATER_TYPE_PARAM_NAME = "Floater Type";
	public final static String FAULT_FLOATER_TYPE_PARAM_INFO = "Specifies how to float ruptures around the faults";
	public final static String FLOATER_TYPE_FULL_DDW = "Only along strike ( rupture full DDW)";
	public final static String FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP = "Along strike and down dip";
	public final static String FLOATER_TYPE_CENTERED_DOWNDIP = "Along strike & centered down dip";
	public final static String FAULT_FLOATER_TYPE_PARAM_DEFAULT = FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP;
	StringParameter faultFloaterTypeParam;
	
	//------------------------------------------------------------------------------- SUBDUCTION FAULT SOURCES

	// Whether or not to include these sources
	public final static String INCLUDE_SUBDUCTION_SOURCES_PARAM_NAME = "Include Subduction-Zone Sources?";
	private BooleanParameter includeSubductionSourcesParam;

	// For rupture offset length along fault parameter
	public final static String SUB_RUP_OFFSET_PARAM_NAME ="Subduction Zone Rupture Offset";
	private final static Double SUB_RUP_OFFSET_DEFAULT = new Double(10);
	private final static String SUB_RUP_OFFSET_PARAM_UNITS = "km";
	private final static String SUB_RUP_OFFSET_PARAM_INFO = "The amount floating ruptures are offset along the subduction zones";
	public final static double SUB_RUP_OFFSET_PARAM_MIN = 1;
	public final static double SUB_RUP_OFFSET_PARAM_MAX = 100;
	DoubleParameter subductionRupOffsetParam;

	// For fault discretization
	public final static String SUB_DISCR_PARAM_NAME ="Subduction Fault Discretization";
	private final static Double SUB_DISCR_PARAM_DEFAULT = new Double(10);
	private final static String SUB_DISCR_PARAM_UNITS = "km";
	private final static String SUB_DISCR_PARAM_INFO = "The discretization of subduction zones";
	public final static double SUB_DISCR_PARAM_MIN = 1;
	public final static double SUB_DISCR_PARAM_MAX = 100;
	DoubleParameter subductionDiscrParam;

	// Mag-scaling relationship parameter stuff
	public final static String SUB_MAG_SCALING_REL_PARAM_NAME = "Subduction-Zone Rupture Scaling";
	private final static String SUB_MAG_SCALING_REL_PARAM_INFO = " Mag-scaling relationship for computing size of floaters";
	StringParameter subductionMagScalingRelParam;

	// Mag-scaling sigma parameter stuff
	public final static String SUB_SCALING_SIGMA_PARAM_NAME =  "Subduction Zone Scaling Sigma";
	private final static String SUB_SCALING_SIGMA_PARAM_INFO =  "The standard deviation of the Area(mag) or Length(M) relationship";
	private Double SUB_SCALING_SIGMA_PARAM_MIN = new Double(0);
	private Double SUB_SCALING_SIGMA_PARAM_MAX = new Double(1);
	private Double SUB_SCALING_SIGMA_PARAM_DEFAULT = new Double(0.0);
	DoubleParameter subductionScalingSigmaParam;

	// rupture aspect ratio parameter stuff
	public final static String SUB_RUP_ASPECT_RATIO_PARAM_NAME = "Subduction Fault Rupture Aspect Ratio";
	private final static String SUB_RUP_ASPECT_RATIO_PARAM_INFO = "The ratio of rupture length to rupture width";
	private Double SUB_RUP_ASPECT_RATIO_PARAM_MIN = new Double(Double.MIN_VALUE);
	private Double SUB_RUP_ASPECT_RATIO_PARAM_MAX = new Double(Double.MAX_VALUE);
	private Double SUB_RUP_ASPECT_RATIO_PARAM_DEFAULT = new Double(1.0);
	DoubleParameter subductionRupAspectRatioParam;

	// Floater Type
	public final static String SUB_FLOATER_TYPE_PARAM_NAME = "Subduction Fault Floater Type";
	public final static String SUB_FLOATER_TYPE_PARAM_INFO = "Specifies how to float ruptures around subduction zones";
	public final static String SUB_FLOATER_TYPE_FULL_DDW = "Only along strike ( rupture full DDW)";
	public final static String SUB_FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP = "Along strike and down dip";
	public final static String SUB_FLOATER_TYPE_CENTERED_DOWNDIP = "Along strike & centered down dip";
	public final static String SUB_FLOATER_TYPE_PARAM_DEFAULT = FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP;
	StringParameter subductionFloaterTypeParam;
	
	
	public final static String SOURCE_CACHE_PARAM_NAME = "Cache Sources";
	public final static String SOURCE_CACHE_PARAM_INFO = "Enables caching of sources for faster repeated computations" +
			" of nearby sites, but requires more memory";
	public final static Boolean SOURCE_CACHE_PARAM_DEFAULT = false;
	private BooleanParameter sourceCacheParam;
	
	private HashMap<Integer, ProbEqkSource> sourceCache = null;
	
	private ArrayList<TectonicRegionType> tectonicRegionTypes;


	/**
	 * No arg constructor.
	 */
	public GEM1ERF() {}


	/**
	 * Constructor that takes lists of each source type.  Set any list as null if there are no associated data types.
	 */
	public GEM1ERF(ArrayList<GEMSourceData> areaSourceDataList,ArrayList<GEMSourceData> griddedSeisSourceDataList,
			ArrayList<GEMSourceData> faultSourceDataList,ArrayList<GEMSourceData> subductionSourceDataList) {
		
		this(areaSourceDataList, griddedSeisSourceDataList, faultSourceDataList, subductionSourceDataList,null);
	}

	/**
	 * Constructor that takes lists of each source type and a CalculationSettings object.  
	 * Set any list as null if there are no associated data types.
	 */
	public GEM1ERF(ArrayList<GEMSourceData> areaSourceDataList,ArrayList<GEMSourceData> griddedSeisSourceDataList,
			ArrayList<GEMSourceData> faultSourceDataList,ArrayList<GEMSourceData> subductionSourceDataList, CalculationSettings calcSet) {
		
		this.areaSourceDataList = areaSourceDataList;
		this.griddedSeisSourceDataList = griddedSeisSourceDataList;
		this.faultSourceDataList = faultSourceDataList;
		this.subductionSourceDataList = subductionSourceDataList;
		
		initialize(calcSet);

	}
	
	/**
	 * This takes a allGemSourceDataList (and parses the list into separate lists for each source type).
	 */
	public GEM1ERF(ArrayList<GEMSourceData> allGemSourceDataList) {
		this(allGemSourceDataList,null);
	}



	/**
	 * This takes a allGemSourceDataList (which get parsed into separate lists) and a CalculationSettings object.
	 */
	public GEM1ERF(ArrayList<GEMSourceData> allGemSourceDataList, CalculationSettings calcSet) {
		parseSourceListIntoDifferentTypes(allGemSourceDataList);
		initialize(calcSet);
	}
	
	protected void parseSourceListIntoDifferentTypes(ArrayList<GEMSourceData> allGemSourceDataList) {

		areaSourceDataList = new ArrayList<GEMSourceData> ();
		griddedSeisSourceDataList = new ArrayList<GEMSourceData> ();
		faultSourceDataList = new ArrayList<GEMSourceData> ();
		subductionSourceDataList = new ArrayList<GEMSourceData> ();
		for(int i=0;i<allGemSourceDataList.size();i++) {
			GEMSourceData srcData = allGemSourceDataList.get(i);
			if(srcData instanceof GEMFaultSourceData)
				faultSourceDataList.add(srcData);
			else if (srcData instanceof GEMSubductionFaultSourceData)
				subductionSourceDataList.add(srcData);
			else if (srcData instanceof GEMPointSourceData)
				griddedSeisSourceDataList.add(srcData);
			else if (srcData instanceof GEMAreaSourceData)
				areaSourceDataList.add(srcData);
			else
				throw new RuntimeException(NAME+": "+srcData.getClass()+" not yet supported");
		}
		
		// make any that are empty null
		if (areaSourceDataList.size() == 0) areaSourceDataList = null;
		if (griddedSeisSourceDataList.size() == 0) griddedSeisSourceDataList = null;
		if (faultSourceDataList.size() == 0) faultSourceDataList = null;
		if (subductionSourceDataList.size() == 0) subductionSourceDataList = null;
	}
	
	
	/**
	 * This initializes the ERF & sets parameters from calcSet (if calcSet != null)
	 * @param calcSet
	 */
	protected void initialize(CalculationSettings calcSet) {

		// create the timespan object with start time and duration in years
		timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
		timeSpan.addParameterChangeListener(this);
		timeSpan.setDuration(50);

		// create and add adj params to list
		initAdjParams();
		
		// set params from calcSet if it's not null
		if(calcSet != null) setParamsFromCalcSettings(calcSet);
		
		// Create adjustable parameter list
		createParamList();

		// Determine which tectonic region types are included
		int numActiveShallow=0;
		int numStableShallow=0;
		int numSubSlab=0;
		int numSubInterface=0;
		ArrayList<GEMSourceData> tempAllData = new ArrayList<GEMSourceData>();
		if(areaSourceDataList != null) tempAllData.addAll(areaSourceDataList);
		if(griddedSeisSourceDataList != null) tempAllData.addAll(griddedSeisSourceDataList);
		if(faultSourceDataList != null) tempAllData.addAll(faultSourceDataList);
		if(subductionSourceDataList != null) tempAllData.addAll(subductionSourceDataList);
		for(int i=0;i<tempAllData.size();i++) {
			TectonicRegionType tectReg = tempAllData.get(i).getTectReg();
			if (tectReg == TectonicRegionType.ACTIVE_SHALLOW) 
				numActiveShallow += 1;
			else if (tectReg == TectonicRegionType.STABLE_SHALLOW) 
				numStableShallow += 1;
			else if (tectReg == TectonicRegionType.SUBDUCTION_SLAB) 
				numSubSlab += 1;
			else if (tectReg == TectonicRegionType.SUBDUCTION_INTERFACE) 
				numSubInterface += 1;
			else throw new RuntimeException("tectonic region type not supported");
		}
		tectonicRegionTypes = new ArrayList<TectonicRegionType>();
		if(numActiveShallow>0) tectonicRegionTypes.add(TectonicRegionType.ACTIVE_SHALLOW);
		if(numStableShallow>0) tectonicRegionTypes.add(TectonicRegionType.STABLE_SHALLOW);
		if(numSubSlab>0) tectonicRegionTypes.add(TectonicRegionType.SUBDUCTION_SLAB);
		if(numSubInterface>0) tectonicRegionTypes.add(TectonicRegionType.SUBDUCTION_INTERFACE);
		if(D) {
			System.out.println("numActiveShallow="+numActiveShallow);
			System.out.println("numStableShallow="+numStableShallow);
			System.out.println("numSubSlab="+numSubSlab);
			System.out.println("numSubInterface="+numSubInterface);
		}
	}
	
	
	// Make the adjustable parameters & the list
	private void initAdjParams() {

		// ---------------------------------------------------------------------------- AREA SOURCES
		
		includeAreaSourceParam = new BooleanParameter(INCLUDE_AREA_SRC_PARAM_NAME,INCLUDE_SRC_PARAM_DEFAULT);
		includeAreaSourceParam.setInfo(INCLUDE_SRC_PARAM_INFO);

		// Create the fault option parameter for area sources
		ArrayList<String> areaSeisRupOptionsStrings = new ArrayList<String>();
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_TYPE_POINT);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_TYPE_LINE);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_TYPE_CROSS_HAIR);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_TYPE_SPOKED);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_TYPE_FINITE_SURF);
		areaSrcRupTypeParam = new StringParameter(AREA_SRC_RUP_TYPE_NAME,areaSeisRupOptionsStrings,
				AREA_SRC_RUP_TYPE_POINT);
		
		// Area lower seismogenic depth parameter
		areaSrcLowerSeisDepthParam = new DoubleParameter(AREA_SRC_LOWER_SEIS_DEPTH_PARAM_NAME,
				AREA_SRC_LOWER_SEIS_DEPTH_PARAM_MIN,
				AREA_SRC_LOWER_SEIS_DEPTH_PARAM_MAX,
				AREA_SRC_LOWER_SEIS_DEPTH_PARAM_UNITS,
				AREA_SRC_LOWER_SEIS_DEPTH_PARAM_DEFAULT);
		areaSrcLowerSeisDepthParam.setInfo(GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_INFO);

		// Area discretization parameter
		areaSrcDiscrParam = new DoubleParameter(AREA_SRC_DISCR_PARAM_NAME,AREA_SRC_DISCR_PARAM_MIN,
				AREA_SRC_DISCR_PARAM_MAX,AREA_SRC_DISCR_PARAM_UNITS,AREA_SRC_DISCR_PARAM_DEFAULT);
		areaSrcDiscrParam.setInfo(AREA_SRC_DISCR_PARAM_INFO);
		
		// Create the mag-scaling relationship param for area sources
		ArrayList<String> magScalingRelAreaOptions = new ArrayList<String>();
		magScalingRelAreaOptions.add(WC1994_MagAreaRelationship.NAME);
		magScalingRelAreaOptions.add(WC1994_MagLengthRelationship.NAME);
		magScalingRelAreaOptions.add(PEER_testsMagAreaRelationship.NAME);
		areaSrcMagScalingRelParam = new StringParameter(AREA_SRC_MAG_SCALING_REL_PARAM_NAME,magScalingRelAreaOptions,
				WC1994_MagLengthRelationship.NAME);
		areaSrcMagScalingRelParam.setInfo(AREA_SRC_MAG_SCALING_REL_PARAM_INFO);
		
		// ---------------------------------------------------------------------------- GRID SOURCES
		
		includeGriddedSeisParam = new BooleanParameter(INCLUDE_GRIDDED_SEIS_PARAM_NAME,INCLUDE_SRC_PARAM_DEFAULT);
		includeGriddedSeisParam.setInfo(INCLUDE_SRC_PARAM_INFO);

		// Rup type options
		ArrayList<String> backSeisRupOptionsStrings = new ArrayList<String>();
		backSeisRupOptionsStrings.add(GRIDDED_SEIS_RUP_TYPE_POINT);
		backSeisRupOptionsStrings.add(GRIDDED_SEIS_RUP_TYPE_LINE);
		backSeisRupOptionsStrings.add(GRIDDED_SEIS_RUP_TYPE_CROSS_HAIR);
		backSeisRupOptionsStrings.add(GRIDDED_SEIS_RUP_TYPE_SPOKED);
		backSeisRupOptionsStrings.add(GRIDDED_SEIS_RUP_TYPE_FINITE_SURF);
		griddedSeisRupTypeParam = new StringParameter(GRIDDED_SEIS_RUP_TYPE_NAME, backSeisRupOptionsStrings,GRIDDED_SEIS_RUP_TYPE_POINT);

		griddedSeisLowerSeisDepthParam = new DoubleParameter(GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_NAME,GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_MIN,
				GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_MAX,GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_UNITS,GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_DEFAULT);
		griddedSeisLowerSeisDepthParam.setInfo(GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_INFO);
		
		// Create the mag-scaling relationship param for griddes seismicity
		ArrayList<String> magScalingRelBackgrOptions = new ArrayList<String>();
		magScalingRelBackgrOptions.add(WC1994_MagAreaRelationship.NAME);
		magScalingRelBackgrOptions.add(WC1994_MagLengthRelationship.NAME);
		magScalingRelBackgrOptions.add(PEER_testsMagAreaRelationship.NAME);
		griddedSeisMagScalingRelParam = new StringParameter(GRIDDED_SEIS_MAG_SCALING_REL_PARAM_NAME,magScalingRelBackgrOptions,
				WC1994_MagLengthRelationship.NAME);
		griddedSeisMagScalingRelParam.setInfo(GRIDDED_SEIS_MAG_SCALING_REL_PARAM_INFO);

		
		// --------------------------------------------------------------------------- FAULT SOURCES
		
		includeFaultSourcesParam = new BooleanParameter(INCLUDE_FAULT_SOURCES_PARAM_NAME,INCLUDE_SRC_PARAM_DEFAULT);
		includeFaultSourcesParam.setInfo(INCLUDE_SRC_PARAM_INFO);

		// Rupture offset
		faultRupOffsetParam = new DoubleParameter(FAULT_RUP_OFFSET_PARAM_NAME,FAULT_RUP_OFFSET_PARAM_MIN,
				FAULT_RUP_OFFSET_PARAM_MAX,FAULT_RUP_OFFSET_PARAM_UNITS,RUP_OFFSET_DEFAULT);
		faultRupOffsetParam.setInfo(FAULT_RUP_OFFSET_PARAM_INFO);

		// Fault discretization parameter
		faultDiscrParam = new DoubleParameter(FAULT_DISCR_PARAM_NAME,FAULT_DISCR_PARAM_MIN,
				FAULT_DISCR_PARAM_MAX,FAULT_DISCR_PARAM_UNITS,FAULT_DISCR_PARAM_DEFAULT);
		faultDiscrParam.setInfo(FAULT_DISCR_PARAM_INFO);

		// create the mag-scaling relationship param
		ArrayList<String> magScalingRelOptions = new ArrayList<String>();
		magScalingRelOptions.add(WC1994_MagAreaRelationship.NAME);
		magScalingRelOptions.add(WC1994_MagLengthRelationship.NAME);
		magScalingRelOptions.add(PEER_testsMagAreaRelationship.NAME);
		faultMagScalingRelParam = new StringParameter(FAULT_MAG_SCALING_REL_PARAM_NAME,magScalingRelOptions,
				WC1994_MagLengthRelationship.NAME);
		faultMagScalingRelParam.setInfo(FAULT_MAG_SCALING_REL_PARAM_INFO);

		// create the mag-scaling sigma param
		faultScalingSigmaParam = new DoubleParameter(FAULT_SCALING_SIGMA_PARAM_NAME,
				FAULT_SCALING_SIGMA_PARAM_MIN, FAULT_SCALING_SIGMA_PARAM_MAX, FAULT_SCALING_SIGMA_PARAM_DEFAULT);
		faultScalingSigmaParam.setInfo(FAULT_SCALING_SIGMA_PARAM_INFO);

		// create the aspect ratio param
		faultRupAspectRatioParam = new DoubleParameter(FAULT_RUP_ASPECT_RATIO_PARAM_NAME,FAULT_RUP_ASPECT_RATIO_PARAM_MIN,
				FAULT_RUP_ASPECT_RATIO_PARAM_MAX,FAULT_RUP_ASPECT_RATIO_PARAM_DEFAULT);
		faultRupAspectRatioParam.setInfo(FAULT_RUP_ASPECT_RATIO_PARAM_INFO);

		ArrayList<String> floaterTypeOptions = new ArrayList<String>();
		floaterTypeOptions.add(FLOATER_TYPE_FULL_DDW);
		floaterTypeOptions.add(FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP);
		floaterTypeOptions.add(FLOATER_TYPE_CENTERED_DOWNDIP);
		faultFloaterTypeParam = new StringParameter(FAULT_FLOATER_TYPE_PARAM_NAME,floaterTypeOptions,
				FAULT_FLOATER_TYPE_PARAM_DEFAULT);
		faultFloaterTypeParam.setInfo(FAULT_FLOATER_TYPE_PARAM_INFO);
		
		// --------------------------------------------------------------------------- SUBDUCTION FAULT SOURCES
		
		includeSubductionSourcesParam = new BooleanParameter(INCLUDE_SUBDUCTION_SOURCES_PARAM_NAME,INCLUDE_SRC_PARAM_DEFAULT);
		includeSubductionSourcesParam.setInfo(INCLUDE_SRC_PARAM_INFO);

		// Rupture offset
		subductionRupOffsetParam = new DoubleParameter(SUB_RUP_OFFSET_PARAM_NAME,SUB_RUP_OFFSET_PARAM_MIN,
				SUB_RUP_OFFSET_PARAM_MAX,SUB_RUP_OFFSET_PARAM_UNITS,SUB_RUP_OFFSET_DEFAULT);
		subductionRupOffsetParam.setInfo(SUB_RUP_OFFSET_PARAM_INFO);

		// Fault discretization parameter
		subductionDiscrParam = new DoubleParameter(SUB_DISCR_PARAM_NAME,SUB_DISCR_PARAM_MIN,
				SUB_DISCR_PARAM_MAX,SUB_DISCR_PARAM_UNITS,SUB_DISCR_PARAM_DEFAULT);
		subductionDiscrParam.setInfo(SUB_DISCR_PARAM_INFO);

		// create the mag-scaling relationship param
		ArrayList<String> sub_magScalingRelOptions = new ArrayList<String>();
		sub_magScalingRelOptions.add(WC1994_MagAreaRelationship.NAME);
		sub_magScalingRelOptions.add(WC1994_MagLengthRelationship.NAME);
		sub_magScalingRelOptions.add(PEER_testsMagAreaRelationship.NAME);
		subductionMagScalingRelParam = new StringParameter(SUB_MAG_SCALING_REL_PARAM_NAME,sub_magScalingRelOptions,
				WC1994_MagAreaRelationship.NAME);
		subductionMagScalingRelParam.setInfo(SUB_MAG_SCALING_REL_PARAM_INFO);

		// create the mag-scaling sigma param
		subductionScalingSigmaParam = new DoubleParameter(SUB_SCALING_SIGMA_PARAM_NAME,
				SUB_SCALING_SIGMA_PARAM_MIN, SUB_SCALING_SIGMA_PARAM_MAX, SUB_SCALING_SIGMA_PARAM_DEFAULT);
		subductionScalingSigmaParam.setInfo(SUB_SCALING_SIGMA_PARAM_INFO);

		// create the aspect ratio param
		subductionRupAspectRatioParam = new DoubleParameter(SUB_RUP_ASPECT_RATIO_PARAM_NAME,SUB_RUP_ASPECT_RATIO_PARAM_MIN,
				SUB_RUP_ASPECT_RATIO_PARAM_MAX,SUB_RUP_ASPECT_RATIO_PARAM_DEFAULT);
		subductionRupAspectRatioParam.setInfo(SUB_RUP_ASPECT_RATIO_PARAM_INFO);

		ArrayList<String> sub_floaterTypeOptions = new ArrayList<String>();
		sub_floaterTypeOptions.add(SUB_FLOATER_TYPE_FULL_DDW);
		sub_floaterTypeOptions.add(SUB_FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP);
		sub_floaterTypeOptions.add(SUB_FLOATER_TYPE_CENTERED_DOWNDIP);
		subductionFloaterTypeParam = new StringParameter(SUB_FLOATER_TYPE_PARAM_NAME,sub_floaterTypeOptions,
				SUB_FLOATER_TYPE_PARAM_DEFAULT);
		subductionFloaterTypeParam.setInfo(SUB_FLOATER_TYPE_PARAM_INFO);
		
		sourceCacheParam = new BooleanParameter(SOURCE_CACHE_PARAM_NAME, SOURCE_CACHE_PARAM_DEFAULT);
		sourceCacheParam.setInfo(SOURCE_CACHE_PARAM_INFO);
		if (sourceCacheParam.getValue())
			sourceCache = new HashMap<Integer, ProbEqkSource>();

		// Add the change listener to parameters
		// -- Area sources
		includeAreaSourceParam.addParameterChangeListener(this);
		areaSrcDiscrParam.addParameterChangeListener(this);
		areaSrcLowerSeisDepthParam.addParameterChangeListener(this);
		areaSrcRupTypeParam.addParameterChangeListener(this);
		areaSrcMagScalingRelParam.addParameterChangeListener(this);
		// -- Grid sources
		includeGriddedSeisParam.addParameterChangeListener(this);
		griddedSeisRupTypeParam.addParameterChangeListener(this);
		griddedSeisLowerSeisDepthParam.addParameterChangeListener(this);
		griddedSeisMagScalingRelParam.addParameterChangeListener(this);
		// -- Fault sources
		includeFaultSourcesParam.addParameterChangeListener(this);
		faultRupOffsetParam.addParameterChangeListener(this);
		faultDiscrParam.addParameterChangeListener(this);
		faultRupAspectRatioParam.addParameterChangeListener(this);
		faultFloaterTypeParam.addParameterChangeListener(this);
		faultMagScalingRelParam.addParameterChangeListener(this);
		faultScalingSigmaParam.addParameterChangeListener(this);
		// -- Subduction sources
		includeSubductionSourcesParam.addParameterChangeListener(this);
		subductionRupOffsetParam.addParameterChangeListener(this);
		subductionDiscrParam.addParameterChangeListener(this);
		subductionRupAspectRatioParam.addParameterChangeListener(this);
		subductionFloaterTypeParam.addParameterChangeListener(this);
		subductionMagScalingRelParam.addParameterChangeListener(this);
		subductionScalingSigmaParam.addParameterChangeListener(this);
		// -- Other
		sourceCacheParam.addParameterChangeListener(this);
	}
	
	
	
	// Make the adjustable parameters & the list
	private void setParamsFromCalcSettings(CalculationSettings calcSet) {

		areaSrcRupTypeParam.setValue(calcSet.getErf().get(SourceType.AREA_SOURCE).get(GEM1ERF.AREA_SRC_RUP_TYPE_NAME).toString());
		areaSrcMagScalingRelParam.setValue(calcSet.getErf().get(SourceType.AREA_SOURCE).get(GEM1ERF.AREA_SRC_MAG_SCALING_REL_PARAM_NAME).toString());
		areaSrcLowerSeisDepthParam.setValue((Double)calcSet.getErf().get(SourceType.AREA_SOURCE).get(AREA_SRC_LOWER_SEIS_DEPTH_PARAM_NAME));
		areaSrcDiscrParam.setValue((Double)calcSet.getErf().get(SourceType.AREA_SOURCE).get(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME));

		griddedSeisRupTypeParam.setValue(calcSet.getErf().get(SourceType.GRID_SOURCE).get(GEM1ERF.GRIDDED_SEIS_RUP_TYPE_NAME).toString());
		griddedSeisLowerSeisDepthParam.setValue((Double)calcSet.getErf().get(SourceType.GRID_SOURCE).get(GEM1ERF.GRIDDED_SEIS_LOWER_SEIS_DEPTH_PARAM_NAME));
		griddedSeisMagScalingRelParam.setValue(calcSet.getErf().get(SourceType.GRID_SOURCE).get(GEM1ERF.GRIDDED_SEIS_MAG_SCALING_REL_PARAM_NAME).toString());

		faultRupOffsetParam.setValue((Double)calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.FAULT_RUP_OFFSET_PARAM_NAME));
		faultDiscrParam.setValue((Double)calcSet.getErf().get(SourceType.FAULT_SOURCE).get(FAULT_DISCR_PARAM_NAME));
		faultMagScalingRelParam.setValue(calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.FAULT_MAG_SCALING_REL_PARAM_NAME).toString());
		faultScalingSigmaParam.setValue((Double)calcSet.getErf().get(SourceType.FAULT_SOURCE).get(FAULT_SCALING_SIGMA_PARAM_NAME));
		faultRupAspectRatioParam.setValue((Double)calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.FAULT_RUP_ASPECT_RATIO_PARAM_NAME));
		faultFloaterTypeParam.setValue(calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.FAULT_FLOATER_TYPE_PARAM_NAME).toString());

		subductionRupOffsetParam.setValue((Double)calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_RUP_OFFSET_PARAM_NAME));
		subductionDiscrParam.setValue((Double)calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_DISCR_PARAM_NAME));
		subductionMagScalingRelParam.setValue(calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_MAG_SCALING_REL_PARAM_NAME).toString());
		subductionScalingSigmaParam.setValue((Double)calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_SCALING_SIGMA_PARAM_NAME));
		subductionRupAspectRatioParam.setValue((Double)calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_RUP_ASPECT_RATIO_PARAM_NAME));
		subductionFloaterTypeParam.setValue(calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_FLOATER_TYPE_PARAM_NAME).toString());

		sourceCacheParam.setValue(calcSet.isSourceCache());
	}


	/**
	 * This put parameters in the ParameterList (depending on settings).
	 * This could be smarter in terms of not showing parameters if certain
	 * GEMSourceData subclasses are not passed in.
	 */
	protected void createParamList() {

		adjustableParams = new ParameterList();

		if(areaSourceDataList != null) {
			adjustableParams.addParameter(includeAreaSourceParam);
			if(includeAreaSourceParam.getValue()) {
				adjustableParams.addParameter(areaSrcDiscrParam);
				adjustableParams.addParameter(areaSrcRupTypeParam);
				if(!areaSrcRupTypeParam.getValue().equals(AREA_SRC_RUP_TYPE_POINT)) {
					adjustableParams.addParameter(areaSrcMagScalingRelParam);
					MagScalingRelationship magScRel = getmagScalingRelationship(areaSrcMagScalingRelParam.getValue());
					if(areaSrcRupTypeParam.getValue().equals(AREA_SRC_RUP_TYPE_FINITE_SURF) || (magScRel instanceof MagAreaRelationship)) {
						adjustableParams.addParameter(areaSrcLowerSeisDepthParam);
					}
				}
			}
		}

		if(griddedSeisSourceDataList != null) {
			adjustableParams.addParameter(includeGriddedSeisParam);
			if(includeGriddedSeisParam.getValue()) {
				adjustableParams.addParameter(griddedSeisRupTypeParam);
				if(!griddedSeisRupTypeParam.getValue().equals(GRIDDED_SEIS_RUP_TYPE_POINT)) {
					adjustableParams.addParameter(griddedSeisMagScalingRelParam);
					MagScalingRelationship magScRel = getmagScalingRelationship(griddedSeisMagScalingRelParam.getValue());
					if(griddedSeisRupTypeParam.getValue().equals(GRIDDED_SEIS_RUP_TYPE_FINITE_SURF) || (magScRel instanceof MagAreaRelationship)) {
						adjustableParams.addParameter(griddedSeisLowerSeisDepthParam);
					}
				}
			}
		}
		
		if(faultSourceDataList != null) {
			adjustableParams.addParameter(includeFaultSourcesParam);
			if(includeFaultSourcesParam.getValue()) {
				adjustableParams.addParameter(faultDiscrParam);
				adjustableParams.addParameter(faultRupOffsetParam);
				adjustableParams.addParameter(faultRupAspectRatioParam);
				adjustableParams.addParameter(faultFloaterTypeParam);
				adjustableParams.addParameter(faultMagScalingRelParam);
				adjustableParams.addParameter(faultScalingSigmaParam);				
			}
		}
		
		if(subductionSourceDataList != null) {
			adjustableParams.addParameter(includeSubductionSourcesParam);
			if(includeSubductionSourcesParam.getValue()) {
				adjustableParams.addParameter(subductionDiscrParam);
				adjustableParams.addParameter(subductionRupOffsetParam);
				adjustableParams.addParameter(subductionRupAspectRatioParam);
				adjustableParams.addParameter(subductionFloaterTypeParam);
				adjustableParams.addParameter(subductionMagScalingRelParam);
				adjustableParams.addParameter(subductionScalingSigmaParam);
			}
		}
		
		adjustableParams.addParameter(sourceCacheParam);

	}



	private MagScalingRelationship getmagScalingRelationship(String magScName) {
		if (magScName.equals(WC1994_MagAreaRelationship.NAME))
			return new WC1994_MagAreaRelationship();
		else if (magScName.equals(WC1994_MagLengthRelationship.NAME))
			return new WC1994_MagLengthRelationship();
		else
			return new PEER_testsMagAreaRelationship();
	}


	protected ProbEqkSource mkFaultSource(GEMFaultSourceData gemFaultSourceData) {
		
		StirlingGriddedSurface faultSurface = new StirlingGriddedSurface(
				gemFaultSourceData.getTrace(),
				gemFaultSourceData.getDip(),
				gemFaultSourceData.getSeismDepthUpp(),
				gemFaultSourceData.getSeismDepthLow(),
                faultDiscrValue);

		FloatingPoissonFaultSource src = null;
		
		if(gemFaultSourceData.getFloatRuptureFlag()){
			
			 src = new FloatingPoissonFaultSource(
					gemFaultSourceData.getMfd(),	//IncrementalMagFreqDist
	                faultSurface,					//EvenlyGriddedSurface			
	                faultMagScalingRel,					// MagScalingRelationship
	                this.faultScalingSigmaValue,				// sigma of the mag-scaling relationship
	                this.faultRupAspectRatioValue,			// floating rupture aspect ration (length/width)
	                this.faultRupOffsetValue,			// floating rupture offset
	                gemFaultSourceData.getRake(),	// average rake of the ruptures
	                duration,						// duration of forecast
	                MINMAG,							// minimum mag considered (probs of those lower set to zero regardless of MFD)
	                faultFloaterTypeValue,				// type of floater (0 for full DDW, 1 for floating both ways, and 2 for floating down center)
	                12.0);  						// mags >= to this forced to be full fault ruptures (set as high value for now)
			
		}
		else{
			
			 src = new FloatingPoissonFaultSource(
					gemFaultSourceData.getMfd(),	//IncrementalMagFreqDist
	                faultSurface,					//EvenlyGriddedSurface			
	                faultMagScalingRel,					// MagScalingRelationship
	                this.faultScalingSigmaValue,				// sigma of the mag-scaling relationship
	                this.faultRupAspectRatioValue,			// floating rupture aspect ration (length/width)
	                this.faultRupOffsetValue,			// floating rupture offset
	                gemFaultSourceData.getRake(),	// average rake of the ruptures
	                duration,						// duration of forecast
	                MINMAG,							// minimum mag considered (probs of those lower set to zero regardless of MFD)
	                faultFloaterTypeValue,				// type of floater (0 for full DDW, 1 for floating both ways, and 2 for floating down center)
	                0.0);  						// mags >= to this forced to be full fault ruptures (set as high value for now)
			
		}
		

		src.setTectonicRegionType(gemFaultSourceData.getTectReg());
		return src;
	}
	
	
	protected ProbEqkSource mkSubductionSource(GEMSubductionFaultSourceData gemSubductFaultSourceData) {
		
		ApproxEvenlyGriddedSurface faultSurface = new ApproxEvenlyGriddedSurface(
				gemSubductFaultSourceData.getTopTrace(),
				gemSubductFaultSourceData.getBottomTrace(),
                subductionDiscrValue);
		
		FloatingPoissonFaultSource src = null;
		
		if(gemSubductFaultSourceData.getFloatRuptureFlag()){
			
			src = new FloatingPoissonFaultSource(
					gemSubductFaultSourceData.getMfd(),	//IncrementalMagFreqDist
	                faultSurface,					//EvenlyGriddedSurface			
	                subductionMagScalingRel,					// MagScalingRelationship
	                this.subductionScalingSigmaValue,				// sigma of the mag-scaling relationship
	                this.subductionRupAspectRatioValue,			// floating rupture aspect ration (length/width)
	                this.subductionRupOffsetValue,			// floating rupture offset
	                gemSubductFaultSourceData.getRake(),	// average rake of the ruptures
	                timeSpan.getDuration(),						// duration of forecast
	                MINMAG,							// minimum mag considered (probs of those lower set to zero regardless of MFD)
	                subductionFloaterTypeValue,					// type of floater (0 for full DDW, 1 for floating both ways, and 2 for floating down center)
	                12.0);  						// mags >= to this forced to be full fault ruptures (set as high value for now)
			
		}
		else{
			
			src = new FloatingPoissonFaultSource(
					gemSubductFaultSourceData.getMfd(),	//IncrementalMagFreqDist
	                faultSurface,					//EvenlyGriddedSurface			
	                subductionMagScalingRel,					// MagScalingRelationship
	                this.subductionScalingSigmaValue,				// sigma of the mag-scaling relationship
	                this.subductionRupAspectRatioValue,			// floating rupture aspect ration (length/width)
	                this.subductionRupOffsetValue,			// floating rupture offset
	                gemSubductFaultSourceData.getRake(),	// average rake of the ruptures
	                timeSpan.getDuration(),						// duration of forecast
	                MINMAG,							// minimum mag considered (probs of those lower set to zero regardless of MFD)
	                subductionFloaterTypeValue,					// type of floater (0 for full DDW, 1 for floating both ways, and 2 for floating down center)
	                0.0);  						// mags >= to this forced to be full fault ruptures (set as high value for now)
			
		}

		src.setTectonicRegionType(gemSubductFaultSourceData.getTectReg());
		return src;
	}

	/**
	 * 
	 * @param areaSourceData
	 * @return ProbEqkSource
	 */
	protected ProbEqkSource mkAreaSource(GEMAreaSourceData areaSourceData) {	
		

		if (areaSrcRupTypeValue.equals(AREA_SRC_RUP_TYPE_POINT)){
			PoissonAreaSource src = new PoissonAreaSource(areaSourceData.getRegion(),AREA_SRC_DISCR_PARAM_DEFAULT,
					areaSourceData.getMagfreqDistFocMech(),areaSourceData.getAveRupTopVsMag(),
					areaSourceData.getAveHypoDepth(),duration,MINMAG);
			src.setTectonicRegionType(areaSourceData.getTectReg());
			return src;
		} else if (areaSrcRupTypeValue.equals(AREA_SRC_RUP_TYPE_LINE)) {
			PoissonAreaSource src = new PoissonAreaSource(areaSourceData.getRegion(),AREA_SRC_DISCR_PARAM_DEFAULT,
					areaSourceData.getMagfreqDistFocMech(),areaSourceData.getAveRupTopVsMag(),
					areaSourceData.getAveHypoDepth(),areaSrcMagScalingRel,areaSrcLowerSeisDepthValue,
					duration,MINMAG);
			src.setTectonicRegionType(areaSourceData.getTectReg());
			return src;
		} else if (areaSrcRupTypeValue.equals(AREA_SRC_RUP_TYPE_CROSS_HAIR)) {
			PoissonAreaSource src = new PoissonAreaSource(areaSourceData.getRegion(),AREA_SRC_DISCR_PARAM_DEFAULT,
					areaSourceData.getMagfreqDistFocMech(),areaSourceData.getAveRupTopVsMag(),
					areaSourceData.getAveHypoDepth(),areaSrcMagScalingRel,areaSrcLowerSeisDepthValue,
					duration,MINMAG,2,0);
			src.setTectonicRegionType(areaSourceData.getTectReg());
			return src;
		} else if (areaSrcRupTypeValue.equals(AREA_SRC_RUP_TYPE_SPOKED)) {
			PoissonAreaSource src = new PoissonAreaSource(areaSourceData.getRegion(),AREA_SRC_DISCR_PARAM_DEFAULT,
					areaSourceData.getMagfreqDistFocMech(),areaSourceData.getAveRupTopVsMag(),
					areaSourceData.getAveHypoDepth(),areaSrcMagScalingRel,areaSrcLowerSeisDepthValue,
					duration,MINMAG,16,0);
			src.setTectonicRegionType(areaSourceData.getTectReg());
			return src;
		} else if(areaSrcRupTypeValue.equals(AREA_SRC_RUP_TYPE_FINITE_SURF)) {
			throw new RuntimeException(NAME+" - "+AREA_SRC_RUP_TYPE_FINITE_SURF+ " is not yet implemented");
	    } else
		    throw new RuntimeException(NAME+" - Unsupported area source rupture type");

	}	
	
	/**
	 * 
	 * @param gridSourceData
	 * @return ProbEqkSource
	 */
	protected ProbEqkSource mkGridSource(GEMPointSourceData gridSourceData) {

		if(griddedSeisRupTypeValue.equals(GRIDDED_SEIS_RUP_TYPE_POINT)) {
			PointEqkSource src = new PointEqkSource(gridSourceData.getHypoMagFreqDistAtLoc(),
					gridSourceData.getAveRupTopVsMag(), 
					gridSourceData.getAveHypoDepth(),
					duration, MINMAG);
			src.setTectonicRegionType(gridSourceData.getTectReg());
			return src;
		}
		else if(griddedSeisRupTypeValue.equals(GRIDDED_SEIS_RUP_TYPE_LINE)) {
			PointToLineSource src = new PointToLineSource(gridSourceData.getHypoMagFreqDistAtLoc(),
					gridSourceData.getAveRupTopVsMag(), 
					gridSourceData.getAveHypoDepth(),
					griddedSeisMagScalingRel,
					griddedSeisLowerSeisDepthValue, 
					duration, MINMAG);
			src.setTectonicRegionType(gridSourceData.getTectReg());
			return src;
		}
		else if(griddedSeisRupTypeValue.equals(GRIDDED_SEIS_RUP_TYPE_CROSS_HAIR)) {
			PointToLineSource src = new PointToLineSource(gridSourceData.getHypoMagFreqDistAtLoc(),
					gridSourceData.getAveRupTopVsMag(), 
					gridSourceData.getAveHypoDepth(),
					griddedSeisMagScalingRel,
					griddedSeisLowerSeisDepthValue, 
					duration, MINMAG,
					2, 0);
			src.setTectonicRegionType(gridSourceData.getTectReg());
			return src;
		}
		else if(griddedSeisRupTypeValue.equals(GRIDDED_SEIS_RUP_TYPE_SPOKED)) {
			PointToLineSource src = new PointToLineSource(gridSourceData.getHypoMagFreqDistAtLoc(),
					gridSourceData.getAveRupTopVsMag(), 
					gridSourceData.getAveHypoDepth(),
					griddedSeisMagScalingRel,
					griddedSeisLowerSeisDepthValue, 
					duration, MINMAG,
					16, 0);
			src.setTectonicRegionType(gridSourceData.getTectReg());
			return src;
		}
		else if(griddedSeisRupTypeValue.equals(GRIDDED_SEIS_RUP_TYPE_FINITE_SURF)) {
			throw new RuntimeException(NAME+" - "+GRIDDED_SEIS_RUP_TYPE_FINITE_SURF+ " is not yet implemented");
		}
		else
			throw new RuntimeException(NAME+" - Unsupported background rupture type");
	}	

	/**
	 * Returns the ith earthquake source
	 *
	 * @param iSource : index of the source needed
	 */
	public ProbEqkSource getSource(int iSource) {
		ProbEqkSource source = null;
		if (sourceCache !=  null) {
			source = sourceCache.get(new Integer(iSource));
		}
		if (source == null) {
			GEMSourceData srcData = gemSourceDataList.get(iSource);
			if(srcData instanceof GEMFaultSourceData)
				source = mkFaultSource((GEMFaultSourceData)srcData);
			else if (srcData instanceof GEMSubductionFaultSourceData)
				source = mkSubductionSource((GEMSubductionFaultSourceData)srcData);
			else if (srcData instanceof GEMPointSourceData)
				source = mkGridSource((GEMPointSourceData)srcData);
			else if (srcData instanceof GEMAreaSourceData)
				source = mkAreaSource((GEMAreaSourceData)srcData);
			else
				throw new RuntimeException(NAME+": "+srcData.getClass()+" not yet supported");
			if (sourceCache != null) {
				System.out.println("Caching source " + iSource);
				sourceCache.put(new Integer(iSource), source);
			}
		}
		return source;
	}

	/**
	 * Get the number of earthquake sources
	 *
	 * @return integer
	 */
	public int getNumSources(){
		return gemSourceDataList.size();
	}

	/**
	 * Get the list of all earthquake sources.
	 *
	 * @return ArrayList of Prob Earthquake sources
	 */
	public ArrayList  getSourceList(){
		ArrayList list = new ArrayList();
		for(int s=0; s<this.getNumSources();s++)
			list.add(getSource(s));
		return list;
	}

	/**
	 * Return the name for this class
	 *
	 * @return : return the name for this class
	 */
	public String getName(){
		return NAME;
	}

	/**
	 * update the forecast
	 **/

	public void updateForecast() {

		// make sure something has changed
		if(parameterChangeFlag) {
		
			// set the primitive parameters here so it's not repeated many times in the source-creation 
			// methods (this could alternatively be done in the parameterChange method)
			
			// ------------------------------------------------------------------------- AREA SOURCE
			areaSrcRupTypeValue = areaSrcRupTypeParam.getValue();
			areaSrcLowerSeisDepthValue = areaSrcLowerSeisDepthParam.getValue();
			areaSrcDiscrValue = areaSrcDiscrParam.getValue();
			areaSrcMagScalingRel = getmagScalingRelationship(areaSrcMagScalingRelParam.getValue());
			
			// ------------------------------------------------------------------------- GRID SOURCE
			griddedSeisRupTypeValue = griddedSeisRupTypeParam.getValue();
			griddedSeisLowerSeisDepthValue = griddedSeisLowerSeisDepthParam.getValue();
			griddedSeisMagScalingRel = getmagScalingRelationship(griddedSeisMagScalingRelParam.getValue());

			// ------------------------------------------------------------------------ FAULT SOURCE
			faultRupOffsetValue = faultRupOffsetParam.getValue();
			faultDiscrValue = faultDiscrParam.getValue();
			faultMagScalingRel = getmagScalingRelationship(faultMagScalingRelParam.getValue());
			faultScalingSigmaValue = faultScalingSigmaParam.getValue();
			faultRupAspectRatioValue = faultRupAspectRatioParam.getValue();
			String floaterTypeName = faultFloaterTypeParam.getValue();
			if(floaterTypeName.equals(this.FLOATER_TYPE_FULL_DDW)) 
				faultFloaterTypeValue = 0;
			else if(floaterTypeName.equals(this.FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP)) 
				faultFloaterTypeValue = 1;
			else // (floaterTypeName.equals(this.FLOATER_TYPE_CENTERED_DOWNDIP)) 
				faultFloaterTypeValue = 2;
			duration = timeSpan.getDuration();
			
			// ------------------------------------------------------------------------ SUBDUCTION FAULT SOURCE
			subductionRupOffsetValue = subductionRupOffsetParam.getValue();
			subductionDiscrValue = subductionDiscrParam.getValue();
			subductionMagScalingRel = getmagScalingRelationship(subductionMagScalingRelParam.getValue());
			subductionScalingSigmaValue = subductionScalingSigmaParam.getValue();
			subductionRupAspectRatioValue = subductionRupAspectRatioParam.getValue();
			String sub_floaterTypeName = subductionFloaterTypeParam.getValue();
			if(sub_floaterTypeName.equals(this.SUB_FLOATER_TYPE_FULL_DDW)) 
				subductionFloaterTypeValue = 0;
			else if(sub_floaterTypeName.equals(this.SUB_FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP)) 
				subductionFloaterTypeValue = 1;
			else // (floaterTypeName.equals(this.FLOATER_TYPE_CENTERED_DOWNDIP)) 
				subductionFloaterTypeValue = 2;
			
			// clear cache (if used) and garbage collect
			if (sourceCache != null) {
				sourceCache = null;
				System.gc();
			}
			
			// make the list of sources
			gemSourceDataList = new ArrayList<GEMSourceData>();
			if(includeAreaSourceParam.getValue() && areaSourceDataList !=null ) 
				gemSourceDataList.addAll(areaSourceDataList);
			if(includeGriddedSeisParam.getValue() && griddedSeisSourceDataList !=null ) 
				gemSourceDataList.addAll(griddedSeisSourceDataList);
			if(includeFaultSourcesParam.getValue() && faultSourceDataList !=null ) 
				gemSourceDataList.addAll(faultSourceDataList);
			if(includeSubductionSourcesParam.getValue() && subductionSourceDataList !=null ) 
				gemSourceDataList.addAll(subductionSourceDataList);
			
			parameterChangeFlag = false;
		}
	}

	/**
	 *  This acts on a parameter change event.
	 *
	 *  This sets the flag to indicate that the sources need to be updated
	 *
	 * @param  event
	 */
	public void parameterChange(ParameterChangeEvent event) {
		super.parameterChange(event);
		String paramName = event.getParameterName();
		
		// for now create new parameter list on every change; make more efficient later?
		createParamList();
		
		if (paramName.equals(SOURCE_CACHE_PARAM_NAME)) {
			if ((Boolean)event.getParameter().getValue()) {
				if (sourceCache == null)
					sourceCache = new HashMap<Integer, ProbEqkSource>();
			} else {
				sourceCache = null;
				System.gc();  // garbage collection
			}
		} else
			parameterChangeFlag = true;

	}

	// this is temporary for testing purposes
	public static void main(String[] args) {

	}
	
	@Override
	public ArrayList<TectonicRegionType> getIncludedTectonicRegionTypes() {
		return tectonicRegionTypes;
	}

}

