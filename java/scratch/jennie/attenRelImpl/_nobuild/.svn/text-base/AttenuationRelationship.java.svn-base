package org.opensha.sha.imr;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.*;






import org.opensha.sha.earthquake.*;
import org.opensha.sha.earthquake.rupForecastImpl.*;

/**
 *  <b>Title:</b> AttenuationRelationship</p> <p>
 *
 *  <b>Description:</b> This is subclass of IntensityMeasureRealtionship .
 *  The shaking is assumed to follow a Gaussian distribution,
 *  which is why there's a getMean() and a getStdDev() method in addition to
 *  the getExceedProbability() method of its parent class.  For this subclass of IMR
 *  the value field of the Intensity-Measure Parameter must be a Double.  As an
 *  abstract class, this implements the basic functionality common to all
 *  subclasses. Various parameters and their attributes (*_NAME, *_UNITS, *_INFO
 *  *_DEFAULT,*_MIN, *_MAX) are declared here to encourage the use of uniform
 *  conventions. Some of these parameters are instantiated in the various init*
 *  methods here, some are not.  If subclasses do not need these params, they can
 *  be ignored.  They can also be overridden if different attributes are desired.<p>
 *
 *  <b>pgaParam</b> - a WarningDoubleParameter representing the natural-log of the
 *  <b>Peak Ground Acceleration</b> Intensity-Measure parameter.
 *  This parameter is instantiated in its entirety in the
 *  initSupportedIntenistyMeasureParams() method here.<br>
 *  PGA_Param.NAME = "PGA"<br>
 *  PGA_UNITS = "g"<br>
 *  PGA_INFO = "Peak Ground Acceleration"<br>
 *  PGA_MIN = 0<br>
 *  PGA_MAX = Double.MAX_VALUE<br>
 *  PGA_WARN_MIN - <i>see code</i><br>
 *  PGA_WARN_MAX - <i>see code</i><br>
 *  PGA_DEFAULT - <i>see code</i><p>
 *
 *  <b>pgvParam</b> - a WarningDoubleParameter representing the natural-log of the
 *  <b>Peak Ground Velocity</b> Intensity-Measure parameter.
 *  This parameter is not instantiated here due to limited use.<br>
 *  PGV_Param.NAME = "PGV"<br>
 *  PGV_UNITS = "g"<br>
 *  PGV_INFO = "Peak Ground Acceleration"<br>
 *  PGV_MIN = 0<br>
 *  PGV_MAX = Double.MAX_VALUE<br>
 *  PGV_WARN_MIN - <i>see code</i><br>
 *  PGV_WARN_MAX - <i>see code</i><br>
 *  PGV_DEFAULT - <i>see code</i><p>
 *
 *  <b>saParam</b> - a WarningDoubleParameter representing the natural-log of the
 *  <b>Response Spectral Acceleration</b> Intensity-Measure Parameter
 *  This parameter is instantiated in its entirety in the
 *  initSupportedIntenistyMeasureParams() method here. However its periodParam independent-
 *  parameter must be created and added in subclasses (since supported periods will vary).<br>
 *  SA_Param.NAME = "SA"<br>
 *  SA_UNITS = "g"<br>
 *  SA_INFO = "Response Spectral Acceleration"<br>
 *  SA_MIN = 0<br>
 *  SA_MAX = Double.MAX_VALUE<br>
 *  SA_WARN_MIN - <i>see code</i><br>
 *  SA_WARN_MAX - <i>see code</i><br>
 *  SA_DEFAULT - <i>see code</i><p>
 *
 * <b>periodParam</b> - a DoubleDiscreteParameter representing the <b>Period</b> associated
 * with the Response-Spectral-Acceleration Parameter (periodParam is an
 * independentParameter of saParam).  This must be created and added to saParam in subclasses.<br>
 * PeriodParam.NAME = "SA Period"<br>
 * PERIOD_UNITS = "sec"<br>
 * PERIOD_INFO = "Oscillator Period for SA"<br>
 * PERIOD_DEFAULT = new Double( 0 )<br>
 * <i>Constraint is created and added in sub-classes</i><p>
 *
 * <b>dampingParam</b> - a DoubleDiscreteParameter representing the <b>Damping</b> level
 * associated with the Response-Spectral-Acceleration Parameter (dampingParam is
 * an independentParameter of saParam).  This parameter is instantiated in its entirety
 * in the initSupportedIntenistyMeasureParams() method here.  This must be added to
 * saParam in subclasses.  If damping values besides 5% are available, add them in
 * subclass and then set to non-editable.<br>
 * DAMPING_NAME = "SA Damping"<br>
 * DAMPING_UNITS = " % "<br>
 * DAMPING_INFO = "Oscillator Damping for SA"<br>
 * DAMPING_DEFAULT = new Double( 5.0 )<br>
 * <i>Constraint is created and added in sublclasses</i><p>
 *
 * <b>magParam</b> - a WarningDoubleParameter representing the earthquake moment <b>Magnitude</b><br>
 * MAG_NAME = "Magnitude".  This parameter is created in the initProbEqkRuptureParams()
 * method here, but the warning constraint must be created and added in subclasses.<br>
 * <i>There are no units for Magnitude</i><br>
 * MAG_INFO = "Earthquake Moment Magnatude"<br>
 * MAG_DEFAULT - <i>see code</i><br>
 * MAG_MIN - <i>see code</i><br>
 * MAG_MAX - <i>see code</i><p>
 *
 * <b>rakeParam</b> - DoubleParameter representing the earthquake rupture  <b>Rake</b><br>
 * RAKE_NAME = "Rake".  This parameter is created in the initProbEqkRuptureParams()
 * method here.<br>
 * RAKE_UNITS = "degrees"<br>
 * RAKE_INFO = "Average rake of earthquake rupture"<br>
 * RAKE_DEFAULT - <i>see code</i><br>
 * RAKE_MIN - <i>see code</i><br>
 * RAKE_MAX - <i>see code</i><p>
 *
 * <b>dipParam</b> - a DoubleParameter representing the earthquake rupture <b>Dip</b><br>
 * DIP_NAME = "Dip".  This parameter is created in the initProbEqkRuptureParams()
 * method here.<br>
 * DIP_UNITS = "degrees"<br>
 * DIP_INFO = "Average dip of earthquake rupture"<br>
 * DIP_DEFAULT - <i>see code</i><br>
 * DIP_MIN - <i>see code</i><br>
 * DIP_MAX - <i>see code</i><p>
 *
 * <b>rupTopDepthParam</b> - a DoubleParameter representing the depth to the top of the earthquake rupture<br>
 * RUP_TOP_NAME = "Rupture Top Depth".  This parameter is created in the initProbEqkRuptureParams()
 * method here.<br>
 * RUP_TOP_UNITS = "km"<br>
 * RUP_TOP_INFO = "Depth to the top of the earthquake rupture"<br>
 * RUP_TOP_DEFAULT - <i>see code</i><br>
 * RUP_TOP_MIN - <i>see code</i><br>
 * RUP_TOP_MAX - <i>see code</i><p>
 *
 * <b>componentParam</b> - a StringParameter representing the <b>Components</b> of shaking
 * that the IMR supports.<br>
 * COMPONENT_NAME = "Component"<br>
 * <i>There are no units for Component</i><br>
 * COMPONENT_DEFAULT = "Average Horizontal"<br>
 * COMPONENT_AVE_HORZ = "Average Horizontal"<br>
 * COMPONENT_OI_AVE_HORZ = "Orient. Ind. Ave. Horz."<br>
 * COMPONENT_RANDOM_HORZ = "Random Horizontal"<br>
 * COMPONENT_VERT = "Vertical";<br>
 * COMPONENT_INFO = "Component of shaking"<br>
 * <i>Constraint will be created and added in subclass</i><p>
 *
 * <b>vs30Param</b> - A WarningDoubleParameter representing the <b>average 30-meter shear-
 * wave velocity at the surface of a site</b>.  This parameter is created in the initSiteParams()
 * method here, but the warning constraint must be created and added in subclasses.<br>
 * VS30_NAME = "Vs30"<br>
 * VS30_UNITS = "m/sec"<br>
 * VS30_INFO = "Average 30 meter shear wave velocity at surface"<br>
 * VS30_DEFAULT - <i>see code</i><br>
 * VS30_MIN = - <i>see code</i><br>
 * VS30_MAX = - <i>see code</i><p>
 *
 * <b>depthTo2pt5kmPerSecParam</b> - A WarningDoubleParameter representing the
 * <b>depth to where shear-wave velocity = 2.5 km/sec</b>.  This parameter is created
 * in the initSiteParams() method here, but the warning constraint must be created
 * and added in subclasses.<br>
 * DEPTH_2pt5_NAME = "Depth 2.5 km/sec"<br>
 * DEPTH_2pt5_UNITS = "km"<br>
 * DEPTH_2pt5_INFO = "The depth to where shear-wave velocity = 2.5 km/sec"<br>
 * DEPTH_2pt5_DEFAULT - <i>see code</i><br>
 * DEPTH_2pt5_MIN = - <i>see code</i><br>
 * DEPTH_2pt5_MAX = - <i>see code</i><p>
 *
 * <b>stdDevTypeParam</b> - A StringParameter representing the various <b>types of standard
 * deviations</b> that an IMR might support; "Total" is the most common (see description
 * below for more details).<br>
 * STD_DEV_TYPE_NAME = "Std Dev Type"<br>
 * STD_DEV_TYPE_INFO = "Type of Standard Deviation"<br>
 * STD_DEV_TYPE_DEFAULT = "Total"<br>
 * STD_DEV_TYPE_TOTAL = "Total"<br>
 * StdDevTypeParam.STD_DEV_TYPE_INTER = "Inter-Event"<br>
 * STD_DEV_TYPE_INTRA = "Intra-Event"<p>
 * STD_DEV_TYPE_NONE = "None (zero)"<br>
 *
 * <b>fltTypeParam</b> - A StringParameter representing <b>different styles of faulting</b>;
 * options are specified in subclasses because nomenclature varies.<br>
 * FLT_TYPE_NAME = "Fault Type"<br>
 * <i>No units for this one</i><br>
 * FLT_TYPE_INFO = "Style of faulting"<p>
 *
 * <b>sigmaTruncTypeParam</b> - A StringParameter representing the <b>various types of truncation
 * available for the Gaussian probability distribution</b>; "1 Sided" is an upper
 * truncation (zero probabilities above); see <i>sigmaTruncLevelParam</i> below for more info.<br>
 * SIGMA_TRUNC_TYPE_NAME = "Gaussian Distribution Truncation"<br>
 * SIGMA_TRUNC_TYPE_INFO = "Type of distribution truncation to apply when computing exceedance probabilities"<br>
 * SIGMA_TRUNC_TYPE_NONE = "None"<br>
 * SIGMA_TRUNC_TYPE_1SIDED = "1 Sided"<br>
 * SIGMA_TRUNC_TYPE_2SIDED = "2 Sided"<br>
 * SIGMA_TRUNC_TYPE_DEFAULT = "None"<p>
 *
 * <b>sigmaTruncLevelParam</b> - A DoubleParameter defining <b>where the Gaussian
 * distribution is truncated </b> (this is ignored if sigmaTruncTypeParam is "None");
 * This level is defined in terms of some number of standard deviations above
 * (and perhaps below) the mean.<br>
 * SIGMA_TRUNC_LEVEL_NAME = "Truncation Level"<br>
 * SIGMA_TRUNC_LEVEL_UNITS = "Std Dev"<br>
 * SIGMA_TRUNC_LEVEL_INFO = "The number of standard deviations, from the mean, where truncation occurs"<br>
 * SIGMA_TRUNC_LEVEL_DEFAULT = 2.0 <br>
 * SIGMA_TRUNC_LEVEL_MIN = Double.MIN_VALUE<br>
 * SIGMA_TRUNC_LEVEL_MAX = Double.MAX_VALUE<p>
 *
 *
 *
 * </p> Note: SWR - SetAll() is not truly robust in case of error. <p>

 * @author     Steven W. Rock & Edward H. Field
 * @created    April 1st, 2002
 * @version    1.0
 */

/* Note: For the sake of simplicity when calling getMean(), getStdDev() and
 * getExceedenceProbability all parameters are looked up and/or calculated
 * within the function call. This may not provide the best performance when calling
 * these functions many times from within a loop where only one parameter is
 * updated. This was done intentionally so that scientists who implement other
 * IMRs can use this one as a template without having to learn the complexities
 * of advanced programming techniques.  A more efficient technique would be to
 * listen for parameter changes and act accordingly. <p>
 *
 */

public abstract class AttenuationRelationship
    extends IntensityMeasureRelationship implements AttenuationRelationshipAPI {

  /**
   *  Classname constant used for debugging statements
   */
  public final static String C = "AttenuationRelationship";

  /**
   *  Prints out debugging statements if true
   */
  protected final static boolean D = false;

  /**
   * PGA parameter, reserved for the natural log of the "Peak Ground Acceleration"
   * Intensity-Measure Parameter that most subclasses will support; all of the "PGA_*"
   * class variables relate to this Parameter. This parameter is instantiated
   * in its entirety in the initSupportedIntenistyMeasureParams() method here.
   */
  protected WarningDoubleParameter pgaParam = null;
  public final static String PGA_Param.NAME = "PGA";
  public final static String PGA_UNITS = "g";
  protected final static Double PGA_DEFAULT = new Double(Math.log(0.1));
  public final static String PGA_INFO = "Peak Ground Acceleration";
  protected final static Double PGA_MIN = new Double(Math.log(Double.MIN_VALUE));
  protected final static Double PGA_MAX = new Double(Double.MAX_VALUE);
  protected final static Double PGA_WARN_MIN = new Double(Math.log(Double.
      MIN_VALUE));
  protected final static Double PGA_WARN_MAX = new Double(Math.log(2.5));

  /**
   * PGV parameter, reserved for the natural log of the "Peak Ground Velocity" Intensity-
   * Measure Parameter that most subclasses will support; all of the "PGV_*"
   * class variables relate to this Parameter.This parameter is not instantiated
   * here due to limited use.
   */
  protected WarningDoubleParameter pgvParam = null;
  public final static String PGV_Param.NAME = "PGV";
  public final static String PGV_UNITS = "cm/sec";
  protected final static Double PGV_DEFAULT = new Double(Math.log(0.1));
  public final static String PGV_INFO = "Peak Ground Velocity";
  protected final static Double PGV_MIN = new Double(Math.log(Double.MIN_VALUE));
  protected final static Double PGV_MAX = new Double(Double.MAX_VALUE);
  protected final static Double PGV_WARN_MIN = new Double(Math.log(Double.
      MIN_VALUE));
  protected final static Double PGV_WARN_MAX = new Double(Math.log(500));
  
  
  
  /**
   * PGD parameter, reserved for the natural log of the "Peak Ground displacement" Intensity-
   * Measure Parameter that most subclasses will support; all of the "PGD_*"
   * class variables relate to this Parameter.This parameter is not instantiated
   * here due to limited use.
   */
  protected WarningDoubleParameter pgdParam = null;
  public final static String PGD_NAME = "PGD";
  public final static String PGD_UNITS = "cm";
  protected final static Double PGD_DEFAULT = new Double(Math.log(0.01));
  public final static String PGD_INFO = "Peak Ground Displacement";
  protected final static Double PGD_MIN = new Double(Math.log(Double.MIN_VALUE));
  protected final static Double PGD_MAX = new Double(Double.MAX_VALUE);
  protected final static Double PGD_WARN_MIN = new Double(Math.log(Double.
      MIN_VALUE));
  protected final static Double PGD_WARN_MAX = new Double(Math.log(2500));

  /**
   * SA parameter, reserved for the the natural log of "Spectral Acceleration"
   * Intensity-Measure Parameter that most subclasses will support; all of the
   * "SA_*" class variables relate to this Parameter.  Note also that periodParam and
   * dampingParam are internal independentParameters of saParam. This parameter
   * is instantiated in its entirety in the initSupportedIntenistyMeasureParams()
   * method here. However its periodParam independent-parameter must be created
   * and added in subclasses.
   */
  protected WarningDoubleParameter saParam = null;
  public final static String SA_Param.NAME = "SA";
  public final static String SA_UNITS = "g";
  protected final static Double SA_DEFAULT = new Double(Math.log(0.5));
  public final static String SA_INFO = "Response Spectral Acceleration";
  protected final static Double SA_MIN = new Double(Math.log(Double.MIN_VALUE));
  protected final static Double SA_MAX = new Double(Double.MAX_VALUE);
  protected final static Double SA_WARN_MIN = new Double(Math.log(Double.
      MIN_VALUE));
  protected final static Double SA_WARN_MAX = new Double(Math.log(3.0));

  /**
   * Period parameter, reserved for the oscillator period that Spectral
   * Acceleration (saParam) depends on (periodParam is an independentParameter
   * of saParam); all of the "PERIOD_*" class variables relate to this
   * Parameter.  This parameter is created and added to saParam in subclasses.
   */
  protected DoubleDiscreteParameter periodParam = null;
  public final static String PeriodParam.NAME = "SA Period";
  public final static String PERIOD_UNITS = "sec";
  protected final static Double PERIOD_DEFAULT = new Double(1.0);
  public final static String PERIOD_INFO = "Oscillator Period for SA";
  // The constraint is created and added in the subclass.


  /**
   * Damping parameter, reserved for the damping level that Spectral
   * Acceleration (saParam) depends on (dampingParam is an independentParameter
   * of saParam); all of the "DAMPING_*" class variables relate to this
   * Parameter.  This parameter is instantiated in its entirety in the
   * initSupportedIntenistyMeasureParams() method here.  This must be added to
   * saParam in subclasses.  If damping values besides 5% are available, add
   * them in subclass and then set to non-editable.
   */
  protected DoubleDiscreteParameter dampingParam = null;
  protected DoubleDiscreteConstraint dampingConstraint = null;
  public final static String DAMPING_NAME = "SA Damping";
  public final static String DAMPING_UNITS = " % ";
  protected final static Double DAMPING_DEFAULT = new Double(5);
  public final static String DAMPING_INFO = "Oscillator Damping for SA";
  //The constraint is created and added in the subclass; most will support only this default value


  /**
   * Magnitude parameter, reserved for representing moment magnitude in all
   * subclasses; all of the "MAG_*" class variables relate to this magParam
   * object.  This parameter is created in the initProbEqkRuptureParams()
   * method here, but the warning constraint must be created and added in subclasses.
   */
  protected WarningDoubleParameter magParam = null;
  public final static String MAG_NAME = "Magnitude";
  // There are no units for Magnitude
  public final static String MAG_INFO = "Earthquake Moment Magnatude";
  protected final static Double MAG_DEFAULT = new Double(5.5);
  protected final static Double MAG_MIN = new Double(0);
  protected final static Double MAG_MAX = new Double(10);
  // warning values are set in subclasses



  /**
   * Rake Parameter, reserved for representing the average rake of the earthquake
   * rupture.  This parameter is created in the initEqkRuptureParams() method
   * here.
   */
  protected DoubleParameter rakeParam = null;
  public final static String RAKE_NAME = "Rake";
  public final static String RAKE_UNITS = "degrees";
  public final static String RAKE_INFO = "Average rake of earthquake rupture";
  public final static Double RAKE_DEFAULT = new Double("0");
  protected final static Double RAKE_MIN = new Double( -180);
  protected final static Double RAKE_MAX = new Double(180);

  /**
   * Dip Parameter, reserved for representing the average rake of the earthquake
   * rupture.  This parameter is created in the initEqkRuptureParams() method
   * here.
   */
  protected WarningDoubleParameter dipParam = null;
  public final static String DIP_NAME = "Dip";
  public final static String DIP_UNITS = "degrees";
  public final static String DIP_INFO = "Average dip of earthquake rupture";
  public final static Double DIP_DEFAULT = new Double("90");
  protected final static Double DIP_MIN = new Double(0);
  protected final static Double DIP_MAX = new Double(90);

  /**
   * rupTopDepth parameter - Depth to top of rupture.  This is created in the
   * initEqkRuptureParams method.
   */
  protected WarningDoubleParameter rupTopDepthParam = null;
  public final static String RUP_TOP_NAME = "Rupture Top Depth";
  public final static String RUP_TOP_UNITS = "km";
  public final static String RUP_TOP_INFO =
      "The depth to the shallowest point on the earthquake rupture surface";
  public final static Double RUP_TOP_DEFAULT = new Double(0);
  protected final static Double RUP_TOP_MIN = new Double(0);
  protected final static Double RUP_TOP_MAX = new Double(30);

  /**
   * Component Parameter, reserved for representing the component of shaking
   * (in 3D space); all of the "COMPONENT_*" class variables relate to this
   * Parameter.
   */
  protected StringParameter componentParam = null;
  public final static String COMPONENT_NAME = "Component";
  // not units for Component
  public final static String COMPONENT_DEFAULT = "Average Horizontal";
  public final static String COMPONENT_AVE_HORZ = "Average Horizontal";
  public final static String COMPONENT_GMRotI50 = "Average Horizontal (GMRotI50)";
  public final static String COMPONENT_RANDOM_HORZ = "Random Horizontal";
  public final static String COMPONENT_VERT = "Vertical";
  public final static String COMPONENT_INFO = "Component of shaking";
  // constraint will be created and added in subclass


  /**
   * Vs30 Parameter, reserved for representing the average shear-wave velocity
   * in the upper 30 meters of a site (a commonly used parameter); all of the
   * "VS30_*" class variables relate to this Parameter.  This parameter is
   * created in the initSiteParams() method here, but the warning constraint
   * must be created and added in subclasses.
   */
  protected WarningDoubleParameter vs30Param = null;
  public final static String VS30_NAME = "Vs30";
  public final static String VS30_UNITS = "m/sec";
  public final static String VS30_INFO =
      "The average shear-wave velocity between 0 and 30-meters depth";
  public final static Double VS30_DEFAULT = new Double("760");
  protected final static Double VS30_MIN = new Double(0.0);
  protected final static Double VS30_MAX = new Double(5000.0);
  // warning values set in subclasses


  /**
   * Depth 2.5 km/sec Parameter, reserved for representing the depth to where
   * shear-wave velocity = 2.5 km/sec ("Z2.5 (m)" in PEER's 2005 NGA flat file);
   * This parameter is created in the initSiteParams() method here, but the
   * warning constraint must be created and added in subclasses.
   */
  protected WarningDoubleParameter depthTo2pt5kmPerSecParam = null;
  public final static String DEPTH_2pt5_NAME = "Depth 2.5 km/sec";
  public final static String DEPTH_2pt5_UNITS = "km";
  public final static String DEPTH_2pt5_INFO =
      "The depth to where shear-wave velocity = 2.5 km/sec";
  public final static Double DEPTH_2pt5_DEFAULT = new Double("1.0");
  protected final static Double DEPTH_2pt5_MIN = new Double(0.0);
  protected final static Double DEPTH_2pt5_MAX = new Double(30000.0);
  // warning values set in subclasses


  /**
   * StdDevType, a StringParameter, reserved for representing the various types of
   * standard deviations that various IMR might support:  "InterEvent" is
   * the event to event variability, "Intra-Event" is the variability within
   * an event, and "Total" (the most common) is the other two two added in quadrature.
   * Other options are defined in some subclasses.
   */
  protected StringParameter stdDevTypeParam = null;
  public final static String STD_DEV_TYPE_NAME = "Std Dev Type";
  // No units for this one
  public final static String STD_DEV_TYPE_INFO = "Type of Standard Deviation";
  public final static String STD_DEV_TYPE_DEFAULT = "Total";
  public final static String STD_DEV_TYPE_TOTAL = "Total";
  public final static String StdDevTypeParam.STD_DEV_TYPE_INTER = "Inter-Event";
  public final static String STD_DEV_TYPE_INTRA = "Intra-Event";
  public final static String STD_DEV_TYPE_NONE = "None (zero)";
  public final static String STD_DEV_TYPE_TOTAL_MAG_DEP =
      "Total (Mag Dependent)";
  public final static String STD_DEV_TYPE_TOTAL_PGA_DEP =
      "Total (PGA Dependent)";
  public final static String STD_DEV_TYPE_INTRA_MAG_DEP =
      "Intra-Event (Mag Dependent)";

  /**
   * FltTypeParam, a StringParameter reserved for representing different
   * styles of faulting.  The options are not specified here because
   * nomenclature generally differs among subclasses.
   */
  protected StringParameter fltTypeParam = null;
  public final static String FLT_TYPE_NAME = "Fault Type";
  // No units for this one
  public final static String FLT_TYPE_INFO = "Style of faulting";

  /**
   * SigmaTruncTypeParam, a StringParameter that represents the type of
   * probability distribution truncation.
   */
  protected StringParameter sigmaTruncTypeParam = null;
  public final static String SIGMA_TRUNC_TYPE_NAME = "Gaussian Truncation";
  public final static String SIGMA_TRUNC_TYPE_INFO = "Type of distribution truncation to apply when computing exceedance probabilities";
  public final static String SIGMA_TRUNC_TYPE_NONE = "None";
  public final static String SIGMA_TRUNC_TYPE_1SIDED = "1 Sided";
  public final static String SIGMA_TRUNC_TYPE_2SIDED = "2 Sided";
  public final static String SIGMA_TRUNC_TYPE_DEFAULT = "None";

  /**
   * SigmaTruncLevelParam, a DoubleParameter that represents where truncation occurs
   * on the Gaussian distribution (in units of standard deviation, relative to the mean).
   */
  protected DoubleParameter sigmaTruncLevelParam = null;
  public final static String SIGMA_TRUNC_LEVEL_NAME = "Truncation Level";
  public final static String SIGMA_TRUNC_LEVEL_UNITS = "Std Dev";
  public final static String SIGMA_TRUNC_LEVEL_INFO =
      "The number of standard deviations, from the mean, where truncation occurs";
  public final static Double SIGMA_TRUNC_LEVEL_DEFAULT = new Double(2.0);
  public final static Double SIGMA_TRUNC_LEVEL_MIN = new Double(Double.
      MIN_VALUE);
  public final static Double SIGMA_TRUNC_LEVEL_MAX = new Double(Double.
      MAX_VALUE);

  /**
   * This allows users to set a maximul distance (beyond which the mean will
   * be effectively zero)
   */
  protected double USER_MAX_DISTANCE = Double.MAX_VALUE;
  protected final static double VERY_SMALL_MEAN = -35.0; // in ln() space

  /**
   *  Common error message = "Not all parameters have been set"
   */
  protected final static String ERR = "Not all parameters have been set";

  /**
   *  List of all Parameters that the mean calculation depends upon, except for
   *  the intensity-measure related parameters (type/level) and any independentdent parameters
   *  they contain.
   */
  protected ParameterList meanIndependentParams = new ParameterList();

  /**
   *  List of all Parameters that the stdDev calculation depends upon, except for
   *  the intensity-measure related parameters (type/level) and any independentdent parameters
   *  they contain.
   */
  protected ParameterList stdDevIndependentParams = new ParameterList();

  /**
   *  List of all Parameters that the exceed. prob. calculation depends upon, except for
   *  the intensity-measure related parameters (type/level) and any independentdent parameters
   *  they contain.  Note that this and its iterator method could be applied in the parent class.
   */
  protected ParameterList exceedProbIndependentParams = new ParameterList();

  /**
   *  List of all Parameters that the IML at exceed. prob. calculation depends upon, except for
   *  the intensity-measure related parameters (type/level) and any independentdent parameters
   *  they contain.
   */
  protected ParameterList imlAtExceedProbIndependentParams = new ParameterList();

  /**
   *  Constructor for the AttenuationRelationship object - subclasses should execute the
   *  various init*() methods (in proper order)
   */
  public AttenuationRelationship() {
    super();
  }

  /**
   * This method sets the user-defined distance beyond which ground motion is
   * set to effectively zero (the mean is a large negative value).
   * @param maxDist
   */
  public void setUserMaxDistance(double maxDist) {
    USER_MAX_DISTANCE = maxDist;
  }

  /**
   *  Sets the value of the currently selected intensityMeasure (if the
   *  value is allowed); this will reject anything that is not a Double.
   *
   * @param  iml                     The new intensityMeasureLevel value
   * @exception  ParameterException  Description of the Exception
   */
  public void setIntensityMeasureLevel(Object iml) throws ParameterException {

    if (! (iml instanceof Double)) {
      throw new ParameterException(C +
                                   ": setIntensityMeasureLevel(): Object not a DoubleParameter, unable to set.");
    }

    setIntensityMeasureLevel( (Double) iml);
  }

  /**
   *  Sets the value of the selected intensityMeasure;
   *
   * @param  iml                     The new intensityMeasureLevel value
   * @exception  ParameterException  Description of the Exception
   */
  public void setIntensityMeasureLevel(Double iml) throws ParameterException {

    if (im == null) {
      throw new ParameterException(C +
                                   ": setIntensityMeasureLevel(): Intensity Measure is null, unable to set."
          );
    }

    this.im.setValue(iml);
  }

  /**
   * This method sets the location in the site.
   * This is helpful because it allows to  set the location within the
   * site without setting the Site Parameters. Thus allowing the capability
   * of setting the site once and changing the location of the site to do the
   * calculations.
   */
  public void setSiteLocation(Location loc) {
    //if site is null create a new Site
    if (site == null) {
      site = new Site();
    }
    site.setLocation(loc);
    setPropagationEffectParams();
  }

  /**
   *  Calculates the value of each propagation effect parameter from the
   *  current Site and ProbEqkRupture objects. <P>
   */
  protected abstract void setPropagationEffectParams();

  /**
   *  This calculates the probability that the intensity-measure level
   *  (the value in the Intensity-Measure Parameter) will be exceeded
   *  given the mean and stdDev computed from current independent parameter
   *  values.  Note that the answer is not stored in the internally held
   *  exceedProbParam (this latter param is used only for the
   *  getIML_AtExceedProb() method).
   *
   * @return                         The exceedProbability value
   * @exception  ParameterException  Description of the Exception
   * @exception  IMRException        Description of the Exception
   */
  protected double getExceedProbabilityFiltered(double mean, double stdDev, double iml) throws
  ParameterException, IMRException {

	    
	    double newPeriod = 0.01;
	    double oldPeriod;
	    oldPeriod = ((Double) periodParam.getValue()).doubleValue();
	  
	    periodParam.setValue(newPeriod);    
	    double pgaMean = getMean();
	    double pgaStdDev = getStdDev();
	    
	    periodParam.setValue(oldPeriod);
	    
	    double corrCoef = 0;  
	    
	    // WUS correlation coefficients
	    	
	    if (oldPeriod >= 0.0) {
	    	corrCoef = Math.min((Math.log(oldPeriod) - Math.log(0.02857)) * (0.931 - 0.976) / (Math.log(0.05) - Math.log(0.02857)) + 0.976,1);
	        if(oldPeriod >= 0.05) {
	        	corrCoef = (Math.log(oldPeriod) - Math.log(0.05)) * (0.633 - 0.931) / (Math.log(0.2) - Math.log(0.05)) + 0.931;
	            if(oldPeriod >= 0.2) {
	            	corrCoef = (Math.log(oldPeriod) - Math.log(0.2)) * (0.59 - 0.633) / (Math.log(2) - Math.log(0.2)) + 0.683;                	
	            }	
	        }
	    }

	    double dEpsilon = 0.1;
	    double probSai = 0;
	    double probPGAj = 0;
	    double exceedprobCAVij = 0;
	    double epsilonSa = (iml-mean)/stdDev;
	    double epsilonSai, epsilonPGAj, sai, pgaj, mag, vs30;
	    double probSaPGA = 0;
	    double probSaPGACAV = 0;
		double pgaFlag = 1;
	    
	    mag = ( (Double) magParam.getValue()).doubleValue();
//	    System.out.println("Mag: " + mag + ", Mean: " + mean + ", StdDev: " + stdDev + ", pgaMean: " + pgaMean + ", pgaStdDev: " + pgaStdDev + ", Correlation: " + corrCoef);
//	    System.out.println("Correct method, old T, new T" + oldPeriod + newPeriod);
	    // This should be changed so that it matches the site vs30 or site class
	    vs30 = 1100.0;
	    
	    
	    for(int i=1;i<=51;++i){
	    	epsilonSai = epsilonSa + (i-1)*dEpsilon;
	    	probSai = getExceedProbability(0,1,epsilonSai-dEpsilon/2)-getExceedProbability(0,1,epsilonSai+dEpsilon/2);
	 //   	sai = mean + stdDev*epsilonSai;
	    	for(int j=1;j<=51;++j){
	    		epsilonPGAj = -2.5 + (j-1)*dEpsilon;
	        	probPGAj = getExceedProbability(0,1,epsilonPGAj-dEpsilon/2)-getExceedProbability(0,1,epsilonPGAj+dEpsilon/2);
	        	pgaj = pgaMean + Math.sqrt(1-corrCoef*corrCoef)*pgaStdDev*epsilonPGAj + corrCoef*epsilonSai*pgaStdDev;
	        	double meanCAVij = -0.405 + 0.509*(pgaj+2.5) - 2.11/(pgaj+4.25) + 0.667*(mag-6.5) - 0.0947*(mag-6.5)*(mag-6.5) - 0.266*(Math.log(vs30)-6);
	        	double sigmaCAV = 0.46;
	        	exceedprobCAVij = getExceedProbability(meanCAVij,sigmaCAV,Math.log(0.16));
	        	probSaPGA = probSaPGA + probSai*probPGAj;
	        	if (Math.exp(pgaj) >= 0.025){
	        		pgaFlag = 1;
	        	}
	        	else {
	        		pgaFlag = 0;
	        	}
	        	probSaPGACAV = probSaPGACAV + probSai*probPGAj*exceedprobCAVij*pgaFlag;
//	        	if (mag == 5 & j ==1 & i == 1){
//	        		System.out.println("Mag: " + mag + ", Mean: " + mean + ", StdDev: " + stdDev + ", pgaMean: " + pgaMean + ", pgaStdDev: " + pgaStdDev + ", Correlation: " + corrCoef);
//	        		System.out.println("Mag: " + mag + ", j, PGAj: " +i+j+ pgaj + ", meanCAV: " + meanCAVij + ", exceedprob: " + exceedprobCAVij + ", probSai: " + probSai + ", probPGAj: " +probPGAj);
//	        	}

	    	}
	    }
	    
	    periodParam.setValue(oldPeriod);
	    
	    double unfilteredProb = getExceedProbability(mean, stdDev, iml);
	    
	    double filteredProb = unfilteredProb*probSaPGACAV/probSaPGA;
	    
//	    if (mag == 5){
//	    System.out.println("Mag: " + mag + ", Mean: " + mean + ", StdDev: " + stdDev + ", pgaMean: " + pgaMean + ", pgaStdDev: " + pgaStdDev + ", Correlation: " + corrCoef);
//	    System.out.println(unfilteredProb + " " + probSaPGACAV + " " + probSaPGA + " " + filteredProb);
//	    }
	    
	    if (unfilteredProb == 0.0) {
	    	return unfilteredProb;
	    } else {
	    	return filteredProb;
	    }
	    	    
}

  public double getExceedProbability() throws ParameterException, IMRException {

    // IS THIS REALLY NEEDED; IS IT SLOWING US DOWN?
    if ( (im == null) || (im.getValue() == null)) {
      throw new ParameterException(C +
                                   ": getExceedProbability(): " +
          "Intensity measure or value is null, unable to run this calculation."
          );
    }

    // Calculate the standardized random variable
    double iml = ((Double) im.getValue()).doubleValue();
    double stdDev = getStdDev();
    double mean = getMean();

    return getExceedProbabilityFiltered(mean, stdDev, iml);
  }

  /**
   *  This calculates the probability that the supplied intensity-measure level
   *  will be exceeded given the mean and stdDev computed from current independent
   *  parameter values.  Note that the answer is not stored in the internally held
   *  exceedProbParam (this latter param is used only for the
   *  getIML_AtExceedProb() method).
   *
   * @return                         The exceedProbability value
   * @exception  ParameterException  Description of the Exception
   * @exception  IMRException        Description of the Exception
   */
  public double getExceedProbability(double iml) throws ParameterException,
      IMRException {

    // set the im parameter in order to verify that it's a permitted value
    im.setValue(new Double(iml));

    return getExceedProbability();
  }


  /**
   *  This calculates the exceed-probability for each SA-Period that
   *  the supplied intensity-measure level
   *  will be exceeded given the mean and stdDev computed from current independent
   *  parameter values.  Note that the answer is not stored in the internally held
   *  exceedProbParam (this latter param is used only for the
   *  getIML_AtExceedProb() method).
   *
   * @return     DiscretizedFuncAPI  The DiscretizedFuncAPI function with each
   * value corresponding the SA Period
   * @exception  ParameterException  Description of the Exception
   * @exception  IMRException        Description of the Exception
   */
  public DiscretizedFuncAPI getSA_ExceedProbSpectrum(double iml) throws ParameterException,
      IMRException {
    this.setIntensityMeasure(this.SA_Param.NAME);
    im.setValue(new Double(iml));
    DiscretizedFuncAPI exeedProbFunction =  new ArbitrarilyDiscretizedFunc();
    ArrayList allowedSA_Periods = periodParam.getAllowedDoubles();
    int size = allowedSA_Periods.size();
    for(int i=0;i<size;++i){
      Double saPeriod = (Double)allowedSA_Periods.get(i);
      getParameter(this.PeriodParam.NAME).setValue(saPeriod);
      exeedProbFunction.set(saPeriod.doubleValue(),getExceedProbability());
    }
    return exeedProbFunction;
  }


  /**
   * This calculates the intensity-measure level for each Sa Period
   * associated with probability
   * held by the exceedProbParam given the mean and standard deviation
   * (according to the chosen truncation type and level).  Note
   * that this does not store the answer in the value of the internally held
   * intensity-measure parameter.
   * @param exceedProb : Sets the Value of the exceed Prob param with this value.
   * @return                         The intensity-measure level
   * @exception  ParameterException  Description of the Exception
   */
  public DiscretizedFuncAPI getSA_IML_AtExceedProbSpectrum(double exceedProb) throws ParameterException,
      IMRException {
    this.setIntensityMeasure(this.SA_Param.NAME);
    //sets the value of the exceedProb Param.
    exceedProbParam.setValue(exceedProb);
    DiscretizedFuncAPI imlFunction =  new ArbitrarilyDiscretizedFunc();
    ArrayList allowedSA_Periods = periodParam.getAllowedDoubles();
    int size = allowedSA_Periods.size();
    for(int i=0;i<size;++i){
      Double saPeriod = (Double)allowedSA_Periods.get(i);
      getParameter(this.PeriodParam.NAME).setValue(saPeriod);
      imlFunction.set(saPeriod.doubleValue(),getIML_AtExceedProb());
    }

    return imlFunction;
  }



  /**
   * This returns (iml-mean)/stdDev, ignoring any truncation.  This gets the iml
   * from the value in the Intensity-Measure Parameter.  SHOULD THIS THROW AN
   * EXCEPTION LIKE GetExceedProbabilityY()?
   * @return double
   */
  public double getEpsilon(){
    double iml = ((Double) im.getValue()).doubleValue();
    return (iml - getMean())/getStdDev();
  }


  /**
   * This returns (iml-mean)/stdDev, ignoring any truncation.
   *
   * @param iml double
   * @return double
   */
  public double getEpsilon(double iml){
    // set the im parameter in order to verify that it's a permitted value
    im.setValue(new Double(iml));

    return getEpsilon();
  }

  /**
   * This method computed the probability of exceeding the IM-level given the
   * mean and stdDev.
   * @param mean
   * @param stdDev
   * @param iml
   * @return
   * @throws ParameterException
   * @throws IMRException
   */
  protected double getExceedProbability(double mean, double stdDev, double iml) throws
      ParameterException, IMRException {

    if (stdDev != 0) {
      double stRndVar = (iml - mean) / stdDev;
      // compute exceedance probability based on truncation type
      if (sigmaTruncTypeParam.getValue().equals(SIGMA_TRUNC_TYPE_NONE)) {
        return GaussianDistCalc.getExceedProb(stRndVar);
      }
      else {
        double numSig = ( (Double) ( (ParameterAPI) sigmaTruncLevelParam).
                         getValue()).doubleValue();
        if (sigmaTruncTypeParam.getValue().equals(SIGMA_TRUNC_TYPE_1SIDED)) {
          return GaussianDistCalc.getExceedProb(stRndVar, 1, numSig);
        }
        else {
          return GaussianDistCalc.getExceedProb(stRndVar, 2, numSig);
        }
      }
    }
    else {
      if (iml > mean) {
        return 0;
      }
      else {
        return 1;
      }
    }
  }

  /**
   *  This fills in the exceedance probability for multiple intensityMeasure
   *  levels (often called a "hazard curve"); the levels are obtained from
   *  the X values of the input function, and Y values are filled in with the
   *  asociated exceedance probabilities. NOTE: THE PRESENT IMPLEMENTATION IS
   *  STRANGE IN THAT WE DON'T NEED TO RETURN ANYTHING SINCE THE FUNCTION PASSED
   *  IN IS WHAT CHANGES (SHOULD RETURN NULL?).
   *
   * @param  intensityMeasureLevels  The function to be filled in
   * @return                         The function filled in
   * @exception  ParameterException  Description of the Exception
   */
  public DiscretizedFuncAPI getExceedProbabilities(
      DiscretizedFuncAPI intensityMeasureLevels
      ) throws ParameterException {

    double stdDev = getStdDev();
    double mean = getMean();

    Iterator it = intensityMeasureLevels.getPointsIterator();
    while (it.hasNext()) {

      DataPoint2D point = (DataPoint2D) it.next();
      point.setY(getExceedProbabilityFiltered(mean, stdDev, point.getX()));
//      System.out.println("ExceedProb: " + getExceedProbabilityFiltered(mean, stdDev, point.getX()));

    }

    return intensityMeasureLevels;
  }

  /**
   * This method will compute the total probability of exceedance for a PointEqkSource
   * (including the probability of each rupture).  It is assumed that this
   * source is Poissonian (not checked).  This saves time by computing distance only
   * once for all ruptures in this source.  This could be extended to include the
   * point-source distance correction as well (a boolean in the constructor?), although
   * this would have to check for each distance type.
   * @param ptSrc
   * @param iml
   * @return
   */
  public double getTotExceedProbability(PointEqkSource ptSrc, double iml) {

    double totProb = 1.0, qkProb;
    ProbEqkRupture tempRup;

    //set the IML
    im.setValue(new Double(iml));

    // set the eqRup- and propEffect-params from the first rupture
    this.setEqkRupture(ptSrc.getRupture(0));

    //now loop over ruptures changing only the magnitude parameter.
    for (int i = 0; i < ptSrc.getNumRuptures(); i++) {
      tempRup = ptSrc.getRupture(i);
      magParam.setValueIgnoreWarning(new Double(tempRup.getMag()));
      qkProb = tempRup.getProbability();

      // check for numerical problems
      if (Math.log(1.0 - qkProb) < -30.0) {
        throw new RuntimeException(
            "Error: The probability for this ProbEqkRupture (" + qkProb +
            ") is too high for a Possion source (~infinite number of events)");
      }

      totProb *= Math.pow(1.0 - qkProb, getExceedProbability());
    }
    return 1 - totProb;
  }

  /**
   *  This calculates the intensity-measure level associated with probability
   *  held by the exceedProbParam given the mean and standard deviation
   * (according to the chosen truncation type and level).  Note
   *  that this does not store the answer in the value of the internally held
   *  intensity-measure parameter.
   *
   * @return                         The intensity-measure level
   * @exception  ParameterException  Description of the Exception
   */
  public double getIML_AtExceedProb() throws ParameterException {

    if (exceedProbParam.getValue() == null) {
      throw new ParameterException(C +
                                   ": getExceedProbability(): " +
          "exceedProbParam or its value is null, unable to run this calculation."
          );
    }

    double exceedProb = ( (Double) ( (ParameterAPI) exceedProbParam).getValue()).
        doubleValue();
    double stRndVar;
    String sigTrType = (String) sigmaTruncTypeParam.getValue();

    // compute the iml from exceed probability based on truncation type:

    // check for the simplest, most common case (median from symmectric truncation)

    if (!sigTrType.equals(SIGMA_TRUNC_TYPE_1SIDED) && exceedProb == 0.5) {
      return getMean();
    }
    else {
      if (sigTrType.equals(SIGMA_TRUNC_TYPE_NONE)) {
        stRndVar = GaussianDistCalc.getStandRandVar(exceedProb, 0, 0, 1e-6);
      }
      else {
        double numSig = ( (Double) ( (ParameterAPI) sigmaTruncLevelParam).
                         getValue()).doubleValue();
        if (sigTrType.equals(SIGMA_TRUNC_TYPE_1SIDED)) {
          stRndVar = GaussianDistCalc.getStandRandVar(exceedProb, 1, numSig,
              1e-6);
        }
        else {
          stRndVar = GaussianDistCalc.getStandRandVar(exceedProb, 2, numSig,
              1e-6);
        }
      }
      return getMean() + stRndVar * getStdDev();
    }
  }

  /**
   *  This calculates the intensity-measure level associated with probability
   *  held by the exceedProbParam given the mean and standard deviation
   * (according to the chosen truncation type and level).  Note
   *  that this does not store the answer in the value of the internally held
   *  intensity-measure parameter.
   * @param exceedProb : Sets the Value of the exceed Prob param with this value.
   * @return                         The intensity-measure level
   * @exception  ParameterException  Description of the Exception
   */
  public double getIML_AtExceedProb(double exceedProb) throws
      ParameterException {

    //sets the value of the exceedProb Param.
    exceedProbParam.setValue(exceedProb);
    return getIML_AtExceedProb();
  }

  /**
   *  Returns an iterator over all the Parameters that the Mean calculation depends upon.
   *  (not including the intensity-measure related paramters and their internal,
   *  independent parameters).
   *
   * @return    The Independent Params Iterator
   */
  public ListIterator getMeanIndependentParamsIterator() {
    return meanIndependentParams.getParametersIterator();
  }

  /**
   *  Returns an iterator over all the Parameters that the StdDev calculation depends upon
   *  (not including the intensity-measure related paramters and their internal,
   *  independent parameters).
   *
   * @return    The Independent Parameters Iterator
   */
  public ListIterator getStdDevIndependentParamsIterator() {
    return stdDevIndependentParams.getParametersIterator();
  }

  /**
   *  Returns an iterator over all the Parameters that the exceedProb calculation
   *  depends upon (not including the intensity-measure related paramters and
   *  their internal, independent parameters).
   *
   * @return    The Independent Params Iterator
   */
  public ListIterator getExceedProbIndependentParamsIterator() {
    return exceedProbIndependentParams.getParametersIterator();
  }

  /**
   *  Returns an iterator over all the Parameters that the IML-at-exceed-
   *  probability calculation depends upon. (not including the intensity-measure
   *  related paramters and their internal, independent parameters).
   *
   * @return    The Independent Params Iterator
   */
  public ListIterator getIML_AtExceedProbIndependentParamsIterator() {
    return imlAtExceedProbIndependentParams.getParametersIterator();
  }

  /**
   * This returns metadata for all parameters (only showing the independent parameters
   * relevant for the presently chosen imt)
   * @return
   */
  public String getAllParamMetadata() {
    String metadata = imlAtExceedProbIndependentParams.
        getParameterListMetadataString();
    metadata += "; " + im.getMetadataString() + " [ ";
    Iterator it = ( (DependentParameter) im).getIndependentParametersIterator();
    while (it.hasNext()) {
      metadata += ( (ParameterAPI) it.next()).getMetadataString() + "; ";
    }
    metadata = metadata.substring(0, metadata.length() - 2);
    metadata += " ]";
    return metadata;

  }

  /**
   *  This creates the following parameters for subclasses: saParam; dampingParam,
   *  and pgaParam; the periodParam (one of saParam's independent parameters) is
   *  created and added in subclasses.  All these parameters are added to the
   *  supportedIMParams list in subclasses.  Note: this must generally be executed
   *  after the initCoefficients() method.<br>
   *
   */
  protected void initSupportedIntensityMeasureParams() {

    // Create SA Parameter:
    DoubleConstraint saConstraint = new DoubleConstraint(SA_MIN, SA_MAX);
    saConstraint.setNonEditable();
    saParam = new WarningDoubleParameter(SA_Param.NAME, saConstraint, SA_UNITS);
    saParam.setInfo(SA_INFO);
    DoubleConstraint warn1 = new DoubleConstraint(SA_WARN_MIN, SA_WARN_MAX);
    warn1.setNonEditable();
    saParam.setWarningConstraint(warn1);

    // Damping-level parameter for SA
    // (overide this in subclass of other damping levels are available)
    dampingConstraint = new DoubleDiscreteConstraint();
    dampingConstraint.addDouble(DAMPING_DEFAULT);
    // leave constrain editable in case subclasses want to add other options
    dampingParam = new DoubleDiscreteParameter(DAMPING_NAME, dampingConstraint,
                                               DAMPING_UNITS, DAMPING_DEFAULT);
    dampingParam.setInfo(DAMPING_INFO);
    dampingParam.setNonEditable();

    // Create PGA Parameter
    DoubleConstraint pgaConstraint = new DoubleConstraint(PGA_MIN, PGA_MAX);
    pgaConstraint.setNonEditable();
    pgaParam = new WarningDoubleParameter(PGA_Param.NAME, pgaConstraint, PGA_UNITS);
    pgaParam.setInfo(PGA_INFO);
    DoubleConstraint warn2 = new DoubleConstraint(PGA_WARN_MIN, PGA_WARN_MAX);
    warn2.setNonEditable();
    pgaParam.setWarningConstraint(warn2);
    pgaParam.setNonEditable();

  }

  /**
   *  Creates the Vs30 parameter for subclasses that use it; subclasses must
   *  create and added the warning constraint and add this parameter to the
   *  siteParams list; subclasses that don't use this vs30Param can simply not
   *  call this method.
   *  <br>
   *
   */
  protected void initSiteParams() {

    // create Vs30Param:
    DoubleConstraint vs30Constraint = new DoubleConstraint(VS30_MIN, VS30_MAX);
    vs30Constraint.setNonEditable();
    vs30Param = new WarningDoubleParameter(VS30_NAME, vs30Constraint,
                                           VS30_UNITS);
    vs30Param.setInfo(VS30_INFO);

    // create the depth to 2.5 shear-wave velocity parameter
    DoubleConstraint c = new DoubleConstraint(DEPTH_2pt5_MIN, DEPTH_2pt5_MAX);
    c.setNullAllowed(true);
    c.setNonEditable();
    depthTo2pt5kmPerSecParam = new WarningDoubleParameter(DEPTH_2pt5_NAME, c,
        DEPTH_2pt5_UNITS);
    depthTo2pt5kmPerSecParam.setInfo(DEPTH_2pt5_INFO);
  }

  /**
   *  Creates the following potential-Earthquake Parameters for subclasses: magParam
   *  (moment Magnitude parameter).  Warning constraints must be created and added
   *  in subclasses. This parameter is also added to the probEqkRuptureParams list
   *  in subclasses.<br>
   *
   */
  protected void initEqkRuptureParams() {

    // Dip Parameter:
    DoubleConstraint dipConstraint = new DoubleConstraint(DIP_MIN, DIP_MAX);
    dipConstraint.setNonEditable();
    dipParam = new WarningDoubleParameter(DIP_NAME, dipConstraint);
    dipParam.setInfo(DIP_INFO);

    // Rake Parameter:
    DoubleConstraint rakeConstraint = new DoubleConstraint(RAKE_MIN, RAKE_MAX);
    rakeConstraint.setNonEditable();
    rakeParam = new DoubleParameter(RAKE_NAME, rakeConstraint);
    rakeParam.setInfo(RAKE_INFO);

    // create RupTopDepthParam
    DoubleConstraint c = new DoubleConstraint(RUP_TOP_MIN, RUP_TOP_MAX);
    rupTopDepthParam = new WarningDoubleParameter(this.RUP_TOP_NAME, c,
                                           this.RUP_TOP_UNITS);
    rupTopDepthParam.setInfo(RUP_TOP_INFO);

  }

  /**
   *  Creates any Propagation-Effect related parameters and adds them to the
   *  propagationEffectParams list<br>
   *
   */
  protected abstract void initPropagationEffectParams();

  /**
   * Adds the Listeners to the parameters so that Attenuation can listen
   * to any kind of changes to parameter values.
   */
  protected  void initParameterEventListeners(){};

  /**
   * Allows to reset the change listeners on the parameters
   */
  public void resetParameterEventListeners(){};

  /**
   * This creates the otherParams list.
   * These are any parameters that the exceedance probability depends upon that is
   * not a supported IMT (or one of their independent parameters) and is not contained
   * in, or computed from, the site or eqkRutpure objects.  Note that this does not
   * include the exceedProbParam (which exceedance probability does not depend on).
   */
  protected void initOtherParams() {

    // Sigma truncation type parameter:
    StringConstraint sigmaTruncTypeConstraint = new StringConstraint();
    sigmaTruncTypeConstraint.addString(SIGMA_TRUNC_TYPE_NONE);
    sigmaTruncTypeConstraint.addString(SIGMA_TRUNC_TYPE_1SIDED);
    sigmaTruncTypeConstraint.addString(SIGMA_TRUNC_TYPE_2SIDED);
    sigmaTruncTypeConstraint.setNonEditable();
    sigmaTruncTypeParam = new StringParameter(SIGMA_TRUNC_TYPE_NAME,
                                              sigmaTruncTypeConstraint,
                                              SIGMA_TRUNC_TYPE_DEFAULT);
    sigmaTruncTypeParam.setInfo(SIGMA_TRUNC_TYPE_INFO);
    sigmaTruncTypeParam.setNonEditable();

    // Sigma truncation level parameter:
    DoubleConstraint sigmaTruncLevelConstraint = new DoubleConstraint(
        SIGMA_TRUNC_LEVEL_MIN, SIGMA_TRUNC_LEVEL_MAX);
    sigmaTruncLevelConstraint.setNonEditable();
    sigmaTruncLevelParam = new DoubleParameter(SIGMA_TRUNC_LEVEL_NAME,
                                               sigmaTruncLevelConstraint,
                                               SIGMA_TRUNC_LEVEL_UNITS,
                                               SIGMA_TRUNC_LEVEL_DEFAULT);
    sigmaTruncLevelParam.setInfo(SIGMA_TRUNC_LEVEL_INFO);
    sigmaTruncLevelParam.setNonEditable();

    // Put parameters in the otherParams list:
    otherParams.clear();
    otherParams.addParameter(sigmaTruncTypeParam);
    otherParams.addParameter(sigmaTruncLevelParam);

  }

  /**
   * 
   * @throws MalformedURLException if returned URL is not a valid URL.
   * @returns the URL to the AttenuationRelationship document on the Web.
   */
  public URL getAttenuationRelationshipURL() throws MalformedURLException{
	  return null;
  }
  
}
