package org.opensha.gem.GEM1.scratch.marco.testParsers;

import java.util.ArrayList;
import java.util.Iterator;

import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.MagScalingRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.PEER_testsMagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagLengthRelationship;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.sha.earthquake.rupForecastImpl.GriddedRegionPoissonEqkSource;
import org.opensha.gem.GEM1.util.SourceType;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultSource;
import org.opensha.sha.earthquake.rupForecastImpl.PointEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.PointToLineSource;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;

import org.opensha.sha.faultSurface.ApproxEvenlyGriddedSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;

/**
 * <p>Title: GEM1ERF </p>
 *
 * @author : 
 * @Date : 
 * @version 1.0
 */

public class GEM1ERF extends EqkRupForecast {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	// name of this ERF
	public final static String NAME = new String("GEM1 Eqk Rup Forecast");

	//for Debug purposes
	private static String C = new String("GEM1ERF");
	private boolean D = false;
	
	protected ArrayList<GEMSourceData> gemSourceDataList;
	
	// some fixed parameters
	final static double MINMAG = 0;   // this sets the minimum mag considered in the forecast (overriding that implied in the source data)
	
	// calculation settings (primitive versions of the adj parameters)
	String backSeisValue;
	String backSeisRupValue;
	String areaSrcValue;
	String areaSrcRupValue;
	double lowerSeisDepthValue;
	double areaSrcLowerSeisDepthValue;
	double areaDiscrValue;
	MagScalingRelationship magScalingRelBackgr;
	MagScalingRelationship magScalingRelArea;
	double rupOffsetValue;
	double faultDiscrValue;
	MagScalingRelationship magScalingRel;
	double sigmaValue;
	double aspectRatioValue;
	int floaterTypeFlag;
	double duration;		// from the timeSpan
	// for subduction fault
	double sub_rupOffsetValue;
	double sub_faultDiscrValue;
	MagScalingRelationship sub_magScalingRel;
	double sub_sigmaValue;
	double sub_aspectRatioValue;
	int sub_floaterTypeFlag;
	double sub_duration;		// from the timeSpan

	// THE REST IS FOR ALL THE ADJUSTABLE PARAMERS:
	
	//-------------------------------------------------------------------------------- AREA SOURCES
	// Treat background seismogenic as point of finite ruptures parameter
	public final static String AREA_SRC_RUP_NAME = new String ("Treat Background Seismicity As");
	public final static String AREA_SRC_RUP_POINT = new String ("Point Sources");
	public final static String AREA_SRC_RUP_LINE = new String ("Line Sources (random or given strike)");
	public final static String AREA_SRC_RUP_CROSS_HAIR = new String ("Cross Hair Line Sources");
	public final static String AREA_SRC_RUP_SPOKED = new String ("16 Spoked Line Sources");
	public final static String AREA_SRC_RUP_FINITE_SURF = new String ("Finite Dipping Sources");
	public final static String AREA_SRC_RUP_POINT_OLD = new String ("Old Point Sources");
	StringParameter areaSrcRupParam;

	// Default lower seismogenic depth of area sources
	public final static String LOWER_SEIS_DEPTH_AREA_SRC_PARAM_NAME = "Default Lower Seis Depth";
	public final static Double LOWER_SEIS_DEPTH_AREA_SRC_PARAM_MIN = new Double(5.0);
	public final static Double LOWER_SEIS_DEPTH_AREA_SRC_PARAM_MAX = new Double(50);
	public final static Double LOWER_SEIS_DEPTH_AREA_SRC_PARAM_DEFAULT = new Double(14);
	public final static String LOWER_SEIS_DEPTH_AREA_SRC_PARAM_UNITS = "km";
	private final static String LOWER_SEIS_DEPTH_AREA_SRC_PARAM_INFO = "The default lower-seimogenic " +
			"depth for area sources=";
	private DoubleParameter areaSrcLowerSeisDepthParam;

	// For area discretization
	public final static String AREA_DISCR_PARAM_NAME ="Area Discretization";
	private final static Double AREA_DISCR_PARAM_DEFAULT = new Double(0.1);
	private final static String AREA_DISCR_PARAM_UNITS = "deg";
	private final static String AREA_DISCR_PARAM_INFO = "The discretization of area sources";
	public final static double AREA_DISCR_PARAM_MIN = new Double(0.01);
	public final static double AREA_DISCR_PARAM_MAX = new Double(1.0);
	DoubleParameter areaDiscrParam;
	
	// Mag-scaling relationship for turning grip points into finite ruptures
	public final static String MAG_SCALING_REL_AREA_SRC_PARAM_NAME = "Background Mag-Scaling";
	private final static String MAG_SCALING_REL_AREA_SRC_PARAM_INFO = " Mag-scaling relationship " +
			"for computing size of background events";
	StringParameter magScalingRelAreaSrcParam;

	//--------------------------------------------------------------------------- GRIDDED SEISMCITY
	// Include or exclude background seis parameter
	public final static String BACK_SEIS_NAME = new String ("Background Seismicity");
	public final static String BACK_SEIS_INCLUDE = new String ("Include");
	public final static String BACK_SEIS_EXCLUDE = new String ("Exclude");
	public final static String BACK_SEIS_ONLY = new String ("Only Background");
	// make the fault-model parameter
	StringParameter backSeisParam;

	// Treat background seis as point of finite ruptures parameter
	public final static String BACK_SEIS_RUP_NAME = new String ("Treat Background Seismicity As");
	public final static String BACK_SEIS_RUP_POINT = new String ("Point Sources");
	public final static String BACK_SEIS_RUP_LINE = new String ("Line Sources (random or given strike)");
	public final static String BACK_SEIS_RUP_CROSS_HAIR = new String ("Cross Hair Line Sources");
	public final static String BACK_SEIS_RUP_SPOKED = new String ("16 Spoked Line Sources");
	public final static String BACK_SEIS_RUP_FINITE_SURF = new String ("Finite Dipping Sources");
	StringParameter backSeisRupParam;

	// default lower seis depth of gridded/background source
	public final static String LOWER_SEIS_DEPTH_BACKGR_PARAM_NAME = "Default Lower Seis Depth";
	public final static Double LOWER_SEIS_DEPTH_BACKGR_PARAM_MIN = new Double(5.0);
	public final static Double LOWER_SEIS_DEPTH_BACKGR_PARAM_MAX = new Double(50);
	public final static Double LOWER_SEIS_DEPTH_BACKGR_PARAM_DEFAULT = new Double(14);
	public final static String LOWER_SEIS_DEPTH_BACKGR_PARAM_UNITS = "km";
	private final static String LOWER_SEIS_DEPTH_BACKGR_PARAM_INFO = "The default lower-seimogenic depth for gridded seismicity=";
	private DoubleParameter lowerSeisDepthParam ;

	// Mag-scaling relationship for turning grip points into finite ruptures
	public final static String MAG_SCALING_REL_BACKGR_PARAM_NAME = "Background Mag-Scaling";
	private final static String MAG_SCALING_REL_BACKGR_PARAM_INFO = " Mag-scaling relationship for computing size of background events";
	StringParameter magScalingRelBackgrParam;

	//------------------------------------------------------------------------------- FAULT SOURCES
	// For rupture offset length along fault parameter
	public final static String RUP_OFFSET_PARAM_NAME ="Rupture Offset";
	private final static Double RUP_OFFSET_DEFAULT = new Double(5);
	private final static String RUP_OFFSET_PARAM_UNITS = "km";
	private final static String RUP_OFFSET_PARAM_INFO = "The amount floating ruptures are offset along the fault";
	public final static double RUP_OFFSET_PARAM_MIN = 1;
	public final static double RUP_OFFSET_PARAM_MAX = 100;
	DoubleParameter rupOffsetParam;

	// For fault discretization
	public final static String FAULT_DISCR_PARAM_NAME ="Fault Discretization";
	private final static Double FAULT_DISCR_PARAM_DEFAULT = new Double(1.0);
	private final static String FAULT_DISCR_PARAM_UNITS = "km";
	private final static String FAULT_DISCR_PARAM_INFO = "The discretization of faults";
	public final static double FAULT_DISCR_PARAM_MIN = 1;
	public final static double FAULT_DISCR_PARAM_MAX = 10;
	DoubleParameter faultDiscrParam;

	// Mag-scaling relationship parameter stuff
	public final static String MAG_SCALING_REL_PARAM_NAME = "Rupture Mag-Scaling";
	private final static String MAG_SCALING_REL_PARAM_INFO = " Mag-scaling relationship for computing size of floaters";
	StringParameter magScalingRelParam;

	// Mag-scaling sigma parameter stuff
	public final static String SIGMA_PARAM_NAME =  "Mag Scaling Sigma";
	private final static String SIGMA_PARAM_INFO =  "The standard deviation of the Area(mag) or Length(M) relationship";
	private Double SIGMA_PARAM_MIN = new Double(0);
	private Double SIGMA_PARAM_MAX = new Double(1);
	private Double SIGMA_PARAM_DEFAULT = new Double(0.0);
	DoubleParameter sigmaParam;

	// rupture aspect ratio parameter stuff
	public final static String ASPECT_RATIO_PARAM_NAME = "Rupture Aspect Ratio";
	private final static String ASPECT_RATIO_PARAM_INFO = "The ratio of rupture length to rupture width";
	private Double ASPECT_RATIO_PARAM_MIN = new Double(Double.MIN_VALUE);
	private Double ASPECT_RATIO_PARAM_MAX = new Double(Double.MAX_VALUE);
	private Double ASPECT_RATIO_PARAM_DEFAULT = new Double(1.0);
	DoubleParameter aspectRatioParam;

	// Floater Type
	public final static String FLOATER_TYPE_PARAM_NAME = "Floater Type";
	public final static String FLOATER_TYPE_PARAM_INFO = "Specifies how to float ruptures around the faults";
	public final static String FLOATER_TYPE_FULL_DDW = "Only along strike ( rupture full DDW)";
	public final static String FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP = "Along strike and down dip";
	public final static String FLOATER_TYPE_CENTERED_DOWNDIP = "Along strike & centered down dip";
	public final static String FLOATER_TYPE_PARAM_DEFAULT = FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP;
	StringParameter floaterTypeParam;
	
	//------------------------------------------------------------------------------- SUBDUCTION FAULT SOURCES
	// For rupture offset length along fault parameter
	public final static String SUB_RUP_OFFSET_PARAM_NAME ="Subduction Fault Rupture Offset";
	private final static Double SUB_RUP_OFFSET_DEFAULT = new Double(5);
	private final static String SUB_RUP_OFFSET_PARAM_UNITS = "km";
	private final static String SUB_RUP_OFFSET_PARAM_INFO = "The amount floating ruptures are offset along the fault";
	public final static double SUB_RUP_OFFSET_PARAM_MIN = 1;
	public final static double SUB_RUP_OFFSET_PARAM_MAX = 100;
	DoubleParameter sub_rupOffsetParam;

	// For fault discretization
	public final static String SUB_FAULT_DISCR_PARAM_NAME ="Subduction Fault Discretization";
	private final static Double SUB_FAULT_DISCR_PARAM_DEFAULT = new Double(1.0);
	private final static String SUB_FAULT_DISCR_PARAM_UNITS = "km";
	private final static String SUB_FAULT_DISCR_PARAM_INFO = "The discretization of faults";
	public final static double SUB_FAULT_DISCR_PARAM_MIN = 1;
	public final static double SUB_FAULT_DISCR_PARAM_MAX = 100;
	DoubleParameter sub_faultDiscrParam;

	// Mag-scaling relationship parameter stuff
	public final static String SUB_MAG_SCALING_REL_PARAM_NAME = "Subduction Fault Rupture Mag-Scaling";
	private final static String SUB_MAG_SCALING_REL_PARAM_INFO = " Mag-scaling relationship for computing size of floaters";
	StringParameter sub_magScalingRelParam;

	// Mag-scaling sigma parameter stuff
	public final static String SUB_SIGMA_PARAM_NAME =  "Subduction Fault Mag Scaling Sigma";
	private final static String SUB_SIGMA_PARAM_INFO =  "The standard deviation of the Area(mag) or Length(M) relationship";
	private Double SUB_SIGMA_PARAM_MIN = new Double(0);
	private Double SUB_SIGMA_PARAM_MAX = new Double(1);
	private Double SUB_SIGMA_PARAM_DEFAULT = new Double(0.0);
	DoubleParameter sub_sigmaParam;

	// rupture aspect ratio parameter stuff
	public final static String SUB_ASPECT_RATIO_PARAM_NAME = "Subduction Fault Rupture Aspect Ratio";
	private final static String SUB_ASPECT_RATIO_PARAM_INFO = "The ratio of rupture length to rupture width";
	private Double SUB_ASPECT_RATIO_PARAM_MIN = new Double(Double.MIN_VALUE);
	private Double SUB_ASPECT_RATIO_PARAM_MAX = new Double(Double.MAX_VALUE);
	private Double SUB_ASPECT_RATIO_PARAM_DEFAULT = new Double(1.0);
	DoubleParameter sub_aspectRatioParam;

	// Floater Type
	public final static String SUB_FLOATER_TYPE_PARAM_NAME = "Subduction Fault Floater Type";
	public final static String SUB_FLOATER_TYPE_PARAM_INFO = "Specifies how to float ruptures around the faults";
	public final static String SUB_FLOATER_TYPE_FULL_DDW = "Only along strike ( rupture full DDW)";
	public final static String SUB_FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP = "Along strike and down dip";
	public final static String SUB_FLOATER_TYPE_CENTERED_DOWNDIP = "Along strike & centered down dip";
	public final static String SUB_FLOATER_TYPE_PARAM_DEFAULT = FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP;
	StringParameter sub_floaterTypeParam;


	/**
	 *
	 * No argument constructor
	 */
	public GEM1ERF() {
		this(null);
	}


	/**
	 * This takes a gemSourceDataList
	 */
	public GEM1ERF(ArrayList<GEMSourceData> gemSourceDataList) {
		
		this.gemSourceDataList = gemSourceDataList;

		// create the timespan object with start time and duration in years
		timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
		timeSpan.addParameterChangeListener(this);
		timeSpan.setDuration(50);

		// create and add adj params to list
		initAdjParams();
	}
	
	/**
	 * This takes a gemSourceDataList and a CalculationSettings object
	 */
	public GEM1ERF(ArrayList<GEMSourceData> gemSourceDataList, CalculationSettings calcSet) {
		
		this.gemSourceDataList = gemSourceDataList;

		// create the timespan object with start time and duration in years
		timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
		timeSpan.addParameterChangeListener(this);
		timeSpan.setDuration(50);

		// create and add adj params to list
		initAdjParamsFromCalcSet(calcSet);
	}
	
	// Make the adjustable parameters & the list
	private void initAdjParams() {

		// ---------------------------------------------------------------------------- GRID SOURCES
		ArrayList<String> backSeisOptionsStrings = new ArrayList<String>();
		backSeisOptionsStrings.add(BACK_SEIS_EXCLUDE);
		backSeisOptionsStrings.add(BACK_SEIS_INCLUDE);
		backSeisOptionsStrings.add(BACK_SEIS_ONLY);
		backSeisParam = new StringParameter(BACK_SEIS_NAME, backSeisOptionsStrings,BACK_SEIS_EXCLUDE);
	
		ArrayList<String> backSeisRupOptionsStrings = new ArrayList<String>();
		backSeisRupOptionsStrings.add(BACK_SEIS_RUP_POINT);
		backSeisRupOptionsStrings.add(BACK_SEIS_RUP_LINE);
		backSeisRupOptionsStrings.add(BACK_SEIS_RUP_CROSS_HAIR);
		backSeisRupOptionsStrings.add(BACK_SEIS_RUP_SPOKED);
		backSeisRupOptionsStrings.add(BACK_SEIS_RUP_FINITE_SURF);
		backSeisRupParam = new StringParameter(BACK_SEIS_RUP_NAME, backSeisRupOptionsStrings,BACK_SEIS_RUP_POINT);

		lowerSeisDepthParam = new DoubleParameter(LOWER_SEIS_DEPTH_BACKGR_PARAM_NAME,LOWER_SEIS_DEPTH_BACKGR_PARAM_MIN,
				LOWER_SEIS_DEPTH_BACKGR_PARAM_MAX,LOWER_SEIS_DEPTH_BACKGR_PARAM_UNITS,LOWER_SEIS_DEPTH_BACKGR_PARAM_DEFAULT);
		lowerSeisDepthParam.setInfo(LOWER_SEIS_DEPTH_BACKGR_PARAM_INFO);
		
		// Create the mag-scaling relationship param for griddes seismicity
		ArrayList<String> magScalingRelBackgrOptions = new ArrayList<String>();
		magScalingRelBackgrOptions.add(WC1994_MagAreaRelationship.NAME);
		magScalingRelBackgrOptions.add(WC1994_MagLengthRelationship.NAME);
		magScalingRelBackgrOptions.add(PEER_testsMagAreaRelationship.NAME);
		magScalingRelBackgrParam = new StringParameter(MAG_SCALING_REL_BACKGR_PARAM_NAME,magScalingRelBackgrOptions,
				WC1994_MagAreaRelationship.NAME);
		magScalingRelBackgrParam.setInfo(MAG_SCALING_REL_BACKGR_PARAM_INFO);

		// ---------------------------------------------------------------------------- AREA SOURCES
		// Create the fault option parameter for area sources
		ArrayList<String> areaSeisRupOptionsStrings = new ArrayList<String>();
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_POINT);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_LINE);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_CROSS_HAIR);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_SPOKED);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_FINITE_SURF);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_POINT_OLD);
		areaSrcRupParam = new StringParameter(AREA_SRC_RUP_NAME,areaSeisRupOptionsStrings,
				AREA_SRC_RUP_POINT);
		
		// Create the mag-scaling relationship param for area sources
		ArrayList<String> magScalingRelAreaOptions = new ArrayList<String>();
		magScalingRelAreaOptions.add(WC1994_MagAreaRelationship.NAME);
		magScalingRelAreaOptions.add(WC1994_MagLengthRelationship.NAME);
		magScalingRelAreaOptions.add(PEER_testsMagAreaRelationship.NAME);
		magScalingRelAreaSrcParam = new StringParameter(MAG_SCALING_REL_AREA_SRC_PARAM_NAME,magScalingRelAreaOptions,
				WC1994_MagAreaRelationship.NAME);
		magScalingRelAreaSrcParam.setInfo(MAG_SCALING_REL_AREA_SRC_PARAM_INFO);
		
		// Area lower seismogenic depth parameter
		areaSrcLowerSeisDepthParam = new DoubleParameter(LOWER_SEIS_DEPTH_AREA_SRC_PARAM_NAME,
				LOWER_SEIS_DEPTH_AREA_SRC_PARAM_MIN,
				LOWER_SEIS_DEPTH_AREA_SRC_PARAM_MAX,
				LOWER_SEIS_DEPTH_AREA_SRC_PARAM_UNITS,
				LOWER_SEIS_DEPTH_AREA_SRC_PARAM_DEFAULT);
		areaSrcLowerSeisDepthParam.setInfo(LOWER_SEIS_DEPTH_BACKGR_PARAM_INFO);

		// Area discretization parameter
		areaDiscrParam = new DoubleParameter(AREA_DISCR_PARAM_NAME,AREA_DISCR_PARAM_MIN,
				AREA_DISCR_PARAM_MAX,AREA_DISCR_PARAM_UNITS,AREA_DISCR_PARAM_DEFAULT);
		areaDiscrParam.setInfo(AREA_DISCR_PARAM_INFO);
		
		// --------------------------------------------------------------------------- FAULT SOURCES
		// Rupture offset
		rupOffsetParam = new DoubleParameter(RUP_OFFSET_PARAM_NAME,RUP_OFFSET_PARAM_MIN,
				RUP_OFFSET_PARAM_MAX,RUP_OFFSET_PARAM_UNITS,RUP_OFFSET_DEFAULT);
		rupOffsetParam.setInfo(RUP_OFFSET_PARAM_INFO);

		// Fault discretization parameter
		faultDiscrParam = new DoubleParameter(FAULT_DISCR_PARAM_NAME,FAULT_DISCR_PARAM_MIN,
				FAULT_DISCR_PARAM_MAX,FAULT_DISCR_PARAM_UNITS,FAULT_DISCR_PARAM_DEFAULT);
		faultDiscrParam.setInfo(FAULT_DISCR_PARAM_INFO);

		// create the mag-scaling relationship param
		ArrayList<String> magScalingRelOptions = new ArrayList<String>();
		magScalingRelOptions.add(WC1994_MagAreaRelationship.NAME);
		magScalingRelOptions.add(WC1994_MagLengthRelationship.NAME);
		magScalingRelOptions.add(PEER_testsMagAreaRelationship.NAME);
		magScalingRelParam = new StringParameter(MAG_SCALING_REL_PARAM_NAME,magScalingRelOptions,
				WC1994_MagAreaRelationship.NAME);
		magScalingRelParam.setInfo(MAG_SCALING_REL_PARAM_INFO);

		// create the mag-scaling sigma param
		sigmaParam = new DoubleParameter(SIGMA_PARAM_NAME,
				SIGMA_PARAM_MIN, SIGMA_PARAM_MAX, SIGMA_PARAM_DEFAULT);
		sigmaParam.setInfo(SIGMA_PARAM_INFO);

		// create the aspect ratio param
		aspectRatioParam = new DoubleParameter(ASPECT_RATIO_PARAM_NAME,ASPECT_RATIO_PARAM_MIN,
				ASPECT_RATIO_PARAM_MAX,ASPECT_RATIO_PARAM_DEFAULT);
		aspectRatioParam.setInfo(ASPECT_RATIO_PARAM_INFO);

		ArrayList<String> floaterTypeOptions = new ArrayList<String>();
		floaterTypeOptions.add(FLOATER_TYPE_FULL_DDW);
		floaterTypeOptions.add(FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP);
		floaterTypeOptions.add(FLOATER_TYPE_CENTERED_DOWNDIP);
		floaterTypeParam = new StringParameter(FLOATER_TYPE_PARAM_NAME,floaterTypeOptions,
				FLOATER_TYPE_PARAM_DEFAULT);
		floaterTypeParam.setInfo(FLOATER_TYPE_PARAM_INFO);
		
		// --------------------------------------------------------------------------- SUBDUCTION FAULT SOURCES
		// Rupture offset
		sub_rupOffsetParam = new DoubleParameter(SUB_RUP_OFFSET_PARAM_NAME,SUB_RUP_OFFSET_PARAM_MIN,
				SUB_RUP_OFFSET_PARAM_MAX,SUB_RUP_OFFSET_PARAM_UNITS,SUB_RUP_OFFSET_DEFAULT);
		sub_rupOffsetParam.setInfo(SUB_RUP_OFFSET_PARAM_INFO);

		// Fault discretization parameter
		sub_faultDiscrParam = new DoubleParameter(SUB_FAULT_DISCR_PARAM_NAME,SUB_FAULT_DISCR_PARAM_MIN,
				SUB_FAULT_DISCR_PARAM_MAX,SUB_FAULT_DISCR_PARAM_UNITS,SUB_FAULT_DISCR_PARAM_DEFAULT);
		sub_faultDiscrParam.setInfo(SUB_FAULT_DISCR_PARAM_INFO);

		// create the mag-scaling relationship param
		ArrayList<String> sub_magScalingRelOptions = new ArrayList<String>();
		sub_magScalingRelOptions.add(WC1994_MagAreaRelationship.NAME);
		sub_magScalingRelOptions.add(WC1994_MagLengthRelationship.NAME);
		sub_magScalingRelOptions.add(PEER_testsMagAreaRelationship.NAME);
		sub_magScalingRelParam = new StringParameter(SUB_MAG_SCALING_REL_PARAM_NAME,sub_magScalingRelOptions,
				WC1994_MagAreaRelationship.NAME);
		sub_magScalingRelParam.setInfo(SUB_MAG_SCALING_REL_PARAM_INFO);

		// create the mag-scaling sigma param
		sub_sigmaParam = new DoubleParameter(SUB_SIGMA_PARAM_NAME,
				SUB_SIGMA_PARAM_MIN, SUB_SIGMA_PARAM_MAX, SUB_SIGMA_PARAM_DEFAULT);
		sub_sigmaParam.setInfo(SUB_SIGMA_PARAM_INFO);

		// create the aspect ratio param
		sub_aspectRatioParam = new DoubleParameter(SUB_ASPECT_RATIO_PARAM_NAME,SUB_ASPECT_RATIO_PARAM_MIN,
				SUB_ASPECT_RATIO_PARAM_MAX,SUB_ASPECT_RATIO_PARAM_DEFAULT);
		sub_aspectRatioParam.setInfo(SUB_ASPECT_RATIO_PARAM_INFO);

		ArrayList<String> sub_floaterTypeOptions = new ArrayList<String>();
		sub_floaterTypeOptions.add(SUB_FLOATER_TYPE_FULL_DDW);
		sub_floaterTypeOptions.add(SUB_FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP);
		sub_floaterTypeOptions.add(SUB_FLOATER_TYPE_CENTERED_DOWNDIP);
		sub_floaterTypeParam = new StringParameter(SUB_FLOATER_TYPE_PARAM_NAME,sub_floaterTypeOptions,
				SUB_FLOATER_TYPE_PARAM_DEFAULT);
		sub_floaterTypeParam.setInfo(SUB_FLOATER_TYPE_PARAM_INFO);

		// Add adjustable parameters to the list
		createParamList();

		// Add the change listener to parameters
		// -- Grid sources
		backSeisParam.addParameterChangeListener(this);  // 1 
		backSeisRupParam.addParameterChangeListener(this); // 2
		lowerSeisDepthParam.addParameterChangeListener(this); // 3
		magScalingRelBackgrParam.addParameterChangeListener(this); // 4
		// -- Fault sources
		rupOffsetParam.addParameterChangeListener(this); // 5 
		faultDiscrParam.addParameterChangeListener(this); // 6 
		aspectRatioParam.addParameterChangeListener(this); // 7
		floaterTypeParam.addParameterChangeListener(this); // 8
		magScalingRelParam.addParameterChangeListener(this); // 9
		// not sure - check later
		sigmaParam.addParameterChangeListener(this); // 10
		// -- Area sources
		areaDiscrParam.addParameterChangeListener(this); // 11
		areaSrcLowerSeisDepthParam.addParameterChangeListener(this); // 12
		areaSrcRupParam.addParameterChangeListener(this); // 13
		magScalingRelAreaSrcParam.addParameterChangeListener(this); // 14
		// -- Subduction sources
		sub_rupOffsetParam.addParameterChangeListener(this); // 15 
		sub_faultDiscrParam.addParameterChangeListener(this); // 16 
		sub_aspectRatioParam.addParameterChangeListener(this); // 17
		sub_floaterTypeParam.addParameterChangeListener(this); // 18
		sub_magScalingRelParam.addParameterChangeListener(this); // 19
		// not sure - check later
		sub_sigmaParam.addParameterChangeListener(this); // 20
	}
	
	// Make the adjustable parameters & the list
	private void initAdjParamsFromCalcSet(CalculationSettings calcSet) {

		// ---------------------------------------------------------------------------- GRID SOURCES
		ArrayList<String> backSeisOptionsStrings = new ArrayList<String>();
		backSeisOptionsStrings.add(BACK_SEIS_EXCLUDE);
		backSeisOptionsStrings.add(BACK_SEIS_INCLUDE);
		backSeisOptionsStrings.add(BACK_SEIS_ONLY);
		backSeisParam = new StringParameter(BACK_SEIS_NAME, backSeisOptionsStrings,BACK_SEIS_EXCLUDE);
	
		ArrayList<String> backSeisRupOptionsStrings = new ArrayList<String>();
		backSeisRupOptionsStrings.add(BACK_SEIS_RUP_POINT);
		backSeisRupOptionsStrings.add(BACK_SEIS_RUP_LINE);
		backSeisRupOptionsStrings.add(BACK_SEIS_RUP_CROSS_HAIR);
		backSeisRupOptionsStrings.add(BACK_SEIS_RUP_SPOKED);
		backSeisRupOptionsStrings.add(BACK_SEIS_RUP_FINITE_SURF);
		backSeisRupParam = new StringParameter(BACK_SEIS_RUP_NAME, backSeisRupOptionsStrings,calcSet.getErf().get(SourceType.GRID_SOURCE).get(GEM1ERF.BACK_SEIS_RUP_NAME).toString());

		lowerSeisDepthParam = new DoubleParameter(LOWER_SEIS_DEPTH_BACKGR_PARAM_NAME,LOWER_SEIS_DEPTH_BACKGR_PARAM_MIN,
				LOWER_SEIS_DEPTH_BACKGR_PARAM_MAX,LOWER_SEIS_DEPTH_BACKGR_PARAM_UNITS,(Double)calcSet.getErf().get(SourceType.GRID_SOURCE).get(GEM1ERF.LOWER_SEIS_DEPTH_BACKGR_PARAM_NAME));
		lowerSeisDepthParam.setInfo(LOWER_SEIS_DEPTH_BACKGR_PARAM_INFO);
		
		// Create the mag-scaling relationship param for griddes seismicity
		ArrayList<String> magScalingRelBackgrOptions = new ArrayList<String>();
		magScalingRelBackgrOptions.add(WC1994_MagAreaRelationship.NAME);
		magScalingRelBackgrOptions.add(WC1994_MagLengthRelationship.NAME);
		magScalingRelBackgrOptions.add(PEER_testsMagAreaRelationship.NAME);
		magScalingRelBackgrParam = new StringParameter(MAG_SCALING_REL_BACKGR_PARAM_NAME,magScalingRelBackgrOptions,
				calcSet.getErf().get(SourceType.GRID_SOURCE).get(GEM1ERF.MAG_SCALING_REL_BACKGR_PARAM_NAME).toString());
		magScalingRelBackgrParam.setInfo(MAG_SCALING_REL_BACKGR_PARAM_INFO);

		// ---------------------------------------------------------------------------- AREA SOURCES
		// Create the fault option parameter for area sources
		ArrayList<String> areaSeisRupOptionsStrings = new ArrayList<String>();
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_POINT);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_LINE);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_CROSS_HAIR);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_SPOKED);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_FINITE_SURF);
		areaSeisRupOptionsStrings.add(AREA_SRC_RUP_POINT_OLD);
		areaSrcRupParam = new StringParameter(AREA_SRC_RUP_NAME,areaSeisRupOptionsStrings,
				calcSet.getErf().get(SourceType.AREA_SOURCE).get(GEM1ERF.AREA_SRC_RUP_NAME).toString());
		
		// Create the mag-scaling relationship param for area sources
		ArrayList<String> magScalingRelAreaOptions = new ArrayList<String>();
		magScalingRelAreaOptions.add(WC1994_MagAreaRelationship.NAME);
		magScalingRelAreaOptions.add(WC1994_MagLengthRelationship.NAME);
		magScalingRelAreaOptions.add(PEER_testsMagAreaRelationship.NAME);
		magScalingRelAreaSrcParam = new StringParameter(MAG_SCALING_REL_AREA_SRC_PARAM_NAME,magScalingRelAreaOptions,
				calcSet.getErf().get(SourceType.AREA_SOURCE).get(GEM1ERF.MAG_SCALING_REL_AREA_SRC_PARAM_NAME).toString());
		magScalingRelAreaSrcParam.setInfo(MAG_SCALING_REL_AREA_SRC_PARAM_INFO);
		
		// Area lower seismogenic depth parameter
		areaSrcLowerSeisDepthParam = new DoubleParameter(LOWER_SEIS_DEPTH_AREA_SRC_PARAM_NAME,
				LOWER_SEIS_DEPTH_AREA_SRC_PARAM_MIN,
				LOWER_SEIS_DEPTH_AREA_SRC_PARAM_MAX,
				LOWER_SEIS_DEPTH_AREA_SRC_PARAM_UNITS,
				(Double)calcSet.getErf().get(SourceType.AREA_SOURCE).get(LOWER_SEIS_DEPTH_AREA_SRC_PARAM_NAME));
		areaSrcLowerSeisDepthParam.setInfo(LOWER_SEIS_DEPTH_BACKGR_PARAM_INFO);

		// Area discretization parameter
		areaDiscrParam = new DoubleParameter(AREA_DISCR_PARAM_NAME,AREA_DISCR_PARAM_MIN,
				AREA_DISCR_PARAM_MAX,AREA_DISCR_PARAM_UNITS,(Double)calcSet.getErf().get(SourceType.AREA_SOURCE).get(GEM1ERF.AREA_DISCR_PARAM_NAME));
		areaDiscrParam.setInfo(AREA_DISCR_PARAM_INFO);
		
		// --------------------------------------------------------------------------- FAULT SOURCES
		// Rupture offset
		rupOffsetParam = new DoubleParameter(RUP_OFFSET_PARAM_NAME,RUP_OFFSET_PARAM_MIN,
				RUP_OFFSET_PARAM_MAX,RUP_OFFSET_PARAM_UNITS,(Double)calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.RUP_OFFSET_PARAM_NAME));
		rupOffsetParam.setInfo(RUP_OFFSET_PARAM_INFO);

		// Fault discretization parameter
		faultDiscrParam = new DoubleParameter(FAULT_DISCR_PARAM_NAME,FAULT_DISCR_PARAM_MIN,
				FAULT_DISCR_PARAM_MAX,FAULT_DISCR_PARAM_UNITS,(Double)calcSet.getErf().get(SourceType.FAULT_SOURCE).get(FAULT_DISCR_PARAM_NAME));
		faultDiscrParam.setInfo(FAULT_DISCR_PARAM_INFO);

		// create the mag-scaling relationship param
		ArrayList<String> magScalingRelOptions = new ArrayList<String>();
		magScalingRelOptions.add(WC1994_MagAreaRelationship.NAME);
		magScalingRelOptions.add(WC1994_MagLengthRelationship.NAME);
		magScalingRelOptions.add(PEER_testsMagAreaRelationship.NAME);
		magScalingRelParam = new StringParameter(MAG_SCALING_REL_PARAM_NAME,magScalingRelOptions,
				calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.MAG_SCALING_REL_PARAM_NAME).toString());
		magScalingRelParam.setInfo(MAG_SCALING_REL_PARAM_INFO);

		// create the mag-scaling sigma param
		sigmaParam = new DoubleParameter(SIGMA_PARAM_NAME,
				SIGMA_PARAM_MIN, SIGMA_PARAM_MAX, (Double)calcSet.getErf().get(SourceType.FAULT_SOURCE).get(SIGMA_PARAM_NAME));
		sigmaParam.setInfo(SIGMA_PARAM_INFO);

		// create the aspect ratio param
		aspectRatioParam = new DoubleParameter(ASPECT_RATIO_PARAM_NAME,ASPECT_RATIO_PARAM_MIN,
				ASPECT_RATIO_PARAM_MAX,(Double)calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.ASPECT_RATIO_PARAM_NAME));
		aspectRatioParam.setInfo(ASPECT_RATIO_PARAM_INFO);

		ArrayList<String> floaterTypeOptions = new ArrayList<String>();
		floaterTypeOptions.add(FLOATER_TYPE_FULL_DDW);
		floaterTypeOptions.add(FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP);
		floaterTypeOptions.add(FLOATER_TYPE_CENTERED_DOWNDIP);
		floaterTypeParam = new StringParameter(FLOATER_TYPE_PARAM_NAME,floaterTypeOptions,
				calcSet.getErf().get(SourceType.FAULT_SOURCE).get(GEM1ERF.FLOATER_TYPE_PARAM_NAME).toString());
		floaterTypeParam.setInfo(FLOATER_TYPE_PARAM_INFO);
		
		// --------------------------------------------------------------------------- SUBDUCTION FAULT SOURCES
		// Rupture offset
		sub_rupOffsetParam = new DoubleParameter(SUB_RUP_OFFSET_PARAM_NAME,SUB_RUP_OFFSET_PARAM_MIN,
				SUB_RUP_OFFSET_PARAM_MAX,SUB_RUP_OFFSET_PARAM_UNITS,(Double)calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_RUP_OFFSET_PARAM_NAME));
		sub_rupOffsetParam.setInfo(SUB_RUP_OFFSET_PARAM_INFO);

		// Fault discretization parameter
		sub_faultDiscrParam = new DoubleParameter(SUB_FAULT_DISCR_PARAM_NAME,SUB_FAULT_DISCR_PARAM_MIN,
				SUB_FAULT_DISCR_PARAM_MAX,SUB_FAULT_DISCR_PARAM_UNITS,(Double)calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_FAULT_DISCR_PARAM_NAME));
		sub_faultDiscrParam.setInfo(SUB_FAULT_DISCR_PARAM_INFO);

		// create the mag-scaling relationship param
		ArrayList<String> sub_magScalingRelOptions = new ArrayList<String>();
		sub_magScalingRelOptions.add(WC1994_MagAreaRelationship.NAME);
		sub_magScalingRelOptions.add(WC1994_MagLengthRelationship.NAME);
		sub_magScalingRelOptions.add(PEER_testsMagAreaRelationship.NAME);
		sub_magScalingRelParam = new StringParameter(SUB_MAG_SCALING_REL_PARAM_NAME,sub_magScalingRelOptions,
				calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_MAG_SCALING_REL_PARAM_NAME).toString());
		sub_magScalingRelParam.setInfo(SUB_MAG_SCALING_REL_PARAM_INFO);

		// create the mag-scaling sigma param
		sub_sigmaParam = new DoubleParameter(SUB_SIGMA_PARAM_NAME,
				SUB_SIGMA_PARAM_MIN, SUB_SIGMA_PARAM_MAX, (Double)calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_SIGMA_PARAM_NAME));
		sub_sigmaParam.setInfo(SUB_SIGMA_PARAM_INFO);

		// create the aspect ratio param
		sub_aspectRatioParam = new DoubleParameter(SUB_ASPECT_RATIO_PARAM_NAME,SUB_ASPECT_RATIO_PARAM_MIN,
				SUB_ASPECT_RATIO_PARAM_MAX,(Double)calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_ASPECT_RATIO_PARAM_NAME));
		sub_aspectRatioParam.setInfo(SUB_ASPECT_RATIO_PARAM_INFO);

		ArrayList<String> sub_floaterTypeOptions = new ArrayList<String>();
		sub_floaterTypeOptions.add(SUB_FLOATER_TYPE_FULL_DDW);
		sub_floaterTypeOptions.add(SUB_FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP);
		sub_floaterTypeOptions.add(SUB_FLOATER_TYPE_CENTERED_DOWNDIP);
		sub_floaterTypeParam = new StringParameter(SUB_FLOATER_TYPE_PARAM_NAME,sub_floaterTypeOptions,
				calcSet.getErf().get(SourceType.SUBDUCTION_FAULT_SOURCE).get(GEM1ERF.SUB_FLOATER_TYPE_PARAM_NAME).toString());
		sub_floaterTypeParam.setInfo(SUB_FLOATER_TYPE_PARAM_INFO);

		// Add adjustable parameters to the list
		createParamList();

		// Add the change listener to parameters
		// -- Grid sources
		backSeisParam.addParameterChangeListener(this);  // 1 
		backSeisRupParam.addParameterChangeListener(this); // 2
		lowerSeisDepthParam.addParameterChangeListener(this); // 3
		magScalingRelBackgrParam.addParameterChangeListener(this); // 4
		// -- Fault sources
		rupOffsetParam.addParameterChangeListener(this); // 5 
		faultDiscrParam.addParameterChangeListener(this); // 6 
		aspectRatioParam.addParameterChangeListener(this); // 7
		floaterTypeParam.addParameterChangeListener(this); // 8
		magScalingRelParam.addParameterChangeListener(this); // 9
		// not sure - check later
		sigmaParam.addParameterChangeListener(this); // 10
		// -- Area sources
		areaDiscrParam.addParameterChangeListener(this); // 11
		areaSrcLowerSeisDepthParam.addParameterChangeListener(this); // 12
		areaSrcRupParam.addParameterChangeListener(this); // 13
		magScalingRelAreaSrcParam.addParameterChangeListener(this); // 14
		// -- Subduction sources
		sub_rupOffsetParam.addParameterChangeListener(this); // 15 
		sub_faultDiscrParam.addParameterChangeListener(this); // 16 
		sub_aspectRatioParam.addParameterChangeListener(this); // 17
		sub_floaterTypeParam.addParameterChangeListener(this); // 18
		sub_magScalingRelParam.addParameterChangeListener(this); // 19
		// not sure - check later
		sub_sigmaParam.addParameterChangeListener(this); // 20
	}


	/**
	 * This put parameters in the ParameterList (depending on settings).
	 * This could be smarter in terms of not showing parameters if certain
	 * GEMSourceData subclasses are not passed in.
	 */
	private void createParamList() {

		adjustableParams = new ParameterList();

		// add adjustable parameters to the list
		adjustableParams.addParameter(backSeisParam);
		
		if(!backSeisParam.getValue().equals(BACK_SEIS_EXCLUDE)) {
			adjustableParams.addParameter(backSeisRupParam);
			if(!backSeisRupParam.getValue().equals(BACK_SEIS_RUP_POINT)) {
				adjustableParams.addParameter(magScalingRelBackgrParam);
				MagScalingRelationship magScRel = getmagScalingRelationship(magScalingRelBackgrParam.getValue());
				if(backSeisRupParam.getValue().equals(BACK_SEIS_RUP_FINITE_SURF) || (magScRel instanceof MagAreaRelationship)) {
					adjustableParams.addParameter(lowerSeisDepthParam);
				}
			}
		}
		adjustableParams.addParameter(areaSrcRupParam);
		adjustableParams.addParameter(areaSrcLowerSeisDepthParam);
		adjustableParams.addParameter(areaDiscrParam);
		adjustableParams.addParameter(faultDiscrParam);
		adjustableParams.addParameter(rupOffsetParam);
		adjustableParams.addParameter(aspectRatioParam);
		adjustableParams.addParameter(floaterTypeParam);
		adjustableParams.addParameter(magScalingRelParam);
		adjustableParams.addParameter(magScalingRelAreaSrcParam);
		adjustableParams.addParameter(sigmaParam);
		adjustableParams.addParameter(sub_faultDiscrParam);
		adjustableParams.addParameter(sub_rupOffsetParam);
		adjustableParams.addParameter(sub_aspectRatioParam);
		adjustableParams.addParameter(sub_floaterTypeParam);
		adjustableParams.addParameter(sub_magScalingRelParam);
		adjustableParams.addParameter(sub_sigmaParam);
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
	                magScalingRel,					// MagScalingRelationship
	                this.sigmaValue,				// sigma of the mag-scaling relationship
	                this.aspectRatioValue,			// floating rupture aspect ration (length/width)
	                this.rupOffsetValue,			// floating rupture offset
	                gemFaultSourceData.getRake(),	// average rake of the ruptures
	                duration,						// duration of forecast
	                MINMAG,							// minimum mag considered (probs of those lower set to zero regardless of MFD)
	                floaterTypeFlag,				// type of floater (0 for full DDW, 1 for floating both ways, and 2 for floating down center)
	                12.0);  						// mags >= to this forced to be full fault ruptures (set as high value for now)
			
		}
		else{
			
			 src = new FloatingPoissonFaultSource(
					gemFaultSourceData.getMfd(),	//IncrementalMagFreqDist
	                faultSurface,					//EvenlyGriddedSurface			
	                magScalingRel,					// MagScalingRelationship
	                this.sigmaValue,				// sigma of the mag-scaling relationship
	                this.aspectRatioValue,			// floating rupture aspect ration (length/width)
	                this.rupOffsetValue,			// floating rupture offset
	                gemFaultSourceData.getRake(),	// average rake of the ruptures
	                duration,						// duration of forecast
	                MINMAG,							// minimum mag considered (probs of those lower set to zero regardless of MFD)
	                floaterTypeFlag,				// type of floater (0 for full DDW, 1 for floating both ways, and 2 for floating down center)
	                0.0);  						// mags >= to this forced to be full fault ruptures (set as high value for now)
			
		}
		

		src.setTectonicRegionType(gemFaultSourceData.getTectReg());
		return src;
	}
	
	
	protected ProbEqkSource mkSubductionSource(GEMSubductionFaultSourceData gemSubductFaultSourceData) {
		
		ApproxEvenlyGriddedSurface faultSurface = new ApproxEvenlyGriddedSurface(
				gemSubductFaultSourceData.getTopTrace(),
				gemSubductFaultSourceData.getBottomTrace(),
                sub_faultDiscrValue);
		
		FloatingPoissonFaultSource src = null;
		
		if(gemSubductFaultSourceData.getFloatRuptureFlag()){
			
			src = new FloatingPoissonFaultSource(
					gemSubductFaultSourceData.getMfd(),	//IncrementalMagFreqDist
	                faultSurface,					//EvenlyGriddedSurface			
	                sub_magScalingRel,					// MagScalingRelationship
	                this.sub_sigmaValue,				// sigma of the mag-scaling relationship
	                this.sub_aspectRatioValue,			// floating rupture aspect ration (length/width)
	                this.sub_rupOffsetValue,			// floating rupture offset
	                gemSubductFaultSourceData.getRake(),	// average rake of the ruptures
	                sub_duration,						// duration of forecast
	                MINMAG,							// minimum mag considered (probs of those lower set to zero regardless of MFD)
	                sub_floaterTypeFlag,					// type of floater (0 for full DDW, 1 for floating both ways, and 2 for floating down center)
	                12.0);  						// mags >= to this forced to be full fault ruptures (set as high value for now)
			
		}
		else{
			
			src = new FloatingPoissonFaultSource(
					gemSubductFaultSourceData.getMfd(),	//IncrementalMagFreqDist
	                faultSurface,					//EvenlyGriddedSurface			
	                sub_magScalingRel,					// MagScalingRelationship
	                this.sub_sigmaValue,				// sigma of the mag-scaling relationship
	                this.sub_aspectRatioValue,			// floating rupture aspect ration (length/width)
	                this.sub_rupOffsetValue,			// floating rupture offset
	                gemSubductFaultSourceData.getRake(),	// average rake of the ruptures
	                sub_duration,						// duration of forecast
	                MINMAG,							// minimum mag considered (probs of those lower set to zero regardless of MFD)
	                sub_floaterTypeFlag,					// type of floater (0 for full DDW, 1 for floating both ways, and 2 for floating down center)
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
//		if (areaSrcRupValue.equals(AREA_SRC_RUP_POINT)){
			// Point sources 
//			PoissonAreaSource src = new PoissonAreaSource(areaSourceData.getRegion(),AREA_DISCR_PARAM_DEFAULT,
//					areaSourceData.getMagfreqDistFocMech(),areaSourceData.getAveRupTopVsMag(),
//					areaSourceData.getAveHypoDepth(),duration,MINMAG);
//			src.setTectonicRegionType(areaSourceData.getTectReg());
//			return src;
//		} else if (areaSrcRupValue.equals(AREA_SRC_RUP_LINE)) {
//			// Finite ruptures 
//			PoissonAreaSource src = new PoissonAreaSource(areaSourceData.getRegion(),AREA_DISCR_PARAM_DEFAULT,
//					areaSourceData.getMagfreqDistFocMech(),areaSourceData.getAveRupTopVsMag(),
//					areaSourceData.getAveHypoDepth(),magScalingRelArea,lowerSeisDepthValue,
//					duration,MINMAG);
//			src.setTectonicRegionType(areaSourceData.getTectReg());
//			return src;
//		} else if (areaSrcRupValue.equals(AREA_SRC_RUP_CROSS_HAIR)) {
//			PoissonAreaSource src = new PoissonAreaSource(areaSourceData.getRegion(),AREA_DISCR_PARAM_DEFAULT,
//					areaSourceData.getMagfreqDistFocMech(),areaSourceData.getAveRupTopVsMag(),
//					areaSourceData.getAveHypoDepth(),magScalingRelArea,lowerSeisDepthValue,
//					duration,MINMAG,2,0);
//			src.setTectonicRegionType(areaSourceData.getTectReg());
//			return src;
//		} else if (areaSrcRupValue.equals(AREA_SRC_RUP_SPOKED)) {
//			PoissonAreaSource src = new PoissonAreaSource(areaSourceData.getRegion(),AREA_DISCR_PARAM_DEFAULT,
//					areaSourceData.getMagfreqDistFocMech(),areaSourceData.getAveRupTopVsMag(),
//					areaSourceData.getAveHypoDepth(),magScalingRelArea,lowerSeisDepthValue,
//					duration,MINMAG,16,0);
//			src.setTectonicRegionType(areaSourceData.getTectReg());
//			return src;
//		} else if(areaSrcRupValue.equals(AREA_SRC_RUP_FINITE_SURF)) {
//			throw new RuntimeException(NAME+" - "+AREA_SRC_RUP_FINITE_SURF+ " is not yet implemented");
//		}  else if(areaSrcRupValue.equals(AREA_SRC_RUP_POINT_OLD)) {
	  		GriddedRegion gridReg = new GriddedRegion(areaSourceData.getRegion(),this.areaDiscrValue,null); 
	  		
	  		// create source
	    	GriddedRegionPoissonEqkSource src = new GriddedRegionPoissonEqkSource(gridReg,areaSourceData.getMagfreqDistFocMech().getFirstMagFreqDist(),
	    			                                   duration,areaSourceData.getMagfreqDistFocMech().getFirstFocalMech().getRake(),
	    			                                   areaSourceData.getMagfreqDistFocMech().getFirstFocalMech().getDip(),
	    			                                   areaSourceData.getAveHypoDepth(),MINMAG);
	    	src.setTectonicRegionType(areaSourceData.getTectReg());
	    	  
		    return src;
//	    } else
//		    throw new RuntimeException(NAME+" - Unsupported area source rupture type");

	}	
	
	/**
	 * 
	 * @param gridSourceData
	 * @return ProbEqkSource
	 */
	protected ProbEqkSource mkGridSource(GEMPointSourceData gridSourceData) {

		if(backSeisRupValue.equals(BACK_SEIS_RUP_POINT)) {
			PointEqkSource src = new PointEqkSource(gridSourceData.getHypoMagFreqDistAtLoc(),
					gridSourceData.getAveRupTopVsMag(), 
					gridSourceData.getAveHypoDepth(),
					duration, MINMAG);
			src.setTectonicRegionType(gridSourceData.getTectReg());
			return src;
		}
		else if(backSeisRupValue.equals(BACK_SEIS_RUP_LINE)) {
			PointToLineSource src = new PointToLineSource(gridSourceData.getHypoMagFreqDistAtLoc(),
					gridSourceData.getAveRupTopVsMag(), 
					gridSourceData.getAveHypoDepth(),
					magScalingRelBackgr,
					lowerSeisDepthValue, 
					duration, MINMAG);
			src.setTectonicRegionType(gridSourceData.getTectReg());
			return src;
		}
		else if(backSeisRupValue.equals(BACK_SEIS_RUP_CROSS_HAIR)) {
			PointToLineSource src = new PointToLineSource(gridSourceData.getHypoMagFreqDistAtLoc(),
					gridSourceData.getAveRupTopVsMag(), 
					gridSourceData.getAveHypoDepth(),
					magScalingRelBackgr,
					lowerSeisDepthValue, 
					duration, MINMAG,
					2, 0);
			src.setTectonicRegionType(gridSourceData.getTectReg());
			return src;
		}
		else if(backSeisRupValue.equals(BACK_SEIS_RUP_SPOKED)) {
			PointToLineSource src = new PointToLineSource(gridSourceData.getHypoMagFreqDistAtLoc(),
					gridSourceData.getAveRupTopVsMag(), 
					gridSourceData.getAveHypoDepth(),
					magScalingRelBackgr,
					lowerSeisDepthValue, 
					duration, MINMAG,
					16, 0);
			src.setTectonicRegionType(gridSourceData.getTectReg());
			return src;
		}
		else if(backSeisRupValue.equals(BACK_SEIS_RUP_FINITE_SURF)) {
			throw new RuntimeException(NAME+" - "+BACK_SEIS_RUP_FINITE_SURF+ " is not yet implemented");
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

		GEMSourceData srcData = gemSourceDataList.get(iSource);
		if(srcData instanceof GEMFaultSourceData)
			return mkFaultSource((GEMFaultSourceData)srcData);
		else if (srcData instanceof GEMSubductionFaultSourceData)
			return mkSubductionSource((GEMSubductionFaultSourceData)srcData);
		else if (srcData instanceof GEMPointSourceData)
			return mkGridSource((GEMPointSourceData)srcData);
		else if (srcData instanceof GEMAreaSourceData)
			return mkAreaSource((GEMAreaSourceData)srcData);
		else
			throw new RuntimeException(NAME+": "+srcData.getClass()+" not yet supported");
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
			areaSrcRupValue = areaSrcRupParam.getValue();
			areaSrcLowerSeisDepthValue = areaSrcLowerSeisDepthParam.getValue();
			areaDiscrValue = areaDiscrParam.getValue();
			magScalingRelArea = getmagScalingRelationship(magScalingRelAreaSrcParam.getValue());
			
			// ------------------------------------------------------------------------- GRID SOURCE
			backSeisValue = backSeisParam.getValue();
			backSeisRupValue = backSeisRupParam.getValue();
			lowerSeisDepthValue = lowerSeisDepthParam.getValue();
			magScalingRelBackgr = getmagScalingRelationship(magScalingRelBackgrParam.getValue());

			// ------------------------------------------------------------------------ FAULT SOURCE
			rupOffsetValue = rupOffsetParam.getValue();
			faultDiscrValue = faultDiscrParam.getValue();
			magScalingRel = getmagScalingRelationship(magScalingRelParam.getValue());
			sigmaValue = sigmaParam.getValue();
			aspectRatioValue = aspectRatioParam.getValue();
			String floaterTypeName = floaterTypeParam.getValue();
			if(floaterTypeName.equals(this.FLOATER_TYPE_FULL_DDW)) 
				floaterTypeFlag = 0;
			else if(floaterTypeName.equals(this.FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP)) 
				floaterTypeFlag = 1;
			else // (floaterTypeName.equals(this.FLOATER_TYPE_CENTERED_DOWNDIP)) 
				floaterTypeFlag = 2;
			duration = timeSpan.getDuration();
			
			// ------------------------------------------------------------------------ SUBDUCTION FAULT SOURCE
			sub_rupOffsetValue = sub_rupOffsetParam.getValue();
			sub_faultDiscrValue = sub_faultDiscrParam.getValue();
			sub_magScalingRel = getmagScalingRelationship(sub_magScalingRelParam.getValue());
			sub_sigmaValue = sub_sigmaParam.getValue();
			sub_aspectRatioValue = sub_aspectRatioParam.getValue();
			String sub_floaterTypeName = sub_floaterTypeParam.getValue();
			if(sub_floaterTypeName.equals(this.SUB_FLOATER_TYPE_FULL_DDW)) 
				sub_floaterTypeFlag = 0;
			else if(sub_floaterTypeName.equals(this.SUB_FLOATER_TYPE_ALONG_STRIKE_AND_DOWNDIP)) 
				sub_floaterTypeFlag = 1;
			else // (floaterTypeName.equals(this.FLOATER_TYPE_CENTERED_DOWNDIP)) 
				sub_floaterTypeFlag = 2;
			sub_duration = timeSpan.getDuration();
			
			

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

		// recreate the parameter list if any of the following were modified
		if(paramName.equals(BACK_SEIS_NAME) || paramName.equals(BACK_SEIS_RUP_NAME) || 
				paramName.equals(MAG_SCALING_REL_BACKGR_PARAM_NAME)){
			createParamList();
		}
		parameterChangeFlag = true;

	}

	// this is temporary for testing purposes
	public static void main(String[] args) {

	}
	/**
	 * This method provides a list of ruptures for source sourceId with a magnitude 
	 * comprised between a lower and an upper threshold 
	 *
	 * @param sourceId			Index of the source
	 * @param mMin				Minimum value of magnitude
	 * @return rupList			List of ruptures with magnitude in a given interval
	 */		
	public ArrayList<ProbEqkRupture> getRupturesMag(int sourceId,double mMin, double mMax) {
		ProbEqkSource prbSrc = (ProbEqkSource) this.getSource(sourceId);
		ArrayList<ProbEqkRupture> rupList = new ArrayList<ProbEqkRupture>();
		
		Iterator<ProbEqkRupture> iter = prbSrc.getRupturesIterator(); 
		while (iter.hasNext()) {
			// Get rupture
			ProbEqkRupture rup = iter.next();
			// Add the rupture to the list 
			if (rup.getMag() >= mMin && rup.getMag() < mMax) rupList.add(rup);
		}
		return rupList;
	}

}

