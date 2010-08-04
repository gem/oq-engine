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

package org.opensha.sha.earthquake.rupForecastImpl.WG02;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.ListIterator;
import java.util.StringTokenizer;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagAreaRelationship;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.exceptions.FaultException;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultSource;
import org.opensha.sha.earthquake.rupForecastImpl.GriddedRegionPoissonEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;

/**
 * <p>Title: WG02_EqkRupForecast</p>
 * <p>Description: Working Group 2002 Earthquake Rupture Forecast.
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author : Edward Field
 * @Date : April, 2003
 * @version 1.0
 */

public class WG02_EqkRupForecast extends EqkRupForecast{

  //for Debug purposes
  private final static String  C = new String("WG02_EqkRupForecast");
  public final static String NAME ="WG02 Eqk Rup Forecast";
  private boolean D = false;

  /**
   * Vectors for holding the various sources, separated by type
   */
  private ArrayList allSources;

 // This is an array holding the relevant lines of the input file
  private ArrayList inputFileStrings = null;

  double rupOffset, gridSpacing, deltaMag;
  String backSeisValue;
  String grTailValue;
  String name;

  /**
   * This constructs a single forecast for a single-iteration run of the WG02 fortran code,
   * where the modal values at each branch tip were given unit weight and all other branches
   * were given a weight of zero.  This no-argument constuctor only supports a duration of
   * 30 years (this can easily be relaxed later is there is demand).
   */
  public WG02_EqkRupForecast() {

    // create the timespan object with start time and duration in years
    timeSpan = new TimeSpan(TimeSpan.YEARS,TimeSpan.YEARS);
    timeSpan.addParameterChangeListener(this);

    String INPUT_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/WG02/singleIterationWithModes.OpenSHA.30yr.txt";
    //String INPUT_FILE_NAME = "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/WEB-INF/dataFiles/singleIterationWithModes.OpenSHA.30yr.txt";
    ArrayList inputFileLines=null;

    // read the lines of the input files into a list
    try{ inputFileLines = FileUtils.loadJarFile( INPUT_FILE_NAME ); }
    catch( FileNotFoundException e){ System.out.println(e.toString()); }
    catch( IOException e){ System.out.println(e.toString());}

    inputFileStrings = new ArrayList();
    int lastLine = inputFileLines.size();
    for(int i=2;i<lastLine;++i)
      inputFileStrings.add(inputFileLines.get(i));

    if (D) System.out.println(C+" firstLineOfStrings ="+inputFileStrings.get(0));
    if (D) System.out.println(C+" LastLineOfStrings ="+inputFileStrings.get(inputFileStrings.size()-1));

    // get the line with the timeSpan info on it
    ListIterator it = inputFileLines.listIterator();
    StringTokenizer st;
    st = new StringTokenizer((String) inputFileLines.get(1));

    st.nextToken();
    st.nextToken();
    st.nextToken();
    st.nextToken();
    int year = new Double(st.nextToken()).intValue();
    double duration = new Double(st.nextToken()).doubleValue();
    int numIterations = new Double(st.nextToken()).intValue();

    inputFileLines =null ;

    if (D) System.out.println("year="+year+"; duration="+duration+"; numIterations="+numIterations);
    timeSpan.setDuractionConstraint(duration,duration);
    timeSpan.setDuration(duration);
    timeSpan.setStartTimeConstraint(TimeSpan.START_YEAR,year,year);
    timeSpan.setStartTime(year);

    // hard code the adjustable parameter values
    rupOffset = 2;
    gridSpacing = 1;
    deltaMag = 0.1;
    backSeisValue = WG02_ERF_Epistemic_List.SEIS_INCLUDE;
    grTailValue = WG02_ERF_Epistemic_List.SEIS_INCLUDE;
    name = "noName";

    // now make the sources
    makeSources();
  }



  public WG02_EqkRupForecast(ArrayList inputFileStrings, double rupOffset, double gridSpacing,
                             double deltaMag, String backSeisValue, String grTailValue, String name,
                             TimeSpan timeSpan) {

    this.inputFileStrings = inputFileStrings;
    this.rupOffset=rupOffset;
    this.gridSpacing=gridSpacing;
    this.deltaMag = deltaMag;
    this.backSeisValue=backSeisValue;
    this.grTailValue=grTailValue;
    this.name = name;
    this.timeSpan = timeSpan;

    // now make the sources
    makeSources();

  }

  /**
   * Make the sources
   *
   * @throws FaultException
   */
  private  void makeSources() throws FaultException{

    if(D) System.out.println(C+": last line of inputFileStrings = "+inputFileStrings.get(inputFileStrings.size()-1));
    allSources = new ArrayList();
    ArrayList grTailSources = new ArrayList();

    FaultTrace faultTrace;
    EvenlyGriddedSurface faultSurface;

    WG02_CharEqkSource wg02_source;
    GriddedRegionPoissonEqkSource backSource = null;
    FloatingPoissonFaultSource grTailSource = null;

    WC1994_MagAreaRelationship magScalingRel = new WC1994_MagAreaRelationship();

    double   lowerSeismoDepth, upperSeismoDepth;
    double lat, lon;
    double dip=0, downDipWidth=0, rupArea;
    double prob, meanMag, magSigma, nSigmaTrunc, rake;
    String fault, rup, sourceName;
    int numPts, i, lineIndex;

    double back_N, back_b, back_M1, back_M2;
    double back_deltaMag = 0.05;  // this needs to be 0.05 to match the M2 of 7.25 (otherwise moment won't be exactly right)
    int back_num;

    double tail_N, tail_b, tail_M1, tail_M2, tail_deltaMag = 0.1;
    int tail_num;
    GutenbergRichterMagFreqDist tail_GR_dist = null;


    // Create iterator over inputFileStrings
    ListIterator it = inputFileStrings.listIterator();
    StringTokenizer st;

    // 1st line has the iteration number
    st = new StringTokenizer(it.next().toString());
    String interation = st.nextToken().toString();

    // 2nd line is background seismicity stuff
    // the vals are N(M�M1), b_val, M1, M2 -- Extrapolate this down to M = 5.0! (M1 > 5.0)
    st = new StringTokenizer(it.next().toString());

    // make the background source if it's desired
    if(backSeisValue.equals(WG02_ERF_Epistemic_List.SEIS_INCLUDE)) {
      back_N = new Double(st.nextToken()).doubleValue();
      back_b = new Double(st.nextToken()).doubleValue();
      back_M1 = new Double(st.nextToken()).doubleValue();
      back_M1 = ((double)Math.round(back_M1*100))/100.0; // round it to nice value
      back_M2 = new Double(st.nextToken()).doubleValue();
      back_num = Math.round((float)((back_M2-5.0)/back_deltaMag)) + 1;
      GutenbergRichterMagFreqDist back_GR_dist = new GutenbergRichterMagFreqDist(5.0, back_num, back_deltaMag,
                                                                                 1.0, back_b);
      back_GR_dist.scaleToCumRate(back_M1,back_N);
// System.out.println("background: M1="+back_M1+"; M2="+back_M2+"; deltaM="+back_deltaMag+"; num="+back_num);
      LocationList locList = new LocationList();
      locList.add(new Location(37.19, -120.61, 0.0));
      locList.add(new Location(36.43, -122.09, 0.0));
      locList.add(new Location(38.23, -123.61, 0.0));
      locList.add(new Location(39.02, -122.08, 0.0));
      GriddedRegion gridReg = 
    	  new GriddedRegion(
    			  locList, BorderType.MERCATOR_LINEAR,0.1, new Location(0,0));
//System.out.println("num background locs = "+gridReg.getNumGridLocs());

      backSource = new GriddedRegionPoissonEqkSource(gridReg, back_GR_dist, timeSpan.getDuration(),
                                                     0.0, 90.0, 0.0); // aveRake=0; aveDip=90; aveDepth=0


      if(D) {
        System.out.println("back_N="+back_N+"\nback_b="+back_b+"\nback_M1="+back_M1+"\nback_M2="+
                           back_M2+"\nback_num="+back_num+"\nback_deltaMag="+back_deltaMag);
        System.out.println("GR_cum_rate(M1)="+back_GR_dist.getCumRate(back_M1));
        System.out.println("GR_cum_rate(5.0)="+back_GR_dist.getCumRate(5.0));
        System.out.println("M2 in GR_dist ="+back_GR_dist.getMaxX());
        System.out.println("num_back_grid_points="+gridReg.getNodeCount());
      }

      // add this source later so it's at the end of the list
    }

    // Now loop over the ruptures within this iteration
    while(it.hasNext()) {

      faultTrace = new FaultTrace("noName");

      // line with fault/rupture index
      st = new StringTokenizer(it.next().toString());
      fault = st.nextToken().toString();
      rup = st.nextToken().toString();

      // line with source name
      st = new StringTokenizer(it.next().toString());
      sourceName = st.nextToken().toString();

      // line with number of fault-trace points
      st = new StringTokenizer(it.next().toString());
      numPts = new Integer(st.nextToken()).intValue();

      // make the fault trace from the next numPts lines
      for(i=0;i<numPts;i++) {
        st = new StringTokenizer(it.next().toString());
        lon = new Double(st.nextToken()).doubleValue();
        lat = new Double(st.nextToken()).doubleValue();
        faultTrace.add(new Location(lat,lon));
      }

      // reverse the order of point if it's the Mt Diable fault
      // so it will be dipping to the right
      if( fault.equals("7") )
        faultTrace.reverse();;

      // line with dip, seisUpper, ddw, and rupArea
      st = new StringTokenizer(it.next().toString());
      dip = new Double(st.nextToken()).doubleValue();
      upperSeismoDepth = new Double(st.nextToken()).doubleValue();
      downDipWidth = new Double(st.nextToken()).doubleValue();
      lowerSeismoDepth = upperSeismoDepth+downDipWidth*Math.sin(dip*Math.PI/180);
      rupArea = new Double(st.nextToken()).doubleValue();

      // line with the GR tail stuff
      st = new StringTokenizer(it.next().toString());
      // skipping for now
      // vals are M1, M2, N(M�M1), b_val
      if(grTailValue.equals(WG02_ERF_Epistemic_List.SEIS_INCLUDE)) {

        tail_M1 = new Double(st.nextToken()).doubleValue();
        if(tail_M1 != 5.0)
          throw new RuntimeException("tail_M1 must equal 5.0!");
        tail_M2 = new Double(st.nextToken()).doubleValue();
        tail_N = new Double(st.nextToken()).doubleValue();
        tail_b = new Double(st.nextToken()).doubleValue();
        tail_num = Math.round((float)((tail_M2-tail_M1)/tail_deltaMag)) + 1;
        // note: the above means M2 won't be exactly the same in what's next
        tail_GR_dist = new GutenbergRichterMagFreqDist(tail_M1, tail_num, tail_deltaMag, 1.0, tail_b);
        tail_GR_dist.scaleToCumRate(tail_M1,tail_N);

      if(D) {
        System.out.println("tail_N="+tail_N+"\ntail_b="+tail_b+"\ntail_M1="+tail_M1+"\ntail_M2="+
                           tail_M2+"\ntail_num="+tail_num+"\ntail_deltaMag="+tail_deltaMag);
        System.out.println("GR_rate(M1)="+tail_GR_dist.getCumRate(tail_M1));
        System.out.println("M2 in GR_dist ="+tail_GR_dist.getMaxX());

      }
        // the source is made later after the fault is created

      }


      // line with prob, meanMag, magSigma, nSigmaTrunc
      st = new StringTokenizer(it.next().toString());
      prob = new Double(st.nextToken()).doubleValue();
      meanMag = new Double(st.nextToken()).doubleValue();
      magSigma = new Double(st.nextToken()).doubleValue();
      nSigmaTrunc = new Double(st.nextToken()).doubleValue();

      faultSurface = new StirlingGriddedSurface(faultTrace,dip,upperSeismoDepth,lowerSeismoDepth,gridSpacing);


      // change the rupArea if it's one of the floating ruptures
      if( rup.equals("11")  || rup.equals("12") )
        rupArea = Math.pow(10.0, meanMag-4.2);  // Ellsworth model 2

      // set the rake (only diff for Mt Diable thrust)
      if( fault.equals("7") )
        rake=90.0;
      else
        rake = 0.0;

      // create the source
      wg02_source = new WG02_CharEqkSource(prob,meanMag,magSigma,nSigmaTrunc, deltaMag,
          faultSurface,rupArea,rupOffset,sourceName,rake);
/*
double tempMoRate = 0.0, m, p;
for(int k=0; k<wg02_source.getNumRuptures(); k++) {
  m = wg02_source.getRupture(k).getMag();
  p =  wg02_source.getRupture(k).getProbability();
  tempMoRate += (-Math.log(1-p)/timeSpan.getDuration())*org.opensha.calc.MomentMagCalc.getMoment(m);
}
System.out.println("Char_momentRate="+tempMoRate);
*/

      // add the source
      allSources.add(wg02_source);

      // now create and add the GR tail source if it's needed
      if(grTailValue.equals(WG02_ERF_Epistemic_List.SEIS_INCLUDE)) {
        grTailSource = new FloatingPoissonFaultSource(tail_GR_dist, faultSurface, magScalingRel,
                                  0.0, 1.0, rupOffset, rake, timeSpan.getDuration());
        grTailSource.setName(sourceName+"_tail");
        // add the source to the temporary list (temporary so it can be appended to the end of allSources later)
        grTailSources.add(grTailSource);
//System.out.println("GR_tail_moment="+tail_GR_dist.getTotalMomentRate()+" ratio="+tail_GR_dist.getTotalMomentRate()/tempMoRate);
      }
    }

    // append the GR_tail sources if need be
    if(grTailValue.equals(WG02_ERF_Epistemic_List.SEIS_INCLUDE))
      allSources.addAll(grTailSources);

    // add the background seis source if need be
    if(backSeisValue.equals(WG02_ERF_Epistemic_List.SEIS_INCLUDE))
      allSources.add(backSource);
  }




    /**
     * Returns the  ith earthquake source
     *
     * @param iSource : index of the source needed
    */
    public ProbEqkSource getSource(int iSource) {

      return (ProbEqkSource) allSources.get(iSource);
    }

    /**
     * Get the number of earthquake sources
     *
     * @return integer
     */
    public int getNumSources(){
      return allSources.size();
    }

     /**
      * Get the list of all earthquake sources.
      *
      * @return ArrayList of Prob Earthquake sources
      */
     public ArrayList  getSourceList(){
       return null;
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

     // does nothing for now
     if(parameterChangeFlag) {
       parameterChangeFlag = false;
     }
   }


   public void listSourceTotalProbs() {
     double p_char, p_tail, p_both, p_tot=1.00;
     int num = getNumSources(), i1, i2;
     for(i1=0; i1 < (num-1)/2; i1++) {
       i2 = i1+(num-1)/2;
       p_char = getSource(i1).computeTotalProb();
       p_tail = getSource(i2).computeTotalProb();
       p_both =  1 - (1-p_char)*(1-p_tail);
       p_both = (double)Math.round(p_both*1000000)/1000000;
       p_tot *= (1-p_both);
       System.out.println((float)p_both+"\t"+getSource(i1).getName()+ "   ("+ (float)p_char+" for char,  and "+(float)p_tail+
                          " for "+getSource(i2).getName()+")");
     }
     // add the background source
     p_both = getSource(num-1).computeTotalProb();
     p_both = (double)Math.round(p_both*1000000)/1000000;
     System.out.println((float)p_both+"\t"+getSource(num-1).getName());
     p_tot *= (1-p_both);

     p_tot = 1.0-p_tot;
     System.out.println((float)p_tot+"\tTotal Probability");

   }

   /**
    * This main method tests the forecast for the singleIterationWithModes case.
    * Specifically, the "p_both" values listed by this method (the total probability
    * for each source" agree well with those listed in the singleIterationWithModes.out3
    * file.  The only exception is for the background seismicity, where our probability
    * is higher due to an error in their code in computing the cumulative rate at mag 5.0.
    * The error is specifically:
    *
    * "backRate(iMonte) = back_N * 10.**(- back_bValue*(exp_MinMag-back_M1))" in wg99_main.f
    *
    * Next I need to check some iterations to make sure nasty things aren't sneaking in.
    * @param args
    */
   public static void main(String[] args) {
     WG02_EqkRupForecast qkCast = new WG02_EqkRupForecast();
     System.out.println("num_sources="+qkCast.getNumSources());
     int num = 0;
     for (int i=0; i < qkCast.getNumSources(); i++) {
       num += qkCast.getNumRuptures(i);
//       System.out.println(qkCast.getSource(i).getName()+" has "+qkCast.getNumRuptures(i)+" ruptures");
     }
     System.out.println("tot_ruptures="+num);


//     System.out.println("num_rups(lastSrc)="+qkCast.getNumRuptures(qkCast.getNumSources()-1));
//     qkCast.listSourceTotalProbs();
  }

}
