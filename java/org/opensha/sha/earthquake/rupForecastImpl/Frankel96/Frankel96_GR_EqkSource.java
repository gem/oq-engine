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

package org.opensha.sha.earthquake.rupForecastImpl.Frankel96;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagLengthRelationship;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;


/**
 * <p>Title: Frankel96_GR_EqkSource </p>
 * <p>Description: frankel 1996 Gutenberg Richter Type B earthquake source</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta & Vipin Gupta
 * @date Sep 2, 2002
 * @version 1.0
 */

public class Frankel96_GR_EqkSource extends ProbEqkSource {


  //for Debug purposes
  private static String  C = "Frankel96_GR_EqkSource";
  private boolean D = false;

  private GutenbergRichterMagFreqDist gR;
  private double rake;
  private double timeSpan;
  //these are the static static defined varibles to be used to find the number of ruptures.
  private final static double RUPTURE_WIDTH =100.0;
  private double rupOffset;
  private int totNumRups;
  private EvenlyGriddedSurface surface;

  /**
   * constructor specifying the values needed for Gutenberg Richter
   * and also for constructing the rupture
   *
   * @param rake  : Average rake of the surface
   * @param bValue : b Value in the GR distribution
   * @param magLower : magLower as in GR distribution
   * @param magUpper : magUpper as in GR distribution
   * @param moRate : moment rate  of GR distribution (N-m/yr)
   * @param delta  : delta as in GR distribution
   * @param surface : Fault Surface
   */
  public Frankel96_GR_EqkSource(double rake,
                                double bValue,
                                double magLower,
                                double magUpper,
                                double moRate,
                                double delta,
                                double rupOffset,
                                EvenlyGriddedSurface surface,
                                String faultName) {

    this.name = faultName+" GR";
    this.rake=rake;
    this.surface=surface;
    this.rupOffset = rupOffset;
    // see here that we have rounded num to nearest integer value

    int num = (int)Math.rint((magUpper - magLower)/delta + 1);
    if( D ) System.out.println("Frankel96_GR_EqkSource:magUpper::"+magUpper);
    if( D ) System.out.println("Frankel96_GR_EqkSource:magLower::"+magLower);
    if( D ) System.out.println("Frankel96_GR_EqkSource:delta::"+delta);
    if( D ) System.out.println("Frankel96_GR_EqkSource:num::"+num);
    probEqkRupture = new ProbEqkRupture();
    probEqkRupture.setAveRake(rake);

    //Setting the GutenbergDistribution
    gR = new GutenbergRichterMagFreqDist(magLower,magUpper,num);
    gR.setAllButTotCumRate(magLower,magUpper,moRate,bValue );

    // This was used for reading his orig file
    //double rate = Math.pow(10,aVal - bValue*magLower);
    //gR.scaleToIncrRate(magLower,rate);

    // Determine number of ruptures
    int numMags = gR.getNum();
    totNumRups=0;
    WC1994_MagLengthRelationship magLength = new WC1994_MagLengthRelationship();
    for(int i=0;i<num;++i){
      double rupLen = magLength.getMedianLength(gR.getX(i),rake);
      totNumRups += getNumRuptures(rupLen);
    }
    if( D ) System.out.println("Frankel96_GR_EqkSource:Frankel96_GR_EqkSource:totNumRups::"+totNumRups);
    if( D ) System.out.println("Frankel96_GR_EqkSource:Frankel96_GR_EqkSource:momentRate::"+gR.getTotalMomentRate());
  }

  /**
   * this functions sums up all the ruptures for all magnitudes
   * @return the total num of rutures for all magnitudes
   */
  public int getNumRuptures() { return totNumRups; }

  /**
   * It returns a list of all the locations which make up the surface for this
   * source.
   *
   * @return LocationList - List of all the locations which constitute the surface
   * of this source
   */
   public LocationList getAllSourceLocs() {
     return this.surface.getLocationList();
   }
   
   public EvenlyGriddedSurfaceAPI getSourceSurface() { return this.surface; }




  /**
   * This method sets the probability of the different rupture surface for different mag
   * @param nthRupture : it is to find the mag and rate to which that rupture number correspond
   * @return the object of the ProbEqkRupture class after setting the probability
   */
  public ProbEqkRupture getRupture(int nthRupture){
    int numMags = gR.getNum();
    double mag=0, rupLen=0;
    int numRups=0, tempNumRups=0;

    if(nthRupture < 0 || nthRupture>=getNumRuptures())
       throw new RuntimeException("Invalid rupture index. This index does not exist");

    // this finds the magnitude:
    WC1994_MagLengthRelationship magLength = new WC1994_MagLengthRelationship();
    for(int i=0;i<numMags;++i){
      mag=gR.getX(i);
      rupLen = magLength.getMedianLength(gR.getX(i),rake);
      numRups = getNumRuptures(rupLen);
      tempNumRups += numRups;
      if(nthRupture < tempNumRups)
        break;
    }

    probEqkRupture.setMag(mag);
    // set probability
    double rate = gR.getY(mag);
    double prob = 1- Math.exp(-timeSpan*rate/numRups);
    probEqkRupture.setProbability(prob);

    // set rupture surface
    probEqkRupture.setRuptureSurface( surface.getNthSubsetSurface(rupLen,
                                      RUPTURE_WIDTH,rupOffset,
                                      nthRupture+numRups-tempNumRups));

    return probEqkRupture;
  }


  /** Set the time span in years
   *
   * @param yrs : timeSpan as specified in  Number of years
   */
  public void setTimeSpan(double yrs) {
   //set the time span in yrs
    timeSpan = yrs;
  }



  /**
   * @param mag
   * @return the total number of ruptures associated with the given mag
   */
  private int getNumRuptures(double rupLen){
    return surface.getNumSubsetSurfaces(rupLen,RUPTURE_WIDTH,rupOffset);
 }


   /**
   * This returns the shortest dist to either end of the fault trace, or to the
   * mid point of the fault trace.
   * @param site
   * @return minimum distance
   */
   public  double getMinDistance(Site site) {

      double min;

      // get first location on fault trace
      LocationVector dir = LocationUtils.vector(site.getLocation(), (Location) surface.get(0,0));
      min = dir.getHorzDistance();

      // get last location on fault trace
      dir = LocationUtils.vector(site.getLocation(),(Location) surface.get(0,surface.getNumCols()-1));
      if (min > dir.getHorzDistance())
          min = dir.getHorzDistance();

      // get mid location on fault trace
      dir = LocationUtils.vector(site.getLocation(),(Location) surface.get(0,(int) surface.getNumCols()/2));
      if (min > dir.getHorzDistance())
          min = dir.getHorzDistance();

      return min;
    }

 /**
  * get the name of this class
  *
  * @return
  */
 public String getName() {
   return name;
  }
}
