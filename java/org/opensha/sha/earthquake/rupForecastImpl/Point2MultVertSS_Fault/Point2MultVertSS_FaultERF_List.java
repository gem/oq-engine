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

package org.opensha.sha.earthquake.rupForecastImpl.Point2MultVertSS_Fault;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagLengthRelationship;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.sha.earthquake.ERF_EpistemicList;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.rupForecastImpl.Point2MultVertSS_FaultSource;
import org.opensha.sha.earthquake.rupForecastImpl.SingleFaultRuptureERF;


/**
 * <p>Title: Point2MultVertSS_FaultERF_List</p>
 * <p>Description: This ERF creates a single Point2MultVertSS_FaultSource
 * for the following user-defined parameters:  </p>
 * <UL>
 * <LI>source latitude
 * <LI>source longitude
 * <LI>magnitude - the magnitude of the point source.
 * <LI>maxRupOffset - The increment by which ruptures are slid (floated) along a given strike
 * <LI>deltaStrike - discretization of strike for the spinning of the ruptures
 * </UL><p>
 * The source not Poissonain, and note that the timeSpan does not influence the ERF at all
 * (because the probability is set by the adjustable parameter).  The timeSpan is returned by
 * this object is therefore null.  The upper and lower seismogenic
 * depths are hard coded at 0 and 1, respectively (because existing distance measures don't depend
 * on the depth extend for vertical strike-slip faults).  Rupture lengths are computed using the
 * Wells and Coppersmith Length(Mag) relationship (hard coded).
 * @author Ned Field
 * Date : September , 2004
 * @version 1.0
 */

public class Point2MultVertSS_FaultERF_List extends ERF_EpistemicList{

  //for Debug purposes
  protected static String  C = new String("Point2MultVertSS_FaultERF_List");
  protected boolean D = false;

  //name for this classs
  public final static String  NAME = "Point2Mult Vertical SS Fault ERF List";

  // this is the source (only 1 for this ERF)
  protected Point2MultVertSS_FaultSource source;

  // these are hard coded for now
  WC1994_MagLengthRelationship magLengthRel = new WC1994_MagLengthRelationship();
  double upperSeisDepth = 0;
  double lowerSeisDepth = 1;

  // adjustable parameter declarations
  DoubleParameter srcLatParam;
  DoubleParameter srcLonParam;
  DoubleParameter magParam;
  DoubleParameter maxRupOffsetParam;
  DoubleParameter deltaStrikeParam;

  // the source-location parameters
  public final static String SRC_LAT_PARAM_NAME = "Latitude";
  private final static String SRC_LAT_PARAM_INFO = "The latitude of the point source";
  private final static String SRC_LAT_PARAM_UNITS = "Degrees";
  private Double SRC_LAT_PARAM_MIN = new Double (-90.0);
  private Double SRC_LAT_PARAM_MAX = new Double (90.0);
  private Double SRC_LAT_PARAM_DEFAULT = new Double (35.71);

  public final static String SRC_LON_PARAM_NAME = "Longitude";
  private final static String SRC_LON_PARAM_INFO = "The longitude of the point source";
  private final static String SRC_LON_PARAM_UNITS = "Degrees";
  private Double SRC_LON_PARAM_MIN = new Double (-360);
  private Double SRC_LON_PARAM_MAX = new Double (360);
  private Double SRC_LON_PARAM_DEFAULT = new Double (-121.1);

  // mag parameter stuff
  public final static String MAG_PARAM_NAME = "Magnitude";
  private final static String MAG_PARAM_INFO = "The  magnitude for the point source";
  private final static String MAG_PARAM_UNITS = null;
  private Double MAG_PARAM_MIN = new Double(5);
  private Double MAG_PARAM_MAX = new Double(10);
  private Double MAG_PARAM_DEFAULT = new Double(7.0);

  // maxRupOffset parameter stuff
  public final static String RUP_OFFSET_PARAM_NAME = "Max Rupture Offset";
  private final static String RUP_OFFSET_PARAM_INFO = "The amount by which ruptures are floated along stike (actual value will be slightly less)";
  private final static String RUP_OFFSET_PARAM_UNITS = "km";
  private Double RUP_OFFSET_PARAM_MIN = new Double(1e-2);
  private Double RUP_OFFSET_PARAM_MAX = new Double(20);
  private Double RUP_OFFSET_PARAM_DEFAULT = new Double(2.0);

  // deltaStrike parameter stuff
  public final static String DELTA_STRIKE_PARAM_NAME = "Delta Strike";
  private final static String DELTA_STRIKE_PARAM_INFO = "Discretization of strike for spinning fault";
  private final static String DELTA_STRIKE_PARAM_UNITS = "degrees";
  private Double DELTA_STRIKE_PARAM_MIN = new Double(1e-2);
  private Double DELTA_STRIKE_PARAM_MAX = new Double(90);
  private Double DELTA_STRIKE_PARAM_DEFAULT = new Double(5.0);


  /**
   * Constructor for this source (no arguments)
   */
  public Point2MultVertSS_FaultERF_List() {

    timeSpan = null;

    // create src lat, lon, & depth param
    srcLatParam = new DoubleParameter(SRC_LAT_PARAM_NAME,SRC_LAT_PARAM_MIN,
        SRC_LAT_PARAM_MAX,SRC_LAT_PARAM_UNITS,SRC_LAT_PARAM_DEFAULT);
    srcLatParam.setInfo(SRC_LAT_PARAM_INFO);
    srcLonParam = new DoubleParameter(SRC_LON_PARAM_NAME,SRC_LON_PARAM_MIN,
        SRC_LON_PARAM_MAX,SRC_LON_PARAM_UNITS,SRC_LON_PARAM_DEFAULT);
    srcLonParam.setInfo(SRC_LON_PARAM_INFO);

    // create the mag param
    magParam = new DoubleParameter(MAG_PARAM_NAME,MAG_PARAM_MIN,
        MAG_PARAM_MAX,MAG_PARAM_UNITS,MAG_PARAM_DEFAULT);
    magParam.setInfo(MAG_PARAM_INFO);

    // create the rake param
    maxRupOffsetParam = new DoubleParameter(RUP_OFFSET_PARAM_NAME,RUP_OFFSET_PARAM_MIN,
        RUP_OFFSET_PARAM_MAX,RUP_OFFSET_PARAM_UNITS,RUP_OFFSET_PARAM_DEFAULT);
    maxRupOffsetParam.setInfo(RUP_OFFSET_PARAM_INFO);

    // create the rake param
    deltaStrikeParam = new DoubleParameter(DELTA_STRIKE_PARAM_NAME,DELTA_STRIKE_PARAM_MIN,
        DELTA_STRIKE_PARAM_MAX,DELTA_STRIKE_PARAM_UNITS,DELTA_STRIKE_PARAM_DEFAULT);
    deltaStrikeParam.setInfo(DELTA_STRIKE_PARAM_INFO);

    // add the adjustable parameters to the list
    adjustableParams.addParameter(srcLatParam);
    adjustableParams.addParameter(srcLonParam);
    adjustableParams.addParameter(magParam);
    adjustableParams.addParameter(maxRupOffsetParam);
    adjustableParams.addParameter(deltaStrikeParam);

    // register the parameters that need to be listened to
    srcLatParam.addParameterChangeListener(this);
    srcLonParam.addParameterChangeListener(this);
    magParam.addParameterChangeListener(this);
    maxRupOffsetParam.addParameterChangeListener(this);
    deltaStrikeParam.addParameterChangeListener(this);
  }



   /**
    * update the source based on the paramters (only if a parameter value has changed)
    */
   public void updateForecast(){
     String S = C + "updateForecast::";

     if(parameterChangeFlag) {

       double lat = ((Double) srcLatParam.getValue()).doubleValue();
       double lon = ((Double) srcLonParam.getValue()).doubleValue();
       double mag = ((Double) magParam.getValue()).doubleValue();
       double prob = 1.0;
       double maxRupOffset = ((Double) maxRupOffsetParam.getValue()).doubleValue();
       double deltaStrike = ((Double) deltaStrikeParam.getValue()).doubleValue();

       source = new Point2MultVertSS_FaultSource(lat, lon, mag, prob, magLengthRel,upperSeisDepth,
                                                 lowerSeisDepth, maxRupOffset,  deltaStrike);

       int numRups = source.getNumRuptures();
       ProbEqkRupture eqkRup;
       for(int i=0; i< numRups; i++) {
         eqkRup = source.getRupture(i);
         this.addERF(new SingleFaultRuptureERF(eqkRup, 1.0),eqkRup.getProbability());
       }
       parameterChangeFlag = false;
     }

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

   // this is temporary for testing purposes
   public static void main(String[] args) {
     Point2MultVertSS_FaultERF_List erfList = new Point2MultVertSS_FaultERF_List();
     erfList.updateForecast();
     System.out.println("numERFs="+erfList.getNumERFs());
     System.out.println("wtOfFirstERF="+erfList.getERF_RelativeWeight(0));
     System.out.println("numSrcsInFirstERF="+erfList.getERF(0).getNumSources());
     System.out.println("numRupsInFirstSrcOfFirstERF="+erfList.getERF(0).getSource(0).getNumRuptures());
     System.out.println("probOfFirstRupInFirstSrcOfFirstERF="+erfList.getERF(0).getSource(0).getRupture(0).getProbability());
     System.out.println(erfList.getERF(0).getSource(0).getRupture(0).getRuptureSurface().getLocation(0,0).getLatitude());
     System.out.println(erfList.getERF(1).getSource(0).getRupture(0).getRuptureSurface().getLocation(0,0).getLatitude());
   }

}
