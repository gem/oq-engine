/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.imr.attenRelImpl;

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.exceptions.IMRException;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerConstraint;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.Parameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.util.SiteTranslator;

/**
 * <b>Title:</b> SiteSpecific_2006_AttenRel<p>
 *
 * <b>Description:</b> This implements the site effect models
 * developed by Bazzuro and Cornell(2004), Baturay and Stewart(2003), applied
 * to the Abrahamson & Silva (1997) rock-site predictions. <p>
 *
 * Supported Intensity-Measure Parameters:<p>
 * <UL>
 * <LI>saParam - Response Spectral Acceleration
 * <LI>pgaParam - Peak Ground Acceleration
 * </UL><p>
 * Other Independent Parameters:<p>
 * <UL>
 * <LI>distanceRupParam - closest distance to surface projection of fault
 * <LI>vs30Param - Average 30-meter shear-wave velocity at the site
 * <LI>softSoilParam - To overide Vs30 and apply NEHPR E (see INFO for details)
 * <LI>fltTypeParam - Style of faulting
 * <LI>isOnHangingWallParam - tells if site is directly over the rupture surface
 * <LI>componentParam - Component of shaking (only one)
 * <LI>stdDevTypeParam - The type of standard deviation
 * </UL><p>
 *
 * @author     Edward H. Field
 * @created    july, 2004
 * @version    1.0
 */


public class SiteSpecific_2006_AttenRel
    extends AttenuationRelationship implements ScalarIntensityMeasureRelationshipAPI,ParameterChangeListener,
    NamedObjectAPI {

  // debugging stuff:
  private final static String C = "SiteSpecific_2006_AttenRel";
  private final static boolean D = false;
  public final static String NAME = "Site Specfic AttenuationRelationship (2006)";
  public final static String SHORT_NAME = "SS2006";
  private static final long serialVersionUID = 1234567890987654369L;


  
  
  // period
  private double[] period = {
		  0.0,0.01,0.02,0.03,0.04,0.05,0.06,0.075,0.09,0.1,0.12,0.15,0.17,0.2,0.24,0.3,0.36,0.4,0.46,0.5,0.60,0.75,0.85,
		  1,1.5,2,3,4,5 };
  //coefficients
  private double[] b1 = {-0.64,-0.64,-0.63,-0.62,-0.61,-0.64,-0.64,-0.64,-0.64,-0.6,-0.56,-0.53,-0.53,
		  -0.52,-0.52,-0.52,-0.51,-0.51,-0.5,-0.5,-0.49,-0.47,-0.46,-0.44,-0.4,-0.38,-0.34,-0.31,-0.3
  };
  private double[] vRef = {418,418,490,324,233,192,181,196,239,257,299,357,406,453,493,532,535,535,
		  535,535,535,535,535,535,535,535,535,535,535
  };
  private double[] c ={-0.36,-0.36,-0.34,-0.33,-0.31,-0.29,-0.25,-0.23,-0.23,-0.25,-0.26,-0.28,
		  -0.29,-0.31,-0.38,-0.44,-0.48,-0.5,-0.55,-0.6,-0.66,-0.69,-0.69,-0.7,-0.72,-0.73,-0.74,-0.75,-0.75
  };
  private double[] b2 ={-0.14,-0.14,-0.12,-0.11,-0.11,-0.11,-0.11,-0.11,-0.12,-0.13,-0.14,
		  -0.18,-0.19,-0.19,-0.16,-0.14,-0.11,-0.1,-0.08,-0.06,-0.03,0,0,0,0,0,0,0,0
  };
  private double[] tau ={
		  0.27,0.27,0.26,0.26,0.26,0.25,0.25,0.24,0.23,0.23,0.24,0.25,0.26,0.27,0.29,0.35,0.38,0.4,
		  0.42,0.42,0.42,0.42,0.42,0.42,0.42,0.43,0.45,0.47,0.49
  };
  private double[] e1 ={0.44,0.44,0.45,0.46,0.47,0.47,0.48,0.48,0.49,0.49,0.49,0.49,0.48,0.47,0.47,
		  0.46,0.46,0.46,0.45,0.45,0.44,0.44,0.44,0.44,0.44,0.44,0.44,0.44,0.44
  };
  private double[] e3 ={0.5,0.5,0.51,0.51,0.51,0.52,0.52,0.52,0.52,0.53,0.53,0.54,0.55,0.56,0.56,0.57,
		  0.57,0.57,0.58,0.59,0.6,0.63,0.63,0.64,0.67,0.69,0.71,0.73,0.75
  };
  
  private ArbitrarilyDiscretizedFunc funcb1 = new ArbitrarilyDiscretizedFunc();
  private ArbitrarilyDiscretizedFunc funcvRef = new ArbitrarilyDiscretizedFunc();
  private ArbitrarilyDiscretizedFunc funcc = new ArbitrarilyDiscretizedFunc();
  private ArbitrarilyDiscretizedFunc funcb2 = new ArbitrarilyDiscretizedFunc();
  private ArbitrarilyDiscretizedFunc functau = new ArbitrarilyDiscretizedFunc();
  private ArbitrarilyDiscretizedFunc funce1 = new ArbitrarilyDiscretizedFunc();
  private ArbitrarilyDiscretizedFunc funce3 = new ArbitrarilyDiscretizedFunc();

  
  
  /**
   *  The object class names for all the supported attenuation ralations (IMRs)
   *  Temp until figure out way to dynamically load classes during runtime
   */
  public final static String BJF_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.BJF_1997_AttenRel";
  public final static String AS_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel";
  public final static String C_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.Campbell_1997_AttenRel";
  public final static String SCEMY_CLASS_NAME = "org.opensha.sha.imr.attenRelImpl.SadighEtAl_1997_AttenRel";
  
  
  //arrayList to store the supported AttenRel objects
  private ArrayList attenRelObjects = new ArrayList();

  

  // warning constraint fields:
  protected final static Double VS30_WARN_MIN = new Double(50.0);
  protected final static Double VS30_WARN_MAX = new Double(760.0);

  // the Soft Soil Parameter
  private BooleanParameter softSoilParam = null;
  public final static String SOFT_SOIL_NAME = "Soft Soil Case";
  public final static String SOFT_SOIL_INFO =
      "Indicates that site is considered NEHRP E regardless of Vs30.\n\n" +
      "Conditions required are undrained shear strength < 24 kPa, " +
      "PI > 20, water content > 40%, and thickness of clay exceeds 3 m.";
  public final static Boolean SOFT_SOIL_DEFAULT = new Boolean(false);

  
  
  //Intercept param
  private DoubleParameter AF_InterceptParam;
  public final static String AF_INTERCEPT_PARAM_NAME = "AF Intercept";
  public final static String AF_INTERCEPT_PARAM_INFO = 
	  "Intercept of the median regression model for the ground response analyses";
  private DoubleConstraint AF_InterceptparamConstraint = new DoubleConstraint(-2,2);
  public final static double AF_INTERCEPT_PARAM_DEFAULT = 0;
  
  //Slope Param
  private DoubleParameter AF_SlopeParam;
  public final static String AF_SLOPE_PARAM_NAME = "AF Slope";
  public final static String AF_SLOPE_PARAM_INFO = 
	  "Slope of the median regression model for the ground response analyses";
  private DoubleConstraint AF_slopeParamConstraint = new DoubleConstraint(-1,1);
  public final static double AF_SLOPE_PARAM_DEFAULT = 0;
  
  //Additive refeerence acceleration param
  private DoubleParameter AF_AddRefAccParam;
  public final static String AF_ADDITIVE_REF_ACCELERATION_PARAM_NAME = "AF Add. Ref. Acceleration";
  public final static String AF_ADDITIVE_REF_ACCELERATION_PARAM_INFO = 
	  "Additive reference acceleration of the median regression model for the ground response " +
	  "analyses. This parameter improves the linear model fit for low Sa(rock) / PGA(rock)" +
	  "values and leads to more relaistic predictons than quadratic models";
  private DoubleConstraint AFaddRefAccParamConstraint = new DoubleConstraint(0,0.5);
  public final static double AF_ADDITIVE_REF_ACCERLATION_DEFAULT = 0.03;
  
  
  //Std. Dev AF param
  private DoubleParameter AF_StdDevParam;
  public final static String AF_STD_DEV_PARAM_NAME = "Std. Dev. AF";
  public final static String AF_STD_DEV_PARAM_INFO = 
	  "Standard Deviation of the amplification factor from the ground response analyses" +
	  " regression model";
  private DoubleConstraint AF_StdDevParamConstraint = new DoubleConstraint(0,1.0);
  public final static double AF_STD_DEV_DEFAULT = 0.3;
  
  //number of runs parameter
  private IntegerParameter numRunsParam;
  public final static String NUM_RUNS_PARAM_NAME = "Number of Runs";
  public final static String NUM_RUNS_PARAM_INFO = "Number of runs of the wave propagation"+
	  " simulation for the site";
  private IntegerConstraint numRunsConstraint = new IntegerConstraint(1,Integer.MAX_VALUE);
  public final static int NUM_RUNS_PARAM_DEFAULT = 1;

  
  //Site Effect correction to apply
  private StringParameter siteEffectCorrectionParam;
  public final static String SITE_EFFECT_PARAM_NAME = "Site Effect Model";
  public final static String SITE_EFFECT_PARAM_INFO = "Select which model to apply for" +
  		" site effect correction";
  private final static String BATURAY_STEWART_MODEL = "Baturay and Stewart (2003)";
  private final static String BAZZURO_CORNELL_MODEL = "Bazzuro and Cornell(2004)";
  
  
  //Rock AttenuationRelationship selector parameter
  private StringParameter rockAttenRelSelectorParam;
  public final static String ROCK_ATTEN_REL_SELECT_PARAM_NAME = "Rock AttenuationRelationship";
  public final static String ROCK_ATTEN_REL_SELECT_PARAM_INFO = "Select from the "+
	  "given Rock AttenuationRelationships ";
  

  // for issuing warnings:
  private transient ParameterChangeWarningListener warningListener = null;
  
  //Rock AttenuationRealtiobnships instances
  private ScalarIntensityMeasureRelationshipAPI attenRel;
  
  private SiteTranslator vs30Trans = new SiteTranslator();
  

  /**
   *  No-Arg constructor. This initializes several ParameterList objects.
   */
  public SiteSpecific_2006_AttenRel(ParameterChangeWarningListener warningListener) {

    super();
    
    this.warningListener = warningListener;
    initCoeffFunctionlist();
    initRockAttenuationRealtionships();
    initRockAttenuationRelationshipSelectorParam();
    initSupportedIntensityMeasureParams();
    initEqkRuptureParams();
    initPropagationEffectParams();
    initSiteParams();		// do only in constructor
    initOtherParams();

    initIndependentParamLists(); // Do this after the above
  }
  
  /**
   * Adds the Coefficients to the ArbitraryDiscretizedFunctions
   *
   */
  private void initCoeffFunctionlist(){
	  int numPeriods = this.period.length;
	  for(int i=0;i<numPeriods;++i){
		  funcb1.set(period[i], b1[i]);
		  funcvRef.set(period[i], vRef[i]);
		  funcc.set(period[i], c[i]);
		  funcb2.set(period[i], b2[i]);
		  functau.set(period[i], tau[i]);
		  funce1.set(period[i], e1[i]);
		  funce3.set(period[i], e3[i]);
	  }
  }
  
  
  private void initRockAttenuationRealtionships(){
	  //arrayList to store the supported AttenRel Class Names with their full package structure.
	   ArrayList supportedAttenRelClasses = new ArrayList();

       //adds all the AttenRel classes to the ArrayList
	    supportedAttenRelClasses.add(BJF_CLASS_NAME);
	    supportedAttenRelClasses.add(AS_CLASS_NAME);
	    supportedAttenRelClasses.add(C_CLASS_NAME);
	    supportedAttenRelClasses.add(SCEMY_CLASS_NAME);
	    
	    createIMRClassInstance(supportedAttenRelClasses);
  }
  
  
  /**
   * Creates a class instance from a string of the full class name including packages.
   * This is how you dynamically make objects at runtime if you don't know which\
   * class beforehand. For example, if you wanted to create a BJF_1997_AttenRel you can do
   * it the normal way:<P>
   *
   * <code>BJF_1997_AttenRel imr = new BJF_1997_AttenRel()</code><p>
   *
   * If your not sure the user wants this one or AS_1997_AttenRel you can use this function
   * instead to create the same class by:<P>
   *
   * <code>BJF_1997_AttenRel imr =
   * (BJF_1997_AttenRel)ClassUtils.createNoArgConstructorClassInstance("org.opensha.sha.imt.attenRelImpl.BJF_1997_AttenRel");
   * </code><p>
   *
   */

   private void createIMRClassInstance(ArrayList  supportedAttenRelClasses){
     
     String S = C + ": createIMRClassInstance(): ";
     int size = supportedAttenRelClasses.size();
     for(int i=0;i< size;++i){
       try {
         Class listenerClass = Class.forName( "org.opensha.commons.param.event.ParameterChangeWarningListener" );
         Object[] paramObjects = new Object[]{ warningListener };
         Class[] params = new Class[]{ listenerClass };
         Class imrClass = Class.forName((String)supportedAttenRelClasses.get(i));
         Constructor con = imrClass.getConstructor( params );
         Object attenRel = con.newInstance( paramObjects );
         this.attenRelObjects.add(attenRel);
       } catch ( ClassCastException e ) {
         System.out.println(S + e.toString());
         throw new RuntimeException( S + e.toString() );
       } catch ( ClassNotFoundException e ) {
         System.out.println(S + e.toString());
         throw new RuntimeException( S + e.toString() );
       } catch ( NoSuchMethodException e ) {
         System.out.println(S + e.toString());
         throw new RuntimeException( S + e.toString() );
       } catch ( InvocationTargetException e ) {
         e.printStackTrace();
         System.out.println(S + e.toString());
         throw new RuntimeException( S + e.toString() );
       } catch ( IllegalAccessException e ) {
         System.out.println(S + e.toString());
         throw new RuntimeException( S + e.toString() );
       } catch ( InstantiationException e ) {
         System.out.println(S + e.toString());
         throw new RuntimeException( S + e.toString() );
       }
     }
     return ;
   }

  
  /**
   * Adds the Rock supported AttenuationRelationships in attenuation selection
   * parameter.
   *
   */
  private void initRockAttenuationRelationshipSelectorParam(){
	  ArrayList rockAttenRelList = new ArrayList();
	  int size = this.attenRelObjects.size();
	  for(int i=0;i<size;++i)
		  rockAttenRelList.add(((AttenuationRelationship)attenRelObjects.get(i)).getName());
	  
	  rockAttenRelSelectorParam = new StringParameter(ROCK_ATTEN_REL_SELECT_PARAM_NAME,
			  rockAttenRelList,(String)rockAttenRelList.get(0));	
	  rockAttenRelSelectorParam.setInfo(ROCK_ATTEN_REL_SELECT_PARAM_INFO);
	  rockAttenRelSelectorParam.addParameterChangeListener(this);
	  attenRel = (AttenuationRelationship)attenRelObjects.get(0);
	  setRockAttenRelAndParamLists();
  }
  
  /**
   * Sets the paramters for selected Rock AttenuationRelationship
   * @param attenRel
   */
  private void setRockAttenRelAndParamLists() {
	  
	  String attenRelName = attenRel.getName();
	  if(attenRelName.equals(AS_1997_AttenRel.NAME)){
		  
		  ParameterAPI siteParam = ((AS_1997_AttenRel)attenRel).getParameter
		                            (AS_1997_AttenRel.SITE_TYPE_NAME);
		  //set the site parameter to rock
		  SiteDataValue<Double> val = new SiteDataValue<Double>(SiteDataAPI.TYPE_VS30,
	    		  SiteDataAPI.TYPE_FLAG_INFERRED, 760d);
	      vs30Trans.setParameterValue(siteParam, val);
		    // set the component to ave horz
		  attenRel.getParameter(ComponentParam.NAME).setValue(
				  ComponentParam.COMPONENT_AVE_HORZ);
		    // overide local params with those in as_1997_attenRel
		    this.sigmaTruncTypeParam = (SigmaTruncTypeParam) attenRel.getParameter(
		    		SigmaTruncTypeParam.NAME);
		    this.sigmaTruncLevelParam = (SigmaTruncLevelParam) attenRel.getParameter(
		    		SigmaTruncLevelParam.NAME);
		    this.exceedProbParam = (DoubleParameter) attenRel.getParameter(
		    		AS_1997_AttenRel.EXCEED_PROB_NAME);
		    this.stdDevTypeParam = (StdDevTypeParam) attenRel.getParameter(
		    		StdDevTypeParam.NAME);
		    
	  }
	  else if(attenRelName.equals(BJF_1997_AttenRel.NAME)){
		  
		   ParameterAPI siteParam = ((BJF_1997_AttenRel)attenRel).getParameter
                                   (Vs30_Param.NAME);
           //set the site parameter to rock
		   SiteDataValue<Double> val = new SiteDataValue<Double>(SiteDataAPI.TYPE_VS30,
		    		  SiteDataAPI.TYPE_FLAG_INFERRED, 760d);
		   vs30Trans.setParameterValue(siteParam, val);
		   // set the component to ave horz
		   attenRel.getParameter(ComponentParam.NAME).setValue(
				   ComponentParam.COMPONENT_AVE_HORZ);
		    // overide local params with those in as_1997_attenRel
		    this.sigmaTruncTypeParam = (SigmaTruncTypeParam) attenRel.getParameter(
		    		SigmaTruncTypeParam.NAME);
		    this.sigmaTruncLevelParam = (SigmaTruncLevelParam) attenRel.getParameter(
		    		SigmaTruncLevelParam.NAME);
		    this.exceedProbParam = (DoubleParameter) attenRel.getParameter(
		    		BJF_1997_AttenRel.EXCEED_PROB_NAME);
		    this.stdDevTypeParam = (StdDevTypeParam) attenRel.getParameter(
		    		StdDevTypeParam.NAME);
	  }
	  else 	if(attenRelName.equals(Campbell_1997_AttenRel.NAME)){
		  
		    ParameterAPI siteParam = ((Campbell_1997_AttenRel)attenRel).getParameter
                                    (Campbell_1997_AttenRel.SITE_TYPE_NAME);
		    //set the site parameter to rock
		    SiteDataValue<Double> val = new SiteDataValue<Double>(SiteDataAPI.TYPE_VS30,
		    		  SiteDataAPI.TYPE_FLAG_INFERRED, 760d);
		    vs30Trans.setParameterValue(siteParam, val);
		    // set the component to ave horz
		    attenRel.getParameter(ComponentParam.NAME).setValue(
		    		ComponentParam.COMPONENT_AVE_HORZ);
		    // overide local params with those in as_1997_attenRel
		    this.sigmaTruncTypeParam = (SigmaTruncTypeParam) attenRel.getParameter(
		    		SigmaTruncTypeParam.NAME);
		    this.sigmaTruncLevelParam = (SigmaTruncLevelParam) attenRel.getParameter(
		    		SigmaTruncLevelParam.NAME);
		    this.exceedProbParam = (DoubleParameter) attenRel.getParameter(
		    		Campbell_1997_AttenRel.EXCEED_PROB_NAME);
		    this.stdDevTypeParam = (StdDevTypeParam) attenRel.getParameter(
		    		StdDevTypeParam.NAME);
	  }
	  else if(attenRelName.equals(SadighEtAl_1997_AttenRel.NAME)){
		  
		    // set the site type to rock
		  attenRel.getParameter(SadighEtAl_1997_AttenRel.SITE_TYPE_NAME).setValue(
				  SadighEtAl_1997_AttenRel.SITE_TYPE_ROCK);
		    // set the component to ave horz
		  attenRel.getParameter(ComponentParam.NAME).setValue(
				  ComponentParam.COMPONENT_AVE_HORZ);
		    // overide local params with those in as_1997_attenRel
		    this.sigmaTruncTypeParam = (SigmaTruncTypeParam) attenRel.getParameter(
		    		SigmaTruncTypeParam.NAME);
		    this.sigmaTruncLevelParam = (SigmaTruncLevelParam) attenRel.getParameter(
		    		SigmaTruncLevelParam.NAME);
		    this.exceedProbParam = (DoubleParameter) attenRel.getParameter(
		    		SadighEtAl_1997_AttenRel.EXCEED_PROB_NAME);
		    this.stdDevTypeParam = (StdDevTypeParam) attenRel.getParameter(
		    		StdDevTypeParam.NAME);
	  }
	  this.saPeriodParam = (PeriodParam) attenRel.getParameter(
		        PeriodParam.NAME);
  }

  /**
   * This does nothing, but is needed.
   */
  protected void setPropagationEffectParams() {

	  
  }  

  /**
   * This listens for parameter changes and updates the primitive parameters accordingly
   * @param e ParameterChangeEvent
   */
  public void parameterChange(ParameterChangeEvent e) {
	
    String pName = e.getParameterName();
    Object val = e.getNewValue();
    if(pName.equals(ROCK_ATTEN_REL_SELECT_PARAM_NAME)){
    	attenRel = getSelectedIMR_Instance((String)this.rockAttenRelSelectorParam.getValue());
    	setRockAttenRelAndParamLists();
    	initSupportedIntensityMeasureParams();
    	initEqkRuptureParams();
    	initPropagationEffectParams();
    	initOtherParams();
    	attenRel.setParamDefaults();
    }
    else if(pName.equals(SITE_EFFECT_PARAM_NAME)){
    	if(val.equals(this.BAZZURO_CORNELL_MODEL)){
    		if(siteParams.containsParameter(vs30Param))
    			siteParams.removeParameter(Vs30_Param.NAME);
    		if(siteParams.containsParameter(SOFT_SOIL_NAME))
    			siteParams.removeParameter(this.SOFT_SOIL_NAME);
    		if(siteParams.containsParameter(NUM_RUNS_PARAM_NAME))
    			siteParams.removeParameter(this.NUM_RUNS_PARAM_NAME);
    	}
    	else{
    		if(!siteParams.containsParameter(vs30Param))
    			siteParams.addParameter(this.vs30Param);
    		if(!siteParams.containsParameter(softSoilParam))
    			siteParams.addParameter(this.softSoilParam);
    		if(!siteParams.containsParameter(numRunsParam))
    			siteParams.addParameter(this.numRunsParam);
    	}
    }
    initIndependentParamLists();
  }  
  

  
  /**
   * This method will return the instance of selected IMR
   * @return : Selected IMR instance
   */
  public ScalarIntensityMeasureRelationshipAPI getSelectedIMR_Instance(String selectedIMR) {
    ScalarIntensityMeasureRelationshipAPI imr = null;
    int size = this.attenRelObjects.size();
    for(int i=0; i<size ; ++i) {
      imr = (ScalarIntensityMeasureRelationshipAPI)attenRelObjects.get(i);
      if(imr.getName().equalsIgnoreCase(selectedIMR))
        break;
    }
    return imr;
  }
 
  
  /**
   *  This sets the eqkRupture related parameters.
   *
   * @param  eqkRupture  The new eqkRupture value
   * @throws InvalidRangeException thrown if rake is out of bounds
   */
  public void setEqkRupture(EqkRupture eqkRupture) throws InvalidRangeException {
    attenRel.setEqkRupture(eqkRupture);
    this.eqkRupture = eqkRupture;
  }

  /**
   *  This sets the site-related parameter (vs30Param) based on what is in
   *  the Site object passed in.  WarningExceptions are ingored
   *
   * @param  site             The new site value which contains a Vs30 Parameter
   * @throws ParameterException Thrown if the Site object doesn't contain a
   * Vs30 parameter
   */
  public void setSite(Site site) throws ParameterException {

	
    AF_InterceptParam.setValue((Double)site.getParameter(AF_INTERCEPT_PARAM_NAME).getValue());
    AF_AddRefAccParam.setValue((Double)site.getParameter(AF_ADDITIVE_REF_ACCELERATION_PARAM_NAME).getValue());
    AF_SlopeParam.setValue((Double)site.getParameter(AF_SLOPE_PARAM_NAME).getValue());
    AF_StdDevParam.setValue((Double)site.getParameter(AF_STD_DEV_PARAM_NAME).getValue());
    String modelType = (String)siteEffectCorrectionParam.getValue();
    if(modelType.equals(this.BATURAY_STEWART_MODEL)){
    	vs30Param.setValueIgnoreWarning((Double)site.getParameter(Vs30_Param.NAME).getValue());
    	softSoilParam.setValue((Boolean)(site.getParameter(SOFT_SOIL_NAME).getValue()));
    	numRunsParam.setValue((Integer)site.getParameter(NUM_RUNS_PARAM_NAME).getValue());
    }
    
    this.site = site;
    // set the location in as_1997_attenRel
    attenRel.setSiteLocation(site.getLocation());
  }



  /**
   * Calculates the mean
   * @return    The mean value
   */
  public double getMean() throws IMRException {

    double asRockSA, lnAF;

     // get selected rock  attenuation relationship SA for rock
    attenRel.setIntensityMeasure(im);
    asRockSA = attenRel.getMean();
    // get the amp factor
    double aVal = ((Double)AF_InterceptParam.getValue()).doubleValue();
    double bVal = ((Double)AF_SlopeParam.getValue()).doubleValue();
    double cVal = ((Double)AF_AddRefAccParam.getValue()).doubleValue();
    lnAF = aVal+bVal*Math.log(Math.exp(asRockSA)+cVal);   
    
    // return the result
    return lnAF +asRockSA;
  }


  /**
   * Returns the Std Dev.
   */
  public double getStdDev(){
	  String stdDevType = stdDevTypeParam.getValue().toString();
	  if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) { // "None (zero)"
		  return 0;
	  }
	  else {
		  String siteCorrectionModelUsed = (String)siteEffectCorrectionParam.getValue();
		  if(siteCorrectionModelUsed.equals(this.BAZZURO_CORNELL_MODEL))
			  return getStdDevForBC();
		  else{
			  float periodParamVal;
			  if(im.getName().equals(SA_Param.NAME))
				  periodParamVal = (float)((Double) saPeriodParam.getValue()).doubleValue();
			  else
				  periodParamVal = 0;
			  
			  if(periodParamVal < 0.75)
				  return getStdDevForBS();
			  else if(periodParamVal > 1.5)
				  return getStdDevForCS();
			  else{
				  //getting the Std Dev for Period of 0.75
				  saPeriodParam.setValue(new Double(0.75));
				  double stdDev_BS = getStdDevForBS();
				  //getting the Std Dev. for period param 1.5
				  saPeriodParam.setValue(new Double(1.5));
				  double stdDev_CS = getStdDevForCS();
				  //setting the period to period selected by the user
				  DecimalFormat format = new DecimalFormat("##.###");
				  saPeriodParam.setValue(new Double(format.format(periodParamVal)));
				  //linear interpolation to get the Std Dev.
				  double stdDev = ((periodParamVal - 0.75)/(1.5 -0.75))*
				  (stdDev_CS - stdDev_BS) + stdDev_BS;
				  return stdDev;
			  }
		  }
	  }
  }
  
  
  /**
   * @return    The stdDev value for Bazzurro and Cornell (2004) Site Correction Model
   */
  private double getStdDevForBC(){
	  double bVal = ((Double)AF_SlopeParam.getValue()).doubleValue();
	  double stdDevAF = ((Double)this.AF_StdDevParam.getValue()).doubleValue();
	  attenRel.setIntensityMeasure(im);
	  double asRockStdDev = attenRel.getStdDev();
	  double stdDev = Math.pow(bVal+1, 2)*Math.pow(asRockStdDev, 2)+Math.pow(stdDevAF, 2);
	  return Math.sqrt(stdDev);
  }

  /**
   * @return    The stdDev value for Baturay and Stewart (2003) Site Correction Model
   */
  private double getStdDevForBS(){
	  double stdDevAF = ((Double)this.AF_StdDevParam.getValue()).doubleValue();
	  int numRuns = ((Integer)this.numRunsParam.getValue()).intValue();
	  boolean softSoilCase = ((Boolean)this.softSoilParam.getValue()).booleanValue();
	  double stdError = stdDevAF/(Math.sqrt(numRuns));
	  double stdDev_gNet;
	  double vs30 = ((Double)vs30Param.getValue()).doubleValue();
	  if(vs30 <= 180 || softSoilCase)
		  stdDev_gNet = 0.38;
	  else
		  stdDev_gNet = 0.56;
	  double stdDev = Math.pow(stdDev_gNet,2)+Math.pow(stdError, 2);
	  return Math.sqrt(stdDev);
  }

  /**
   * @return    The stdDev value for Choi and Stewart (2005) model
   */
  private double getStdDevForCS() throws IMRException {

      double vs30, sigmaV, sigmaAS;

      double periodParamVal = ((Double)this.saPeriodParam.getValue()).doubleValue();
            
      // set vs30 from the parameters
      if ( ( (Boolean) softSoilParam.getValue()).booleanValue()) {
        vs30 = 174;
      }
      else {
        try {
          vs30 = ( (Double) vs30Param.getValue()).doubleValue();
        }
        catch (NullPointerException e) {
          throw new IMRException(C + ": getStdDev(): " + ERR);
        }
      }

      // set sigmaV
      if (vs30 < 260) {
        sigmaV = funce1.getInterpolatedY(periodParamVal);
      }
      else if (vs30 < 360) {
        sigmaV = funce1.getInterpolatedY(periodParamVal) +
            ((funce3.getInterpolatedY(periodParamVal) - funce1.getInterpolatedY(periodParamVal)) / Math.log(360 / 260)) *
            Math.log(vs30 / 260);
      }
      else {
        sigmaV = funce3.getInterpolatedY(periodParamVal);
      }

      return Math.sqrt(sigmaV * sigmaV + functau.getInterpolatedY(periodParamVal) * functau.getInterpolatedY(periodParamVal));
   
  }

  
  public void setParamDefaults() {

    //((ParameterAPI)this.iml).setValue( IML_DEFAULT );
    vs30Param.setValueAsDefault();
    softSoilParam.setValue(new Boolean(false));
    String rockAttenDefaultVal = (String)rockAttenRelSelectorParam.getAllowedStrings().get(0);
    rockAttenRelSelectorParam.setValue(rockAttenDefaultVal);
    siteEffectCorrectionParam.setValue(BATURAY_STEWART_MODEL);
    this.AF_AddRefAccParam.setValue(new Double(this.AF_ADDITIVE_REF_ACCERLATION_DEFAULT));
    this.AF_InterceptParam.setValue(new Double(this.AF_INTERCEPT_PARAM_DEFAULT));
    this.AF_SlopeParam.setValue(new Double(this.AF_SLOPE_PARAM_DEFAULT));
    this.AF_StdDevParam.setValue(new Double(this.AF_STD_DEV_DEFAULT));
    this.numRunsParam.setValue(new Integer(this.NUM_RUNS_PARAM_DEFAULT));
    attenRel.setParamDefaults();
    this.initRockAttenuationRealtionships();
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
    ListIterator it = attenRel.getMeanIndependentParamsIterator();
    ArrayList siteParamNames = new ArrayList();
    ListIterator siteTypeParamIterator = this.siteParams.getParametersIterator();
    
    while(siteTypeParamIterator.hasNext()){
  	  ParameterAPI siteParam = (ParameterAPI)siteTypeParamIterator.next();
  	  siteParamNames.add(siteParam.getName());
    }
    int numSiteParams = siteParamNames.size();
    while (it.hasNext()) {
      Parameter param = (Parameter) it.next();
	  if (!(param.getName().equals(ComponentParam.NAME)))  {
		  boolean isSiteTypeParam = false;
		  for(int i=0;i<numSiteParams;++i){
			 String siteParamName = (String)siteParamNames.get(i);
			 
			 if(param.getName().equals(siteParamName)){
				 isSiteTypeParam = true;
				 break;
			 }
		  }
		  if(!isSiteTypeParam && !meanIndependentParams.containsParameter(param))
		        meanIndependentParams.addParameter(param);
	  }
    }

    // params that the stdDev depends upon
    stdDevIndependentParams.clear();
     it = attenRel.getStdDevIndependentParamsIterator();
    while (it.hasNext()) {
        Parameter param = (Parameter) it.next();
  	  	if (!(param.getName().equals(ComponentParam.NAME)))  {
  		  boolean isSiteTypeParam = false;
  		  for(int i=0;i<numSiteParams;++i){
  			 String siteParamName = (String)siteParamNames.get(i);
  			 if(param.getName().equals(siteParamName)){
  				 isSiteTypeParam = true;
  				 break;
  			 }
  		  }
    	 if(!isSiteTypeParam && !stdDevIndependentParams.containsParameter(param))
			   stdDevIndependentParams.addParameter(param);

  	  	}
     }

    // params that the exceed. prob. depends upon
    exceedProbIndependentParams.clear();
    it = attenRel.getExceedProbIndependentParamsIterator();
    while (it.hasNext()) {
        Parameter param = (Parameter) it.next();
  	  	if (!(param.getName().equals(ComponentParam.NAME)))  {
  		  boolean isSiteTypeParam = false;
  		  for(int i=0;i<numSiteParams;++i){
  			 String siteParamName = (String)siteParamNames.get(i);
  			 if(param.getName().equals(siteParamName)){
  				 isSiteTypeParam = true;
  				 break;
  			 }
  		  }
		 if(!isSiteTypeParam && !exceedProbIndependentParams.containsParameter(param))
	  		exceedProbIndependentParams.addParameter(param);

  	  	}
     }

    //  adding the other params like Component , SiteCorrectionModel etc to the mean, std Dev and exceepProb paramlist.
    	meanIndependentParams.addParameter(componentParam);
    	meanIndependentParams.addParameter(rockAttenRelSelectorParam);
    	meanIndependentParams.addParameter(siteEffectCorrectionParam);
    	stdDevIndependentParams.addParameter(componentParam);
    	stdDevIndependentParams.addParameter(rockAttenRelSelectorParam);
    	stdDevIndependentParams.addParameter(siteEffectCorrectionParam);
    	exceedProbIndependentParams.addParameter(componentParam);
    	exceedProbIndependentParams.addParameter(rockAttenRelSelectorParam);
    	exceedProbIndependentParams.addParameter(siteEffectCorrectionParam);

    
    //adding the site related parameters to the mean, std Dev and exceepProb paramlist.
    String siteCorrectionModel = (String)siteEffectCorrectionParam.getValue();
    ListIterator lit = siteParams.getParametersIterator();
    if(siteCorrectionModel.equals(this.BATURAY_STEWART_MODEL)){
	    while(lit.hasNext()){
	    	ParameterAPI param = (ParameterAPI)lit.next();
	    	meanIndependentParams.addParameter(param);
	    	stdDevIndependentParams.addParameter(param);
	    	exceedProbIndependentParams.addParameter(param);
	    }
    }
    else{
    	while(lit.hasNext()){
	    	ParameterAPI param = (ParameterAPI)lit.next();
	    	if(!param.getName().equals(Vs30_Param.NAME) && 
	    		!param.getName().equals(this.NUM_RUNS_PARAM_NAME)	&&
	    		!param.getName().equals(this.softSoilParam.getName())){
		    	meanIndependentParams.addParameter(param);
		    	stdDevIndependentParams.addParameter(param);
		    	exceedProbIndependentParams.addParameter(param);
	    	}
	    }
    }
    imlAtExceedProbIndependentParams.clear();
    // params that the IML at exceed. prob. depends upon
    imlAtExceedProbIndependentParams.addParameterList(
        exceedProbIndependentParams);
    imlAtExceedProbIndependentParams.addParameter(exceedProbParam);

  }

  /**
   *  Creates the Vs30 site parameter and adds it to the siteParams list.
   *  Makes the parameters noneditable.
   */
  protected void initSiteParams() {

	vs30Param = new Vs30_Param(VS30_WARN_MIN, VS30_WARN_MAX);

    // make the Soft Soil parameter
    softSoilParam = new BooleanParameter(SOFT_SOIL_NAME, SOFT_SOIL_DEFAULT);
    softSoilParam.setInfo(SOFT_SOIL_INFO);
    
    //make the AF intercept paarameter
    AF_InterceptParam = new DoubleParameter(this.AF_INTERCEPT_PARAM_NAME,
    		AF_InterceptparamConstraint,this.AF_INTERCEPT_PARAM_DEFAULT);
    AF_InterceptParam.setInfo(this.AF_INTERCEPT_PARAM_INFO);
    
    //make the AF slope parameter
    this.AF_SlopeParam = new DoubleParameter(this.AF_SLOPE_PARAM_NAME,
    		this.AF_slopeParamConstraint,this.AF_SLOPE_PARAM_DEFAULT);
    AF_SlopeParam.setInfo(this.AF_SLOPE_PARAM_INFO);
    
    //make theb AF Additive Reference Paramerter
    this.AF_AddRefAccParam = new DoubleParameter(this.AF_ADDITIVE_REF_ACCELERATION_PARAM_NAME,
    		this.AFaddRefAccParamConstraint,this.AF_ADDITIVE_REF_ACCERLATION_DEFAULT);
    AF_AddRefAccParam.setInfo(this.AF_ADDITIVE_REF_ACCELERATION_PARAM_INFO);
    
    //make the AF Std. Dev.
    this.AF_StdDevParam = new DoubleParameter(this.AF_STD_DEV_PARAM_NAME,
    		this.AF_StdDevParamConstraint,this.AF_STD_DEV_DEFAULT);
    
    AF_StdDevParam.setInfo(this.AF_STD_DEV_PARAM_INFO);
    
    //make the number of runs parameter
    this.numRunsParam = new IntegerParameter(this.NUM_RUNS_PARAM_NAME,
    		this.numRunsConstraint,this.NUM_RUNS_PARAM_DEFAULT);
    numRunsParam.setInfo(this.NUM_RUNS_PARAM_INFO);
    
    
    // add it to the siteParams list:
    siteParams.clear();
    siteParams.addParameter(AF_InterceptParam);
    siteParams.addParameter(AF_SlopeParam);
    siteParams.addParameter(AF_AddRefAccParam);
    siteParams.addParameter(AF_StdDevParam);
    siteParams.addParameter(vs30Param);
    siteParams.addParameter(softSoilParam);
    siteParams.addParameter(numRunsParam);

  }

  /**
   *  Creates the two Potential Earthquake parameters (magParam and
   *  fltTypeParam) and adds them to the eqkRuptureParams
   *  list. Makes the parameters noneditable.
   */
  protected void initEqkRuptureParams() {

	eqkRuptureParams.clear();
    ListIterator it = attenRel.getEqkRuptureParamsIterator();
    while (it.hasNext()) {
      eqkRuptureParams.addParameter( (Parameter) it.next());
    }
  }

  /**
   *  Creates the single Propagation Effect parameter and adds it to the
   *  propagationEffectParams list. Makes the parameters noneditable.
   */
  protected void initPropagationEffectParams() {
    propagationEffectParams.clear();
    ListIterator it = attenRel.getPropagationEffectParamsIterator();
    while (it.hasNext()) {
      propagationEffectParams.addParameter( (Parameter) it.next());
    }

  }

  /**
   *  Creates the two supported IM parameters (PGA and SA), as well as the
   *  independenParameters of SA (periodParam and dampingParam) and adds
   *  them to the supportedIMParams list. Makes the parameters noneditable.
   */
  protected void initSupportedIntensityMeasureParams() {

    supportedIMParams.clear();
    Iterator it = attenRel.getSupportedIntensityMeasuresIterator();
    while (it.hasNext()) {
      ParameterAPI imParam = (ParameterAPI)it.next();
      if(imParam.getName().equals(SA_Param.NAME))
         supportedIMParams.addParameter( imParam);
    }
  }

  /**
   *  Creates other Parameters that the mean or stdDev depends upon,
   *  such as the Component or StdDevType parameters.
   */
  protected void initOtherParams() {

    // init other params defined in parent class -- Don't need this
    // super.initOtherParams();

    // the Component Parameter (not supporting AS_1997's vertical)
    StringConstraint constraint = new StringConstraint();
    constraint.addString(ComponentParam.COMPONENT_AVE_HORZ);
    constraint.setNonEditable();
    componentParam = new ComponentParam(constraint,componentParam.COMPONENT_AVE_HORZ);

    // add this to the list
    otherParams.clear();
    otherParams.addParameter(rockAttenRelSelectorParam);
    
//  create the Site Effect correction parameter
    ArrayList siteEffectCorrectionModelList = new ArrayList();
    siteEffectCorrectionModelList.add(this.BATURAY_STEWART_MODEL);
    siteEffectCorrectionModelList.add(this.BAZZURO_CORNELL_MODEL);
    StringConstraint siteEffectCorrectionConstraint = new StringConstraint(siteEffectCorrectionModelList);
    this.siteEffectCorrectionParam = new StringParameter(this.SITE_EFFECT_PARAM_NAME,
    		siteEffectCorrectionConstraint,(String)siteEffectCorrectionModelList.get(0));
    siteEffectCorrectionParam.setInfo(this.SITE_EFFECT_PARAM_INFO);
    siteEffectCorrectionParam.addParameterChangeListener(this);
    otherParams.addParameter(siteEffectCorrectionParam);
    otherParams.addParameter(componentParam);
    Iterator it = attenRel.getOtherParamsIterator();
    Parameter param;
    while (it.hasNext()) {
      param = (Parameter) it.next();
      if (!ComponentParam.NAME.equals(param.getName())) {
        otherParams.addParameter(param);
      }
    }

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

}
