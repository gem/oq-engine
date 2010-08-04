package scratch.datamind;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceJBParameter;

/**
 * <b>Title:</b> AmbraseyEtAl_1996_AttenRel<p>
 *
 * <b>Description:</b> This implements the Attenuation Relationship
 * developed by N.N.Ambraseys, K.A.Simpson and J.J.Bommer (1996) <p>
 *
 * Supported Intensity-Measure Parameters:<p>
 * <UL>
 * <LI>pgaParam - Peak Ground Acceleration
 * <LI>saParam - Response Spectral Acceleration
 * </UL><p>
 * Other Independent Parameters:<p>
 * <UL>
 * <LI>magParam - moment Magnitude
 * <LI>distanceJBParam - closest distance to surface projection of fault
 * </UL></p>
 * 
 *<p>
 *
 * Verification: 
 * 
 *</p>
 *
 *
 * @author     Riccardo Giannitrapani, Paolo Bianchini, Laura Peruzza
 * @created    June, 2008
 * @version    1.0
 */


public class AmbraseysEtAl_1996_AttenRel
    extends AttenuationRelationship implements
    ScalarIntensityMeasureRelationshipAPI,
    NamedObjectAPI, ParameterChangeListener {


		public static void main(String[] args) {
			// TODO Auto-generated method stub
			AmbraseysEtAl_1996_AttenRel ar = new AmbraseysEtAl_1996_AttenRel(null);
			
			System.out.println("Hello world from DataMind!");
			System.out.println("A first test on Ambraseys EtAl 1996 attenuation relation");

			System.out.println(Math.exp(ar.getMean(0, SITE_TYPE_ROCK, 500, 0, 5)));

		}

	
	
  // Debugging stuff
  private final static String C = "AmbraseysEtAl_1996_AttenRel";
  private final static boolean D = false;
  public final static String SHORT_NAME = "AmbraseysEtAl1996";
  private static final long serialVersionUID = 1234567890987654353L;


  // Name of IMR
  public final static String NAME = "Ambraseys et al. (1996)";

  
  // coefficients:
  // note that index 0 is for PGA 
  // the coefficients were originally for frequencies: 0.5, 1, 2.5, 5, 10, 25, 35, PGA

  double[] period= {0, 0.10, 0.15, 0.20, 0.30, 0.50, 1, 1.5, 2};
  double[] c1= {  -1.48, -0.84,-0.98 , -1.21, -1.55, -2.25, -3.17, -3.61, -3.79};
  double[] c2= {  0.266, 0.219, 0.247, 0.284, 0.338, 0.420, 0.508, 0.524, 0.503};
  double[] c4= {  -0.922, -0.954,-0.938, -0.922, -0.933, -0.913, -0.885, -0.817, -0.728};
  double[] ca= {  0.117, 0.078, 0.143, 0.135, 0.133, 0.147, 0.128, 0.109, 0.101};
  double[] cs= {  0.124, 0.027, 0.085, 0.142, 0.148, 0.201, 0.219, 0.204, 0.182};
  double[] h0= {  3.5, 4.5, 4.7, 4.2, 4.2, 3.3, 4.3, 3.0, 3.2};
  double[] sig= { 0.25, 0.27, 0.27, 0.27, 0.30, 0.32, 0.32, 0.31, 0.32};

  private HashMap indexFromPerHashMap;

  private int iper;
  private double vs30, rjb, mag;
  private String siteType;
  private boolean parameterChange;

  protected final static Double MAG_WARN_MIN = new Double(4);
  protected final static Double MAG_WARN_MAX = new Double(7.3);
  protected final static Double DISTANCE_JB_WARN_MIN = new Double(0.0);
  protected final static Double DISTANCE_JB_WARN_MAX = new Double(500.0);
  
  /**
   * Site Type Parameter ("Rock/Shallow-Soil" versus "Deep-Soil")
   */
  private StringParameter siteTypeParam = null;
  public final static String SITE_TYPE_NAME = "AS Site Type";
  // no units
  public final static String SITE_TYPE_INFO =
      "Geological conditions at the site";
  public final static String SITE_TYPE_ROCK = "Rock";
  public final static String SITE_TYPE_STIFF = "Stiff";
  public final static String SITE_TYPE_SOIL = "Soil";
  public final static String SITE_TYPE_DEFAULT = SITE_TYPE_ROCK;

  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;

  /**
   *  This initializes several ParameterList objects.
   */
  public AmbraseysEtAl_1996_AttenRel(ParameterChangeWarningListener
                                    warningListener) {

    super();

    this.warningListener = warningListener;

    initSupportedIntensityMeasureParams();
    indexFromPerHashMap = new HashMap();
    for (int i = 0; i < period.length ; i++) {
      indexFromPerHashMap.put(new Double(period[i]), new Integer(i));
    }

    initEqkRuptureParams();
    initPropagationEffectParams();
    initSiteParams();

    initIndependentParamLists(); // This must be called after the above
    initParameterEventListeners(); //add the change listeners to the parameters

  }

  /**
   *  This sets the eqkRupture related parameters (magParam)
   *  based on the eqkRupture passed in.
   *  The internally held eqkRupture object is also set as that
   *  passed in.  Warning constrains are ingored.
   *
   * @param  eqkRupture  The new eqkRupture value
   * @throws InvalidRangeException thrown if rake is out of bounds
   */
  public void setEqkRupture(EqkRupture eqkRupture) throws InvalidRangeException {

    magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));
    this.eqkRupture = eqkRupture;
    setPropagationEffectParams();

  }

  /**
   *  This sets the site-related parameter (siteTypeParam) based on what is in
   *  the Site object passed in (the Site object must have a parameter with
   *  the same name as that in siteTypeParam).  This also sets the internally held
   *  Site object as that passed in.
   *
   * @param  site             The new site object
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Vs30 parameter
   */
  public void setSite(Site site) throws ParameterException {

    this.site = site;
    setPropagationEffectParams();

  }

  /**
   * 
   */
  protected void setPropagationEffectParams() {

    if ( (this.site != null) && (this.eqkRupture != null)) {

      distanceJBParam.setValue(eqkRupture, site);

    }
  }

  /**
   * This function returns the array index for the coeffs corresponding to the chosen IMT
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
    else
    {
    iper = ( (Integer) indexFromPerHashMap.get(saPeriodParam.getValue())).intValue();
    }
    

    parameterChange = true;
    intensityMeasureChanged = false;

  }

  /**
   * Calculates the mean of the exceedence probability distribution. <p>
   * @return    The mean value
   */
  public double getMean() {
	  
	  // check if distance is beyond the user specified max
	  if (rjb > USER_MAX_DISTANCE) {
		  return VERY_SMALL_MEAN;
	  }
	  
	  if (intensityMeasureChanged) {
		  setCoeffIndex(); // intensityMeasureChanged is set to false in this method
	  }

	  return getMean(iper, siteType, vs30, rjb, mag);
  }

  /**
   * @return    The stdDev value
   */
  public double getStdDev() {
    if (intensityMeasureChanged) {
      setCoeffIndex();// intensityMeasureChanged is set to false in this method
    }
    return getStdDev(iper, rjb, mag);
  }
  
  
  /**
   * Allows the user to set the default parameter values for the selected Attenuation
   * Relationship.
   */
  public void setParamDefaults() {

    magParam.setValueAsDefault();
    distanceJBParam.setValueAsDefault();
    saParam.setValueAsDefault();
    saPeriodParam.setValueAsDefault();
    saDampingParam.setValueAsDefault();
    pgaParam.setValueAsDefault();
    siteTypeParam.setValue(SITE_TYPE_DEFAULT);
//    stdDevTypeParam.setValueAsDefault();

    rjb = ( (Double) distanceJBParam.getValue()).doubleValue();
    mag = ( (Double) magParam.getValue()).doubleValue();
    siteType = siteTypeParam.getValue().toString();

  }

  /**
   * This creates the lists of independent parameters that the various dependent
   * parameters (mean, standard deviation, exceedance probability, and IML at
   * exceedance probability) depend upon. NOTE: these lists do not include anything
   * about the intensity-measure parameters or any of thier internal
   * independentParamaters.
   */
  protected void initIndependentParamLists() {

    // params that the mean depends upon
    meanIndependentParams.clear();
    meanIndependentParams.addParameter(distanceJBParam);
    // meanIndependentParams.addParameter(vs30Param);
    meanIndependentParams.addParameter(magParam);
    meanIndependentParams.addParameter(siteTypeParam);
    
    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
    stdDevIndependentParams.addParameter(distanceJBParam);
    stdDevIndependentParams.addParameter(magParam);

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    exceedProbIndependentParams.addParameterList(meanIndependentParams);
//    exceedProbIndependentParams.addParameter(sigmaTruncTypeParam);
//    exceedProbIndependentParams.addParameter(sigmaTruncLevelParam);

    // params that the IML at exceed. prob. depends upon
    imlAtExceedProbIndependentParams.addParameterList(
        exceedProbIndependentParams);
    imlAtExceedProbIndependentParams.addParameter(exceedProbParam);
  }

  /**
   * This sets the site and eqkRu passed in. Warning constrains are ingored.
   * @param propEffect
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Vs30 parameter
   * @throws InvalidRangeException thrown if rake is out of bounds
   */
  public void setPropagationEffect(PropagationEffect propEffect) throws
      InvalidRangeException, ParameterException {

    this.site = propEffect.getSite();
    this.eqkRupture = propEffect.getEqkRupture();

    magParam.setValueIgnoreWarning(new Double(eqkRupture.getMag()));

    propEffect.setParamValue(distanceJBParam);
  }
  
  
  /**
   *  Creates the Site-Type parameter and adds it to the siteParams list.
   *  Makes the parameters noneditable.
   */
  protected void initSiteParams() {	  

    StringConstraint siteConstraint = new StringConstraint();
    siteConstraint.addString(SITE_TYPE_ROCK);
    siteConstraint.addString(SITE_TYPE_STIFF);
    siteConstraint.addString(SITE_TYPE_SOIL);
    siteConstraint.setNonEditable();
    siteTypeParam = new StringParameter(SITE_TYPE_NAME, siteConstraint, null);
    siteTypeParam.setInfo(SITE_TYPE_INFO);
    siteTypeParam.setNonEditable();

    siteParams.clear();
    siteParams.addParameter(siteTypeParam);

  }

  /**
   *  Creates the one Earthquake parameters (magParam) and adds it to the eqkRuptureParams
   *  list. Makes the parameter noneditable.
   */
  protected void initEqkRuptureParams() {

	magParam = new MagParam(MAG_WARN_MIN, MAG_WARN_MAX);

    eqkRuptureParams.clear();
    eqkRuptureParams.addParameter(magParam);
  }

  /**
   *  Creates the Propagation Effect parameters and adds them to the
   *  propagationEffectParams list. Makes the parameters noneditable.
   */
  protected void initPropagationEffectParams() {

	distanceJBParam = new DistanceJBParameter(0.0);
    distanceJBParam.addParameterChangeWarningListener(warningListener);
    DoubleConstraint warn = new DoubleConstraint(DISTANCE_JB_WARN_MIN,
                                                 DISTANCE_JB_WARN_MAX);
    warn.setNonEditable();
    distanceJBParam.setWarningConstraint(warn);
    distanceJBParam.setNonEditable();

    propagationEffectParams.addParameter(distanceJBParam);

  }

  /**
   *  Creates the two supported IM parameters (PGA and SA), as well as the
   *  independenParameters of SA (periodParam and dampingParam) and adds
   *  them to the supportedIMParams list. Makes the parameters noneditable.
   */
  protected void initSupportedIntensityMeasureParams() {

    // Create saParam's "Period" independent parameter:
    DoubleDiscreteConstraint periodConstraint = new DoubleDiscreteConstraint();
    for (int i = 0; i < period.length; i++) {
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

  public double getMean(int iper, String siteType, double vs30, double rjb, double mag) {

    // 
	int SR, SA, SS;
	double logY;
	if (siteType.equals(SITE_TYPE_ROCK))
	{
		SR = 1;
		SA = 0;
		SS = 0;
	} else 	if (siteType.equals(SITE_TYPE_STIFF))
	{
		SR = 0;
		SA = 1;
		SS = 0;
	} else 
	{
		SR = 0;
		SA = 0;
		SS = 1;
	}


	
	double rM = Math.sqrt(rjb*rjb+h0[iper]*h0[iper]);
	
	// XXX TEMP, mancano i termini SA e SS per il tipo di terreno
	logY = c1[iper] + c2[iper]*mag + c4[iper]*Math.log10(rM) + ca[iper]*SA + cs[iper]*SS;
	  	
    return (logY*Math.log(10));
  }

  public double getStdDev(int iper, double rjb, double mag) {
	  	  
	  return (sig[iper]);
	  
  }

  /**
   * This listens for parameter changes and updates the primitive parameters accordingly
   * @param e ParameterChangeEvent
   */
  public void parameterChange(ParameterChangeEvent e) {

    String pName = e.getParameterName();
    Object val = e.getNewValue();
    parameterChange = true;
    if (pName.equals(DistanceJBParameter.NAME)) {
      rjb = ( (Double) val).doubleValue();
    }
    else if (pName.equals(magParam.NAME)) {
      mag = ( (Double) val).doubleValue();
    }
    else if (pName.equals(PeriodParam.NAME) ) {
    	intensityMeasureChanged = true;
    }
    else if (pName.equals(SITE_TYPE_NAME) ) {
      siteType = val.toString();
    }

  }

  /**
   * Allows to reset the change listeners on the parameters
   */
  public void resetParameterEventListeners(){
    distanceJBParam.removeParameterChangeListener(this);
    magParam.removeParameterChangeListener(this);
    saPeriodParam.removeParameterChangeListener(this);

    this.initParameterEventListeners();
  }

  /**
   * Adds the parameter change listeners. This allows to listen to when-ever the
   * parameter is changed.
   */
  protected void initParameterEventListeners() {

    distanceJBParam.addParameterChangeListener(this);
    magParam.addParameterChangeListener(this);
    saPeriodParam.addParameterChangeListener(this);
    siteTypeParam.addParameterChangeListener(this);
  }

  /**
   * 
   * @throws MalformedURLException if returned URL is not a valid URL.
   * @returns the URL to the AttenuationRelationship document on the Web.
   */
  public URL getAttenuationRelationshipURL() throws MalformedURLException{
	  return new URL("http://www.opensha.org/documentation/modelsImplemented/attenRel/BA_2008.html");
  }   
  
}