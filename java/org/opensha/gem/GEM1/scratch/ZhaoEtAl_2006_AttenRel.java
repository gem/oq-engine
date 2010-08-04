package org.opensha.gem.GEM1.scratch;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.OtherParams.TectonicRegionTypeParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.util.TectonicRegionType;

public class ZhaoEtAl_2006_AttenRel extends AttenuationRelationship implements ScalarIntensityMeasureRelationshipAPI,
NamedObjectAPI, ParameterChangeListener {

	// Debugging stuff
	private final static String C = "ZhaoEtAl_2006_AttenRel";
	private final static boolean D = false;
	public final static String SHORT_NAME = "ZhaoEtAl2006";
	private static final long serialVersionUID = 1234567890987654353L;	

	// Name of IMR
	public final static String NAME = "ZhaoEtAl (2006)";
	// Coefficients
	// index -1 is for PGA
	// coefficients Table 4 (page 903)

	private final double[] period = {
			0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60,
			0.70, 0.80, 0.90, 1.00, 1.25, 1.50, 2.00, 2.50, 3.00, 4.00, 5.00};
	private final double[] a = {
			1.101, 1.076, 1.118, 1.134, 1.147, 1.149, 1.163, 1.200, 1.250, 1.293, 
			1.336, 1.386, 1.433, 1.479, 1.551, 1.621, 1.694, 1.748, 1.759, 1.826, 1.825}; // checked with table 4
	private final double[] b = { 
			-0.00564, -0.00671, -0.00787, -0.00722, -0.00659, -0.00590, -0.00520, -0.00422, -0.00338, -0.00282,
			-0.00258, -0.00242, -0.00232, -0.00220, -0.00207, -0.00224, -0.00201, -0.00187, -0.00147, -0.00195, -0.00237}; // checked
	private final double[] c = {
			0.0055, 0.0075, 0.0090, 0.0100, 0.0120, 0.0140, 0.0150, 0.0100, 0.0060, 0.003,
			0.0025, 0.0022, 0.0020, 0.0020, 0.0020, 0.0020, 0.0025, 0.0028, 0.0032, 0.004, 0.005}; // checked with table 4
//	private final double[] d = {
//			1.080, 1.060, 1.083, 1.053, 1.014, 0.966, 0.934, 0.959, 1.008, 1.088, 
//			1.084, 1.088, 1.109, 1.115, 1.083, 1.091, 1.055, 1.052, 1.025, 1.044, 1.065};
	// These are the coefficients taken from the Zhao's code
	private final double[] d = {
			1.07967,1.05984,1.08274,1.05292,1.01360,0.96638,0.93427,0.95880,1.00779,1.08773,
			1.08384,1.08849,1.10920,1.11474,1.08295,1.09117,1.05492,1.05191,1.02452,1.04356,1.06518};
	private final double[] e = {
			0.01412,  0.01463, 0.01423, 0.01509, 0.01462, 0.01459, 0.01458, 0.01257, 0.01114, 0.010190, 
			0.009790, 0.00944, 0.00972, 0.01005, 0.01003, 0.00928, 0.00833, 0.00776, 0.00644, 0.005900, 0.00510};
//	
//	private final double[] Sr = {
//			0.251, 0.251, 0.240, 0.251, 0.260, 0.269, 0.259, 0.248, 0.247, 0.233, 
//			0.220, 0.232, 0.220, 0.211, 0.251, 0.248, 0.263, 0.262, 0.307, 0.353, 0.248};
	private final double[] Sr = {
			0.2509,0.2513,0.2403,0.2506,0.2601,0.2690,0.2590,0.2479,0.2470,0.2326,
			0.2200,0.2321,0.2196,0.2107,0.2510,0.2483,0.2631,0.2620,0.3066,0.3529,0.2485}; // from zhao's code
//	private final double[] Si = {
//			0.000,  0.000,  0.000,  0.000,  0.000,  0.000,  0.000, -0.041, -0.053, -0.103, 
//			-0.146, -0.164, -0.206, -0.239, -0.256, -0.306, -0.321, -0.337, -0.331, -0.390, -0.498}; 
	private final double[] Si = {
			 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000,-0.0412,-0.0528,-0.1034,
			-0.1460,-0.1638,-0.2062,-0.2393,-0.2557,-0.3065,-0.3214,-0.3366,-0.3306,-0.3898,-0.4978}; // from zhao's code
	// On the BSSA paper
	private final double[] Ss = {
			2.607, 2.764, 2.156, 2.161, 1.901, 1.814, 2.181, 2.432, 2.629, 2.702, 
			2.654, 2.480, 2.332, 2.233, 2.029, 1.589, 0.966, 0.789, 1.037, 0.561, 0.225}; // checked with table 4
	// From Zhao's code
	private final double[] SsZhao = {
			 0.0557, 0.1047, 0.1276, 0.0780, 0.1074, 0.0753, 0.0058,-0.0120,-0.0448,-0.0727,
			-0.1082,-0.1257,-0.1859,-0.2268,-0.2370,-0.2400,-0.2332,-0.2804,-0.2305,-0.2548,-0.3551};
//	private final double[] Ssl = {
//			-0.528, -0.551, -0.420, -0.431, -0.372, -0.360, -0.450, -0.506, -0.554, -0.575, 
//			-0.572, -0.540, -0.522, -0.509, -0.469, -0.379, -0.248, -0.221, -0.263, -0.169, -0.120};
	private final double[] Ssl = {
			-0.5284,-0.5507,-0.4201,-0.4315,-0.3715,-0.3601,-0.4505,-0.5061,-0.5538,-0.5746,
			-0.5721,-0.5397,-0.5216,-0.5094,-0.4692,-0.3787,-0.2484,-0.2215,-0.2625,-0.1689,-0.1201}; // from zhao's code
	// From Zhao's code
	private final double[] Sslr = {
			2.6069,2.7638,2.1558,2.1613,1.9012,1.8138,2.1809,2.4316,2.6292,2.7015,
			2.6541,2.4801,2.3323,2.2329,2.0286,1.5886,0.9661,0.7889,1.0370,0.5608,0.2248};

	// coefficients Table 5 (page 903)
	// subscript c= crustal events; i = interface events, s = slab (or intra-slab) events
	// In the Zhao's code these coefficients are missing (no hard rock conditions?)
	private final double[] Ch = {
			0.293, 0.939, 1.499, 1.462, 1.280, 1.121, 0.852, 0.365,-0.207,-0.705,
			-1.144,-1.609,-2.023,-2.451,-3.243,-3.888,-4.783,-5.444,-5.839,-6.598,-6.752}; // checked with table 5
//	private final double[] C1 = {
//			1.111, 1.684, 2.061, 1.916, 1.669, 1.468, 1.172, 0.655, 0.071,-0.429,
//			-0.866,-1.325,-1.732,-2.152,-2.923,-3.548,-4.410,-5.049,-5.431,-6.181,-6.347};
	private final double[] C1 = {
			 1.1111, 1.6845, 2.0609, 1.9165, 1.6688, 1.4683, 1.1720, 0.6548, 0.0713,-0.4288,
			-0.8656,-1.3250,-1.7322,-2.1522,-2.9226,-3.5476,-4.4102,-5.0492,-5.4307,-6.1813,-6.3471}; // from zhao's code
//	private final double[] C2 = {
//			1.344, 1.793, 2.135, 2.168, 2.085, 1.942, 1.683, 1.127, 0.515,-0.003,
//			-0.449,-0.928,-1.349,-1.776,-2.542,-3.169,-4.039,-4.698,-5.089,-5.882,-6.051};
	private final double[] C2 = {
			 1.3440, 1.7930, 2.1346, 2.1680, 2.0854, 1.9416, 1.6829, 1.1271, 0.5149,-0.0027,
			-0.4493,-0.9284,-1.3490,-1.7757,-2.5422,-3.1689,-4.0387,-4.6979,-5.0890,-5.8821,-6.0512}; // from zhao's code
//	private final double[] C3 = {
//			1.355, 1.747, 2.031, 2.052, 2.001, 1.941, 1.808, 1.482, 0.934, 0.394,
//			-0.111,-0.620,-1.066,-1.523,-2.327,-2.979,-3.871,-4.496,-4.893,-5.698,-5.873};
	private final double[] C3 = {
			 1.3548, 1.7474, 2.0311, 2.0518, 2.0007, 1.9407, 1.8083, 1.4825,0.9339,0.3936,
			-0.1109,-0.6200,-1.0665,-1.5228,-2.3272,-2.9789,-3.8714,-4.4963,-4.8932,-5.6981,-5.8733}; // from zhao's code
//	private final double[] C4 = {
//			1.420, 1.814, 2.082, 2.113, 2.030, 1.937, 1.770, 1.397, 0.955, 0.559, 
//			0.188,-0.246,-0.643,-1.084,-1.936,-2.661,-3.640,-4.341,-4.758,-5.588,-5.798};
	private final double[] C4 = {
			1.4204, 1.8140, 2.0818, 2.1128, 2.0302, 1.9367, 1.7697, 1.3967, 0.9549, 0.5591,
			0.1880,-0.2463,-0.6430,-1.0840,-1.9364,-2.6613,-3.6396,-4.3414,-4.7585,-5.5879,-5.7984}; // from zhao's code
	
//	private final double[] sigma = {
//			0.604,0.640,0.694,0.702,0.692,0.682,0.670,0.659,0.653,0.653,
//			0.652,0.647,0.653,0.657,0.660,0.664,0.669,0.671,0.667,0.647,0.643};
	private final double[] sigma = {
			0.6039,0.6399,0.6936,0.7017,0.6917,0.6823,0.6696,0.6589,0.6530,0.6527,
			0.6516,0.6467,0.6525,0.6570,0.6601,0.6640,0.6694,0.6706,0.6671,0.6468,0.6431};
//	private final double[] tau = {0.398,0.444,0.49,0.46,0.423,0.391,0.379,0.39,0.389,0.401,0.408,
//	 		0.418,0.411,0.41,0.402,0.408,0.414,0.411,0.396,0.382,0.377};
	private final double[] tau = {
			0.3976,0.4437,0.4903,0.4603,0.4233,0.3908,0.3790,0.3897,0.3890,0.4014,
			0.4079,0.4183,0.4106,0.4101,0.4021,0.4076,0.4138,0.4108,0.3961,0.3821,0.3766};
	
	private final double[] Qc = {
			 0.000,  0.000, 0.000,  0.000,  0.000,  0.0000, 0.0000, 0.0000,-0.0126,-0.0329,
			-0.0501,-0.065,-0.0781,-0.0899,-0.1148,-0.1351,-0.1672,-0.1921,-0.2124,-0.2445,-0.2694}; // checked with table 6 
	private final double[] Wc = {
			0.0000,0.0000,0.0000,0.000,0.0000,0.000,0.0000,0.0000,0.0116,0.0202,
			0.0274,0.0336,0.0391,0.044,0.0545,0.063,0.0764,0.0869,0.0954,0.1088,0.1193};
	private final double[] Tau_c ={
			0.303,0.326,0.342,0.331,0.312,0.298,0.300,0.346,0.338,0.349,
			0.351,0.356,0.348,0.338,0.313,0.306,0.283,0.287,0.278,0.273,0.275};
	private final double[] Qi = {
			0.0000, 0.0000, 0.0000,-0.0138,-0.0256,-0.0348,-0.0423,-0.0541,-0.0632,-0.0707,
			-0.0771,-0.0825,-0.0874,-0.0917,-0.1009,-0.1083,-0.1202,-0.1293,-0.1368,-0.1486,-0.1578};
	private final double[] Wi = {
			0.0000,0.0000,0.0000,0.0286,0.0352,0.0403,0.0445,0.0511,0.0562,0.0604,
			0.0639,0.0670,0.0697,0.0721,0.0772,0.0814,0.0880,0.0931,0.0972,0.1038,0.1090};
	private final double[] Ps = {
			0.1392,0.1636,0.1690,0.1669,0.1631,0.1588,0.1544,0.146,0.1381,0.1307,
			0.1239,0.1176,0.1116,0.106,0.0933,0.0821,0.0628,0.0465,0.0322,0.0083,-0.0117};
	private final double[] Qs = {
			0.1584,0.1932,0.2057,0.1984,0.1856, 0.1714, 0.1573, 0.1309, 0.1078, 0.0878,
			0.0705,0.0556,0.0426,0.0314,0.0093,-0.0062,-0.0235,-0.0287,-0.0261,-0.0065,0.0246};
	private final double[] Ws = {
			-0.0529,-0.0841,-0.0877,-0.0773,-0.0644,-0.0515,-0.0395,-0.0183,-0.0008,0.0136,
			 0.0254, 0.0352, 0.0432, 0.0498, 0.0612, 0.0674, 0.0692, 0.0622, 0.0496,0.0150,-0.0268};
	private final double[] Tau_s = {
			0.321,0.378,0.420,0.372,0.324,0.294,0.284,0.278,0.272,0.285,
			0.29, 0.299,0.289,0.286,0.277,0.282,0.300,0.292,0.274,0.281,0.296};
	// From Zhao's code
	private final double[] Tau_i = {
			0.308,0.343,0.403,0.367,0.328,0.289,0.280,0.271,0.277,0.296,
			0.313,0.329,0.324,0.328,0.339,0.352,0.360,0.356,0.338,0.307,0.272};
	// From Zhao's code
	private final double[] Tau_S = {
			0.321,0.378,0.420,0.372,0.324,0.294,0.284,0.278,0.272,0.285,
			0.290,0.299,0.289,0.286,0.277,0.282,0.300,0.292,0.274,0.281,0.296};
	
	//	private final double[] sigmaT = {0.723,0.779,0.849,0.839,0.811,0.786,0.77,0.766,0.76,0.766,0.769,0.77,0.771,0.775,0.773,0.779,0.787,0.786,0.776,0.751,0.745};

	// Hashmap

	private HashMap<Double, Integer> indexFromPerHashMap;

	private int iper;
	private double mag, rRup;

	//	private double stdDevType;
	private String siteType; 
	private String focMechType;
	private String stdDevType;
	private String tecRegType;

	//	private boolean parameterChange;
	private PropagationEffect propagationEffect;

	// Site class Definitions - 
	private StringParameter siteTypeParam = null;
	public final static String SITE_TYPE_INFO = "Geological conditions at the site";
	public final static String SITE_TYPE_NAME = "Zhao et al 2006 Site Type";

	// Hard rock description: Vs30 > 1100m/s calculated from site period ()equivalent of NEHRP Class A 
	public final static String SITE_TYPE_HARD_ROCK = "Hard Rock";
	// Rock description: Vs30 > 600m/s calculated from site period (T<2.0sec) and equivalent of NEHRP Class A+B
	public final static String SITE_TYPE_ROCK = " Rock";
	// Hard rock description: 300< Vs30 = 600m/s calculated from site period (0.2=T<0.4sec) and equivalent of NEHRP Class C
	public final static String SITE_TYPE_HARD_SOIL = "Hard Soil";
	// Hard rock description: 200< Vs30 = 300m/s calculated from site period (0.4=T<0.6sec) and equivalent of NEHRP Class D
	public final static String SITE_TYPE_MEDIUM_SOIL = "Medium Soil";
	// Hard rock description: Vs30 =200m/s calculated from site period (T=0.6sec) and equivalent of NEHRP Class A
	public final static String SITE_TYPE_SOFT_SOIL = "Soft Soil";
	public final static String SITE_TYPE_DEFAULT = SITE_TYPE_ROCK;//SITE_TYPE_HARD_ROCK;

	// Style of faulting options
	// Only crustal events with reverse fault mechanism 
	public final static String FLT_TEC_ENV_CRUSTAL = TectonicRegionType.ACTIVE_SHALLOW.toString();
	public final static String FLT_TEC_ENV_INTERFACE = TectonicRegionType.SUBDUCTION_INTERFACE.toString();
	public final static String FLT_TEC_ENV_SLAB = TectonicRegionType.SUBDUCTION_SLAB.toString();

	public final static String FLT_FOC_MECH_REVERSE = "Reverse";
	public final static String FLT_FOC_MECH_NORMAL = "Normal";
	public final static String FLT_FOC_MECH_STRIKE_SLIP = "Strike-slip";
	public final static String FLT_FOC_MECH_UNKNOWN = "Unknown";

	protected final static Double MAG_WARN_MIN = new Double(5);
	protected final static Double MAG_WARN_MAX = new Double(8.3);

	protected final static Double DISTANCE_RUP_WARN_MIN = new Double(0.0);
	protected final static Double DISTANCE_RUP_WARN_MAX = new Double(500.0);
	
	// depth hypocentre
	protected final static Double DEPTH_HYPO_WARN_MIN = new Double(0.0);
	protected final static Double DEPTH_HYPO_WARN_MAX = new Double(125.0);

	// for issuing warnings:
	private transient ParameterChangeWarningListener warningListener = null;

	/**
	 *  This initializes several ParameterList objects.
	 */
	public ZhaoEtAl_2006_AttenRel(ParameterChangeWarningListener warningListener) {

		super();

		this.warningListener = warningListener;

		initSupportedIntensityMeasureParams();
		
		indexFromPerHashMap = new HashMap<Double, Integer>();
		for (int i = 0; i < period.length; i++) { 
			//			System.out.println(period[i]+" "+i);
			indexFromPerHashMap.put(new Double(period[i]), new Integer(i));
		}

		initEqkRuptureParams();
		initSiteParams();
		initPropagationEffectParams();
		initOtherParams();
		initIndependentParamLists(); // This must be called after the above
		initParameterEventListeners(); //add the change listeners to the parameters
		
		if (D) System.out.println("--- ZhaoEtAl_2006_AttenRel end");

	}
	/**
	 * This sets the eqkRupture related parameters (magParam and fltTypeParam)
	 * based on the eqkRupture passed in. The internally held eqkRupture object
	 * is also set as that passed in. Warning constrains are ignored.
	 * 
	 * @param eqkRupture
	 *            The new eqkRupture value
	 * @throws InvalidRangeException
	 *             If not valid rake angle
	 */
	public void setEqkRupture(EqkRupture eqkRupture) throws InvalidRangeException {
		magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));		
		this.eqkRupture = eqkRupture;
		setPropagationEffectParams();
		// TODO
		//	    setFaultTypeFromRake(eqkRupture.getAveRake());
	}

	/**
	 * This sets the site-related parameter (siteTypeParam) based on what is in
	 * the Site object passed in (the Site object must have a parameter with the
	 * same name as that in siteTypeParam). This also sets the internally held
	 * Site object as that passed in.
	 * 
	 * @param site
	 *            The new site object
	 * @throws ParameterException
	 *             Thrown if the Site object doesn't contain a Vs30 parameter
	 */
	public void setSite(Site site) throws ParameterException {	 	
    	
//		System.out.println("Zhao et al --->"+site.getParameter(SITE_TYPE_NAME).getValue());
		
		siteTypeParam.setValue((String) site.getParameter(SITE_TYPE_NAME).getValue());
		this.site = site;
		setPropagationEffectParams();
	}

	/**
	 * This sets the site and eqkRupture, and the related parameters, from the
	 * propEffect object passed in. Warning constrains are ignored.
	 * 
	 * @param propEffect
	 * @throws ParameterException
	 *             
	 * @throws InvalidRangeException
	 *             If not valid distance, depth??? to check!!!
	 */

	public void setPropagationEffectParams() {
		// Set the distance to rupture
		if ( (this.site != null) && (this.eqkRupture != null)) {
			distanceRupParam.setValue(eqkRupture,site);
		}
	}

	/**
	 * This sets the site and eqkRupture, and the related parameters,
	 *  from the propEffect object passed in. Warning constrains are ingored.
	 * @param propEffect
	 * @throws ParameterException Thrown if the Site object doesn't contain a
	 * Vs30 parameter
	 * @throws InvalidRangeException    If not valid rake angle
	 */
	public void setPropagationEffect(PropagationEffect propEffect) throws
	ParameterException, InvalidRangeException {

		this.site = propEffect.getSite();
		this.eqkRupture = propEffect.getEqkRupture();
		siteTypeParam.setValue((String)site.getParameter(SITE_TYPE_NAME).getValue());
		magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
		
		// TODO
		//	    setFaultTypeFromRake(eqkRupture.getAveRake());

		// set the distance param
		propEffect.setParamValue(distanceRupParam);
	}

	/**
	 * 
	 * @throws ParameterException
	 */
	protected void setCoeffIndex() throws ParameterException {

		// Check that parameter exists
		if (im == null) {
			throw new ParameterException(C +
					": updateCoefficients(): " +
					"The Intensity Measusre Parameter has not been set yet, unable to process."
			);
		}

		if (im.getName().equalsIgnoreCase(PGA_Param.NAME)) {
			iper = 0;
		}
		else {
			iper = ((Integer) indexFromPerHashMap.get(saPeriodParam.getValue())).intValue();
		}
		intensityMeasureChanged = false;
	}

	/**
	 * 
	 */
	public double getMean() { 

		// Check if distance is beyond the user specified max
		if (rRup > USER_MAX_DISTANCE) {
			return VERY_SMALL_MEAN;
		}

		if (intensityMeasureChanged) {
			setCoeffIndex();// intensityMeasureChanged is set to false in this method
		}

		// Return the computed mean 
		return getMean(iper,mag,rRup);
	}

	/**
	 * @return    The stdDev value
	 */
	public double getStdDev() {

		if (intensityMeasureChanged) {
			setCoeffIndex();// intensityMeasureChanged is set to false in this method
		}
		return getStdDev(iper, stdDevType, tecRegType);
	}

	/**
	 * Allows the user to set the default parameter values for the selected Attenuation
	 * Relationship.
	 */
	public void setParamDefaults() {

		magParam.setValueAsDefault();
		fltTypeParam.setValueAsDefault();
		tectonicRegionTypeParam.setValueAsDefault();
		distanceRupParam.setValueAsDefault();
		saParam.setValueAsDefault();
		saPeriodParam.setValueAsDefault();
		saDampingParam.setValueAsDefault();
		pgaParam.setValueAsDefault();
		stdDevTypeParam.setValueAsDefault();
		siteTypeParam.setValue(SITE_TYPE_DEFAULT);

		mag = ((Double) magParam.getValue()).doubleValue();
		rRup = ((Double) distanceRupParam.getValue()).doubleValue();
		focMechType = fltTypeParam.getValue().toString();
		tecRegType = tectonicRegionTypeParam.getValue().toString();
		siteType = siteTypeParam.getValue().toString();
	}


	/**
	 *  Creates the two Potential Earthquake parameters (magParam and
	 *  fltTypeParam) and adds them to the eqkRuptureParams
	 *  list. Makes the parameters non-editable.
	 */
	protected void initEqkRuptureParams() {

		if (D) System.out.println("--- initEqkRuptureParams");
		
		// Magnitude parameter
		magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);

		// Focal mechanism
		StringConstraint fltConstr = new StringConstraint(); 
		fltConstr.addString(FLT_FOC_MECH_REVERSE);
		fltConstr.addString(FLT_FOC_MECH_NORMAL);
		fltConstr.addString(FLT_FOC_MECH_STRIKE_SLIP);
		fltConstr.addString(FLT_FOC_MECH_UNKNOWN);
		fltTypeParam = new FaultTypeParam(fltConstr,FLT_FOC_MECH_REVERSE);

		// Add parameters 
		eqkRuptureParams.clear();
		eqkRuptureParams.addParameter(magParam);
		eqkRuptureParams.addParameter(fltTypeParam);

		if (D) System.out.println("--- initEqkRuptureParams end");
	}

	/**
	 *  Creates the Site-Type parameter and adds it to the siteParams list.
	 *  Makes the parameters non-edit-able.
	 */
	protected void initSiteParams() {
		// 
		StringConstraint siteConstraint = new StringConstraint();
		siteConstraint.addString(SITE_TYPE_HARD_ROCK);
		siteConstraint.addString(SITE_TYPE_ROCK);
		siteConstraint.addString(SITE_TYPE_HARD_SOIL);
		siteConstraint.addString(SITE_TYPE_MEDIUM_SOIL);
		siteConstraint.addString(SITE_TYPE_SOFT_SOIL);
		siteConstraint.setNonEditable();
		//
		siteTypeParam = new StringParameter(SITE_TYPE_NAME, siteConstraint, null);
		siteTypeParam.setInfo(SITE_TYPE_INFO);
		siteTypeParam.setNonEditable();
		// Add siteTypeParam to the set of parameters describing the site
		siteParams.clear();
		siteParams.addParameter(siteTypeParam);  
	}

	/**
	 *  Creates the Propagation Effect parameters and adds them to the
	 *  propagationEffectParams list. Makes the parameters non-editable.
	 */
	protected void initPropagationEffectParams() {
		distanceRupParam = new DistanceRupParameter(0.0);
		distanceRupParam.addParameterChangeWarningListener(warningListener);
		DoubleConstraint warn = new DoubleConstraint(DISTANCE_RUP_WARN_MIN, DISTANCE_RUP_WARN_MAX);
		warn.setNonEditable();
		distanceRupParam.setWarningConstraint(warn);

		distanceRupParam.setNonEditable();
		propagationEffectParams.addParameter(distanceRupParam);
	}

	/**
	 *  Creates other Parameters that the mean or stdDev depends upon,
	 *  such as the Component or StdDevType parameters.
	 */
	protected void initOtherParams() {

		if (D) System.out.println("--- initOtherParams");
		
		// init other params defined in parent class
		super.initOtherParams();
		
		// The stdDevType Parameter
		StringConstraint stdDevTypeConstraint = new StringConstraint();
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_NONE);
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTER);
		stdDevTypeConstraint.addString(StdDevTypeParam.STD_DEV_TYPE_INTRA);
		stdDevTypeConstraint.setNonEditable();
		stdDevTypeParam = new StdDevTypeParam(stdDevTypeConstraint);
		
	    // The Component Parameter
	    StringConstraint constraint = new StringConstraint();
	    // GEM1 GMPE contract: table 1 says Geometric mean
	    constraint.addString(ComponentParam.COMPONENT_AVE_HORZ);
	    constraint.setNonEditable();
	    componentParam = new ComponentParam(constraint,ComponentParam.COMPONENT_AVE_HORZ);
		
		// Seismotectonic region
		constraint = new StringConstraint();
		constraint.addString(FLT_TEC_ENV_CRUSTAL);
		constraint.addString(FLT_TEC_ENV_SLAB);
		constraint.addString(FLT_TEC_ENV_INTERFACE);
		constraint.setNonEditable();
		tectonicRegionTypeParam = new TectonicRegionTypeParam(constraint,FLT_TEC_ENV_INTERFACE); // Constraint and default value
		
		// add these to the list
		otherParams.addParameter(stdDevTypeParam);
		otherParams.addParameter(componentParam);
		otherParams.replaceParameter(tectonicRegionTypeParam.NAME, tectonicRegionTypeParam);

	}	

	/**
	 * This creates the lists of independent parameters that the various dependent
	 * parameters (mean, standard deviation, exceedance probability, and IML at
	 * exceedance probability) depend upon. NOTE: these lists do not include anything
	 * about the intensity-measure parameters or any of their internal
	 * independentParamaters.
	 */
	protected void initIndependentParamLists() {

		// params that the mean depends upon
		meanIndependentParams.clear();
		meanIndependentParams.addParameter(magParam);
		meanIndependentParams.addParameter(fltTypeParam);
		meanIndependentParams.addParameter(tectonicRegionTypeParam);
		meanIndependentParams.addParameter(distanceRupParam);
		meanIndependentParams.addParameter(siteTypeParam);

		// params that the stdDev depends upon
		stdDevIndependentParams.clear();
		stdDevIndependentParams.addParameter(saPeriodParam);
		stdDevIndependentParams.addParameter(tectonicRegionTypeParam);
		stdDevIndependentParams.addParameter(stdDevTypeParam);
		
		// params that the exceed. prob. depends upon
		exceedProbIndependentParams.clear();
		exceedProbIndependentParams.addParameterList(meanIndependentParams);
		exceedProbIndependentParams.addParameter(stdDevTypeParam);
		exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
		exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

		// params that the IML at exceed. prob. depends upon
		imlAtExceedProbIndependentParams.addParameterList(
				exceedProbIndependentParams);
		imlAtExceedProbIndependentParams.addParameter(exceedProbParam);
	}

	/**
	 *  Creates the two supported IM parameters (PGA and SA), as well as the
	 *  independenParameters of SA (periodParam and dampingParam) and adds
	 *  them to the supportedIMParams list. Makes the parameters non-editable.
	 */
	protected void initSupportedIntensityMeasureParams() {
		// Create saParam:
		DoubleDiscreteConstraint periodConstraint = new DoubleDiscreteConstraint();
		for (int i = 1; i < period.length; i++) {
			periodConstraint.addDouble(new Double(period[i]));
		}
		periodConstraint.setNonEditable();
		saPeriodParam = new PeriodParam(periodConstraint);
		saDampingParam = new DampingParam();
		saParam = new SA_Param(saPeriodParam, saDampingParam);
		saParam.setNonEditable();

		//  Create PGA Parameter (pgaParam):
		pgaParam = new PGA_Param();
		pgaParam.setNonEditable();

		// Add the warning listeners:
		saParam.addParameterChangeWarningListener(warningListener);
		pgaParam.addParameterChangeWarningListener(warningListener);

		// Put parameters in the supportedIMParams list:
		supportedIMParams.clear();
		supportedIMParams.addParameter(saParam);
		supportedIMParams.addParameter(pgaParam);	
	}

	/**
	 * get the name of this IMR
	 *
	 * @returns the name of this IMR
	 */
	public String getName() {
		return NAME;
	}

	/**
	 * Returns the Short Name of each AttenuationRelationship
	 * @return String
	 */
	public String getShortName() {
		return SHORT_NAME;
	}

	/**
	 * 
	 * @param iper
	 * @param mag
	 * @param rRup
	 * @return
	 */
	public double getMean(int iper, double mag, double rRup) {

		double hypodepth;
		double flag_sc  = 0.0; // This is unity for crustal events - Otherwise 0
		double flag_Fr  = 0.0; // This is unity for reverse crustal events - Otherwise 0
		double flag_Si  = 0.0; // This is unity for interface events - Otherwise 0
		double flag_Ss  = 0.0; // This is unity for slab events - Otherwise 0
		double flag_Ssl = 0.0; // This is unity for slab events - Otherwise 0
		
		double hc = 125;
		double hlow = 15; // see bottom of left column page 902
		double delta_h = 0.0;
		double mc;
		double pFa = 0.0;
		double qFa = 0.0; 
		double wFa = 0.0; 
		double m2CorrFact = 0.0;

		// Site term correction
		double soilCoeff = 0.0;
		if (D) System.out.println("Site conditions: "+siteType);
		if (siteType.equals(SITE_TYPE_HARD_ROCK)){
			// Vs30 > 1100
			if (D) System.out.println("Hard Rock");
			soilCoeff = Ch[iper];
		} else if (siteType.equals(SITE_TYPE_ROCK)) {	
			// 600 < Vs30 < 1100
			if (D) System.out.println("Rock");
			soilCoeff = C1[iper];
		} else if (siteType.equals(SITE_TYPE_HARD_SOIL)) {
			// 300 < Vs30 < 600
			if (D) System.out.println("Hard soil");
			soilCoeff = C2[iper];
		} else if (siteType.equals(SITE_TYPE_MEDIUM_SOIL)) {
			// 200 < Vs30 < 300
			if (D) System.out.println("Medium soil");
			soilCoeff = C3[iper];
		} else if (siteType.equals(SITE_TYPE_SOFT_SOIL)) {	
			// Vs30 = 200
			if (D) System.out.println("Soft soil");
			soilCoeff = C4[iper];
		} else {
			throw new RuntimeException("\n  Unrecognized site type \n");
		}
		
		// Setting the flags in order to account for tectonic region and focal mechanism
		if (D) System.out.println("getMean: "+tecRegType);
		if (focMechType.equals(FLT_FOC_MECH_REVERSE) && tecRegType.equals(FLT_TEC_ENV_CRUSTAL)){
			flag_Fr = 1.0;
			// 
			mc  = 6.3;
			pFa = 0.0;
			qFa = Qc[iper];
			wFa = Wc[iper];
			if (D) System.out.println("Crustal - reverse");
		} else if (tecRegType.equals(FLT_TEC_ENV_CRUSTAL)){
			flag_sc = 1.0;
			// 
			mc  = 6.3;
			pFa = 0.0; 
			qFa = Qc[iper];
			wFa = Wc[iper];
			if (D) System.out.println("Crustal - other");
		} else if (tecRegType.equals(FLT_TEC_ENV_INTERFACE)){
			flag_Si = 1.0;
			// 
			mc  = 6.3;
			pFa = 0.0; 
			qFa = Qi[iper];
			wFa = Wi[iper];
			if (D) System.out.println("Interface - all");
		} else if (tecRegType.equals(FLT_TEC_ENV_SLAB)){
			flag_Ss  = 1.0;
			flag_Ssl = 1.0;
			//
			mc  = 6.5;
			pFa = Ps[iper];
			qFa = Qs[iper];
			wFa = Ws[iper];
			if (D) System.out.println("Slab - all");
		} else {
			System.out.println("+++"+tecRegType.toString()+"--");
			System.out.println("+++"+focMechType.toString()+"--");
			throw new RuntimeException("\n  Cannot handle this combination: \n  tectonic region + focal mechanism ");
		}
		
		// Computing the hypocentral depth
//		System.out.println("Zhao et al -->"+this.eqkRupture.getInfo());
	
		EvenlyGriddedSurfaceAPI surf = this.eqkRupture.getRuptureSurface();
		
		// ---------------------------------------------------------------------- MARCO 2010.03.15
		// Compute the hypocenter as the middle point of the rupture
		double hypoLon = 0.0;
		double hypoLat = 0.0;
		double hypoDep = 0.0;
		double cnt = 0.0;
		for (int j=0; j < surf.getNumCols(); j++){
			for (int k=0; k < surf.getNumRows(); k++){
				hypoLon += surf.getLocation(k,j).getLongitude();
				hypoLat += surf.getLocation(k,j).getLatitude();
				hypoDep = hypoDep + surf.getLocation(k,j).getDepth();
				//System.out.println(surf.getLocation(k,j).getDepth());
				cnt += 1;
			}
		}
		double chk = surf.getNumCols() * surf.getNumRows();
		//System.out.println(cnt+" "+chk);
		
		hypoLon = hypoLon / cnt;
		hypoLat = hypoLat / cnt;
		hypoDep = hypoDep / cnt;
		hypodepth = hypoDep;
//		System.out.println("computed hypocentral depth:"+hypodepth);
//		hypodepth = this.eqkRupture.getHypocenterLocation().getDepth();
//		System.out.println("real hypocentral depth:"+hypodepth);
		// ---------------------------------------------------------------------- MARCO 2010.03.15
		
		// Depth dummy variable delta_h for depth term = e[iper]*(hypodepth-hc)*delta_h
		if (hypodepth > hlow){
			delta_h=1;
			if (hypodepth < hc){
				hypodepth = hypodepth - hlow;
			} else {
				hypodepth = hc - hlow;
			}
		} else {
			delta_h=0;
		}

		// Correction factor
		m2CorrFact = pFa * (mag-mc) +  qFa * Math.pow((mag-mc),2.0) + wFa;
		if (D) System.out.printf("corr fact: %10.6f mag: %5.2f\n",m2CorrFact,mag);
		
		// TODO The assignment of this variable mu
		// MARCO 
		//System.out.printf("(%.0f) %.0f slab (%.0f %.0f) \n",flag_Fr,flag_Si,flag_Ss,flag_Ssl);
		//System.out.printf("%.3f %.3f %.3f %.3f \n",a[iper],b[iper],c[iper],d[iper]);
		//System.out.printf("%.3f %.3f %.3f %.3f\n",rRup,Qs[iper],Ws[iper],mag);
		//System.out.printf("%.3f %.3f %.3f %.3f %.3f\n",rRup,Qc[iper],Wc[iper],mc,Sr[iper]);
		//System.out.printf("%.3f %.3f %.3f %.3f \n",hypodepth,Qi[iper],Wi[iper],mc);
		
		double r = rRup + c[iper]*Math.exp(d[iper]*mag);
//		System.out.println(hypodepth+" "+rRup+" "+Si[iper]+" "+Qi[iper]+" "+Wi[iper]);
//		System.out.println("  r: "+r);
//		System.out.println("  hypo term: "+e[iper] * hypodepth * delta_h+" hypo dep:"+hypodepth);
		
		double lnGm = a[iper] * mag + b[iper] * rRup - Math.log(r) + 
			e[iper] * hypodepth * delta_h +
			flag_Fr * Sr[iper] + 
			flag_Si * Si[iper] + 
			// The following options give the same results (the first takes what's written in the 
			// BSSA paper the second follows Zhao's code implementation
			flag_Ss * Ss[iper] + flag_Ssl * Ssl[iper] * Math.log(rRup) + // Option 1
//			flag_Ss *SsZhao[iper] + flag_Ssl * Ssl[iper] * (Math.log(rRup)-Math.log(125.0)) + // Option 2
			soilCoeff;
		
		// Return the computed mean value
		lnGm += m2CorrFact;
		
		// Convert form cm/s2 to g
		return Math.log(Math.exp(lnGm)/981);
	}	
	/**
	 * This gets the standard deviation for specific parameter settings.  We might want another 
	 * version that takes the actual SA period rather than the period index.
	 * @param iper
	 * @param vs30
	 * @param f_rv
	 * @param f_nm
	 * @param rRup
	 * @param distRupMinusJB_OverRup
	 * @param distRupMinusDistX_OverRup
	 * @param f_hw
	 * @param dip
	 * @param mag
	 * @param depthTop
	 * @param aftershock
	 * @param stdDevType
	 * @param f_meas
	 * @return
	 */
	public double getStdDev(int iper, String stdDevType, String tecRegType) {

		if (tecRegType.equals(FLT_TEC_ENV_CRUSTAL)){
			  if(stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
				  return Math.sqrt(Tau_c[iper]*Tau_c[iper]+sigma[iper]*sigma[iper]);
			  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
				  return 0;
			  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
				  return sigma[iper];
			  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
				  return Tau_c[iper];
			  else 
				  return Double.NaN;
		} else if (tecRegType.equals(FLT_TEC_ENV_INTERFACE)) {
			  if(stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
				  return Math.sqrt(Tau_i[iper]*Tau_i[iper]+sigma[iper]*sigma[iper]);
			  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
				  return 0;
			  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
				  return sigma[iper];
			  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
				  return Tau_i[iper];
			  else 
				  return Double.NaN; 
		} else if (tecRegType.equals(FLT_TEC_ENV_SLAB)) {
			  if(stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_TOTAL))
				  return Math.sqrt(Tau_s[iper]*Tau_s[iper]+sigma[iper]*sigma[iper]);
			  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE))
				  return 0;
			  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTER))
				  return sigma[iper];
			  else if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_INTRA))
				  return Tau_s[iper];
			  else 
				  return Double.NaN; 
		}
		return 0;
	}


	/**
	 * This listens for parameter changes and updates the primitive parameters accordingly
	 * @param e ParameterChangeEvent
	 */
	public void parameterChange(ParameterChangeEvent e) {

		String pName = e.getParameterName();
		Object val = e.getNewValue();
		
		if (D) System.out.println("Changed param: "+pName);

		if (pName.equals(DistanceRupParameter.NAME)) {
			rRup = ( (Double) val).doubleValue();
		} 
		else if (pName.equals(MagParam.NAME)) {
			mag = ( (Double) val).doubleValue();
		} 
		else if (pName.equals(StdDevTypeParam.NAME)) {
			stdDevType = (String) val;
		} 
		else if (pName.equals(FaultTypeParam.NAME)) {
			focMechType = fltTypeParam.getValue().toString();
		} 
		else if (pName.equals(TectonicRegionTypeParam.NAME)) {
			tecRegType = tectonicRegionTypeParam.getValue().toString();
			if (D) System.out.println("tecRegType new value:"+tecRegType);
		} 
		else if (pName.equals(SITE_TYPE_NAME)) {
			siteType = this.getParameter(this.SITE_TYPE_NAME).getValue().toString();
		}
		else if (pName.equals(PeriodParam.NAME) ) {
			intensityMeasureChanged = true;
		}
	}
	/**
	 * Allows to reset the change listeners on the parameters
	 */
	public void resetParameterEventListeners(){
		magParam.removeParameterChangeListener(this);
		fltTypeParam.removeParameterChangeListener(this);
		tectonicRegionTypeParam.removeParameterChangeListener(this);
		siteTypeParam.removeParameterChangeListener(this);
		distanceRupParam.removeParameterChangeListener(this);
		stdDevTypeParam.removeParameterChangeListener(this);
		saPeriodParam.removeParameterChangeListener(this);
		this.initParameterEventListeners();
	}
	/**
	 * Adds the parameter change listeners. This allows to listen to when-ever the
	 * parameter is changed.
	 */
	protected void initParameterEventListeners() {
		if (D) System.out.println("--- initParameterEventListeners begin");
		
		magParam.addParameterChangeListener(this);
		fltTypeParam.addParameterChangeListener(this);
		tectonicRegionTypeParam.addParameterChangeListener(this);
		siteTypeParam.addParameterChangeListener(this);
		distanceRupParam.addParameterChangeListener(this);
		stdDevTypeParam.addParameterChangeListener(this);
		saPeriodParam.addParameterChangeListener(this);
		
		if (D) System.out.println("--- initParameterEventListeners end");
	}


	/**
	 * This provides a URL where more info on this model can be obtained
	 * @throws MalformedURLException if returned URL is not a valid URL.
	 * @returns the URL to the AttenuationRelationship document on the Web.
	 */
	public URL getInfoURL() throws MalformedURLException{
		return new URL("http://www.opensha.org/documentation/modelsImplemented/attenRel/ZhaoEtAl_2006.html");
	}

}
