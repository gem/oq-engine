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

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * <p>Title: PointEqkSource </p>
 * <p>Description: This makes a point source based on the inputs of the various constructors:</p>
 * </UL><p>
 *
 * If an IncrementalMagFreqDist (or HypoMagFreqDistAtLoc) and duration have been given, 
 * then the source is Poissonian and it is assumed that the duration units are the same
 * as those for the rates in the IncrementalMagFreqDist.  Also, magnitudes below the minimum
 * are ignored, as are those with zero rates.  If magnitude/probability have
 * been given, the source has only one rupture and is not Poissonian.</p>
 *
 * @author Edward Field
 * @version 1.0
 */

public class PointEqkSource extends ProbEqkSource implements java.io.Serializable{

  //for Debug purposes
  private static String  C = new String("PointEqkSource");
  private static String NAME = "Point Eqk Source";
  private boolean D = false;

  private Location location;
  private double aveDip=Double.NaN;
  private double aveRake=Double.NaN;
  private double duration=Double.NaN;
  private double minMag = Double.NaN;

  // to hold the non-zero mags and rates
  private ArrayList<Double> mags, rates, rakes, dips;
  private boolean variableDepthRakeAndDip = false;
  private ArbitrarilyDiscretizedFunc aveRupTopVersusMag;
  private double defaultHypoDepth;


  /**
   * Constructor specifying the Location, the IncrementalMagFreqDist, the duration,
   * the average rake, the dip, and the minimum magnitude to consider from the magFreqDist
   * in making the source (those below are ingored).  The source is set as Poissonian
   * with this constructor.
   *
   */
  public PointEqkSource(Location loc, IncrementalMagFreqDist magFreqDist,double duration,
                        double aveRake, double aveDip, double minMag){
    this.location =loc;
    this.duration=duration;
    this.aveRake=aveRake;
    this.aveDip=aveDip;
    this.minMag=minMag;

    // set the magFreqDist
    setMagsAndRates(magFreqDist);

    isPoissonian = true;

    // make the prob qk rupture
    probEqkRupture = new ProbEqkRupture();
    probEqkRupture.setPointSurface(location, aveDip);
    probEqkRupture.setAveRake(aveRake);
    /*if( D ) System.out.println("PointEqkSource Constructor: totNumRups="+magsAndRates.getNum()+
                               "; aveDip="+probEqkRupture.getRuptureSurface().getAveDip()+
                               "; aveRake="+ probEqkRupture.getAveRake());*/
  }


  /**
   * Constructor specifying the location, the IncrementalMagFreqDist, the duration,
   * the average rake, and the dip.  This sets minMag to zero (magnitudes from magFreqDist
   * below are ignored in making the source). The source is set as Poissonian with this constructor.
   *
   */
  public PointEqkSource(Location loc, IncrementalMagFreqDist magFreqDist,double duration,
                        double aveRake, double aveDip){
    this( loc,  magFreqDist, duration, aveRake,  aveDip, 0.0);

  }

  


  /**
   * This constructor takes a HypoMagFreqDistAtLoc object, depth as a function of mag (aveRupTopVersusMag), 
   * and a default depth (defaultHypoDepth).  The depth of each point source is set according to the
   * mag using the aveRupTopVersusMag function; if mag is below the minimum x value of this function,
   * then defaultHypoDepth is applied.  Note that the depth value in HypoMagFreqDistAtLoc.getLocation()
   * is ignored here (that location is cloned here and the depth is overwritten).  This sets the source as
   * Poissonian
   */
  public PointEqkSource(HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc,
			ArbitrarilyDiscretizedFunc aveRupTopVersusMag, double defaultHypoDepth,
			double duration, double minMag){
    this.aveRupTopVersusMag = aveRupTopVersusMag;
    this.defaultHypoDepth = defaultHypoDepth;
    this.duration = duration;
    this.minMag = minMag;
    this.isPoissonian = true;
    this.location = hypoMagFreqDistAtLoc.getLocation().clone();
    this.setAll(hypoMagFreqDistAtLoc);
    this.variableDepthRakeAndDip = true;
    probEqkRupture = new ProbEqkRupture();

  }


  /**
   * Constructor specifying the location, a magnitude and probability,
   * the average rake, and the dip.  The source is set as Poissonian with this
   * constructor.
   *
   */
  public PointEqkSource(Location loc, double magnitude,double probability,
                        double aveRake, double aveDip){
    this.location =loc;
    this.aveRake=aveRake;
    this.aveDip=aveDip;

    // add the one magnitude to the mags list
    mags = new ArrayList();
    mags.add(new Double(magnitude));

    this.isPoissonian = false;

    // make the prob qk rupture
    probEqkRupture = new ProbEqkRupture();
    probEqkRupture.setPointSurface(location, aveDip);
    probEqkRupture.setAveRake(aveRake);
    probEqkRupture.setProbability(probability);
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
   locList.add(this.location);
   return locList;
 }
 
 public EvenlyGriddedSurfaceAPI getSourceSurface() { return probEqkRupture.getRuptureSurface(); }


 /**
  * This creates the lists of mags and non-zero rates (above minMag).
  * @param magFreqDist
  */
 private void setAll(HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc) {

	 // make list of non-zero rates and mags (if mag >= minMag)
	 mags = new ArrayList();
	 rates = new ArrayList();
	 rakes = new ArrayList();
	 dips = new ArrayList();
	 IncrementalMagFreqDist[] magFreqDists = hypoMagFreqDistAtLoc.getMagFreqDistList();
	 FocalMechanism[] focalMechanisms = hypoMagFreqDistAtLoc.getFocalMechanismList();
	 for (int i=0; i<magFreqDists.length; i++) {
		 FocalMechanism focalMech = focalMechanisms[i];
		 IncrementalMagFreqDist magFreqDist = magFreqDists[i];
		 for (int m=0; m<magFreqDist.getNum(); m++){
			 if(magFreqDist.getY(m) > 0 && magFreqDist.getX(m) >= minMag){
				 mags.add(new Double(magFreqDist.getX(m)));
				 rates.add(new Double(magFreqDist.getY(m)));
				 rakes.add(new Double(focalMech.getRake()));
				 dips.add(new Double(focalMech.getDip()));
			 }
		 }
	 }
 }


  /**
   * This creates the lists of mags and non-zero rates (above minMag).
   * @param magFreqDist
   */
  private void setMagsAndRates(IncrementalMagFreqDist magFreqDist) {

    // make list of non-zero rates and mags (if mag >= minMag)
    //magsAndRates = new ArbitrarilyDiscretizedFunc();
    mags = new ArrayList();
    rates = new ArrayList();
    for (int i=0; i<magFreqDist.getNum(); ++i){
        if(magFreqDist.getY(i) > 0 && magFreqDist.getX(i) >= minMag){
          mags.add(new Double(magFreqDist.getX(i)));
          rates.add(new Double(magFreqDist.getY(i)));
        }
    }

   // if (D) System.out.println(C+" numNonZeroMagDistPoints="+magsAndRates.getNum());
  }


  /**
   * @return the number of rutures (equals number of mags with non-zero rates)
   */
  public int getNumRuptures() {
    return mags.size();
  }


  /**
   * This makes and returns the nth probEqkRupture for this source.
   */
  public ProbEqkRupture getRupture(int nthRupture){

    // set the magnitude
	double mag = mags.get(nthRupture).doubleValue();
    probEqkRupture.setMag(mag);

    // set the probability if it's Poissonian (otherwise this was already set)
    if(isPoissonian)
      probEqkRupture.setProbability(1 - Math.exp(-duration*((Double)rates.get(nthRupture)).doubleValue()));

    // set the rake, depth, and dip if necessary
    if(variableDepthRakeAndDip) {
    	probEqkRupture.setAveRake(rakes.get(nthRupture).doubleValue());
    	double depth;
    	if(mag < this.aveRupTopVersusMag.getMinX())
    		depth = this.defaultHypoDepth;
    	else
    		depth = aveRupTopVersusMag.getClosestY(mag);
//    	location.setDepth(depth);
    	location = new Location(
    			location.getLatitude(), location.getLongitude(), depth);
    	probEqkRupture.setPointSurface(location, dips.get(nthRupture).doubleValue());
    }
    
    // return the ProbEqkRupture
    return probEqkRupture;
  }


  /**
   * This sets the duration used in computing Poisson probabilities.  This assumes
   * the same units as in the magFreqDist rates.  This is ignored if the source in non-Poissonian.
   * @param duration
   */
  public void setDuration(double duration) {
    this.duration=duration;
  }


  /**
  * This gets the duration used in computing Poisson probabilities (it may be NaN
  * if the source is not Poissonian).
  * @param duration
  */
  public double getDuration() {
    return duration;
  }


  /**
   * This sets the location
   * @param loc
   */
  public void setLocation(Location loc) {
	  if(!variableDepthRakeAndDip) {
		    location = loc;
		    probEqkRupture.setPointSurface(location, aveDip);		  
	  }
	  else
		  throw new RuntimeException(C+"-- Error - can't set Location when variableDepthRakeAndDip = true");
  }

  /**
   * This gets the location
   * @return Location
   */
  public Location getLocation(){
    return location;
  }

  /**
   * This gets the minimum magnitude to be considered from the mag-freq dist (those
   * below are ignored in making the source).  This will be NaN if the source is not
   * Poissonian.
   * @return minMag
   */
  public double getMinMag(){
    return minMag;
  }


     /**
   * This returns the shortest horizontal dist to the point source.
   * @param site
   * @return minimum distance
   */
   public  double getMinDistance(Site site) {
      return LocationUtils.horzDistance(site.getLocation(), location);
    }

 /**
  * get the name of this class
  *
  * @return
  */
 public String getName() {
   return C;
  }
}
