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

package org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases;


import java.util.ArrayList;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.PEER_testsMagAreaRelationship;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfFromSimpleFaultData;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.FrankelGriddedSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;


/**
 * <p>Title: PEER_NonPlanarFaultForecast </p>
 * <p>Description: Fault 1 Equake rupture forecast. The Peer Group Test cases </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Ned Field
 * Date : Nov 30, 2002
 * @version 1.0
 */

public class PEER_NonPlanarFaultForecast extends EqkRupForecast{

  /**
   * @todo variables
   */
  //for Debug purposes
  private static String  C = new String("PEER_NonPlanarFaultForecast");
  private boolean D = false;

  //name for this classs
  public final static String  NAME = "PEER Non Planar Fault Forecast";


  // the prob eqk source (only one)
  private FloatingPoissonFaultSource source;
  private ArrayList sourceList;

  PEER_testsMagAreaRelationship magScalingRel = new PEER_testsMagAreaRelationship();
  private double rupAspectRatio = 2;
  private double minMag = 5;  // the minimum magnitude to consider in the forecast

  // grid spacing parameter stuff
  public final static String GRID_PARAM_NAME =  "Fault Grid Spacing";
  private Double DEFAULT_GRID_VAL = new Double(1);
  public final static String GRID_PARAM_UNITS = "kms";
  private final static double GRID_PARAM_MIN = .001;
  private final static double GRID_PARAM_MAX = 1000;

  //rupture offset parameter stuff
  public final static String OFFSET_PARAM_NAME =  "Offset";
  private Double DEFAULT_OFFSET_VAL = new Double(1);
  public final static String OFFSET_PARAM_UNITS = "kms";
  private final static double OFFSET_PARAM_MIN = .01;
  private final static double OFFSET_PARAM_MAX = 10000;

  // Mag-length sigma parameter stuff
  public final static String SIGMA_PARAM_NAME =  "Mag Length Sigma";
  private double SIGMA_PARAM_MIN = 0;
  private double SIGMA_PARAM_MAX = 1;
  public Double DEFAULT_SIGMA_VAL = new Double(0.0);

  // slip rate prameter stuff
  public final static String SLIP_RATE_NAME = "Slip Rate";
  public final static String SLIP_RATE_UNITS = "mm/yr";
  public final static double SLIP_RATE_MIN = 0.0;
  public final static double SLIP_RATE_MAX = 1e5;
  public final static Double SLIP_RATE_DEFAULT = new Double(2);

  // parameter for magUpper of the GR dist
  public static final String GR_MAG_UPPER=new String("Mag Upper");
  public static final String GR_MAG_UPPER_INFO=new String("Max mag of the GR distribution (must be an increment of 0.05)");
  public final static Double GR_MAG_UPPER_DEFAULT = new Double(7.15);

  // dip direction parameter stuff
  public final static String DIP_DIRECTION_NAME = new String ("Dip LocationVector");
  public final static String DIP_DIRECTION_EAST = new String ("East");
  public final static String DIP_DIRECTION_WEST = new String ("West");

  // segmentation parameter stuff
  public final static String SEGMENTATION_NAME = new String ("Segmentation Model");
  public final static String SEGMENTATION_NO = new String ("Unsegmented");
  public final static String SEGMENTATION_YES = new String ("Segmented");

  // fault-model parameter stuff
  public final static String FAULT_MODEL_NAME = new String ("Fault Model");
  public final static String FAULT_MODEL_FRANKEL = new String ("Frankel's");
  public final static String FAULT_MODEL_STIRLING = new String ("Stirling's");

  // make the grid spacing parameter
  private DoubleParameter gridParam=new DoubleParameter(GRID_PARAM_NAME,GRID_PARAM_MIN,
      GRID_PARAM_MAX,GRID_PARAM_UNITS,DEFAULT_GRID_VAL);

  // make the rupture offset parameter
  private DoubleParameter offsetParam = new DoubleParameter(OFFSET_PARAM_NAME,OFFSET_PARAM_MIN,
      OFFSET_PARAM_MAX,OFFSET_PARAM_UNITS,DEFAULT_OFFSET_VAL);

  // make the mag-length sigma parameter
  private DoubleParameter lengthSigmaParam = new DoubleParameter(SIGMA_PARAM_NAME,
      SIGMA_PARAM_MIN, SIGMA_PARAM_MAX, DEFAULT_SIGMA_VAL);


  // make the mag-length sigma parameter
  private DoubleParameter slipRateParam = new DoubleParameter(SLIP_RATE_NAME,
      SLIP_RATE_MIN, SLIP_RATE_MAX, SLIP_RATE_UNITS, SLIP_RATE_DEFAULT);

  // make the magUpper parameter
  private DoubleParameter magUpperParam = new DoubleParameter(GR_MAG_UPPER,GR_MAG_UPPER_DEFAULT);

  // make the segmetation model parameter
  private ArrayList dipDirectionStrings=new ArrayList();
  private StringParameter dipDirectionParam;

  // make the segmetation model parameter
  private ArrayList segModelNamesStrings=new ArrayList();
  private StringParameter segModelParam;

  // make the fault-model parameter
  private ArrayList faultModelNamesStrings = new ArrayList();
  private StringParameter faultModelParam;

  // fault stuff
  private FaultTrace faultTraceAll, faultTraceA, faultTraceB, faultTraceC, faultTraceD, faultTraceE;
  public final static double LOWER_SEISMO_DEPTH = 12.0;
  public final static  double UPPER_SEISMO_DEPTH = 1.0;
  public final static  double DIP=60.0;
  public final static  double RAKE=-90.0;

  // Fault trace locations
  private final static Location traceLoc1 = new Location(37.609531,-121.7168636,1.0);     // southern most point
  private final static Location traceLoc2 = new Location(37.804854,-121.8580591,1.0);
  private final static Location traceLoc3 = new Location(38.000000,-122.0000000,1.0);
  private final static Location traceLoc4 = new Location(38.224800,-122.0000000,1.0);
  private final static Location traceLoc5 = new Location(38.419959,-121.8568637,1.0);
  private final static Location traceLoc6 = new Location(38.614736,-121.7129562,1.0);     // northern most point

  // GR mag freq dist stuff
  private GutenbergRichterMagFreqDist grMagFreqDist;
  public final static  double GR_MIN = 0.05;
  public final static  double GR_MAX = 9.95;
  public final static  int GR_NUM = 100;
  public final static  double GR_BVALUE = 0.9;
  public final static  double GR_MAG_LOWER = 0.05;


  /**
   * This constructor makes the parameters and sets up the source
   *
   * No argument constructor
   */
  public PEER_NonPlanarFaultForecast() {

    // create the timespan object with start time and duration in years
    timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
    timeSpan.addParameterChangeListener(this);

    // make the dipDirectionParam
    dipDirectionStrings.add(DIP_DIRECTION_EAST);
    dipDirectionStrings.add(DIP_DIRECTION_WEST);
    dipDirectionParam = new StringParameter(DIP_DIRECTION_NAME,dipDirectionStrings,DIP_DIRECTION_EAST);

    // make the segModelParam
    segModelNamesStrings.add(SEGMENTATION_NO);
    segModelNamesStrings.add(SEGMENTATION_YES);
    segModelParam = new StringParameter(SEGMENTATION_NAME,segModelNamesStrings,
                                      (String)segModelNamesStrings.get(0));

    // make the faultModelParam
    faultModelNamesStrings.add(FAULT_MODEL_FRANKEL);
    faultModelNamesStrings.add(FAULT_MODEL_STIRLING);
    faultModelParam = new StringParameter(FAULT_MODEL_NAME, faultModelNamesStrings,(String)faultModelNamesStrings.get(0));

    // now add the parameters to the adjustableParams list
    adjustableParams.addParameter(gridParam);
    adjustableParams.addParameter(offsetParam);
    adjustableParams.addParameter(lengthSigmaParam);
    adjustableParams.addParameter(slipRateParam);
    adjustableParams.addParameter(magUpperParam);
    adjustableParams.addParameter(segModelParam);
    adjustableParams.addParameter(faultModelParam);
    adjustableParams.addParameter(dipDirectionParam);

    // listen for change in the parameters
    gridParam.addParameterChangeListener(this);
    offsetParam.addParameterChangeListener(this);
    lengthSigmaParam.addParameterChangeListener(this);
    slipRateParam.addParameterChangeListener(this);
    magUpperParam.addParameterChangeListener(this);
    segModelParam.addParameterChangeListener(this);
    faultModelParam.addParameterChangeListener(this);
    dipDirectionParam.addParameterChangeListener(this);

    // make the mag-freq dits
    grMagFreqDist = new GutenbergRichterMagFreqDist(GR_MIN, GR_MAX, GR_NUM);

    // make the fault traces
    faultTraceAll = new FaultTrace("Non Planar Fault");
    faultTraceAll.add(traceLoc1);
    faultTraceAll.add(traceLoc2);
    faultTraceAll.add(traceLoc3);
    faultTraceAll.add(traceLoc4);
    faultTraceAll.add(traceLoc5);
    faultTraceAll.add(traceLoc6);

    faultTraceE = new FaultTrace("Non Planar Fault");
    faultTraceE.add(traceLoc1);
    faultTraceE.add(traceLoc2);

    faultTraceD = new FaultTrace("Non Planar Fault");
    faultTraceD.add(traceLoc2);
    faultTraceD.add(traceLoc3);

    faultTraceC = new FaultTrace("Non Planar Fault");
    faultTraceC.add(traceLoc3);
    faultTraceC.add(traceLoc4);

    faultTraceB = new FaultTrace("Non Planar Fault");
    faultTraceB.add(traceLoc4);
    faultTraceB.add(traceLoc5);

    faultTraceA = new FaultTrace("Non Planar Fault");
    faultTraceA.add(traceLoc5);
    faultTraceA.add(traceLoc6);


  }





  /**
   * update the sources based on the user paramters, only when user has changed any parameter
   */
   public void updateForecast(){
     String S = C + "updateForecast: ";

     if(parameterChangeFlag) {

       sourceList = new ArrayList();

       String dipDir = (String) dipDirectionParam.getValue();

       // reverse the order of the points if it's dipping west
       boolean reversed = false;
       if(dipDir.equals(DIP_DIRECTION_WEST)) {
         faultTraceAll.reverse();
         faultTraceA.reverse();
         faultTraceB.reverse();
         faultTraceC.reverse();
         faultTraceD.reverse();
         faultTraceE.reverse();
         reversed = true;
       }

       // get the segmentation type
       String segType = (String) segModelParam.getValue();
       double gridSpacing = ((Double)gridParam.getValue()).doubleValue();

       // get a fault factory based on the chosen fault model
       String faultModel = (String) faultModelParam.getValue();

       double offset = ((Double)offsetParam.getValue()).doubleValue();
       double lengthSigma = ((Double)lengthSigmaParam.getValue()).doubleValue();
       double magUpper = ((Double) magUpperParam.getValue()).doubleValue();
       double slipRate = ((Double) slipRateParam.getValue()).doubleValue() / 1000.0;  // last is to convert to meters/yr
       double ddw = (LOWER_SEISMO_DEPTH-UPPER_SEISMO_DEPTH)/Math.sin(DIP*Math.PI/180);

       if(segType.equals(SEGMENTATION_NO)){

         // Make the mag freq dist
         double faultArea = faultTraceAll.getTraceLength() * ddw * 1e6;  // the last is to convert to meters
         double totMoRate = 3e10*faultArea*slipRate;
         grMagFreqDist.setAllButTotCumRate(GR_MAG_LOWER, magUpper, totMoRate,GR_BVALUE);

         // make the fault surface
         EvenlyGriddedSurfFromSimpleFaultData surfaceAll;
         if (faultModel.equals(FAULT_MODEL_FRANKEL)) {
           surfaceAll = new FrankelGriddedSurface(faultTraceAll, DIP, UPPER_SEISMO_DEPTH, LOWER_SEISMO_DEPTH, gridSpacing);
         }
         else {
           surfaceAll = new StirlingGriddedSurface(faultTraceAll, DIP, UPPER_SEISMO_DEPTH, LOWER_SEISMO_DEPTH, gridSpacing);
         }

         // make the source
         source = new FloatingPoissonFaultSource(grMagFreqDist,(EvenlyGriddedSurface)surfaceAll,
                                             magScalingRel,lengthSigma,rupAspectRatio,offset,
                                             RAKE,timeSpan.getDuration(),minMag);
         // add it to the source list
         sourceList.add(source);

       }
       // Segmented Case:
       else {

         // Make the mag freq dist
         double faultArea = faultTraceA.getTraceLength() * ddw * 1e6; // the last is to convert to meters
         double totMoRate = 3e10 * faultArea * slipRate;
         grMagFreqDist.setAllButTotCumRate(GR_MAG_LOWER, magUpper, totMoRate,
                                           GR_BVALUE);

         if (D) System.out.println("Segment lengths:\n\n" +
                                   "\tA - " + faultTraceA.getTraceLength() +
                                   "\n" +
                                   "\tB - " + faultTraceB.getTraceLength() +
                                   "\n" +
                                   "\tC - " + faultTraceC.getTraceLength() +
                                   "\n" +
                                   "\tD - " + faultTraceD.getTraceLength() +
                                   "\n" +
                                   "\tE - " + faultTraceE.getTraceLength() +
                                   "\n");

         //make source A:
         EvenlyGriddedSurfFromSimpleFaultData surfaceA;
         if (faultModel.equals(FAULT_MODEL_FRANKEL))
           surfaceA = new FrankelGriddedSurface(faultTraceA, DIP,
                                                UPPER_SEISMO_DEPTH,
                                                LOWER_SEISMO_DEPTH, gridSpacing);
         else
           surfaceA = new StirlingGriddedSurface(faultTraceA, DIP,
                                                 UPPER_SEISMO_DEPTH,
                                                 LOWER_SEISMO_DEPTH,
                                                 gridSpacing);
         source = new FloatingPoissonFaultSource(grMagFreqDist,
                                                 (EvenlyGriddedSurface)
                                                 surfaceA,
                                                 magScalingRel, lengthSigma,
                                                 rupAspectRatio, offset,
                                                 RAKE, timeSpan.getDuration(),
                                                 minMag);
         sourceList.add(source);

         //make source B:
         EvenlyGriddedSurfFromSimpleFaultData surfaceB;
         if (faultModel.equals(FAULT_MODEL_FRANKEL))
           surfaceB = new FrankelGriddedSurface(faultTraceB, DIP,
                                                UPPER_SEISMO_DEPTH,
                                                LOWER_SEISMO_DEPTH, gridSpacing);
         else
           surfaceB = new StirlingGriddedSurface(faultTraceB, DIP,
                                                 UPPER_SEISMO_DEPTH,
                                                 LOWER_SEISMO_DEPTH,
                                                 gridSpacing);
         source = new FloatingPoissonFaultSource(grMagFreqDist,
                                                 (EvenlyGriddedSurface)
                                                 surfaceB,
                                                 magScalingRel, lengthSigma,
                                                 rupAspectRatio, offset,
                                                 RAKE, timeSpan.getDuration(),
                                                 minMag);
         sourceList.add(source);

         //make source C:
         EvenlyGriddedSurfFromSimpleFaultData surfaceC;
         if (faultModel.equals(FAULT_MODEL_FRANKEL))
           surfaceC = new FrankelGriddedSurface(faultTraceC, DIP,
                                                UPPER_SEISMO_DEPTH,
                                                LOWER_SEISMO_DEPTH, gridSpacing);
         else
           surfaceC = new StirlingGriddedSurface(faultTraceC, DIP,
                                                 UPPER_SEISMO_DEPTH,
                                                 LOWER_SEISMO_DEPTH,
                                                 gridSpacing);
         source = new FloatingPoissonFaultSource(grMagFreqDist,
                                                 (EvenlyGriddedSurface)
                                                 surfaceC,
                                                 magScalingRel, lengthSigma,
                                                 rupAspectRatio, offset,
                                                 RAKE, timeSpan.getDuration(),
                                                 minMag);
         sourceList.add(source);

         //make source D:
         EvenlyGriddedSurfFromSimpleFaultData surfaceD;
         if (faultModel.equals(FAULT_MODEL_FRANKEL))
           surfaceD = new FrankelGriddedSurface(faultTraceD, DIP,
                                                UPPER_SEISMO_DEPTH,
                                                LOWER_SEISMO_DEPTH, gridSpacing);
         else
           surfaceD = new StirlingGriddedSurface(faultTraceD, DIP,
                                                 UPPER_SEISMO_DEPTH,
                                                 LOWER_SEISMO_DEPTH,
                                                 gridSpacing);
         source = new FloatingPoissonFaultSource(grMagFreqDist,
                                                 (EvenlyGriddedSurface)
                                                 surfaceD,
                                                 magScalingRel, lengthSigma,
                                                 rupAspectRatio, offset,
                                                 RAKE, timeSpan.getDuration(),
                                                 minMag);
         sourceList.add(source);

         //make source E:
         EvenlyGriddedSurfFromSimpleFaultData surfaceE;
         if (faultModel.equals(FAULT_MODEL_FRANKEL))
           surfaceE = new FrankelGriddedSurface(faultTraceE, DIP,
                                                UPPER_SEISMO_DEPTH,
                                                LOWER_SEISMO_DEPTH, gridSpacing);
         else
           surfaceE = new StirlingGriddedSurface(faultTraceE, DIP,
                                                 UPPER_SEISMO_DEPTH,
                                                 LOWER_SEISMO_DEPTH,
                                                 gridSpacing);
         source = new FloatingPoissonFaultSource(grMagFreqDist,
                                                 (EvenlyGriddedSurface) surfaceE,
                                                 magScalingRel, lengthSigma,
                                                 rupAspectRatio, offset,
                                                 RAKE, timeSpan.getDuration(),
                                                 minMag);
         sourceList.add(source);

       }


       if(D) {
         System.out.println(S);
         System.out.println("   rate�5="+(float)grMagFreqDist.getCumRate(5.05));
         System.out.println("   segType = "+segType);
         System.out.println("   faultModel = "+faultModel);
         System.out.println("   magUpper = "+magUpper);
         System.out.println("   slipRate = "+slipRate);
         System.out.println("   gridSpacing = "+gridSpacing);
         System.out.println("   offset = "+offset);
         System.out.println("   lengthSigma = "+lengthSigma);
       }

       // un-reverse the order of the fault trace points if reversed earlier
       if(reversed) {
         faultTraceAll.reverse();
         faultTraceA.reverse();
         faultTraceB.reverse();
         faultTraceC.reverse();
         faultTraceD.reverse();
         faultTraceE.reverse();
       }


     }
     parameterChangeFlag = false;
   }




   /**
    * Return the earhthquake source at index i. This methos returns the reference to
    * the class variable. So, when you call this method again, result from previous
    * method call is no longer valid.
    * this is  fast but dangerous method
    *
    * @param iSource : index of the source needed
    *
    * @return Returns the ProbEqkSource at index i
    *
    */
   public ProbEqkSource getSource(int iSource) {

    return (ProbEqkSource) sourceList.get(iSource);
   }


   /**
    * Get the number of earthquake sources
    *
    * @return integer value specifying the number of earthquake sources
    */
   public int getNumSources(){
     return sourceList.size();
   }

    /**
     *  Clone is returned.
     * All the 3 different ArrayList source List are combined into the one ArrayList list
     * So, list can be save in ArrayList and this object subsequently destroyed
     *
     * @return ArrayList of Prob Earthquake sources
     */
    public ArrayList  getSourceList(){
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

}
