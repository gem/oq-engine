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

package org.opensha.sha.earthquake.rupForecastImpl;

import java.util.ArrayList;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.param.SimpleFaultParameter;


/**
 * <p>Title: SingleFaultRuptureERF</p>
 * <p>Description: This ERF has a single-source with a single,
 * full-fault rupture.   The following are the user-defined parameters:  </p>
 * <UL>
 * <LI>magnitude
 * <LI>probability (the timeSpan is null because it has no influence on the forecast)
 * <LI>ruptureSurface - any EvenlyDiscretizedSurface
 * <LI>rake - that rake (in degrees) assigned to all ruptures.
 * </UL><p>
 * The source is not Poissonian.
 * @author Ned Field
 * Date : Sept, 2004
 * @version 1.0
 */

public class SingleFaultRuptureERF extends EqkRupForecast{

  //for Debug purposes
  private static String  C = "SingleFaultRuptureERF";
  private boolean D = false;

  //name for this classs
  public final static String  NAME = "Single Fault Rupture ERF";

  // this is the source (only 1 for this ERF)
  private FaultRuptureSource source;

  // mag parameter stuff
  public final static String MAG_PARAM_NAME = "Magnitude";
  private final static String MAG_PARAM_INFO = "The  magnitude of the rupture";
  private final static String MAG_PARAM_UNITS = null;
  private Double MAG_PARAM_MIN = new Double(5);
  private Double MAG_PARAM_MAX = new Double(10);
  private Double MAG_PARAM_DEFAULT = new Double(7.0);

  // prob parameter stuff
  public final static String PROB_PARAM_NAME = "Probability";
  private final static String PROB_PARAM_INFO = "The probability of the rupture";
  private final static String PROB_PARAM_UNITS = null;
  private Double PROB_PARAM_MIN = new Double(0);
  private Double PROB_PARAM_MAX = new Double(1);
  private Double PROB_PARAM_DEFAULT = new Double(1.0);

  // fault parameter name
  public final static String FAULT_PARAM_NAME = "Fault Parameter";

  // rake parameter stuff
  public final static String RAKE_PARAM_NAME = "Rake";
  private final static String RAKE_PARAM_INFO = "The rake of the rupture (direction of slip)";
  private final static String RAKE_PARAM_UNITS = "degrees";
  private Double RAKE_PARAM_MIN = new Double(-180);
  private Double RAKE_PARAM_MAX = new Double(180);
  private Double RAKE_PARAM_DEFAULT = new Double(0.0);

  // parameter declarations
  DoubleParameter magParam;
  DoubleParameter probParam;
  SimpleFaultParameter faultParam;
  DoubleParameter rakeParam;


  /**
   * Constructor for this source (no arguments)
   */
  public SingleFaultRuptureERF() {

    timeSpan = null;
    // create the timespan object with start time and duration in years
    //timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
    //timeSpan.addParameterChangeListener(this);

    // create the mag param
    magParam = new DoubleParameter(MAG_PARAM_NAME,MAG_PARAM_MIN,
        MAG_PARAM_MAX,MAG_PARAM_UNITS,MAG_PARAM_DEFAULT);
    magParam.setInfo(MAG_PARAM_INFO);

    // create the prob param
    probParam = new DoubleParameter(PROB_PARAM_NAME,PROB_PARAM_MIN,
        PROB_PARAM_MAX,PROB_PARAM_UNITS,PROB_PARAM_DEFAULT);
    probParam.setInfo(PROB_PARAM_INFO);

    // make the fault parameter
    faultParam = new SimpleFaultParameter(FAULT_PARAM_NAME);

    // create the rake param
    rakeParam = new DoubleParameter(RAKE_PARAM_NAME,RAKE_PARAM_MIN,
        RAKE_PARAM_MAX,RAKE_PARAM_UNITS,RAKE_PARAM_DEFAULT);
    rakeParam.setInfo(RAKE_PARAM_INFO);

    // add the adjustable parameters to the list
    adjustableParams.addParameter(magParam);
    adjustableParams.addParameter(probParam);
    adjustableParams.addParameter(rakeParam);
    adjustableParams.addParameter(faultParam);

    // register the parameters that need to be listened to
    rakeParam.addParameterChangeListener(this);
    faultParam.addParameterChangeListener(this);
    magParam.addParameterChangeListener(this);
    probParam.addParameterChangeListener(this);
  }

  /**
   * Constructor for this source
   */
  public SingleFaultRuptureERF(EqkRupture eqkRupture, double probability) {
    this();
    magParam.setValue(eqkRupture.getMag());
    rakeParam.setValue(eqkRupture.getAveRake());
    faultParam.setValue(eqkRupture.getRuptureSurface());
    probParam.setValue(probability);
    updateForecast();
  }



   /**
    * update the source based on the paramters (only if a parameter value has changed)
    */
   public void updateForecast(){
     String S = C + "updateForecast::";

     if(parameterChangeFlag) {
       source = new FaultRuptureSource(((Double) magParam.getValue()).doubleValue(),
                                             (EvenlyGriddedSurface) faultParam.getValue(),
                                             ((Double) rakeParam.getValue()).doubleValue(),
                                             ((Double) probParam.getValue()).doubleValue());
       parameterChangeFlag = false;
     }

   }


   /**
    * Return the earhthquake source at index i.   Note that this returns a
    * pointer to the source held internally, so that if any parameters
    * are changed, and this method is called again, the source obtained
    * by any previous call to this method will no longer be valid.
    *
    * @param iSource : index of the desired source (only "0" allowed here).
    *
    * @return Returns the ProbEqkSource at index i
    *
    */
   public ProbEqkSource getSource(int iSource) {

     // we have only one source
    if(iSource!=0)
      throw new RuntimeException("Only 1 source available, iSource should be equal to 0");

    return source;
   }


   /**
    * Returns the number of earthquake sources (always "1" here)
    *
    * @return integer value specifying the number of earthquake sources
    */
   public int getNumSources(){
     return 1;
   }


    /**
     *  This returns a list of sources (contains only one here)
     *
     * @return ArrayList of Prob Earthquake sources
     */
    public ArrayList  getSourceList(){
      ArrayList v =new ArrayList();
      v.add(source);
      return v;
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
    * This overides the parent method to ignore whatever is passed in
    * (because timeSpan is always null in this class)
    * @param timeSpan : TimeSpan object
    */
   public void setTimeSpan(TimeSpan time) {
     // do nothing
   }

}
