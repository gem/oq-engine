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

package org.opensha.sha.earthquake.rupForecastImpl.Frankel02;

import java.util.ArrayList;
import java.util.Iterator;

import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.FrankelGriddedSurface;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
;



/**
 * <p>Title: Frankel02_TypeB_EqkSource </p>
 * <p>Description: This implements Frankel's floating-rupture Gutenberg Richter
 * source used in the 2002 version of his code.  We made this, rather than using
 * the more general FloatingPoissonFaultSource only for enhanced performance (e.g.,
 * no need to float down dip or to support Area(Mag) uncertainties.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta & Vipin Gupta
 * @date Sep 2, 2002
 * @version 1.0
 */

public class Frankel02_TypeB_EqkSource extends ProbEqkSource {


  //for Debug purposes
  private static String  C = "Frankel02_GR_EqkSource";
  private boolean D = false;

  private double rake;
  protected double duration;
  //these are the static static defined varibles to be used to find the number of ruptures.
  private final static double RUPTURE_WIDTH =100.0;
  private double rupOffset;
  private int totNumRups;
  private EvenlyGriddedSurface surface;
  private ArrayList mags, rates;
  private MagAreaRelationship magAreaRel;

  
  /**
   * empty constructor
   *
   */
  public Frankel02_TypeB_EqkSource() {}

  
  
  /**
   * constructor specifying the values needed for the source
   *
   * @param magFreqDist - any IncrementalMagFreqDist
   * @param surface - any EvenlyGriddedSurface
   * @param rupOffset - floating rupture offset (km)
   * @param rake - rake for all ruptures
   * @param duration - forecast duration (yrs)
   * @param sourceName - source name
   */
  public Frankel02_TypeB_EqkSource(IncrementalMagFreqDist magFreqDist,
		  EvenlyGriddedSurface surface,
		  double rupOffset,
		  double rake,
		  double duration,
		  String sourceName) {
	  
	  this.magAreaRel=null;
	  updateAll(magFreqDist, surface, rupOffset, rake, duration, sourceName);
  }
  
  
  public void setAll(IncrementalMagFreqDist magFreqDist,
		  EvenlyGriddedSurface surface,
		  double rupOffset,
		  double rake,
		  double duration,
		  String sourceName) {
	  
	  this.magAreaRel=null;
	  updateAll(magFreqDist, surface, rupOffset, rake, duration, sourceName);
  }

    
  public void setAll(IncrementalMagFreqDist magFreqDist,
		  EvenlyGriddedSurface surface,
		  double rupOffset,
		  double rake,
		  double duration,
		  String sourceName,
		  MagAreaRelationship magAreaRel) {
	  
	  this.magAreaRel=magAreaRel;
	  updateAll(magFreqDist, surface, rupOffset, rake, duration, sourceName);
  }

    
  private void updateAll(IncrementalMagFreqDist magFreqDist,
		  EvenlyGriddedSurface surface,
		  double rupOffset,
		  double rake,
		  double duration,
		  String sourceName) {
	  
	  this.surface=surface;
	  this.rupOffset = rupOffset;
	  this.rake=rake;
	  this.duration = duration;
	  this.name = sourceName;
	  
	  probEqkRupture = new ProbEqkRupture();
	  probEqkRupture.setAveRake(rake);
	  
	  // get a list of mags and rates for non-zero rates
	  mags = new ArrayList();
	  rates = new ArrayList();
	  for (int i=0; i<magFreqDist.getNum(); ++i){
		  if(magFreqDist.getY(i) > 0){
			  //magsAndRates.set(magFreqDist.getX(i),magFreqDist.getY(i));
			  mags.add(new Double(magFreqDist.getX(i)));
			  rates.add(new Double(magFreqDist.getY(i)));
		  }
	  }

    // Determine number of ruptures
    int numMags = mags.size();
    totNumRups=0;
    for(int i=0;i<numMags;++i){
      double rupLen = getRupLength(((Double)mags.get(i)).doubleValue());
      totNumRups += getNumRuptures(rupLen);
    }
  }

  /**
   * 
   * @return
   */
  public EvenlyGriddedSurface getSourceSurface() { return this.surface; }

  public int getNumRuptures() { return totNumRups; }


  /**
   * This gets the ProbEqkRupture object for the nth Rupture
   */
  public ProbEqkRupture getRupture(int nthRupture){
    int numMags = mags.size();
    double mag=0, rupLen=0;
    int numRups=0, tempNumRups=0, iMag=-1;

    if(nthRupture < 0 || nthRupture>=getNumRuptures())
       throw new RuntimeException("Invalid rupture index. This index does not exist");

    // this finds the magnitude for the nthRupture:
    // alt would be to store a rup-mag mapping
    for(int i=0;i<numMags;++i){
      mag = ((Double)mags.get(i)).doubleValue();
      iMag = i;
      rupLen = getRupLength(mag);
      if(D) System.out.println("mag="+mag+"; rupLen="+rupLen);
      numRups = getNumRuptures(rupLen);
      tempNumRups += numRups;
      if(nthRupture < tempNumRups)
        break;
    }

    probEqkRupture.setMag(mag);
    // set probability
    double rate = ((Double)rates.get(iMag)).doubleValue();
    double prob = 1- Math.exp(-duration*rate/numRups);
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
  public void setDuration(double yrs) {
   //set the time span in yrs
    duration = yrs;
  }


  /**
   * This returns the rupture length implied by the magAreaRel (length=area/DDW), or if the magAreaRel is null then
   * the Wells & Coppersmith (1994) "All" equation is used (the latter is what Frankel's 2002 code uses).
   * @param mag
   * @return
   */
  private double getRupLength(double mag){ 
	  if(this.magAreaRel == null)
		  return Math.pow(10.0,-3.22+0.69*mag); 
	  else
		  return magAreaRel.getMedianArea(mag)/surface.getSurfaceWidth();
  }

  /**
   * @param rupLen
   * @return the total number of ruptures associated with the given rupLen
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


  /**
   * this is to test the code
   * @param args
   */
  public static void main(String[] args) {
    FaultTrace fltTr = new FaultTrace("name");
    fltTr.add(new Location(33.0,-122,0));
    fltTr.add(new Location(34.0,-122,0));
    FrankelGriddedSurface surface = new FrankelGriddedSurface(fltTr,90,0,10,1);

    GutenbergRichterMagFreqDist gr = new GutenbergRichterMagFreqDist(6.5,3,0.5,6.5,7.5,1.0e14,1.0);
    System.out.println("cumRate="+(float)gr.getTotCumRate());

    Frankel02_TypeB_EqkSource src = new Frankel02_TypeB_EqkSource(gr,surface,
                                                            10.0,0.0,1,"name");
    ProbEqkRupture rup;
    for(int i=0; i< src.getNumRuptures();i++) {
      rup = src.getRupture(i);
      System.out.print("rup #"+i+":\n\tmag="+rup.getMag()+"\n\tprob="+
                          rup.getProbability()+"\n\tRup Ends: "+
                          (float)rup.getRuptureSurface().getLocation(0,0).getLatitude()+"  "+
                          (float)rup.getRuptureSurface().getLocation(0,rup.getRuptureSurface().getNumCols()-1).getLatitude()+
                          "\n\n");
    }

  }

  /**
   * It returns a list of all the locations which make up the surface for this
   * source.
   *
   * @return LocationList - List of all the locations which constitute the surface
   * of this source
   */
  public LocationList getAllSourceLocs() {
    LocationList locList = new LocationList();
    Iterator it = this.surface.getAllByRowsIterator();
    while(it.hasNext()) locList.add((Location)it.next());
    return locList;
  }

}
