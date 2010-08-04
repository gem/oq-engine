/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final;


import java.util.ArrayList;
import java.util.EventObject;
import java.util.Iterator;

import org.opensha.commons.calc.FaultMomentCalc;
import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Ellsworth_A_WG02_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Ellsworth_B_WG02_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.HanksBakun2002_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Shaw_2007_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Somerville_2006_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WGCEP_2007_PowLaw_MagAreaRel;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.ValueWeight;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.ParameterListParameter;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.refFaultParamDb.vo.DeformationModelSummary;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FaultRuptureSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.A_Faults.A_FaultSegmentedSourceGenerator;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.A_FaultsFetcher;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.B_FaultsFetcher;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.EventRates;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.NonCA_FaultsFetcher;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelSummaryFinal;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.griddedSeis.NSHMP_GridSourceGenerator;
import org.opensha.sha.magdist.ArbIncrementalMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;
import org.opensha.sha.magdist.TaperedGR_MagFreqDist;


/**
 * @author 
 *
 */
public class UCERF2 extends EqkRupForecast {
	//for Debug purposes
	private static String  C = new String("EqkRateModel2_ERF");
	private boolean D = true;

	// name of this ERF
	public final static String NAME = new String("WGCEP Eqk Rate Model 2 ERF");

//	ArrayList allSourceNames;

	public final static double MIN_MAG = 5.05;
	public final static double MAX_MAG = 8.95;
	public final static double DELTA_MAG = 0.1;
	public final static int NUM_MAG = (int)Math.round((MAX_MAG-MIN_MAG)/DELTA_MAG) + 1;

	// public final static double B_FAULT_GR_MAG_LOWER = 6.5;
	public final static double BACKGROUND_MAG_LOWER = 5.0;
	
	// Fault Grid Spacing
	public final static double GRID_SPACING = 1;
	public final static double RUP_OFFSET = 5;


	public final static double BACK_SEIS_DEPTH = 5.0;

	// this is the moment rate taken from A, B, and C sources and put into background seismicity
	private double totMoRateReduction;

	// various summed MFDs
	private SummedMagFreqDist bFaultCharSummedMFD, bFaultGR_SummedMFD, aFaultSummedMFD, cZoneSummedMFD, nonCA_B_FaultsSummedMFD;
	private IncrementalMagFreqDist totBackgroundMFD;
	private ArrayList<IncrementalMagFreqDist>  cZonesMFD_List;

	/*
	 * Static variables for input files
	 */
	//private final static String IN_FILE_PATH = "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/WEB-INF/dataFiles/frankel02_inputfiles/";
	private final static String IN_FILE_PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_Final/";
	public final static String NON_CA_SOURCES_FILENAME = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_Final/data/NearCA_NSHMP/NonCA_Faults.txt";
	
	private ArrayList allSources;

	// background seismicity inlcude/exclude param
	public final static String BACK_SEIS_NAME = new String ("Background Seismicity");
	public final static String BACK_SEIS_INCLUDE = new String ("Include");
	public final static String BACK_SEIS_EXCLUDE = new String ("Exclude");
	public final static String BACK_SEIS_ONLY = new String ("Only Background");
	public final static String BACK_SEIS_DEFAULT = BACK_SEIS_INCLUDE;
	private ArrayList backSeisOptionsStrings = new ArrayList();
	private StringParameter backSeisParam;

	// background seismicity treated as param
	public final static String BACK_SEIS_RUP_NAME = new String ("Treat Background Seismicity As");
	public final static String BACK_SEIS_RUP_POINT = new String ("Point Sources");
	public final static String BACK_SEIS_RUP_FINITE = new String ("One Random Strike Fault");
	public final static String BACK_SEIS_RUP_CROSSHAIR = new String ("Two perpendicular faults");
	public final static String BACK_SEIS_RUP_DEFAULT = BACK_SEIS_RUP_CROSSHAIR;
	private ArrayList backSeisRupStrings = new ArrayList();
	private StringParameter backSeisRupParam;

	// background seismicity max-mag param
	public final static String BACK_SEIS_MAG_NAME = "Backgroud Seis Mmax";
	public final static Double BACK_SEIS_MAG_MIN = new Double(5.0);
	public final static Double BACK_SEIS_MAG_MAX = new Double(9.0);
	public final static Double BACK_SEIS_MAG_DEFAULT = new Double(7.0);
	private final static String BACK_SEIS_MAG_INFO = "Maximum Magnitude for background seismicity";
	private DoubleParameter backSeisMaxMagParam ;

	// For rupture offset lenth along fault parameter
	public final static String RUP_OFFSET_PARAM_NAME ="Rupture Offset";
	private Double DEFAULT_RUP_OFFSET_VAL= new Double(10);
	private final static String RUP_OFFSET_PARAM_UNITS = "km";
	private final static String RUP_OFFSET_PARAM_INFO = "Length of offset for floating ruptures";
	public final static double RUP_OFFSET_PARAM_MIN = 1;
	public final static double RUP_OFFSET_PARAM_MAX = 100;
	private DoubleParameter rupOffset_Param;
	
	// Floater Type
	public final static String FLOATER_TYPE_PARAM_NAME = "Floater Type";
	public final static String FULL_DDW_FLOATER = "Only along strike ( rupture full DDW)";
	public final static String STRIKE_AND_DOWNDIP_FLOATER = "Along strike and down dip";
	public final static String CENTERED_DOWNDIP_FLOATER = "Along strike & centered down dip";
	public final static String FLOATER_TYPE_PARAM_DEFAULT = CENTERED_DOWNDIP_FLOATER;
	private StringParameter floaterTypeParam;
	
	// rate for M>=5
	public final static String TOT_MAG_RATE_PARAM_NAME = "Total M�5 Rate";
	public final static Double TOT_MAG_RATE_MIN = new Double(2.0);
	public final static Double TOT_MAG_RATE_MAX = new Double(20.0);
	public final static Double TOT_MAG_RATE_DEFAULT = new Double(3.6);
	private final static String TOT_MAG_RATE_INFO = "Total rate of M�5 events in the RELM test region (e.g, 3.60 for no aftershocks, or 7.84 including aftershocks)";
	private DoubleParameter totalMagRateParam ;

	// Aftershock/Foreshock Fraction
	public final static String AFTERSHOCK_FRACTION_PARAM_NAME = "Fraction Smaller Events & Aftershocks";
	public final static Double AFTERSHOCK_FRACTION_MIN = new Double(0.0);
	public final static Double AFTERSHOCK_FRACTION_MAX = new Double(1.0);
	public final static Double AFTERSHOCK_FRACTION_DEFAULT = new Double(0.1);
	private final static String AFTERSHOCK_FRACTION_INFO = "Fraction of moment rate released in foreshocks and aftershocks";
	private DoubleParameter aftershockFractionParam ;

	// Coupling Coefficient
	public final static String COUPLING_COEFF_PARAM_NAME = "Coupling Coefficient";
	public final static Double COUPLING_COEFF_MIN = new Double(0.0);
	public final static Double COUPLING_COEFF_MAX = new Double(1.0);
	public final static Double COUPLING_COEFF_DEFAULT = new Double(1.0);
	private final static String COUPLING_COEFF_INFO = "Fraction of moment rate on A & B faults released via seismogenic processes (e.g., excluding afterslip)";
	private DoubleParameter couplingCoeffParam ;

	//choose mag area relationship
	public final static String MAG_AREA_RELS_PARAM_NAME = "Mag-Area Relationship";
	private final static String MAG_AREA_RELS_PARAM_INFO = "Mag-Area Relationship for computing mean mag from area or vice versa";
	private StringParameter magAreaRelParam;
	private ArrayList magAreaRelationships;

	// choose deformation model
	public final static String DEFORMATION_MODEL_PARAM_NAME = "Deformation Model";
	private final static String DEFORMATION_MODEL_PARAM_INFO = "D2.1 to D2.3 use Fault Model 2.1, and D2.4 to D2.6 use Fault Model 2.2";
	private StringParameter deformationModelsParam;
	private DeformationModelSummaryFinal deformationModelSummaryFinal = new DeformationModelSummaryFinal();
	private ArrayList<DeformationModelSummary> deformationModelSummariesList;

	// aseismic factor interpolated
	public final static String ASEIS_INTER_PARAM_NAME = "Aseis Factor Reduces Area?";
	private final static String ASEIS_INTER_PARAM_INFO = "Otherwise it reduces slip rate";
	private BooleanParameter aseisFactorInterParam; 

	/*	
	// constrain A-fault segment rates boolean
	public final static String CONSTRAIN_A_SEG_RATES_PARAM_NAME = "Constrain Segment Rates?";
	private final static String CONSTRAIN_A_SEG_RATES_PARAM_INFO = "Constrain A-fault segments rates (add equations to inversion)";
	private BooleanParameter constrainA_SegRatesParam; 
	 */
	// relative a-priori weights (CHANGE NAME TO REMOVE "REL")
	public final static String REL_A_PRIORI_WT_PARAM_NAME = "Wt On A-Priori Rates";
	private final static Double REL_A_PRIORI_WT_PARAM_MIN = new Double(0.0);
	private final static Double REL_A_PRIORI_WT_PARAM_MAX = new Double(Double.MAX_VALUE);
	private final static Double REL_A_PRIORI_WT_PARAM_DEFAULT = new Double(1e-4);
	private final static String REL_A_PRIORI_WT_PARAM_INFO = "Applied as rate/uncert (this is important to understand!)";
	private DoubleParameter relativeA_PrioriWeightParam; 

	// relative segment rate weights
	public final static String REL_SEG_RATE_WT_PARAM_NAME = "Relative Wt On Segment Rates";
	private final static Double REL_SEG_RATE_WT_PARAM_MIN = new Double(0);
	private final static Double REL_SEG_RATE_WT_PARAM_MAX = new Double(Double.MAX_VALUE);
	public final static Double REL_SEG_RATE_WT_PARAM_DEFAULT = new Double(0);
	private final static String REL_SEG_RATE_WT_PARAM_INFO = "Relative to that put on the sement slip rates";
	private DoubleParameter relativeSegRateWeightParam; 

	// connect more B-Faults boolean
	public final static String CONNECT_B_FAULTS_PARAM_NAME = "Connect More B Faults?";
	private final static String CONNECT_B_FAULTS_PARAM_INFO = "Connect nearby B-Faults";
	private BooleanParameter connectMoreB_FaultsParam;

	// A-fault rupture model seg vs unseg type
	public final static String RUP_MODEL_TYPE_NAME = "A-Fault Solution Type";
	public final static String RUP_MODEL_TYPE_INFO = "The type of solution to apply for all A-Fault Sources";
	public final static String UNSEGMENTED_A_FAULT_MODEL = "Unsegmented Model";
	public final static String SEGMENTED_A_FAULT_MODEL = "Segmented Model";
	private StringParameter rupModelParam;

	//	 rupture model type
	public final static String SEGMENTED_RUP_MODEL_TYPE_NAME = "Segmented A-Fault Solution Types";
	public final static String SEGMENTED_RUP_MODEL_TYPE_INFO = "To set the a-prior solution for each type-A Fault Source";
	private ParameterListParameter segmentedRupModelParam;

	// min rate param 1
	public final static String MIN_A_FAULT_RATE_1_PARAM_NAME = "Min Fraction for Unknown Ruptures";
	private final static Double MIN_A_FAULT_RATE_MIN = new Double(0.0);
	private final static Double MIN_A_FAULT_RATE_MAX = new Double(1.0);
	public final static Double MIN_A_FAULT_RATE_1_DEFAULT = new Double(0.5);
	private final static String MIN_A_FAULT_RATE_1_INFO = "The min rate for unknown ruptures, defined as fraction of min non-zero a-priori rate";
	private DoubleParameter minA_FaultRate1Param;

	// min rate param 2
	public final static String MIN_A_FAULT_RATE_2_PARAM_NAME = "Min Fraction for Unlikely Ruptures";
	public final static Double MIN_A_FAULT_RATE_2_DEFAULT = new Double(0.1);
	private final static String MIN_A_FAULT_RATE_2_INFO = "The min rate for unlikely ruptures, defined as fraction of min non-zero a-priori rate";
	private DoubleParameter minA_FaultRate2Param;
	/*
	// preserve minimum A-fault rates param
	public final static String PRESERVE_MIN_A_FAULT_RATE_PARAM_NAME = "Preserve Min A Fault Rates?";
	private final static String PRESERVE_MIN_A_FAULT_RATE_PARAM_INFO = "This will prevent rates from being lower than the minimum in the a-priori model";
	private BooleanParameter preserveMinAFaultRateParam;
	 */
	// weighted inversion param
	public final static String WEIGHTED_INVERSION_PARAM_NAME = "Weighted Inversion?";
	private final static String WEIGHTED_INVERSION_PARAM_INFO = "Use segment rate and slip rate uncertainties to weight the inversion";
	private BooleanParameter weightedInversionParam;

	//	 A-fault slip-model type
	public final static String SLIP_MODEL_TYPE_NAME = "A-Fault Slip Model";
	public final static String SLIP_MODEL_TYPE_INFO = "Type of slip on a segment for each rupture on all A-Fault Sources";
	private StringParameter slipModelParam;

	// % char vs GR param
	public final static String CHAR_VS_GR_PARAM_NAME = "% Char vs GR";
	private final static Double CHAR_VS_GR_MIN = new Double(.0);
	private final static Double CHAR_VS_GR_MAX = new Double(100.0);
	private final static Double CHAR_VS_GR_DEFAULT = new Double(67.0);
	private final static String CHAR_VS_GR_INFO = "The % moment rate put into characteristic (vs GR) events on B-Faults (and A-Faults for un-segmented option)";
	private DoubleParameter percentCharVsGRParam; 

	// char mag sigma >=0 and <=1
	public final static String MAG_SIGMA_PARAM_NAME = "Mag Sigma";
	private final static Double MAG_SIGMA_MIN = new Double(0.0);
	private final static Double MAG_SIGMA_MAX = new Double(1.0);
	public final static Double MAG_SIGMA_DEFAULT = new Double(0.12);
	private final static String MAG_SIGMA_INFO = "Standard Deviation for characteristic MFD";
	private DoubleParameter magSigmaParam;

	// Char mag trunc level (units is number of sigmas) >=0 and <=6
	// Mag truncation level
	public final static String TRUNC_LEVEL_PARAM_NAME = "Truncation Level";
	private final static String TRUNC_LEVEL_PARAM_UNITS = "Number of sigmas";
	private final static Double TRUNC_LEVEL_MIN = new Double(0.0);
	private final static Double TRUNC_LEVEL_MAX = new Double(6.0);
	public final static Double TRUNC_LEVEL_DEFAULT = new Double(2.0);
	private final static String TRUNC_LEVEL_INFO = "This defines the last non-zero value on the characteristic MFD";
	private DoubleParameter truncLevelParam;

	public final static String B_FAULTS_B_VAL_PARAM_NAME = "B-Faults b-value";
	public final static String B_FAULTS_B_VAL_PARAM_INFO = "GR-distribution b-value to apply to B-Faults";
	public final static Double B_FAULT_GR_B_DEFAULT= new Double(0.8);
	public final static Double B_VAL_MIN = new Double(-1);
	public final static Double B_VAL_MAX = new Double(2);
	private DoubleParameter bFaultB_ValParam;

	public final static String A_FAULTS_B_VAL_PARAM_NAME = "A-Faults b-value";
	public final static String A_FAULTS_B_VAL_PARAM_INFO = "GR-distribution b-value to apply to A-Faults";
	public final static Double A_FAULT_GR_B_DEFAULT= new Double(0.0);
	public final static Double A_VAL_MIN = new Double(-1);
	public final static Double A_VAL_MAX = new Double(2);
	private DoubleParameter aFaultB_ValParam;

	public final static String BACK_SEIS_B_VAL_PARAM_NAME = "Background Seis b-value";
	public final static String BACK_SEIS_B_VAL_PARAM_INFO = "GR-distribution b-value to apply to the background seismicity";
	public final static Double BACK_SEIS_B_DEFAULT = new Double(0.9);
	// min and max same as for bFaultB_ValParam
	private DoubleParameter regionB_ValParam;

	// B-Fault Min Mag
	public final static String B_FAULTS_MIN_MAG = "B-Faults Min Mag";
	private final static Double B_FAULTS_MIN_MAG_DEFAULT = new Double(6.5);
	private final static String B_FAULTS_MIN_MAG_INFO = "Min Mag to apply to B-Faults GR-distribution";
	private DoubleParameter bFaultsMinMagParam;

	/*
	// whether to inlcude C-zones
	public final static String INCLUDE_C_ZONES  = "Include C Zones?";
	private final static Boolean INCLUDE_C_ZONES_DEFAULT = new Boolean(true);
	private BooleanParameter includeC_ZonesParam;
	 */
//	C-zone weight
	public final static String C_ZONE_WT_PARAM_NAME  = "C-Zone Weight";
	private final static Double C_ZONE_WT_DEFAULT = new Double(0.5);
	private final static String C_ZONE_WT_INFO = "Weight to apply to type C-zones";
	private DoubleParameter c_ZoneWtParam;


	// fraction to put into background
	public final static String ABC_MO_RATE_REDUCTION_PARAM_NAME = "Fract MoRate to Background";
	public final static Double ABC_MO_RATE_REDUCTION_MIN = new Double(0);
	public final static Double ABC_MO_RATE_REDUCTION_MAX = new Double(1);
	public final static Double ABC_MO_RATE_REDUCTION_DEFAULT = new Double(0.0);
	public final static String ABC_MO_RATE_REDUCTION_INFO = "Fraction of Moment Rate to take from A & B Faults & C zones to put into background seismicity";
	private DoubleParameter moRateFracToBackgroundParam;

	// Mean Mag Correction
	public final static String MEAN_MAG_CORRECTION = "Mean Mag Correction";
	private final static Double MEAN_MAG_CORRECTION_MIN = new Double(-0.5);
	private final static Double MEAN_MAG_CORRECTION_MAX = new Double(0.5);
	public final static Double MEAN_MAG_CORRECTION_DEFAULT = new Double(0.0);
	private final static String MEAN_MAG_CORRECTION_INFO = "Increment added to mean mag as additional epistemic uncertainity";
	private DoubleParameter meanMagCorrectionParam;

	// set for background
	public final static String SET_FOR_BCK_PARAM_NAME = "MFD for Background";
	private final static String SET_FOR_BCK_PARAM_FRAC_MO_RATE_TR_GR = "Trunc. GR (Mmax from fraction)";
	private final static String SET_FOR_BCK_PARAM_FRAC_MO_RATE_TA_GR = "Tapered GR (Mcorner from fraction)";
	private final static String SET_FOR_BCK_PARAM_BCK_MAX_MAG = "Trunc. GR (w/ set Mmax)";
	private final static String SET_FOR_BCK_PARAM_NSHMP07 = "NSHMP07 MFD";
	private final static String SET_FOR_BCK_PARAM_INFO = "This specifies the type of magnitude-frequency dist. to use for the background";
	private StringParameter setForBckParam;

	// NSHMP Bulge Reduction Param
//	public final static String BULGE_REDUCTION_PARAM_NAME = "NSHMP Bulge Reduction?";
//	private final static String BULGE_REDUCTION_PARAM_INFO = "This reduces california backgroud seis. rates by a factor of 3 for M>6.5";
//	private BooleanParameter bulgeReductionBooleanParam;

	// NSHMP Max-Mag Grid Param
//	public final static String MAX_MAG_GRID_PARAM_NAME = "Apply Max-Mag Grid?";
//	private final static String MAX_MAG_GRID_PARAM_INFO = "This applies spatially variable mag-mags in background sies.";
//	private BooleanParameter maxMagGridBooleanParam;

	// Probability Model Param
	public final static String PROB_MODEL_PARAM_NAME = "Probability Model";
	public final static String PROB_MODEL_PARAM_INFO = "Probability Model for Time Dependence";
	public final static String PROB_MODEL_POISSON = "Poisson";
	public final static String PROB_MODEL_BPT = "BPT";
	public final static String PROB_MODEL_EMPIRICAL = "Empirical";
	public final static String PROB_MODEL_DEFAULT = PROB_MODEL_BPT;
	private StringParameter probModelParam;

	// Aperiodicity Param
	public final static String APERIODICITY_PARAM_NAME = "Aperiodicity";
	private final static String APERIODICITY_PARAM_INFO = "Aperiodicity for Time dependence";
	private final static Double APERIODICITY_PARAM_MIN = new Double(0.1);
	private final static Double APERIODICITY_PARAM_MAX = new Double(2.0);
	private final static Double APERIODICITY_PARAM_DEFAULT = new Double(0.5);
	private DoubleParameter aperiodicityParam;

	//	Default Aperiodicity Param
	public final static String DEF_APERIODICITY_PARAM_NAME = "Default Aperiodicity";
	private final static String DEF_APERIODICITY_PARAM_INFO = "Default Aperiodicity for Time dependence";
	private final static Double DEF_APERIODICITY_PARAM_MIN = new Double(0.1);
	private final static Double DEF_APERIODICITY_PARAM_MAX = new Double(2.0);
	private final static Double DEF_APERIODICITY_PARAM_DEFAULT = new Double(0.5);
	private DoubleParameter defaultAperiodicityParam;

	// Segment Dependent Aperiodicity Param
	public final static String SEG_DEP_APERIODICITY_PARAM_NAME = "Seg Dependent Aperiodicity";
	private final static String SEG_DEP_APERIODICITY_PARAM_INFO = "Segment Aperiodicity for Time dependence";
	private final static Boolean SEG_DEP_APERIODICITY_PARAM_DEFAULT = new Boolean(false);
	private BooleanParameter segDepAperiodicityParam;

	// Time duration
	private final static double DURATION_DEFAULT = 30;
	private final static double DURATION_MIN = 1;
	private final static double DURATION_MAX = 100;

	//start time
	private final static int START_TIME_DEFAULT = 2007;
	private final static int START_TIME_MIN = 2007;
	private final static int START_TIME_MAX = 2107;

	// 
	private double[] totalRelativeGriddedRates;
	private CaliforniaRegions.RELM_GRIDDED region = new CaliforniaRegions.RELM_GRIDDED();

	// A and B faults fetcher
	private A_FaultsFetcher aFaultsFetcher = new A_FaultsFetcher();
	private B_FaultsFetcher bFaultsFetcher  = new B_FaultsFetcher();
	private EmpiricalModel empiricalModel = new EmpiricalModel();

	private ArrayList aFaultSourceGenerators; 
	private ArrayList<UnsegmentedSource> bFaultSources;
	private ArrayList<ProbEqkSource> nonCA_bFaultSources;
	

	private B_FaultFixes bFaultFixes = new B_FaultFixes(); 

	private NSHMP_GridSourceGenerator nshmp_gridSrcGen = new NSHMP_GridSourceGenerator();

	private boolean reCalcB_Faults=true, reCalcBck=true, reCalcA_Faults=true;
	private boolean reCalcC_Zones=true, updateA_FaultsFetcher=true, updateB_FaultsFetcher=true, reCalcNonCA_B_Fauts=true;

	/**
	 *
	 * No argument constructor
	 */
	public UCERF2() {

		// create and add adj params
		initAdjParams();

		// set param defaults
		setParamDefaults();

		// put parameters in the parameter List object	
		createParamList();

//		create the timespan parameter, to allow the user to set the timespan to be
		//time independent or time dependent.
		setTimespanParameter();

		// add the change listener to parameters so that forecast can be updated
		// whenever any paramater changes
		//faultModelParam.addParameterChangeListener(this);
		rupOffset_Param.addParameterChangeListener(this);
		backSeisParam.addParameterChangeListener(this);
		backSeisRupParam.addParameterChangeListener(this);
		deformationModelsParam.addParameterChangeListener(this);
		rupModelParam.addParameterChangeListener(this);
		connectMoreB_FaultsParam.addParameterChangeListener(this);
		this.probModelParam.addParameterChangeListener(this);
		this.segDepAperiodicityParam.addParameterChangeListener(this);
		updateFetchersBasedonDefModels();
	}

	/**
	 * Get A-Faults fetcher
	 * @return
	 */
	public A_FaultsFetcher getA_FaultsFetcher() {
		return this.aFaultsFetcher;
	}


	/**
	 * This intializes the adjustable parameters
	 */
	private void initAdjParams() {

		// NOTE THAT VALUES SET IN THE CONSTRUCTORS ARE OVER RIDDEN BY CALLING THE setParamDefaults()
		// NETHOD AT THE END

		// background seismicity include/exclude  
		backSeisOptionsStrings.add(BACK_SEIS_EXCLUDE);
		backSeisOptionsStrings.add(BACK_SEIS_INCLUDE);
		backSeisOptionsStrings.add(BACK_SEIS_ONLY);
		backSeisParam = new StringParameter(BACK_SEIS_NAME, backSeisOptionsStrings,BACK_SEIS_DEFAULT);

		// backgroud treated as point sources/finite sources
		backSeisRupStrings.add(BACK_SEIS_RUP_POINT);
		backSeisRupStrings.add(BACK_SEIS_RUP_FINITE);
		backSeisRupStrings.add(BACK_SEIS_RUP_CROSSHAIR);
		backSeisRupParam = new StringParameter(BACK_SEIS_RUP_NAME, backSeisRupStrings,BACK_SEIS_RUP_DEFAULT);

		// back seis Mmax
		backSeisMaxMagParam = new DoubleParameter(BACK_SEIS_MAG_NAME, BACK_SEIS_MAG_MIN, BACK_SEIS_MAG_MAX,
				BACK_SEIS_MAG_DEFAULT);
		backSeisMaxMagParam.setInfo(BACK_SEIS_MAG_INFO);

		// rup offset
		rupOffset_Param = new DoubleParameter(RUP_OFFSET_PARAM_NAME,RUP_OFFSET_PARAM_MIN,
				RUP_OFFSET_PARAM_MAX,RUP_OFFSET_PARAM_UNITS,DEFAULT_RUP_OFFSET_VAL);
		rupOffset_Param.setInfo(RUP_OFFSET_PARAM_INFO);

		// total M>-5 rate
		totalMagRateParam = new DoubleParameter(TOT_MAG_RATE_PARAM_NAME, TOT_MAG_RATE_MIN,
				TOT_MAG_RATE_MAX, TOT_MAG_RATE_DEFAULT);
		totalMagRateParam.setInfo(TOT_MAG_RATE_INFO);

		// Aftershock/Foreshock fraction
		aftershockFractionParam = new DoubleParameter(AFTERSHOCK_FRACTION_PARAM_NAME, AFTERSHOCK_FRACTION_MIN,
				AFTERSHOCK_FRACTION_MAX, AFTERSHOCK_FRACTION_DEFAULT);
		aftershockFractionParam.setInfo(AFTERSHOCK_FRACTION_INFO);

		// Coupling coeff
		couplingCoeffParam = new DoubleParameter(COUPLING_COEFF_PARAM_NAME, COUPLING_COEFF_MIN,
				COUPLING_COEFF_MAX, COUPLING_COEFF_DEFAULT);
		couplingCoeffParam.setInfo(COUPLING_COEFF_INFO);


		// % char vs GR param
		percentCharVsGRParam = new DoubleParameter(CHAR_VS_GR_PARAM_NAME, CHAR_VS_GR_MIN,
				CHAR_VS_GR_MAX, CHAR_VS_GR_DEFAULT);
		percentCharVsGRParam.setInfo(CHAR_VS_GR_INFO);

		// aseis factor param
		aseisFactorInterParam = new BooleanParameter(ASEIS_INTER_PARAM_NAME, new Boolean(true));
		aseisFactorInterParam.setInfo(ASEIS_INTER_PARAM_INFO);

		// relativeA_PrioriWeightParam
		relativeA_PrioriWeightParam = new DoubleParameter(REL_A_PRIORI_WT_PARAM_NAME, REL_A_PRIORI_WT_PARAM_MIN,
				REL_A_PRIORI_WT_PARAM_MAX, REL_A_PRIORI_WT_PARAM_DEFAULT);
		relativeA_PrioriWeightParam.setInfo(REL_A_PRIORI_WT_PARAM_INFO);

		//
		relativeSegRateWeightParam = new DoubleParameter(REL_SEG_RATE_WT_PARAM_NAME, REL_SEG_RATE_WT_PARAM_MIN,
				REL_SEG_RATE_WT_PARAM_MAX, REL_SEG_RATE_WT_PARAM_DEFAULT);
		relativeSegRateWeightParam.setInfo(REL_SEG_RATE_WT_PARAM_INFO);
		/*		
		// constrainA_SegRatesParam
		constrainA_SegRatesParam = new BooleanParameter(CONSTRAIN_A_SEG_RATES_PARAM_NAME, new Boolean(true));
		constrainA_SegRatesParam.setInfo(CONSTRAIN_A_SEG_RATES_PARAM_INFO);
		 */
		/*		
		// preserveMinAFaultRateParam
		preserveMinAFaultRateParam = new BooleanParameter(PRESERVE_MIN_A_FAULT_RATE_PARAM_NAME, true);
		preserveMinAFaultRateParam.setInfo(PRESERVE_MIN_A_FAULT_RATE_PARAM_INFO);
		 */	
		// min rate param 1
		minA_FaultRate1Param = new DoubleParameter(MIN_A_FAULT_RATE_1_PARAM_NAME, MIN_A_FAULT_RATE_MIN, MIN_A_FAULT_RATE_MAX,
				MIN_A_FAULT_RATE_1_DEFAULT);
		minA_FaultRate1Param.setInfo(MIN_A_FAULT_RATE_1_INFO);

		// min rate param 2
		minA_FaultRate2Param = new DoubleParameter(MIN_A_FAULT_RATE_2_PARAM_NAME, MIN_A_FAULT_RATE_MIN, MIN_A_FAULT_RATE_MAX,
				MIN_A_FAULT_RATE_2_DEFAULT);
		minA_FaultRate2Param.setInfo(MIN_A_FAULT_RATE_2_INFO);

		// weightedInversionParam
		weightedInversionParam = new BooleanParameter(WEIGHTED_INVERSION_PARAM_NAME, true);
		weightedInversionParam.setInfo(WEIGHTED_INVERSION_PARAM_INFO);

		// connect more B Faults
		connectMoreB_FaultsParam = new BooleanParameter(CONNECT_B_FAULTS_PARAM_NAME, true);
		connectMoreB_FaultsParam.setInfo(CONNECT_B_FAULTS_PARAM_INFO);

		//		 make objects of Mag Area Relationships
		magAreaRelationships = new ArrayList();
		magAreaRelationships.add(new Ellsworth_A_WG02_MagAreaRel() );
		magAreaRelationships.add(new Ellsworth_B_WG02_MagAreaRel());
		magAreaRelationships.add(new HanksBakun2002_MagAreaRel());
		magAreaRelationships.add(new Somerville_2006_MagAreaRel());
		magAreaRelationships.add(new WGCEP_2007_PowLaw_MagAreaRel());
		magAreaRelationships.add(new Shaw_2007_MagAreaRel());
		//magAreaRelationships.add(new WC1994_MagAreaRelationship());
		// array List of Mag Area Rel names
		ArrayList magAreaNamesList = new ArrayList();
		for(int i=0; i<magAreaRelationships.size(); ++i)
			magAreaNamesList.add(((MagAreaRelationship)magAreaRelationships.get(i)).getName());
		magAreaRelParam = new StringParameter(MAG_AREA_RELS_PARAM_NAME, magAreaNamesList, (String)magAreaNamesList.get(1));
		magAreaRelParam.setInfo(MAG_AREA_RELS_PARAM_INFO);


		// deformation model param
		deformationModelSummariesList = this.deformationModelSummaryFinal.getAllDeformationModels();
		// make a list of deformation model names
		ArrayList deformationModelNames = new ArrayList();
		for(int i=0; i<deformationModelSummariesList.size(); ++i) {
			deformationModelNames.add(((DeformationModelSummary)deformationModelSummariesList.get(i)).getDeformationModelName());
//			System.out.println(i+" "+
//			((DeformationModelSummary)deformationModelsList.get(i)).getDeformationModelName()+"  "+
//			((DeformationModelSummary)deformationModelsList.get(i)).getDeformationModelId());
		}
		deformationModelsParam = new StringParameter(DEFORMATION_MODEL_PARAM_NAME,deformationModelNames, (String)deformationModelNames.get(0) );
		deformationModelsParam.setInfo(DEFORMATION_MODEL_PARAM_INFO);


		// A-Fault model type
		ArrayList<String> rupModels = new ArrayList<String>();
		rupModels.add(SEGMENTED_A_FAULT_MODEL);
		rupModels.add(UNSEGMENTED_A_FAULT_MODEL);
		rupModelParam = new StringParameter(RUP_MODEL_TYPE_NAME, rupModels, rupModels.get(0));
		rupModelParam.setInfo(RUP_MODEL_TYPE_INFO);

		// segmented fault model param
		makeSegmentedA_FaultParam();

		// A-fault slip type
		slipModelParam = new StringParameter(SLIP_MODEL_TYPE_NAME, 
				A_FaultSegmentedSourceGenerator.getSupportedSlipModels(), 
				A_FaultSegmentedSourceGenerator.TAPERED_SLIP_MODEL);
		slipModelParam.setInfo(SLIP_MODEL_TYPE_INFO);

		// mag Sigma Param
		magSigmaParam = new DoubleParameter(MAG_SIGMA_PARAM_NAME, MAG_SIGMA_MIN, MAG_SIGMA_MAX,
				MAG_SIGMA_DEFAULT);
		magSigmaParam.setInfo(MAG_SIGMA_INFO);

		// trunc level
		truncLevelParam = new DoubleParameter(TRUNC_LEVEL_PARAM_NAME, TRUNC_LEVEL_MIN, TRUNC_LEVEL_MAX,
				TRUNC_LEVEL_PARAM_UNITS, TRUNC_LEVEL_DEFAULT);
		truncLevelParam.setInfo(TRUNC_LEVEL_INFO);

		bFaultB_ValParam = new DoubleParameter(B_FAULTS_B_VAL_PARAM_NAME, this.B_VAL_MIN, this.B_VAL_MAX, this.B_FAULT_GR_B_DEFAULT);
		bFaultB_ValParam.setInfo(B_FAULTS_B_VAL_PARAM_INFO);
		regionB_ValParam = new DoubleParameter(BACK_SEIS_B_VAL_PARAM_NAME, this.B_VAL_MIN, this.B_VAL_MAX, this.BACK_SEIS_B_DEFAULT);
		regionB_ValParam.setInfo(BACK_SEIS_B_VAL_PARAM_INFO);

		aFaultB_ValParam = new DoubleParameter(A_FAULTS_B_VAL_PARAM_NAME, A_VAL_MIN, A_VAL_MAX, A_FAULT_GR_B_DEFAULT);
		aFaultB_ValParam.setInfo(A_FAULTS_B_VAL_PARAM_INFO);

		moRateFracToBackgroundParam = new DoubleParameter(ABC_MO_RATE_REDUCTION_PARAM_NAME, 
				ABC_MO_RATE_REDUCTION_MIN, ABC_MO_RATE_REDUCTION_MAX, 
				ABC_MO_RATE_REDUCTION_DEFAULT);
		moRateFracToBackgroundParam.setInfo(ABC_MO_RATE_REDUCTION_INFO);


		// Mean Mag Correction
		meanMagCorrectionParam = new DoubleParameter(MEAN_MAG_CORRECTION, 
				MEAN_MAG_CORRECTION_MIN, MEAN_MAG_CORRECTION_MAX,
				MEAN_MAG_CORRECTION_DEFAULT);
		meanMagCorrectionParam.setInfo(MEAN_MAG_CORRECTION_INFO);

//		B-Fault Min Mag
		bFaultsMinMagParam = new DoubleParameter(B_FAULTS_MIN_MAG, 5.0, 8.0, B_FAULTS_MIN_MAG_DEFAULT);
		bFaultsMinMagParam.setInfo(B_FAULTS_MIN_MAG_INFO);


		// C-zone weight
//		includeC_ZonesParam = new BooleanParameter(INCLUDE_C_ZONES, INCLUDE_C_ZONES_DEFAULT);
		c_ZoneWtParam  = new DoubleParameter(C_ZONE_WT_PARAM_NAME, 0.0, 1.0, C_ZONE_WT_DEFAULT);
		c_ZoneWtParam.setInfo(C_ZONE_WT_INFO);

		// set for background
		ArrayList<String> options = new ArrayList<String>();
		options.add(SET_FOR_BCK_PARAM_FRAC_MO_RATE_TR_GR);
		options.add(SET_FOR_BCK_PARAM_FRAC_MO_RATE_TA_GR);
		options.add(SET_FOR_BCK_PARAM_BCK_MAX_MAG);
		options.add(SET_FOR_BCK_PARAM_NSHMP07);
		setForBckParam = new StringParameter(SET_FOR_BCK_PARAM_NAME, options, 
				SET_FOR_BCK_PARAM_NSHMP07);
		setForBckParam.setInfo(SET_FOR_BCK_PARAM_INFO);
		setForBckParam.addParameterChangeListener(this);

//		bulgeReductionBooleanParam = new BooleanParameter(BULGE_REDUCTION_PARAM_NAME,true);
//		bulgeReductionBooleanParam.setInfo(BULGE_REDUCTION_PARAM_INFO);

//		this.maxMagGridBooleanParam = new BooleanParameter(MAX_MAG_GRID_PARAM_NAME,true);
//		maxMagGridBooleanParam.setInfo(MAX_MAG_GRID_PARAM_INFO);

		// Probability Model Param
		ArrayList<String> probModelOptions = new ArrayList<String>();
		probModelOptions.add(PROB_MODEL_POISSON);
		probModelOptions.add(PROB_MODEL_BPT);
		probModelOptions.add(PROB_MODEL_EMPIRICAL);
		probModelParam = new StringParameter(PROB_MODEL_PARAM_NAME, probModelOptions, PROB_MODEL_DEFAULT);
		probModelParam.setInfo(PROB_MODEL_PARAM_INFO);


		// Aperiodicity Param
		aperiodicityParam = new DoubleParameter(APERIODICITY_PARAM_NAME, 
				APERIODICITY_PARAM_MIN, APERIODICITY_PARAM_MAX,
				APERIODICITY_PARAM_DEFAULT);
		aperiodicityParam.setInfo(APERIODICITY_PARAM_INFO);


		//	Default Aperiodicity Param
		defaultAperiodicityParam = new DoubleParameter(DEF_APERIODICITY_PARAM_NAME, 
				DEF_APERIODICITY_PARAM_MIN, DEF_APERIODICITY_PARAM_MAX,
				DEF_APERIODICITY_PARAM_DEFAULT);
		defaultAperiodicityParam.setInfo(DEF_APERIODICITY_PARAM_INFO);


		// Segment Dependent Aperiodicity Param
		segDepAperiodicityParam = new BooleanParameter(SEG_DEP_APERIODICITY_PARAM_NAME, SEG_DEP_APERIODICITY_PARAM_DEFAULT);
		segDepAperiodicityParam.setInfo(SEG_DEP_APERIODICITY_PARAM_INFO);
		
		// Floater Type Param
		ArrayList<String> floaterTypes = new ArrayList<String>();
		floaterTypes.add(FULL_DDW_FLOATER);
		floaterTypes.add(STRIKE_AND_DOWNDIP_FLOATER);
		floaterTypes.add(CENTERED_DOWNDIP_FLOATER);
		floaterTypeParam = new StringParameter(FLOATER_TYPE_PARAM_NAME, floaterTypes, FLOATER_TYPE_PARAM_DEFAULT);
		
	}


	// Set default value for parameters
	public void setParamDefaults() {
		backSeisParam.setValue(BACK_SEIS_DEFAULT);
		// backgroud treated as point sources/finite soource
		backSeisRupParam.setValue(BACK_SEIS_RUP_DEFAULT);
		// back seis Mmax
		backSeisMaxMagParam.setValue(BACK_SEIS_MAG_DEFAULT);
		// rup offset
		rupOffset_Param.setValue(DEFAULT_RUP_OFFSET_VAL);
		// total M>-5 rate
		totalMagRateParam.setValue(TOT_MAG_RATE_DEFAULT);
		// Aftershock/Foreshock fraction
		aftershockFractionParam.setValue(AFTERSHOCK_FRACTION_DEFAULT);
		// Coupling coeff
		couplingCoeffParam.setValue(COUPLING_COEFF_DEFAULT);
		// % char vs GR param
		percentCharVsGRParam.setValue(CHAR_VS_GR_DEFAULT);
		// aseis factor param
		aseisFactorInterParam.setValue(true);
		// relativeA_PrioriWeightParam
		relativeA_PrioriWeightParam.setValue(REL_A_PRIORI_WT_PARAM_DEFAULT);
		// relativeSegRateWeightParam
		relativeSegRateWeightParam.setValue(REL_SEG_RATE_WT_PARAM_DEFAULT);		
		// preserveMinAFaultRateParam
//		preserveMinAFaultRateParam.setValue(true);
		minA_FaultRate1Param.setValue(MIN_A_FAULT_RATE_1_DEFAULT);
		minA_FaultRate2Param.setValue(MIN_A_FAULT_RATE_2_DEFAULT);
		// weightedInversionParam
		weightedInversionParam.setValue(true);	
		// connect more B Faults
		connectMoreB_FaultsParam.setValue(true);
		connectMoreB_FaultsParam.setInfo(CONNECT_B_FAULTS_PARAM_INFO);
		//Mag Area Relationships
		magAreaRelParam.setValue(Ellsworth_B_WG02_MagAreaRel.NAME);
		// deformation model
		deformationModelsParam.setValue(deformationModelSummariesList.get(0).getDeformationModelName() );
		rupModelParam.setValue(SEGMENTED_A_FAULT_MODEL);
		// segmented fault model param	
		Iterator it = this.segmentedRupModelParam.getParametersIterator();
		while(it.hasNext()) { // set the specfiied rup model in each A fault
			StringParameter param = (StringParameter)it.next();
			ArrayList<String> allowedVals = param.getAllowedStrings();
			param.setValue(allowedVals.get(0));
		}
		// A-fault slip type
		slipModelParam.setValue(A_FaultSegmentedSourceGenerator.TAPERED_SLIP_MODEL);
		// mag Sigma Param
		magSigmaParam.setValue(MAG_SIGMA_DEFAULT);
		// trunc level
		truncLevelParam.setValue(TRUNC_LEVEL_DEFAULT);
		// B-Fault B-Value
		bFaultB_ValParam.setValue(B_FAULT_GR_B_DEFAULT);
		// A-Fault B-Value
		aFaultB_ValParam.setValue(A_FAULT_GR_B_DEFAULT);
		// Regional B-Value
		regionB_ValParam.setValue(BACK_SEIS_B_DEFAULT);
		moRateFracToBackgroundParam.setValue(ABC_MO_RATE_REDUCTION_DEFAULT);
		// Mean Mag Correction
		meanMagCorrectionParam.setValue(MEAN_MAG_CORRECTION_DEFAULT);
		//		 B-Fault Min Mag
		bFaultsMinMagParam.setValue(B_FAULTS_MIN_MAG_DEFAULT);
		// C-zone wt
		c_ZoneWtParam.setValue(C_ZONE_WT_DEFAULT);
		// set for background
		setForBckParam.setValue(SET_FOR_BCK_PARAM_NSHMP07);
//		bulgeReductionBooleanParam.setValue(true);
//		maxMagGridBooleanParam.setValue(true);

		probModelParam.setValue(PROB_MODEL_DEFAULT);
		aperiodicityParam.setValue(APERIODICITY_PARAM_DEFAULT);
		defaultAperiodicityParam.setValue(DEF_APERIODICITY_PARAM_DEFAULT);
		segDepAperiodicityParam.setValue(SEG_DEP_APERIODICITY_PARAM_DEFAULT);	
		floaterTypeParam.setValue(FLOATER_TYPE_PARAM_DEFAULT);

	}

	/**
	 * Whether to include the aftershocks
	 * 
	 * @return
	 */
	public boolean areAfterShocksIncluded() {
		// Check if NSHMP solution chosen
		String setForBackground = (String)setForBckParam.getValue();
		if(setForBackground.equalsIgnoreCase(this.SET_FOR_BCK_PARAM_NSHMP07))
			return false;
		double rate = ((Double)getParameter(TOT_MAG_RATE_PARAM_NAME).getValue()).doubleValue();
		boolean includeAfterShocks;
		if(rate > 5.85) includeAfterShocks = true;
		else includeAfterShocks = false;
		return includeAfterShocks;
	}	

	/**
	 * Put parameters in theParameterList
	 */
	private void createParamList() {
		adjustableParams = new ParameterList();
		//	 add adjustable parameters to the list
//		adjustableParams.addParameter(faultModelParam);		not needed for now
//		adjustableParams.addParameter(rupOffset_Param);		not needed for now
		adjustableParams.addParameter(deformationModelsParam);
		adjustableParams.addParameter(moRateFracToBackgroundParam);
		adjustableParams.addParameter(couplingCoeffParam);
		adjustableParams.addParameter(aftershockFractionParam);
//		adjustableParams.addParameter(aseisFactorInterParam);
		adjustableParams.addParameter(rupModelParam);
		String rupModel = (String)rupModelParam.getValue();
		if(rupModel.equalsIgnoreCase(SEGMENTED_A_FAULT_MODEL)) {
			adjustableParams.addParameter(segmentedRupModelParam);
			adjustableParams.addParameter(slipModelParam);
			adjustableParams.addParameter(relativeA_PrioriWeightParam);
			adjustableParams.addParameter(relativeSegRateWeightParam);
			adjustableParams.addParameter(weightedInversionParam);
			adjustableParams.addParameter(minA_FaultRate1Param);
			adjustableParams.addParameter(minA_FaultRate2Param);
//			adjustableParams.addParameter(preserveMinAFaultRateParam);
		}

		if(rupModel.equalsIgnoreCase(UNSEGMENTED_A_FAULT_MODEL)) adjustableParams.addParameter(aFaultB_ValParam);
		adjustableParams.addParameter(magAreaRelParam);
		adjustableParams.addParameter(magSigmaParam);
		adjustableParams.addParameter(truncLevelParam);
		adjustableParams.addParameter(meanMagCorrectionParam);
		adjustableParams.addParameter(percentCharVsGRParam);
		adjustableParams.addParameter(this.floaterTypeParam);
		adjustableParams.addParameter(bFaultB_ValParam);
		adjustableParams.addParameter(bFaultsMinMagParam);
		adjustableParams.addParameter(connectMoreB_FaultsParam);
		adjustableParams.addParameter(backSeisParam);	
		if(!backSeisParam.getValue().equals(BACK_SEIS_EXCLUDE))
			adjustableParams.addParameter(backSeisRupParam);
		adjustableParams.addParameter(c_ZoneWtParam);
		adjustableParams.addParameter(setForBckParam);
		String setForBackground = (String)setForBckParam.getValue();
		if(setForBackground.equalsIgnoreCase(SET_FOR_BCK_PARAM_FRAC_MO_RATE_TR_GR) || setForBackground.equalsIgnoreCase(SET_FOR_BCK_PARAM_FRAC_MO_RATE_TA_GR)) {
			adjustableParams.addParameter(totalMagRateParam);
			adjustableParams.addParameter(regionB_ValParam);
		}
		else if(setForBackground.equalsIgnoreCase(SET_FOR_BCK_PARAM_BCK_MAX_MAG)) {
			adjustableParams.addParameter(totalMagRateParam);
			adjustableParams.addParameter(regionB_ValParam);
			adjustableParams.addParameter(backSeisMaxMagParam);
		}
		else {
			// the else case (SET_FOR_BCK_PARAM_NSHMP07) adds nothing here
//			adjustableParams.addParameter(bulgeReductionBooleanParam);
//			adjustableParams.addParameter(maxMagGridBooleanParam);
		}
		adjustableParams.addParameter(probModelParam);
		if(this.probModelParam.getValue().equals(PROB_MODEL_BPT)) { // if time dependent prob model is chosen
			adjustableParams.addParameter(this.segDepAperiodicityParam);
			boolean isSegDepApriodicity = ((Boolean)segDepAperiodicityParam.getValue()).booleanValue();
			if(isSegDepApriodicity) adjustableParams.addParameter(this.defaultAperiodicityParam);
			else adjustableParams.addParameter(this.aperiodicityParam);
		}
	}

	/**
	 * Rup Model options for each A-fault in case of segmented 
	 *
	 */
	private void makeSegmentedA_FaultParam() {
		ParameterList paramList = new ParameterList();
		ArrayList<String> faultNames = aFaultsFetcher.getAllFaultNames();
		for(int i=0; i<faultNames.size(); ++i) {
			ArrayList<String> supportedRupModels = aFaultsFetcher.getRupModels(faultNames.get(i));
			StringParameter rupModelParam = new StringParameter(faultNames.get(i), supportedRupModels, supportedRupModels.get(0));
			paramList.addParameter(rupModelParam);
		}
		segmentedRupModelParam = new ParameterListParameter(this.SEGMENTED_RUP_MODEL_TYPE_NAME, paramList);
		segmentedRupModelParam.setInfo(this.SEGMENTED_RUP_MODEL_TYPE_INFO);
	}

	/**
	 * Get the info on the selected deformation model
	 * @return
	 */
	private DeformationModelSummary getSelectedDeformationModelSummary() {
		String selectedDefModel  = (String) deformationModelsParam.getValue();
		for(int i=0; i<deformationModelSummariesList.size(); ++i) {
			DeformationModelSummary deformationModelSum = (DeformationModelSummary)deformationModelSummariesList.get(i);
			if(deformationModelSum.getDeformationModelName().equalsIgnoreCase(selectedDefModel)) {
				return deformationModelSum;
			}
		}
		return null;
	}

	/**
	 * Return list of objects of MagAreaRelationships which are supported by this model
	 * @return
	 */
	public ArrayList getMagAreaRelationships() {
		return this.magAreaRelationships;
	}


	/**
	 * Get the selected Mag Area relationship
	 * @return
	 */
	public MagAreaRelationship getMagAreaRelationship() {
		String magAreaRelName = (String)this.magAreaRelParam.getValue();
		// iterate over all Mag Area relationships to find the selected one
		for(int i=0; i<magAreaRelationships.size(); ++i) {
			MagAreaRelationship magAreaRel = (MagAreaRelationship)magAreaRelationships.get(i);
			if(magAreaRel.getName().equalsIgnoreCase(magAreaRelName))
				return magAreaRel;
		}

		return null;
	}



	/**
	 * Returns the  ith earthquake source
	 *
	 * @param iSource : index of the source needed
	 */
	public ProbEqkSource getSource(int iSource) {
		if(iSource<allSources.size()) // everything but the grid sources
			return (ProbEqkSource) allSources.get(iSource);
		else {
			if(this.backSeisRupParam.getValue().equals(BACK_SEIS_RUP_CROSSHAIR))
				return nshmp_gridSrcGen.getCrosshairGriddedSource(iSource - allSources.size(), timeSpan.getDuration());
			else return nshmp_gridSrcGen.getRandomStrikeGriddedSource(iSource - allSources.size(), timeSpan.getDuration());
		}
	}

	/**
	 * Get the number of earthquake sources
	 *
	 * @return integer
	 */
	public int getNumSources(){
		if(backSeisParam.getValue().equals(BACK_SEIS_INCLUDE)||
				backSeisParam.getValue().equals(UCERF2.BACK_SEIS_ONLY))
			return allSources.size() + nshmp_gridSrcGen.getNumSources();
		else return allSources.size();
	}


	/**
	 * This can be vastly simplified if and when NSHMP07 treatment is the only option
	 *
	 */
	private void  makeBackgroundGridSources() {

		// get the total rate of M�5 events & b-value
		double rate = ((Double)totalMagRateParam.getValue()).doubleValue();
		double bValue = ((Double)regionB_ValParam.getValue()).doubleValue();

		double totRateABC = aFaultSummedMFD.getTotalIncrRate()+bFaultCharSummedMFD.getTotalIncrRate()+
		bFaultGR_SummedMFD.getTotalIncrRate()+cZoneSummedMFD.getTotalIncrRate()+this.nonCA_B_FaultsSummedMFD.getTotalIncrRate();

		double totBackRate = rate-totRateABC;

		String backgroundTreatment = (String) setForBckParam.getValue();
		if(backgroundTreatment.equals(SET_FOR_BCK_PARAM_FRAC_MO_RATE_TR_GR) ||
				backgroundTreatment.equals(SET_FOR_BCK_PARAM_FRAC_MO_RATE_TA_GR)) {
			double totMoRateABC = aFaultSummedMFD.getTotalMomentRate()+bFaultCharSummedMFD.getTotalMomentRate()+
			bFaultGR_SummedMFD.getTotalMomentRate()+cZoneSummedMFD.getTotalMomentRate()+nonCA_B_FaultsSummedMFD.getTotalMomentRate();
			//restore the original, total moment rate:
			totMoRateABC /= (1-totMoRateReduction);
			// now get background component:
			double moRateFracToBackground = ((Double)moRateFracToBackgroundParam.getValue()).doubleValue();
			double totBackMoRate = totMoRateABC*moRateFracToBackground;
			if(backgroundTreatment.equals(SET_FOR_BCK_PARAM_FRAC_MO_RATE_TR_GR)) {
				totBackgroundMFD = new GutenbergRichterMagFreqDist(MIN_MAG, NUM_MAG, DELTA_MAG);
				if(moRateFracToBackground > 0)
					((GutenbergRichterMagFreqDist) totBackgroundMFD).setAllButMagUpper(MIN_MAG, totBackMoRate, totBackRate, bValue, true);
				// NOTE that momentRate is not exactly conserved here due to mag discretization
			}
			else {
				totBackgroundMFD = new TaperedGR_MagFreqDist(MIN_MAG, NUM_MAG, DELTA_MAG);
				if(moRateFracToBackground > 0)
					((TaperedGR_MagFreqDist) totBackgroundMFD).setAllButCornerMag(MIN_MAG, totBackMoRate, totBackRate, bValue);
			}
//			System.out.println(totBackMoRate+", "+totBackRate+", "+bValue+", "+totBackgroundMFD.getTotalMomentRate());
		}
		else if(backgroundTreatment.equals(SET_FOR_BCK_PARAM_BCK_MAX_MAG)) {
			double magMax = ((Double)backSeisMaxMagParam.getValue()).doubleValue();
			totBackgroundMFD = new GutenbergRichterMagFreqDist(MIN_MAG, NUM_MAG, DELTA_MAG);
			((GutenbergRichterMagFreqDist) totBackgroundMFD).setAllButTotMoRate(MIN_MAG, magMax, totBackRate, bValue);
		}
		else { // the SET_FOR_BCK_PARAM_NSHMP07 case
//			boolean bulgeReduction = ((Boolean)bulgeReductionBooleanParam.getValue()).booleanValue();
//			boolean maxMagGrid = ((Boolean)maxMagGridBooleanParam.getValue()).booleanValue();
			totBackgroundMFD = nshmp_gridSrcGen.getTotMFDForRegion(null, false,true,true, true);
			// totBackgroundMFD = getNSHMP02_Backgr_MFD();
			// totBackgroundMFD.scaleToCumRate(5.0,totBackRate);

			// Test of Golden's proposed solution
			//for(int i=totBackgroundMFD.getXIndex(6.5);i<totBackgroundMFD.getNum();i++)
			//	totBackgroundMFD.set(i,0.33*totBackgroundMFD.getY(i));
		}
		String backSeis = (String)backSeisParam.getValue();
		ArrayList<ProbEqkSource> backgroundSources;
		// if background sources are included
		// if background sources are included
		if(backSeis.equalsIgnoreCase(UCERF2.BACK_SEIS_INCLUDE) || 
				backSeis.equalsIgnoreCase(UCERF2.BACK_SEIS_ONLY)) {
			String backSeisRup = (String)this.backSeisRupParam.getValue();
			if(backSeisRup.equalsIgnoreCase(UCERF2.BACK_SEIS_RUP_POINT)) {
				nshmp_gridSrcGen.setAsPointSources(true);
				//allSources.addAll(nshmp_gridSrcGen.getAllRandomStrikeGriddedSources(timeSpan.getDuration()));
				
			} else if(backSeisRup.equalsIgnoreCase(UCERF2.BACK_SEIS_RUP_FINITE)) {
				nshmp_gridSrcGen.setAsPointSources(false);
				//allSources.addAll(nshmp_gridSrcGen.getAllRandomStrikeGriddedSources(timeSpan.getDuration()));

			} else { // Cross hair ruptures
				nshmp_gridSrcGen.setAsPointSources(false);
				//allSources.addAll(nshmp_gridSrcGen.getAllCrosshairGriddedSources(timeSpan.getDuration()));

			}
			allSources.addAll(nshmp_gridSrcGen.getAllFixedStrikeSources(timeSpan.getDuration()));
		}

		this.reCalcBck = false; 

//		System.out.println(totBackgroundMFD.getTotalMomentRate()+","+totBackgroundMFD.getTotalIncrRate());


		//

		// now subtract the A, B, & C fault/zone rates
		//rate -= this.bFaultCharSummedMFD.getTotalIncrRate();
		//rate -= this.bFaultGR_SummedMFD.getTotalIncrRate();
		//	rate -= this.aFaultSummedMFD.getTotalIncrRate();
		/*
		 totBackgroundMFD = new IncrementalMagFreqDist(MIN_MAG, NUM_MAG, DELTA_MAG);
		 IncrementalMagFreqDist cumTotBackgroundMFD = new IncrementalMagFreqDist(MIN_MAG, NUM_MAG, DELTA_MAG);
		 double backRate, targetRate, aRate, bRateGR, bRateChar, cRate, mag;
		 for(int i=0; i<totBackgroundMFD.getNum(); i++) {
		 mag = totBackgroundMFD.getX(i);
		 if(mag <= magMax) {
		 targetRate = targetRegionalMFD.getCumRate(mag);
		 aRate = aFaultSummedMFD.getCumRate(mag);
		 bRateGR = bFaultGR_SummedMFD.getCumRate(mag);
		 bRateChar = bFaultCharSummedMFD.getCumRate(mag);
		 cRate = cZoneSummedMFD.getCumRate(mag);
		 backRate = targetRate - aRate - bRateGR - bRateChar - cRate;
		 //if(mag==5) System.out.println(targetRate +" "+ aRate +" "+bRateGR +" "+bRateChar+" "+cRate+" "+backRate);
		  if (backRate > 0) cumTotBackgroundMFD.set(mag,backRate);
		  }
		  }
		  int i;
		  for( i=0; i<totBackgroundMFD.getNum()-1; i++) {
		  totBackgroundMFD.set(i, cumTotBackgroundMFD.getY(i) - cumTotBackgroundMFD.getY(i+1) );
		  }
		  totBackgroundMFD.set(i, cumTotBackgroundMFD.getY(i));
		 */
	}

	/**
	 * This returns the total MFD for the NSHMP02 background seismicity (not including
	 * their C zones).  The data here were generated by running the method:
	 * Frankel02_AdjustableEqkRupForecast.getTotalBackgroundMFD_InsideRELM_region()
	 * and then shifting the mags by 0.05 (done in the main method of that class).

	 * @return
	 */
	private IncrementalMagFreqDist getNSHMP02_Backgr_MFD() {
		IncrementalMagFreqDist nshmp02_Backgr_MFD = new IncrementalMagFreqDist(MIN_MAG, NUM_MAG, DELTA_MAG);
		nshmp02_Backgr_MFD.set(5.0, 0.6585475);
		nshmp02_Backgr_MFD.set(5.1, 0.54740715);
		nshmp02_Backgr_MFD.set(5.2, 0.45473993);
		nshmp02_Backgr_MFD.set(5.3, 0.37777004);
		nshmp02_Backgr_MFD.set(5.4, 0.31383651);
		nshmp02_Backgr_MFD.set(5.5, 0.26072985);
		nshmp02_Backgr_MFD.set(5.6, 0.21661529);
		nshmp02_Backgr_MFD.set(5.7, 0.17996927);
		nshmp02_Backgr_MFD.set(5.8, 0.14947392);
		nshmp02_Backgr_MFD.set(5.9, 0.12414886);
		nshmp02_Backgr_MFD.set(6.0, 0.1005595);
		nshmp02_Backgr_MFD.set(6.1, 0.081493765);
		nshmp02_Backgr_MFD.set(6.2, 0.06763025);
		nshmp02_Backgr_MFD.set(6.3, 0.056068648);
		nshmp02_Backgr_MFD.set(6.4, 0.046449963);
		nshmp02_Backgr_MFD.set(6.5, 0.034433957);
		nshmp02_Backgr_MFD.set(6.6, 0.025387786);
		nshmp02_Backgr_MFD.set(6.7, 0.020769943);
		nshmp02_Backgr_MFD.set(6.8, 0.016882885);
		nshmp02_Backgr_MFD.set(6.9, 0.013718917);
		nshmp02_Backgr_MFD.set(7.0, 0.0021095828);
//		nshmp02_Backgr_MFD.set(7.1, 3.271536E-4);
//		nshmp02_Backgr_MFD.set(7.2, 2.0748665E-4);
//		nshmp02_Backgr_MFD.set(7.3, 1.3159173E-4);
//		nshmp02_Backgr_MFD.set(7.4, 1.09453234E-4);

		return nshmp02_Backgr_MFD;
	}


	/**
	 * This currently just computes the MFD for each C zone (need to add the actual sources).
	 * Adding the actual sources should be easy from nshmp_srcGen
	 *
	 */
	private void makeC_ZoneSources() {
		cZoneSummedMFD = new SummedMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		cZonesMFD_List = new ArrayList<IncrementalMagFreqDist> ();
		double cZoneWt = ((Double)c_ZoneWtParam.getValue()).doubleValue();
		if(cZoneWt > 0.0) {
//			if(((Boolean)includeC_ZonesParam.getValue()).booleanValue()) {
			/* 			
			String []names = { "Foothills Fault System", "Mohawk-Honey Lake Zone",
					"Northeastern California", "Western Nevada", "Eastern California Shear Zone N",
					"Eastern California Shear Zone S", "Imperial Valley", "San Gorgonio Knot"};

			double[] slipRates = { 0.1, 4.0, 8.0, 8.0, 7.0, 10.0, 14.0, 2.0}; // mm/yr
			double[] depthTop = { 0, 0, 0, 0, 0, 0, 0, 0}; // km
			double[] depthBottom = { 12, 15, 15, 15, 14, 15.5, 12.6, 7}; //km
			double[] strike = { 325, 335, 315, 315, 320, 320, 310, 290};
			double[] length = { 360, 88, 230, 245, 180, 88, 58, 100 }; // km
			double[] magLower = {6.0, 6.5, 6.5, 6.5, 6.5, 6.5, 6.5, 6.5}; 
			double[] magUpper = {7.0, 7.3, 7.3, 7.3, 7.6, 7.6, 7.3, 7.3};
			 */
			
			/*
			 * "Foothills Fault System" = area1 or shear1
			 * "Mohawk-Honey Lake Zone" = area3 or shear3
			 * "Northeastern California" = area2 or shear2
			 * "Western Nevada" = area4 or shear4 or Reno
			 * "Eastern California Shear Zone" = Mojave
			 */

			String []names = {"Foothills Fault System", "Mohawk-Honey Lake Zone",
					"Northeastern California", "Western Nevada", 
					"Eastern California Shear Zone", "San Gorgonio Knot"};

			double[] slipRates = { 0.1, 4.0, 4.0, 8.0, 4.0, 4.0}; // mm/yr
			double[] depthTop = { 0, 0, 0, 0, 0, 0}; // km
			double[] depthBottom = { 12, 15, 15, 15, 15, 18}; //km
			double[] strike = { 325, 315, 335, 315, 313, 293};
			double[] length = { 360, 88, 230, 245, 219, 102}; // km
			double[] magLower = {6.5, 6.5, 6.5, 6.5, 6.5, 6.5}; 
			double[] magUpper = {7.6, 7.6, 7.6, 7.6, 7.6, 7.6};

			double bValue = 0.8;
			double moRate, slipRate;
			for(int i=0; i<names.length; ++i) {
				// reduce slip rate by total moment rate reduction
//				slipRate = (1-totMoRateReduction)*slipRates[i]/1000.0;
				slipRate = cZoneWt*slipRates[i]/1000.0;
				moRate = FaultMomentCalc.getMoment((depthBottom[i]-depthTop[i])*length[i]*1e6, slipRate);
				GutenbergRichterMagFreqDist grMFD = new GutenbergRichterMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
				grMFD.setAllButTotCumRate(magLower[i]+DELTA_MAG/2, magUpper[i]-DELTA_MAG/2, moRate, bValue);
				grMFD.setName(names[i]);
				cZonesMFD_List.add(grMFD);
				cZoneSummedMFD.addIncrementalMagFreqDist(grMFD);
			}
		}
		this.reCalcC_Zones = false;
	}

	private void mkA_FaultSegmentedSources() {
		double relativeA_PrioriWeight = ((Double)relativeA_PrioriWeightParam.getValue()).doubleValue();
		double relativeSegRateWeight = ((Double)relativeSegRateWeightParam.getValue()).doubleValue();
		double magSigma  = ((Double) magSigmaParam.getValue()).doubleValue();
		double magTruncLevel = ((Double) truncLevelParam.getValue()).doubleValue();
		ParameterList rupModels = (ParameterList) this.segmentedRupModelParam.getValue();
		String slipModel = (String)slipModelParam.getValue();
		boolean isAseisReducesArea = ((Boolean) aseisFactorInterParam.getValue()).booleanValue();
		double meanMagCorrection = ((Double)meanMagCorrectionParam.getValue()).doubleValue();
//		boolean preserveMinAFaultRate = ((Boolean) preserveMinAFaultRateParam.getValue()).booleanValue();
		boolean wtedInversion = ((Boolean) weightedInversionParam.getValue()).booleanValue();
		// this gets a list of FaultSegmentData objects (one for each A fault, and for the deformation model previously set)
		ArrayList aFaultSegmentData = aFaultsFetcher.getFaultSegmentDataList(isAseisReducesArea);
		aFaultSourceGenerators = new ArrayList();
		aFaultSummedMFD = new SummedMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		double duration = timeSpan.getDuration();
//		boolean isTimeIndepenent = isTimeIndependent();
		double startYear = Double.NaN, aperiodicity = Double.NaN;
		boolean isSegDependentAperiodicity = false;

		if(this.probModelParam.getValue().equals(PROB_MODEL_BPT)) { // for time dependence
			startYear = this.timeSpan.getStartTimeYear();
			isSegDependentAperiodicity = ((Boolean)this.segDepAperiodicityParam.getValue()).booleanValue();
			aperiodicity = ((Double)this.aperiodicityParam.getValue()).doubleValue();
		}

		for(int i=0; i<aFaultSegmentData.size(); ++i) {
			FaultSegmentData segmentData = (FaultSegmentData) aFaultSegmentData.get(i);
			ValueWeight[] aPrioriRates = aFaultsFetcher.getAprioriRupRates(segmentData.getFaultName(), (String)rupModels.getValue(segmentData.getFaultName()));

			// set the min-rate constraint and correct bogus, indicator rates in aPrioriRates
			double minRates[] = new double[aPrioriRates.length];
			double minRateFrac1 = ((Double)minA_FaultRate1Param.getValue()).doubleValue(); // for unknown ruptures
			double minRateFrac2 = ((Double)minA_FaultRate2Param.getValue()).doubleValue(); // for unlikely ruptures
			double minRate = Double.MAX_VALUE;
			for(int rup=0; rup<aPrioriRates.length; rup++) // find minimum, ignoring values less than zero which are indicators
				if(aPrioriRates[rup].getValue() < minRate && aPrioriRates[rup].getValue() >= 0) minRate = aPrioriRates[rup].getValue();
			for(int rup=0; rup<aPrioriRates.length; rup++) {
				double rate = aPrioriRates[rup].getValue();
				if(rate >= 0) minRates[rup] = minRate*minRateFrac1; // treat it as unknowns
				else if (rate == -1) {
					minRates[rup] = minRate*minRateFrac1;
					aPrioriRates[rup].setValue(0.0);   // over ride bogus indicator value with zero
				}
				else if (rate == -2) {
					minRates[rup] = minRate*minRateFrac2;
					aPrioriRates[rup].setValue(0.0);   // over ride bogus indicator value with zero
				}
				else 
					throw new RuntimeException("Problem with a-priori rates for fault "+segmentData.getFaultName());
//				System.out.println(rup+"  "+(float)minRates[rup]+"  "+segmentData.getFaultName());
			}

			A_FaultSegmentedSourceGenerator aFaultSourceGenerator = new A_FaultSegmentedSourceGenerator(segmentData, 
					getMagAreaRelationship(), slipModel, aPrioriRates, magSigma, 
					magTruncLevel, totMoRateReduction, meanMagCorrection,minRates, 
					wtedInversion, relativeSegRateWeight, relativeA_PrioriWeight);
			aFaultSourceGenerators.add(aFaultSourceGenerator);
			if(this.probModelParam.getValue().equals(PROB_MODEL_POISSON)) // time Independent
				allSources.addAll(aFaultSourceGenerator.getTimeIndependentSources(duration));
			else if(this.probModelParam.getValue().equals(PROB_MODEL_BPT)) { // Time dependence
				allSources.addAll(aFaultSourceGenerator.getTimeDependentSources(duration, startYear, aperiodicity, isSegDependentAperiodicity));
			} else { // Empirical Model
				allSources.addAll(aFaultSourceGenerator.getTimeDepEmpiricalSources(duration, empiricalModel));
			}
			aFaultSummedMFD.addIncrementalMagFreqDist(aFaultSourceGenerator.getTotalRupMFD());
			//System.out.println("************"+i+"******"+aFaultSummedMFD.toString());
		
		
	}
		reCalcA_Faults=false;
	}


	/**
	 * This is a quick fix.  We should really use our A_FaultFloatingSource since it has a lot of
	 * other capabilities.
	 *
	 */
	private void mkA_FaultUnsegmentedSources() {
		double magSigma  = ((Double) magSigmaParam.getValue()).doubleValue();
		double magTruncLevel = ((Double) truncLevelParam.getValue()).doubleValue();
//		double fractCharVsGR= ((Double) percentCharVsGRParam.getValue()).doubleValue()/100.0;
		double fractCharVsGR= 0.0;
		MagAreaRelationship magAreaRel = getMagAreaRelationship();
		boolean isAseisReducesArea = ((Boolean) aseisFactorInterParam.getValue()).booleanValue();
		double bValue = ((Double) aFaultB_ValParam.getValue()).doubleValue();
		double meanMagCorrection = ((Double)meanMagCorrectionParam.getValue()).doubleValue();
		double minMagGR = ((Double) bFaultsMinMagParam.getValue()).doubleValue();
//		this gets a list of FaultSegmentData objects (one for each A fault, and for the deformation model previously set)	
		ArrayList aFaultSegmentData = aFaultsFetcher.getFaultSegmentDataList(isAseisReducesArea);
		aFaultSourceGenerators = new ArrayList();
		aFaultSummedMFD = new SummedMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		double duration = timeSpan.getDuration();
		EmpiricalModel empiricalModel  = null;
		int floaterType = getFloaterType();
		if(this.probModelParam.getValue().equals(this.PROB_MODEL_EMPIRICAL)) empiricalModel = this.empiricalModel;
			
		for(int i=0; i<aFaultSegmentData.size(); ++i) {
			FaultSegmentData segmentData = (FaultSegmentData) aFaultSegmentData.get(i);	
			UnsegmentedSource source = new UnsegmentedSource( segmentData,  magAreaRel, 
					fractCharVsGR,  MIN_MAG, MAX_MAG, NUM_MAG, magSigma, magTruncLevel, 
					minMagGR, bValue, totMoRateReduction, Double.NaN, Double.NaN, 
					meanMagCorrection, empiricalModel, floaterType);
			source.setDuration(duration);
//			the following isn't really correct (not a srcGen, but rather a src)
			aFaultSourceGenerators.add(source);
			allSources.add(source);
			aFaultSummedMFD.addIncrementalMagFreqDist(source.getMagFreqDist());   		
		}
		reCalcA_Faults=false;
	}
	
	/**
	 * Get the Types of floaters desired
	 * @param floaterType - FULL_DDW_FLOATER (0) = only along strike ( rupture full DDW); 
	 *                      STRIKE_AND_DOWNDIP_FLOATER (1) = float along strike and down dip;
	 *                      CENTERED_DOWNDIP_FLOATER (2) = float along strike & centered down dip

	 * @return
	 */
	private int getFloaterType() {
		String floaterType = (String)floaterTypeParam.getValue();
		if(floaterType.equalsIgnoreCase(FULL_DDW_FLOATER)) return UnsegmentedSource.FULL_DDW_FLOATER;
		else if(floaterType.equalsIgnoreCase(STRIKE_AND_DOWNDIP_FLOATER)) return UnsegmentedSource.STRIKE_AND_DOWNDIP_FLOATER;
		else if(floaterType.equalsIgnoreCase(CENTERED_DOWNDIP_FLOATER)) return UnsegmentedSource.CENTERED_DOWNDIP_FLOATER;
		throw new RuntimeException("Unsupported Floating ruptures option");
	}

	private void mkB_FaultSources() {
		double magSigma  = ((Double) magSigmaParam.getValue()).doubleValue();
		double magTruncLevel = ((Double) truncLevelParam.getValue()).doubleValue();
		double fractCharVsGR= ((Double) percentCharVsGRParam.getValue()).doubleValue()/100.0;
		MagAreaRelationship magAreaRel = getMagAreaRelationship();
		boolean isAseisReducesArea = ((Boolean) aseisFactorInterParam.getValue()).booleanValue();
		double meanMagCorrection = ((Double)meanMagCorrectionParam.getValue()).doubleValue();
		double minMagGR = ((Double) bFaultsMinMagParam.getValue()).doubleValue();
		double bValue = ((Double) bFaultB_ValParam.getValue()).doubleValue();
//		this gets a list of FaultSegmentData objects (one for each B fault, and for the deformation model previously set)
		ArrayList bFaultSegmentData = bFaultsFetcher.getFaultSegmentDataList(isAseisReducesArea);
//		ArrayList B_faultCharMFDs = new ArrayList();
//		ArrayList B_faultGR_MFDs = new ArrayList();
		bFaultCharSummedMFD= new SummedMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		bFaultGR_SummedMFD= new SummedMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		int floaterType = getFloaterType();
		bFaultSources = new ArrayList();
		double duration = timeSpan.getDuration();
		double fixMag, fixRate;
		try{
			EmpiricalModel empiricalModel  = null;
			if(this.probModelParam.getValue().equals(this.PROB_MODEL_EMPIRICAL)) empiricalModel = this.empiricalModel;

			//FileWriter fw1 = new FileWriter("B_Char_Temp.txt");
			//FileWriter fw2 = new FileWriter("B_GR_Temp.txt");
			for(int i=0; i<bFaultSegmentData.size(); ++i) {
				FaultSegmentData segmentData = (FaultSegmentData)bFaultSegmentData.get(i);
//				Fixes no longer used
//				fixMag = bFaultFixes.getMag(segmentData.getFaultName());
//				fixRate = bFaultFixes.getRate(segmentData.getFaultName());
				fixMag = Double.NaN;
				fixRate = Double.NaN;
				//if(!Double.isNaN(fixMag)) {
				//	System.out.println(segmentData.getFaultName()+","+fixMag+","+fixRate);
				//}
				// skip Mendocino (hard coded for now)
				if(segmentData.getFaultName().equals("Mendocino") ||
						segmentData.getFaultName().equals("Brawley (Seismic Zone), alt 1")	||
						segmentData.getFaultName().equals("Brawley (Seismic Zone), alt 2") ||
						segmentData.getFaultName().equals("Carson Range (Genoa)") ||
						segmentData.getFaultName().equals("Antelope Valley")) {
//					System.out.println(segmentData.getFaultName());
					continue;
				}
				UnsegmentedSource source = new UnsegmentedSource( segmentData,  magAreaRel, 
						fractCharVsGR,  MIN_MAG, MAX_MAG, NUM_MAG, magSigma, magTruncLevel,minMagGR, 
						bValue, totMoRateReduction, fixMag, fixRate, 
						meanMagCorrection, empiricalModel, floaterType);
				source.setDuration(duration);
				bFaultSources.add(source);
				allSources.add(source);
				IncrementalMagFreqDist charMagFreqDist = source.getCharMagFreqDist();
				//fw1.write(segmentData.getFaultName()+";"+(float)charMagFreqDist.getCumRate(6.5)+"\n");
				bFaultCharSummedMFD.addIncrementalMagFreqDist(charMagFreqDist);
				IncrementalMagFreqDist grMagFreqDist = source.getGR_MagFreqDist();
				if(source.getGR_MagFreqDist() != null)  {// will be null if char mag is lower than mag lower of GR
					bFaultGR_SummedMFD.addIncrementalMagFreqDist(grMagFreqDist);
					//fw2.write(segmentData.getFaultName()+";"+(float)grMagFreqDist.getCumRate(6.5)+"\n");
				}
			}
			
			reCalcB_Faults=false;
			//fw1.close();
			//fw2.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	private void mkNonCA_B_FaultSources() {
		double magSigma  = ((Double) magSigmaParam.getValue()).doubleValue();
		double magTruncLevel = ((Double) truncLevelParam.getValue()).doubleValue();
		double duration = timeSpan.getDuration();
		NonCA_FaultsFetcher fetcher = new NonCA_FaultsFetcher();
		EmpiricalModel empiricalModel  = null;
		if(this.probModelParam.getValue().equals(PROB_MODEL_EMPIRICAL)) empiricalModel = this.empiricalModel;
		ArrayList sources = fetcher.getSources(NON_CA_SOURCES_FILENAME, duration, magSigma, magTruncLevel,RUP_OFFSET, empiricalModel);
		nonCA_bFaultSources = new ArrayList();
		nonCA_bFaultSources.addAll(sources);
		allSources.addAll(sources);
		nonCA_B_FaultsSummedMFD = fetcher.getSummedMFD();
		reCalcNonCA_B_Fauts=false;
//System.out.println("Non CA B-Faults");
//for(int i=0; i <nonCA_bFaultSources.size(); i++)
//	System.out.println(nonCA_bFaultSources.get(i).getName());
	}



	/**
	 * Get a List of A_FaultSegmentedSorce objects. 
	 * Returns a list of  UnsegmentedFaultSource in case of unsegmented.
	 * 
	 * @return
	 */
	public ArrayList get_A_FaultSourceGenerators() {
		return this.aFaultSourceGenerators;
	}

	
	/**
	 * Get a List of Non-CA b Fault sources 
	 * 
	 * @return
	 */
	public ArrayList getNonCA_B_FaultSources() {
		return this.nonCA_bFaultSources;
	}

	/**
	 * Get a List of b Fault sources (objects of UnsegmentedFaultSource)
	 * 
	 * @return
	 */
	public ArrayList get_B_FaultSources() {
		return this.bFaultSources;
	}



	/**
	 * Get the list of all earthquake sources.
	 *
	 * @return ArrayList of Prob Earthquake sources
	 */
	public ArrayList  getSourceList(){
		ArrayList sourceList = new ArrayList();
		sourceList.addAll(allSources);

		
		boolean isBackground = backSeisParam.getValue().equals(UCERF2.BACK_SEIS_INCLUDE) ||
				backSeisParam.getValue().equals(UCERF2.BACK_SEIS_ONLY);
		
		if( isBackground &&
				this.backSeisRupParam.getValue().equals(UCERF2.BACK_SEIS_RUP_CROSSHAIR))
			sourceList.addAll(nshmp_gridSrcGen.getAllCrosshairGriddedSources(timeSpan.getDuration()));
		else if(isBackground)
			sourceList.addAll(nshmp_gridSrcGen.getAllRandomStrikeGriddedSources(timeSpan.getDuration()));

		return sourceList;
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
	 * @return
	 */
	public ArrayList<ArbitrarilyDiscretizedFunc> getObsIncrMFD(boolean includeAftershocks) {
		boolean includeAfterShocks = areAfterShocksIncluded();
		ArrayList<EvenlyDiscretizedFunc> obsCumMFD = getObsCumMFD(includeAfterShocks);
		return getIncrFromCumMFD(obsCumMFD);
	}
	
	
	/**
	 * Get observed incremental MFD for No Cal region
	 * @return
	 */
	public ArrayList<ArbitrarilyDiscretizedFunc> getObsIncrNoCalMFD() {
		ArrayList<EvenlyDiscretizedFunc> obsCumMFD = this.getObsCumNoCalMFD();
		return getIncrFromCumMFD(obsCumMFD);
	}

	/**
	 * Get observed incremental MFD for So Cal region
	 * @return
	 */
	public ArrayList<ArbitrarilyDiscretizedFunc> getObsIncrSoCalMFD() {
		ArrayList<EvenlyDiscretizedFunc> obsCumMFD = this.getObsCumSoCalMFD();
		return getIncrFromCumMFD(obsCumMFD);
	}
	/**
	 * Get the incremental MFD from Cum MFD
	 * @param obsCumMFD
	 * @return
	 */
	private ArrayList<ArbitrarilyDiscretizedFunc> getIncrFromCumMFD(ArrayList<EvenlyDiscretizedFunc> obsCumMFD) {
		ArrayList<ArbitrarilyDiscretizedFunc> obsIncrMFDList = new ArrayList<ArbitrarilyDiscretizedFunc>();
		// Only get the best estimate because 95% conf bounds may not be legit 
		for(int i=0; i<1; ++i) {
			EvenlyDiscretizedFunc cumMFD = obsCumMFD.get(i);
			ArbIncrementalMagFreqDist arbIncrMFD = new ArbIncrementalMagFreqDist(cumMFD.getMinX()+UCERF2.DELTA_MAG, cumMFD.getMaxX()-UCERF2.DELTA_MAG, 24);
//			System.out.println("deltaMag="+arbIncrMFD.getDelta()+"  "+arbIncrMFD.getMinX()+"  "+arbIncrMFD.getMaxX());
			arbIncrMFD.setCumRateDist(cumMFD);
			ArbitrarilyDiscretizedFunc arbDiscFun = new ArbitrarilyDiscretizedFunc();
			arbDiscFun.set(5.1, arbIncrMFD.getY(5.1));
			arbDiscFun.set(5.5, arbIncrMFD.getY(5.5));
			arbDiscFun.set(6.0, arbIncrMFD.getY(6.0));
			arbDiscFun.set(6.5, arbIncrMFD.getY(6.5));
			arbDiscFun.set(7.0, arbIncrMFD.getY(7.0));
			arbDiscFun.set(7.4, arbIncrMFD.getY(7.4));
			obsIncrMFDList.add(arbDiscFun);
		}
		return obsIncrMFDList;
	}

	
	/**
	 * This returns an ArrayList of EvenlyDiscretizedFunc that have cumulative 
	 * MFD for Karen Felzer's observed MFD in NoCal Polygon 
	 * and upper and lower confidence MFDs
	 * ( sent by Karen via  email on 09/27/07).
	 * @return
	 */
	public ArrayList<EvenlyDiscretizedFunc> getObsCumNoCalMFD() {
		EvenlyDiscretizedFunc obsCumMFD = new IncrementalMagFreqDist(5.0, 7.5, 6);
		EvenlyDiscretizedFunc obsCumLowMFD = new IncrementalMagFreqDist(5.0, 7.5, 6);
		EvenlyDiscretizedFunc obsCumHighMFD = new IncrementalMagFreqDist(5.0, 7.5, 6);
		double[] cumRates = {    1.32,      0.56,      0.25,      0.06,      0.03,      0.007};
		double[] cumRatesLow =  {1.32-0.26, 0.56-0.18, 0.25-0.13, 0.06-0.03, 0.03-0.02, 0.007-0.0066};
		double[] cumRatesHigh = {1.32+0.30, 0.56+0.23, 0.25+0.2, 0.06+0.05, 0.03+0.044, 0.007+0.026};


		for(int i=5; i>=0; i--) {
			obsCumMFD.set(i, cumRates[i]);
			obsCumLowMFD.set(i, cumRatesLow[i]);
			obsCumHighMFD.set(i, cumRatesHigh[i]);
		}
		obsCumMFD.setInfo("Cumulative MFD for observed catalog for No Cal polygon (from Karen Felzer's Sep 27, 2007 email)");
		obsCumLowMFD.setInfo("Lower 95% confidence of cumulative MFD for No Cal polygon(from Karen Felzer's Sep 27, 2007 email)");
		obsCumHighMFD.setInfo("Upper 95% confidence of cumulative MFD for No Cal polygon (from Karen Felzer's Sep 27, 2007 email)");

		ArrayList obsCumList = new ArrayList();
		obsCumList.add(obsCumMFD);
		obsCumList.add(obsCumLowMFD);
		obsCumList.add(obsCumHighMFD);
		return obsCumList;
	}
	
	
	/**
	 * This returns an ArrayList of EvenlyDiscretizedFunc that have cumulative 
	 * MFD for Karen Felzer's observed MFD in SoCal Polygon 
	 * and upper and lower confidence MFDs
	 * ( sent by Karen via  email on 09/27/07).
	 * @return
	 */
	public ArrayList<EvenlyDiscretizedFunc> getObsCumSoCalMFD() {
		EvenlyDiscretizedFunc obsCumMFD = new IncrementalMagFreqDist(5.0, 7.5, 6);
		EvenlyDiscretizedFunc obsCumLowMFD = new IncrementalMagFreqDist(5.0, 7.5, 6);
		EvenlyDiscretizedFunc obsCumHighMFD = new IncrementalMagFreqDist(5.0, 7.5, 6);
		double[] cumRates = {    1.43,      0.77,      0.31,      0.16,      0.043,      0.014};
		double[] cumRatesLow =  {1.43-0.27, 0.77-0.21, 0.31-0.13, 0.16-0.06, 0.043-0.03, 0.014-0.012};
		double[] cumRatesHigh = {1.43+0.30, 0.77+0.25, 0.31+0.18, 0.16+0.09, 0.043+0.05, 0.014+0.03};


		for(int i=5; i>=0; i--) {
			obsCumMFD.set(i, cumRates[i]);
			obsCumLowMFD.set(i, cumRatesLow[i]);
			obsCumHighMFD.set(i, cumRatesHigh[i]);
		}
		obsCumMFD.setInfo("Cumulative MFD for observed catalog for So Cal polygon (from Karen Felzer's Sep 27, 2007 email)");
		obsCumLowMFD.setInfo("Lower 95% confidence of cumulative MFD for So Cal polygon(from Karen Felzer's Sep 27, 2007 email)");
		obsCumHighMFD.setInfo("Upper 95% confidence of cumulative MFD for So Cal polygon (from Karen Felzer's Sep 27, 2007 email)");

		ArrayList obsCumList = new ArrayList();
		obsCumList.add(obsCumMFD);
		obsCumList.add(obsCumLowMFD);
		obsCumList.add(obsCumHighMFD);
		return obsCumList;
	}


	/**
	 * This returns an ArrayList of EvenlyDiscretizedFunc that have cumulative 
	 * MFD for Karen Felzer's observed MFD and upper and lower confidence MFDs
	 * (from Table 21 of Appendix_I_v04.pdf sent by Karen via  email on 09/24/07).
	 * @return
	 */
	public static ArrayList<EvenlyDiscretizedFunc> getObsCumMFD(boolean includeAftershocks) {
		EvenlyDiscretizedFunc obsCumMFD = new IncrementalMagFreqDist(5.0, 7.5, 6);
		EvenlyDiscretizedFunc obsCumLowMFD = new IncrementalMagFreqDist(5.0, 7.5, 6);
		EvenlyDiscretizedFunc obsCumHighMFD = new IncrementalMagFreqDist(5.0, 7.5, 6);
		double[] cumRatesWith =     {7.5,      2.4,      0.74,      0.23,       0.07,       0.017};
		double[] cumRatesLowWith =  {7.5-3.94,  2.4-1.1,  0.74-0.34, 0.23-0.11,  0.07-0.04,  0.017-0.013};
		double[] cumRatesHighWith = {7.5+3.0, 2.4+0.95, 0.74+0.29, 0.23+0.12, 0.07+0.06, 0.017+0.022};
		double[] cumRates = {    4.17,      1.65,      0.65,      0.24,      0.09,      0.02};
		double[] cumRatesLow =  {4.17-1.95, 1.65-0.66, 0.65-0.26, 0.24-0.11, 0.09-0.04, 0.02-0.016};
		double[] cumRatesHigh = {4.17+1.67, 1.65+0.66, 0.65+0.31, 0.24+0.11, 0.09+0.06, 0.02+0.024};


		if(includeAftershocks) {
			cumRates = cumRatesWith;
			cumRatesLow = cumRatesLowWith;
			cumRatesHigh = cumRatesHighWith;
		}

		for(int i=5; i>=0; i--) {
			obsCumMFD.set(i, cumRates[i]);
			obsCumLowMFD.set(i, cumRatesLow[i]);
			obsCumHighMFD.set(i, cumRatesHigh[i]);
		}
		if(includeAftershocks) {
			obsCumMFD.setInfo("Cumulative MFD for observed catalog including aftershocks (Table 21 of Karen Felzer's Appendix_I_v03.pdf)");
			obsCumLowMFD.setInfo("Lower 98% confidence of cumulative MFD for observed catalog including aftershocks (Table 21 of Karen Felzer's Appendix_I_v03.pdf)");
			obsCumHighMFD.setInfo("Upper 98% confidence of cumulative MFD for observed catalog including aftershocks (Table 21 of Karen Felzer's Appendix_I_v03.pdf)");
		}
		else {
			obsCumMFD.setInfo("Cumulative MFD for observed catalog excluding aftershocks (from Karen Felzer's Aug 27, 2007 email)");
			obsCumLowMFD.setInfo("Lower 95% confidence of cumulative MFD for observed catalog excluding aftershocks (from Karen Felzer's Aug 27, 2007 email)");
			obsCumHighMFD.setInfo("Upper 95% confidence of cumulative MFD for observed catalog excluding aftershocks (from Karen Felzer's Aug 27, 2007 email)");
		}

		/*
		 * Convert into incremental and find the moment rate
		 * 
		 IncrementalMagFreqDist mfd = new IncrementalMagFreqDist(5, 7.5, 6);
		for(int i=0; i<mfd.getNum(); ++i) {
			if(i==mfd.getNum()-1)
				mfd.set(i, obsCumMFD.getInterpolatedY(mfd.getX(i)));
			else 	
				mfd.set(i, obsCumMFD.getInterpolatedY(mfd.getX(i)) - obsCumMFD.getInterpolatedY(mfd.getX(i+1)));
		}
		System.out.println(mfd.toString());
		System.out.println("IncludeAftershocks="+includeAftershocks+", moRate="+mfd.getTotalMomentRate());

		 */

		ArrayList obsCumList = new ArrayList();
		obsCumList.add(obsCumMFD);
		obsCumList.add(obsCumLowMFD);
		obsCumList.add(obsCumHighMFD);
		return obsCumList;
	}

	
	
	/**
	 * Note that it calculates the WG02 region by including the complete San Gregorio
	 * 
	 * @param magProbDist
	 * @param region
	 */
	public void getTotal_B_FaultsProb(DiscretizedFuncAPI magProbDist, 
			Region region) {
		int numMags = magProbDist.getNum();
		for(int i=0; i<numMags; ++i) {
			double prob = 1;
			double minMag = magProbDist.getX(i);
			for(int srcIndex=0; srcIndex < bFaultSources.size(); srcIndex++)
				prob *= getProbForUnsegmentedSrc(bFaultSources.get(srcIndex), 
						 minMag,  region);
			magProbDist.set(i, 1.0 - prob);
		}
	}
	
	/**
	 * Get Probability for unsegmented source. Region does not matter if it WG02 region
	 * and faultName is San Gregorio
	 * 
	 * @param unsegmentedSrc
	 * @param minMag
	 * @param region
	 * @return
	 */
	private double getProbForSegmentedSrc(A_FaultSegmentedSourceGenerator segmentedSrcGenerator, 
			double minMag, Region region) {
		String faultName = segmentedSrcGenerator.getFaultSegmentData().getFaultName();
		if(faultName.equals("N. San Andreas")
				&& region instanceof CaliforniaRegions.WG02_GRIDDED) 
			return (1-segmentedSrcGenerator.getApproxTotFaultProb(minMag, null));
		else return 1-segmentedSrcGenerator.getApproxTotFaultProb(minMag, region);

	}
	
	/**
	 * Get Probability for unsegmented source. Region does not matter if it WG02 region
	 * and faultName is San Gregorio
	 * 
	 * @param unsegmentedSrc
	 * @param minMag
	 * @param region
	 * @return
	 */
	private double getProbForUnsegmentedSrc(UnsegmentedSource unsegmentedSrc, 
			double minMag, Region region) {
		String faultName = unsegmentedSrc.getFaultSegmentData().getFaultName();
		if((faultName.equals("San Gregorio Connected") || faultName.equals("N. San Andreas"))
				&& (region instanceof CaliforniaRegions.WG02_GRIDDED)) 
			return (1-unsegmentedSrc.computeApproxTotalProbAbove(minMag, null));
		else return 1-unsegmentedSrc.computeApproxTotalProbAbove(minMag, region);

	}
	
	/**
	 * Get Probs for a particular B-Fault
	 * 
	 * @param bFaultName
	 * @param magProbDist
	 * @param region
	 */
	public void getProbsForB_Fault(String bFaultName,
			DiscretizedFuncAPI magProbDist, Region region ) {
		int numMags = magProbDist.getNum();
		for(int srcIndex=0; srcIndex < bFaultSources.size(); srcIndex++) {
			if(bFaultSources.get(srcIndex).getFaultSegmentData().getFaultName().equals(bFaultName)) {
				for(int i=0; i<numMags; ++i) {
					double minMag = magProbDist.getX(i);
					double prob = getProbForUnsegmentedSrc(bFaultSources.get(srcIndex), 
							minMag,  region);
					magProbDist.set(i, 1-prob);
				}
				break;
			}
		}
	}
	

	public void getTotal_NonCA_B_FaultsProb(DiscretizedFuncAPI magProbDist, Region region) {
		int numMags = magProbDist.getNum();
		for(int i=0; i<numMags; ++i) {
			double prob = 1;
			double minMag = magProbDist.getX(i);
			for(int srcIndex=0; srcIndex < nonCA_bFaultSources.size(); srcIndex++)
				prob *= (1-nonCA_bFaultSources.get(srcIndex).computeApproxTotalProbAbove(minMag, region));
			magProbDist.set(i, 1.0-prob);
		}
	}
	
	/**
	 * Note that it calculates the WG02 region by including the complete N. San Andreas
	 * 
	 * @param magProbDist
	 * @param region
	 */
	public void getTotal_A_FaultsProb(DiscretizedFuncAPI magProbDist, 
			Region region) {
		int numMags = magProbDist.getNum();
		for(int i=0; i<numMags; ++i) {
			double prob = 1;
			double minMag = magProbDist.getX(i);
			for(int srcIndex=0; srcIndex < aFaultSourceGenerators.size(); srcIndex++) {
				Object source = aFaultSourceGenerators.get(srcIndex);
				if(source instanceof A_FaultSegmentedSourceGenerator) { // Segmented source 
					prob *= getProbForSegmentedSrc((A_FaultSegmentedSourceGenerator)source, minMag, region);
				}
				else  { // unsegmneted source
					prob *= this.getProbForUnsegmentedSrc((UnsegmentedSource)source, minMag, region);
				}
			}
			magProbDist.set(i, 1.0-prob);
		}
	}
	
	/**
	 * Note that it calculates the WG02 region by including the complete N. San Andreas
	 * 
	 * @param magProbDist
	 * @param region
	 */
	public void getProbForA_Fault(String aFaultName, DiscretizedFuncAPI magProbDist, 
			Region region) {
		int numMags = magProbDist.getNum();
		for(int srcIndex=0; srcIndex < aFaultSourceGenerators.size(); srcIndex++) {
			Object source = aFaultSourceGenerators.get(srcIndex);
			if(source instanceof A_FaultSegmentedSourceGenerator) { // Segmented source
				A_FaultSegmentedSourceGenerator srcGen = (A_FaultSegmentedSourceGenerator)source;
				if(srcGen.getFaultSegmentData().getFaultName().equals(aFaultName)) {
					for(int i=0; i<numMags; ++i) {
						double minMag = magProbDist.getX(i);
						double prob = getProbForSegmentedSrc(srcGen, minMag, region);
						magProbDist.set(i, 1-prob);
					}
					break;
				}
					
			}
			else  { // Unsegmented source
				UnsegmentedSource unsegmentedSrc = (UnsegmentedSource)source;
				if(aFaultName.equalsIgnoreCase("San Jacinto")) {
					DiscretizedFuncAPI sj1 = magProbDist.deepClone();
					DiscretizedFuncAPI sj2 = magProbDist.deepClone();
					getProbForA_Fault("San Jacinto (SB to C)", sj1, region);
					getProbForA_Fault("San Jacinto (CC to SM)", sj2, region);
					for(int i=0; i<numMags; ++i) {
						double prob = (1-sj1.getY(i))*(1-sj2.getY(i));
						magProbDist.set(i, 1-prob);
					}
					break;
				}
				else if(unsegmentedSrc.getFaultSegmentData().getFaultName().equals(aFaultName)) {
					for(int i=0; i<numMags; ++i) {
						double minMag = magProbDist.getX(i);
						double prob = getProbForUnsegmentedSrc(unsegmentedSrc, minMag, region);
						magProbDist.set(i, 1-prob);
					}
					break;
				}
			}
		}
	}

	// this assumes not time dependence
	public void getTotal_BackgroundProb(DiscretizedFuncAPI magProbDist, Region region) {
		int numMags = magProbDist.getNum();
//		boolean applyBulgeReduction = ((Boolean)bulgeReductionBooleanParam.getValue()).booleanValue();
//		boolean applyMaxMagGrid = ((Boolean)maxMagGridBooleanParam.getValue()).booleanValue();
		IncrementalMagFreqDist incrMFD= this.nshmp_gridSrcGen.getTotMFDForRegion(region, false, true, true, true);
		for(int i=0; i<numMags; ++i) {
			double minMag = magProbDist.getX(i);
			// make sure it goes to next highest; 1e-5 is to avoid numerical inprecisions
			int index = (int) Math.ceil((minMag-MIN_MAG-1e-5)/this.DELTA_MAG);
			magProbDist.set(i, 1-Math.exp(-timeSpan.getDuration()*incrMFD.getCumRate(index)));
		}
	}

	

	// this assumes not time dependence
	public void getTotal_BackgroundMFD(DiscretizedFuncAPI magFreqDist, Region region) {
		int numMags = magFreqDist.getNum();
//		boolean applyBulgeReduction = ((Boolean)bulgeReductionBooleanParam.getValue()).booleanValue();
//		boolean applyMaxMagGrid = ((Boolean)maxMagGridBooleanParam.getValue()).booleanValue();
		IncrementalMagFreqDist incrMFD= this.nshmp_gridSrcGen.getTotMFDForRegion(region, false, true, true, true);
		for(int i=0; i<numMags; ++i) {
			double minMag = magFreqDist.getX(i);
			// make sure it goes to next highest; 1e-5 is to avoid numerical inprecisions
			int index = (int) Math.ceil((minMag-MIN_MAG-1e-5)/this.DELTA_MAG);
			magFreqDist.set(i, incrMFD.getCumRate(index));
		}
	}

	// this assumes no time dependence
	public void getTotal_C_ZoneProb(DiscretizedFuncAPI magProbDist, Region region) {
		int numMags = magProbDist.getNum();
		IncrementalMagFreqDist incrMFD= this.nshmp_gridSrcGen.getTotalC_ZoneMFD_InRegion(region);
		for(int i=0; i<numMags; ++i) {
			double minMag = magProbDist.getX(i);
			// make sure it goes to next highest; 1e-5 is to avoid numerical inprecisions
			int index = (int) Math.ceil((minMag-MIN_MAG-1e-5)/this.DELTA_MAG);
			magProbDist.set(i, 1-Math.exp(-timeSpan.getDuration()*incrMFD.getCumRate(index)));
		}
	}

	public void getTotalProb(DiscretizedFuncAPI magProbDist, Region region) {
		int numMags = magProbDist.getNum();
		DiscretizedFuncAPI bFaultsProbDist = magProbDist.deepClone();
		DiscretizedFuncAPI nonCA_B_FaultsProbDist = magProbDist.deepClone();
		DiscretizedFuncAPI aFaultsProbDist = magProbDist.deepClone();
		DiscretizedFuncAPI bckProbDist = magProbDist.deepClone();
		DiscretizedFuncAPI cZoneProbDist = magProbDist.deepClone();
		
		getTotal_B_FaultsProb(bFaultsProbDist, region);
		getTotal_NonCA_B_FaultsProb(nonCA_B_FaultsProbDist, region);
		getTotal_A_FaultsProb(aFaultsProbDist, region);
		getTotal_BackgroundProb(bckProbDist, region);
		getTotal_C_ZoneProb(cZoneProbDist, region);
		
		for(int i=0; i<numMags; ++i) {
			double prob = 1;
			prob *= 1-bFaultsProbDist.getY(i);
			prob *= 1-nonCA_B_FaultsProbDist.getY(i);
			prob *= 1-aFaultsProbDist.getY(i);
			prob *= 1-bckProbDist.getY(i);
			prob *= 1-cZoneProbDist.getY(i);
			magProbDist.set(i, 1.0-prob);
		}
	}
	


	public IncrementalMagFreqDist getTotal_B_FaultsCharMFD() {
		return this.bFaultCharSummedMFD;
		//return new SummedMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
	}

	public IncrementalMagFreqDist getTotal_B_FaultsGR_MFD() {
		return this.bFaultGR_SummedMFD;
		//return new SummedMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
	} 

	public IncrementalMagFreqDist getTotal_NonCA_B_FaultsMFD() {
		return this.nonCA_B_FaultsSummedMFD;
	}
	
	public IncrementalMagFreqDist getTotal_A_FaultsMFD() {
		return this.aFaultSummedMFD;
	}

	public IncrementalMagFreqDist getTotal_BackgroundMFD() {
		return this.totBackgroundMFD;

	}

	public IncrementalMagFreqDist getTotal_C_ZoneMFD() {
		return this.cZoneSummedMFD;
		//return new SummedMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
	}

	/**
	 * Return a list of MFDs, one for each C zone
	 * @return
	 */
	public ArrayList<IncrementalMagFreqDist> getC_ZoneMFD_List() {
		return this.cZonesMFD_List;
	}

	public IncrementalMagFreqDist getTotalMFD() {
		SummedMagFreqDist totalMFD = new SummedMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		totalMFD.addIncrementalMagFreqDist(bFaultCharSummedMFD);
		totalMFD.addIncrementalMagFreqDist(bFaultGR_SummedMFD);
		totalMFD.addIncrementalMagFreqDist(aFaultSummedMFD);
		totalMFD.addIncrementalMagFreqDist(totBackgroundMFD);
		totalMFD.addIncrementalMagFreqDist(cZoneSummedMFD);
		totalMFD.addIncrementalMagFreqDist(nonCA_B_FaultsSummedMFD);
		return totalMFD;
	}


	/**
	 * This returns the summed GeneralizedPredictionError for all A-faults
	 * @return
	 */
	public double getGeneralPredErr() {
		double genPredErr = 0;
		Iterator it = this.aFaultSourceGenerators.iterator();
		while(it.hasNext()) {
			A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator)it.next();
			if(source.getTotalAPrioriRate() > 0.0) // filter out any bogus models (i.e., a-priori models not yet avail)
				genPredErr += source.getGeneralizedPredictionError();
		}
		return genPredErr;
	}

	/**
	 * This returns the summed NormModSlipRateError for all A-faults
	 * @return
	 */
	public double getModSlipRateError() {
		double modSlipRateError=0;
		Iterator it = this.aFaultSourceGenerators.iterator();
		while(it.hasNext()) {
			A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator)it.next();
			if(source.getTotalAPrioriRate() > 0.0) // filter out any bogus models (i.e., a-priori models not yet avail)
				modSlipRateError+=source.getNormModSlipRateError();
		}
		return modSlipRateError;
	}

	/**
	 * This returns the summed getNormDataER_Error for all A-faults
	 * @return
	 */
	public double getDataER_Err() {
		double dataER_Error=0;
		Iterator it = this.aFaultSourceGenerators.iterator();
		while(it.hasNext()) {
			A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator)it.next();
			if(source.getTotalAPrioriRate() > 0.0) // filter out any bogus models (i.e., a-priori models not yet avail)
				dataER_Error+=source.getNormDataER_Error();
		}
		return dataER_Error;
	}

	/**
	 * Get summed Normalized A-Priori rate error for all A faults
	 * @return
	 */
	public double getNormalizedA_PrioriRateErr() {
		double aPrioriRateError=0;
		Iterator it = this.aFaultSourceGenerators.iterator();
		while(it.hasNext()) {
			A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator)it.next();
			if(source.getTotalAPrioriRate() > 0.0) // filter out any bogus models (i.e., a-priori models not yet avail)
				aPrioriRateError+=source.getA_PrioriModelError();
		}
		return aPrioriRateError;
	}

	/**
	 * Get summed Non-Normzlized A-Priori Rate error for all A faults
	 * @return
	 */
	public double getNonNormalizedA_PrioriRateErr() {
		double nonNorm_aPrioriRateError=0;
		Iterator it = this.aFaultSourceGenerators.iterator();
		while(it.hasNext()) {
			A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator)it.next();
//			System.out.println(source.getName()+"  "+ source.getTotalAPrioriRate()+"  "+(source.getTotalAPrioriRate() > 0.0));
			if(source.getTotalAPrioriRate() > 0.0) // filter out any bogus models (i.e., a-priori models not yet avail)
				nonNorm_aPrioriRateError+=source.getNonNormA_PrioriModelError();
		}
		return nonNorm_aPrioriRateError;
	}


	

	/**
	 * update the forecast
	 **/

	public void updateForecast() {
		// update both A and B-Faults
		if(this.updateA_FaultsFetcher) this.updateFetchersBasedonDefModels();
		if(this.updateB_FaultsFetcher) { // only update B-Faults
			bFaultsFetcher.setDeformationModel( ((Boolean) connectMoreB_FaultsParam.getValue()).booleanValue(), 
					getSelectedDeformationModelSummary(), aFaultsFetcher);
			updateB_FaultsFetcher = false;
		}
		// compute total moment rate reduction for A/B faults (fraction to reduce by)
		double totToKeep = 1;
		// 1st remove that which goes to the background
		totToKeep *= 1.0-((Double) moRateFracToBackgroundParam.getValue()).doubleValue();
		// now remove that which goes to aseismicity
		totToKeep *= ((Double)couplingCoeffParam.getValue()).doubleValue();
		// finally, remove that which goes to aftershocks
		totToKeep *= 1-((Double) aftershockFractionParam.getValue()).doubleValue();
		totMoRateReduction = 1.0-totToKeep;

		// System.out.println("totMoRateReduction="+totMoRateReduction);
		this.allSources = new ArrayList();
		String rupModel = (String) rupModelParam.getValue();

		//System.out.println("Creating A Fault sources");
		if(rupModel.equalsIgnoreCase(UNSEGMENTED_A_FAULT_MODEL)) {

			// Note that BPT is same as Poisson in case of Unsegmented A-Fault sources
			mkA_FaultUnsegmentedSources();

			// Calculate Predicted event rates at the locations where we have obs (given in Tom Parson's excel sheet)
			// These are stored in the aFaultsFetcher for others to reference later
			ArrayList<EventRates> eventRatesList = this.aFaultsFetcher.getEventRatesList();
			int numSources = this.aFaultSourceGenerators.size();
			//System.out.println(numSources);
			for(int locIndex=0; locIndex<eventRatesList.size(); ++locIndex) {
				EventRates event = eventRatesList.get(locIndex);	
				double rate = 0, obsRate = 0;
				Location loc;
				for(int iSource=0; iSource<numSources; ++iSource) {
					UnsegmentedSource source = (UnsegmentedSource)aFaultSourceGenerators.get(iSource);
					if(source.getFaultSegmentData().getFaultName().equalsIgnoreCase(event.getFaultName())) {
						loc = new Location(event.getLatitude(), event.getLongitude());
						rate+=source.getPredEventRate(loc);
						obsRate+=source.getPredObsEventRate(loc);  // this one is reduced by the probability of it being paleoseismically observed
					}
				}
				event.setPredictedRate(rate);
				event.setPredictedObsRate(obsRate);
			}	
		}
		else 
			mkA_FaultSegmentedSources();
		/* */
		//System.out.println("Creating B Fault sources");
		mkB_FaultSources();
		
		mkNonCA_B_FaultSources();

		//System.out.println("Creating C Zone Fault sources");
		makeC_ZoneSources();

		//System.out.println("Creating Background sources");
		makeBackgroundGridSources();

	}

	/**
	 * Creates the timespan object based on if it is time dependent or time independent model.
	 */
	private void setTimespanParameter() {
		if (this.probModelParam.getValue().equals(PROB_MODEL_BPT)) {
			// create the time-dep timespan object with start time and duration in years
			timeSpan = new TimeSpan(TimeSpan.YEARS, TimeSpan.YEARS);
			// set duration
			timeSpan.setDuractionConstraint(DURATION_MIN, DURATION_MAX);
			timeSpan.setDuration(DURATION_DEFAULT);
			// set the start year 
			timeSpan.setStartTimeConstraint(TimeSpan.START_YEAR, START_TIME_MIN, START_TIME_MAX);
			timeSpan.setStartTime(START_TIME_DEFAULT);

			timeSpan.addParameterChangeListener(this);
		}
		else {
			// create the time-ind timespan object with start time and duration in years
			timeSpan = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS);
			timeSpan.setDuration(DURATION_DEFAULT);
			timeSpan.addParameterChangeListener(this);

		}
	}

	/**
	 *  This is the main function of this interface. Any time a control
	 *  paramater or independent paramater is changed by the user in a GUI this
	 *  function is called, and a paramater change event is passed in.
	 *
	 *  This sets the flag to indicate that the sources need to be updated
	 *
	 * @param  event
	 */
	public void parameterChange(ParameterChangeEvent event) {
		super.parameterChange(event);
		String paramName = event.getParameterName();

		/*if(paramName.equalsIgnoreCase(DEFORMATION_MODEL_PARAM_NAME)) {
			this.reCalcA_Faults = true;
			this.reCalcB_Faults = true;
		} else if(paramName.equalsIgnoreCase(ABC_MO_RATE_REDUCTION_PARAM_NAME)) {
			this.reCalcBck = true;
			this.reCalcA_Faults = true;
			this.reCalcB_Faults = true;
		} else if(paramName.equalsIgnoreCase(COUPLING_COEFF_PARAM_NAME)) {
			this.reCalcBck = true;
			this.reCalcA_Faults = true;
			this.reCalcB_Faults = true;
		}else if(paramName.equalsIgnoreCase(AFTERSHOCK_FRACTION_PARAM_NAME)) {
			this.reCalcBck = true;
			this.reCalcA_Faults = true;
			this.reCalcB_Faults = true;
		} else if(paramName.equalsIgnoreCase(RUP_MODEL_TYPE_NAME)) {
			this.reCalcA_Faults = true;
			this.reFetchFromDatabase =true;
		} else if(paramName.equalsIgnoreCase(this.SEGMENTED_A_FAULT_MODEL)) {
			this.reCalcA_Faults = true;
		} else if(paramName.equalsIgnoreCase(this.SLIP_MODEL_TYPE_NAME)) {
			this.reCalcA_Faults = true;
		} else if(paramName.equalsIgnoreCase(this.REL_A_PRIORI_WT_PARAM_NAME)) {
			this.reCalcA_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.REL_SEG_RATE_WT_PARAM_NAME)) {
			this.reCalcA_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.WEIGHTED_INVERSION_PARAM_NAME)) {
			this.reCalcA_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.MIN_A_FAULT_RATE_1_PARAM_NAME)) {
			this.reCalcA_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.MIN_A_FAULT_RATE_2_PARAM_NAME)) {
			this.reCalcA_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.MAG_AREA_RELS_PARAM_NAME)) {
			this.reCalcA_Faults = true;
			this.reCalcB_Faults  = true;
		}else if(paramName.equalsIgnoreCase(this.A_FAULTS_B_VAL_PARAM_NAME)) {
			this.reCalcA_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.MAG_SIGMA_PARAM_NAME)) {
			this.reCalcA_Faults = true;
			this.reCalcB_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.TRUNC_LEVEL_PARAM_NAME)) {
			this.reCalcA_Faults = true;
			this.reCalcB_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.MEAN_MAG_CORRECTION)) {
			this.reCalcA_Faults  =true;
			this.reCalcB_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.CHAR_VS_GR_PARAM_NAME)) {
			this.reCalcB_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.B_FAULTS_B_VAL_PARAM_NAME)) {
			this.reCalcB_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.B_FAULTS_MIN_MAG)) {
			this.reCalcB_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.CONNECT_B_FAULTS_PARAM_NAME)) {
			this.reFetchFromDatabase = true;
			this.reCalcB_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.C_ZONE_WT_PARAM_NAME)) {
			this.reCalcC_Zones  = true;
		}else if(paramName.equalsIgnoreCase(this.SET_FOR_BCK_PARAM_NAME)) {
			this.reCalcBck = true;
		}else if(paramName.equalsIgnoreCase(this.TOT_MAG_RATE_PARAM_NAME)) {
			this.reCalcBck = true;
		}else if(paramName.equalsIgnoreCase(this.BACK_SEIS_B_VAL_PARAM_NAME)) {
			this.reCalcBck = true;
		}else if(paramName.equalsIgnoreCase(this.MAX_MAG_GRID_PARAM_NAME)) {
			this.reCalcBck = true;
		}else if(paramName.equalsIgnoreCase(this.BULGE_REDUCTION_PARAM_NAME)) {
			this.reCalcBck = true;
		}else if(paramName.equalsIgnoreCase(this.BACK_SEIS_MAG_NAME)) {
			this.reCalcBck = true;
		} else if(paramName.equalsIgnoreCase(this.PROB_MODEL_PARAM_NAME)) {
			this.reCalcA_Faults  =true;
			this.reCalcB_Faults = true;
		} else if(paramName.equalsIgnoreCase(this.SEG_DEP_APERIODICITY_PARAM_NAME)) {
			this.reCalcA_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.DEF_APERIODICITY_PARAM_NAME)) {
			this.reCalcA_Faults = true;
		}else if(paramName.equalsIgnoreCase(this.APERIODICITY_PARAM_NAME)) {
			this.reCalcA_Faults = true;
		}*/
		
		if(paramName.equalsIgnoreCase(SET_FOR_BCK_PARAM_NAME) ||
				paramName.equalsIgnoreCase(SEG_DEP_APERIODICITY_PARAM_NAME) ||
				paramName.equalsIgnoreCase(BACK_SEIS_NAME)) {
			createParamList();
		} else if(paramName.equalsIgnoreCase(PROB_MODEL_PARAM_NAME)) {
			createParamList();
			setTimespanParameter();
			timeSpanChange(new EventObject(timeSpan));
		} else if (paramName.equalsIgnoreCase(RUP_MODEL_TYPE_NAME)) {
			createParamList();
			this.updateA_FaultsFetcher = true;
		} else if(paramName.equalsIgnoreCase(CONNECT_B_FAULTS_PARAM_NAME)) { // whether more B-Faults need to be connected
			//bFaultsFetcher.setDeformationModel( ((Boolean) connectMoreB_FaultsParam.getValue()).booleanValue(), 
				//	getSelectedDeformationModelSummary(), aFaultsFetcher);
			//bFaultsFetcher.test_writeFileAfterCombiningB_Faults();
			this.updateB_FaultsFetcher = true;
		} else if(paramName.equalsIgnoreCase(DEFORMATION_MODEL_PARAM_NAME)) { // if deformation model changes, update the files to be read
			this.updateA_FaultsFetcher = true;
			this.updateB_FaultsFetcher = true;
			//bFaultsFetcher.test_writeFileAfterCombiningB_Faults();
		} 
	}


	/**
	 *  Function that must be ?
	 *
	 * @param  event  The Event which triggered this function call
	 */
	public void timeSpanChange(EventObject event) {
		
		parameterChangeFlag = true;
		
	}
	

	/**
	 * Update fetchers based on selected deformation model
	 *
	 */
	private void updateFetchersBasedonDefModels() {
		String rupModelName = (String)this.rupModelParam.getValue();
		boolean isUnsegmented;
		if(rupModelName.equalsIgnoreCase(UNSEGMENTED_A_FAULT_MODEL)) isUnsegmented= true;
		else isUnsegmented = false;
		aFaultsFetcher.setDeformationModel(getSelectedDeformationModelSummary(), isUnsegmented);


		/*

		 ArrayList<String> faultNames = aFaultsFetcher.getAllFaultNames();
		for(int i=0; i<faultNames.size(); ++i) {
			FaultSegmentData faultSegData = aFaultsFetcher.getFaultSegmentData(faultNames.get(i), false);
			for(int j=0; j<faultSegData.getNumSegments(); ++j) {
				SegmentTimeDepData segTimeDepData = aFaultsFetcher.getSegTimeDepData(faultNames.get(i), j);
				System.out.println(segTimeDepData.getLastEventCalendarYr()+","+segTimeDepData.getSlip()+","+segTimeDepData.getAperiodicity());
			}

		}*/

		bFaultsFetcher.setDeformationModel( ((Boolean) connectMoreB_FaultsParam.getValue()).booleanValue(), 
				getSelectedDeformationModelSummary(), aFaultsFetcher);
		this.updateA_FaultsFetcher = false;
		this.updateB_FaultsFetcher = false;
	}


	/**
	 * This generates text to console that can be pasted into a Matlab *.m file and then
	 * executed in Matlab to compare the Java NNSL solutions to those in Matlab (script
	 * writes the max absolute difference).  Make sure the MATLAB_TEST in A_FaultSegmentedSource
	 * is set as true before running this.  Paste the results into a name.m file, put this where
	 * Matlab can find it, and then type "name" in Matlab.
	 * 
	 * Everything here compares well (except the case below).  That is, the max abs diff
	 * was generally less that 1e-10, got as low as 1e-7 on Elsinore, and 1e-5 on S. SAF.
	 * 
	 *  The following case did not converge in Matlab:
	 *
	 *  % Hanks & Bakun (2002) Mag-Area Rel.
	 *  % Min Rate Model
	 *  % WGCEP-2002 model (Dsr prop to Vs)
	 *  CASE_2_0_2
	 *  S._San_Andreas
	 *  
	 *  By dividing the right and left sides of the equation by 10, the Matlab solution 
	 *  converged with a max absolute-value difference from that here of 1.3243e-04
	 *  (the rates of 5 ruptures differed by 1e-4 when rounded to nearest 1e-4).
	 */
	private void makeMatlabNNLS_testScript() {
//		throw new RuntimeException ("Method unsupported exception");
		ArrayList magAreaOptions = ((StringConstraint)magAreaRelParam.getConstraint()).getAllowedStrings();
//		ArrayList rupModelOptions = ((StringConstraint)rupModelParam.getConstraint()).getAllowedStrings();
		ArrayList slipModelOptions = ((StringConstraint)slipModelParam.getConstraint()).getAllowedStrings();
		for(int imag=0; imag<magAreaOptions.size();imag++)
//			for(int irup=0; irup<rupModelOptions.size();irup++)
			for(int islip=0; islip<slipModelOptions.size();islip++) {
				magAreaRelParam.setValue((String)magAreaOptions.get(imag));
//				rupModelParam.setValue(rupModelOptions.get(irup));
				slipModelParam.setValue((String)slipModelOptions.get(islip));
				System.out.println("% "+magAreaOptions.get(imag)+
//						"\n% " + rupModelOptions.get(irup) +
						"\n% " + slipModelOptions.get(islip));
				System.out.println("display CASE_"+imag+"_"+islip);
//				System.out.println("display CASE_"+imag+"_"+irup+"_"+islip);
				mkA_FaultSegmentedSources();
			}
	}

	/*
	 * This examines time-pred probs for the N SAF
	 */
	public static void testNSAF_TimePredProbs() {
		UCERF2 erRateModel2_ERF = new UCERF2();
		erRateModel2_ERF.setParamDefaults();
		erRateModel2_ERF.updateForecast();
		int nsaf_index = 3;
		A_FaultSegmentedSourceGenerator nsaf_src_gen = (A_FaultSegmentedSourceGenerator)erRateModel2_ERF.get_A_FaultSourceGenerators().get(nsaf_index);
		ArrayList<FaultRuptureSource> junk = nsaf_src_gen.getTimeDependentSources(30,2007,0.5, false);
		int nrup = nsaf_src_gen.getNumRupSources();
		double[] wg02_probs = new double[nrup];
		for(int r=0;r<nrup;r++) wg02_probs[r] = nsaf_src_gen.getRupSourceProb(r);
		
		double[] timePredProbs = nsaf_src_gen.tryTimePredProbs(30,2007,0.5);
		
		System.out.println("wg02_probs\ttimePredProbs\twg02_probs/timePredProbs");
		for(int r=0;r<nrup;r++) {
			System.out.println((float)wg02_probs[r]+"\t"+(float)timePredProbs[r]+"\t"+
					(float)(wg02_probs[r]/timePredProbs[r])+"\t"+nsaf_src_gen.getLongRupName(r));
		}	
	}
	
	public static void simulateSSAF_events() {
		UCERF2 erRateModel2_ERF = new UCERF2();
		erRateModel2_ERF.setParamDefaults();
		erRateModel2_ERF.updateForecast();
		int ssaf_index = 4;
		A_FaultSegmentedSourceGenerator ssaf_src_gen = (A_FaultSegmentedSourceGenerator)erRateModel2_ERF.get_A_FaultSourceGenerators().get(ssaf_index);
		ArrayList<FaultRuptureSource> junk = ssaf_src_gen.getTimeDependentSources(30,2007,0.5, false);
		ssaf_src_gen.simulateEvents(20000);
		junk = ssaf_src_gen.getTimeDependentSources(30,2007,0.5, true);
		ssaf_src_gen.simulateEvents(20000);
	}

	// this is temporary for testing purposes
	public static void main(String[] args) {
		//testNSAF_TimePredProbs();
		//simulateSSAF_events();
		
		UCERF2 erRateModel2_ERF = new UCERF2();
		erRateModel2_ERF.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(UCERF2.PROB_MODEL_POISSON);
		erRateModel2_ERF.updateForecast();
		System.out.println(erRateModel2_ERF.getTotal_BackgroundMFD().getCumRateDistWithOffset());
		/*EvenlyDiscretizedFunc cumMFD = erRateModel2_ERF.getTotalMFD().getCumRateDistWithOffset();
		DiscretizedFuncAPI cumMFD_fromProb = cumMFD.deepClone();
		erRateModel2_ERF.getTotalProb(cumMFD_fromProb, null);
		for(int i=0; i <cumMFD_fromProb.getNum();i++){
			cumMFD_fromProb.set(i,-Math.log(1-cumMFD_fromProb.getY(i))/erRateModel2_ERF.getTimeSpan().getDuration());
			System.out.println(i+"\t"+cumMFD.getY(i)+"\t"+cumMFD_fromProb.getY(i)+"\t"+cumMFD.getY(i)/cumMFD_fromProb.getY(i));
		}*/
		//System.out.println(cumMFD.toString());
		//System.out.println(cumMFD.toString());
		
		
		//erRateModel2_ERF.makeMatlabNNLS_testScript();
	}
}