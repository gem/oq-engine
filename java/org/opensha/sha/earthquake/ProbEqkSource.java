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

package org.opensha.sha.earthquake;

import java.util.ArrayList;
import java.util.Iterator;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.imr.param.OtherParams.TectonicRegionTypeParam;
import org.opensha.sha.util.TectonicRegionType;
/**
 * <p>Title: ProbEqkSource</p>
 * <p>Description: Class for Probabilistic earthquake source.
 * Note that the tectonicRegionType must be one of the options given by the TYPE_* options in the class
 * org.opensha.sha.imr.param.OtherParams.TectonicRegionTypeParam, and the default here is the
 * TYPE_ACTIVE_SHALLOW option in that class.  Subclasses must override this in the constructor,
 *  or users can change the value using the setTectonicRegion() method here.</p>
 *
 * @author Ned Field, Nitin Gupta, Vipin Gupta
 * @date Aug 27, 2002
 * @version 1.0
 */

public abstract class ProbEqkSource implements EqkSourceAPI, NamedObjectAPI {

  /**
   * Name of this class
   */
  protected String name = new String("ProbEqkSource");
  
  // This represents the tectonic region type for this source (as well as the default)
  private TectonicRegionType tectonicRegionType = TectonicRegionType.ACTIVE_SHALLOW;


  /**
   * This is private variable which saves a earthquake rupture
   */
  protected ProbEqkRupture probEqkRupture;

  //index of the source as defined by the Earthquake Rupture Forecast
  private int sourceIndex;


  /**
   * This boolean tells whether the source is Poissonian, which will influence the
   * calculation sequence in the HazardCurveCalculator.  Note that the default value
   * is true, so non-Poissonian sources will need to overide this value.
   */
  protected boolean isPoissonian = true;

  /**
   * string to save the information about this source
   */
  private String info;


  /**
   * This method tells whether the source is Poissonian, which will influence the
   * calculation sequence in the HazardCurveCalculator
   */
  public boolean isSourcePoissonian() {
    return isPoissonian;
  }

  /**
   * Get the iterator over all ruptures
   * This function returns the iterator for the rupturelist after calling the method getRuptureList()
   * @return the iterator object for the RuptureList
   */
  public Iterator getRupturesIterator() {
   ArrayList v= getRuptureList();
   return v.iterator();
  }


  /**
   * Checks if the source is Poission.
   * @return boolean
   */
  public boolean isPoissonianSource(){
    return isPoissonian;
  }

  /**
   * This computes some measure of the minimum distance between the source and
   * the site passed in.  This is useful for ignoring sources that are at great
   * distanced from a site of interest.  Actual implementation depend on subclass.
   * @param site
   * @return minimum distance
   */
  public abstract double getMinDistance(Site site);

  /**
   * Get the number of ruptures for this source
   *
   * @return returns an integer value specifying the number of ruptures for this source
   */
  public abstract int getNumRuptures() ;

  /**
   * Get the ith rupture for this source
   * This is a handle(or reference) to existing class variable. If this function
   *  is called again, then output from previous function call will not remain valid
   *  because of passing by reference
   * It is a secret, fast but dangerous method
   *
   * @param i  ith rupture
   */
  public abstract ProbEqkRupture getRupture(int nRupture);


  /**
   * this function can be used if a clone is wanted instead of handle to class variable
   * Subsequent calls to this function will not affect the result got previously.
   * This is in contrast with the getRupture(int i) function
   *
   * @param nRupture
   * @return the clone of the probEqkRupture
   */
  public ProbEqkRupture getRuptureClone(int nRupture){
    ProbEqkRupture eqkRupture =getRupture(nRupture);
    ProbEqkRupture eqkRuptureClone= (ProbEqkRupture)eqkRupture.clone();
    return eqkRuptureClone;
  }

  /**
   * Returns the ArrayList consisting of all ruptures for this source
   * all the objects are cloned. so this vector can be saved by the user
   *
   * @return ArrayList consisting of the rupture clones
   */
  public ArrayList getRuptureList() {
    ArrayList v= new ArrayList();
    for(int i=0; i<getNumRuptures();i++)
      v.add(getRuptureClone(i));
    return v;
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
   * Set the info for this Prob Eqk source
   * @param infoString : Info
   * @return
   */
  public void setInfo(String infoString) {
    this.info = new String(infoString);
  }

  /**
   * Get the info for this source
   *
   * @return
   */
  public String getInfo() {
    return info;
  }


  /**
   * Returns the Source Metadata.
   * Source Metadata provides info. about the following :
   * <ul>
   * <li>source index - As defined in ERF
   * <li>Num of Ruptures  in the given source
   * <li>Is source poisson - true or false
   * <li>Total Prob. of the source
   * <li>Name of the source
   * </ul>
   * All this source info is represented as String in one line with each element
   * seperated by a tab ("\t").
   * @return String
   */
  public String getSourceMetadata() {
    //source Metadata
    String sourceMetadata;
    sourceMetadata = sourceIndex+"\t";
    sourceMetadata += getNumRuptures()+"\t";
    sourceMetadata += isPoissonian+"\t";
    sourceMetadata += (float)computeTotalProb()+"\t";
    sourceMetadata += "\""+getName()+"\"";
    return sourceMetadata;
  }



  /**
   * This computes the total probability for this source
   * (a sum of the probabilities of all the ruptures)
   * @return
   */
  public double computeTotalProb() {
    return computeTotalProbAbove(-10.0);
  }


  /**
 * This computes the total probability of all rutures great than or equal to the
 * given mangitude
 * @return
 */
  public double computeTotalProbAbove(double mag) {
	  return computeTotalProbAbove( mag, null);
  }
  
  /**
   * This computes the Approx total probability of all ruptures great than or equal to the
   * given mangitude.
   * It checks the 2 end points of the rupture to see whether the rupture lies within region
   * If both points are within region, rupture is assumed to be in region
   * 
   * @return
   */
  public double computeApproxTotalProbAbove(double mag,Region region) {
	  double totProb=0;
	  ProbEqkRupture tempRup;
	  for(int i=0; i<getNumRuptures(); i++) {
		  tempRup = getRupture(i);
		  if(tempRup.getMag() < mag) continue;
		  totProb+=getApproxRupProbWithinRegion(tempRup, region);
	  }
	  if(isPoissonian)
		  return 1 - Math.exp(totProb);
	  else
		  return totProb;
  }
  
  /**
   * This computes the total probability of all rutures great than or equal to the
   * given mangitude
   * @return
   */
  public double computeTotalProbAbove(double mag,Region region) {
	  double totProb=0;
	  ProbEqkRupture tempRup;
	  for(int i=0; i<getNumRuptures(); i++) {
		  tempRup = getRupture(i);
		  if(tempRup.getMag() < mag) continue;
		  totProb+=getRupProbWithinRegion(tempRup, region);
	  }
	  if(isPoissonian)
		  return 1 - Math.exp(totProb);
	  else
		  return totProb;
  }
  
  /**
   * Get rupture probability within a region. It finds the fraction of rupture surface points 
   * within the region and then adjusts the probability accordingly.
   * 
   * @param tempRup
   * @param region
   * @return
   */
  private double getRupProbWithinRegion(ProbEqkRupture tempRup, Region region) {
	  int numLocsInside = 0;
	  int totPoints = 0;
	  if(region!=null) {
		  // get num surface points inside region
		  Iterator locIt = tempRup.getRuptureSurface().getLocationsIterator();
		  while(locIt.hasNext()) {
			  if(region.contains((Location)locIt.next())) ++numLocsInside;
			  ++totPoints;
		  }
	  } else {
		  numLocsInside=1;
		  totPoints = numLocsInside;
	  }
	  if(isPoissonian)
		  return Math.log(1-tempRup.getProbability()*numLocsInside/(double)totPoints);
	  else
		  return tempRup.getProbability()*numLocsInside/(double)totPoints;
  }
  
  /**
   * Get rupture probability within a region. 
   * It first checks whether the end points are within region. If yes,
   * then rupture is considered within the region
   * Else It finds the fraction of rupture FAULT TRACE (not the surface) points 
   * within the region and then adjusts the probability accordingly.
   * 
   * 
   * @param tempRup
   * @param region
   * @return
   */
  private double getApproxRupProbWithinRegion(ProbEqkRupture tempRup, Region region) {
	  int numLocsInside = 0;
	  int totPoints = 0;
	  if(region!=null) {
		  // get num surface points inside region
		  EvenlyGriddedSurfaceAPI rupSurface = tempRup.getRuptureSurface();
		  Location loc1 = rupSurface.getLocation(0, 0);
		  Location loc2 = rupSurface.getLocation(0, rupSurface.getNumCols()-1);
		  // if both surface points are within region, rupture is considered within region
		  if(region.contains(loc1) && region.contains(loc2)) {
			  numLocsInside=1;
			  totPoints = numLocsInside;
		  } else { // if both points are not within region, calculate rupProb
			  Iterator locIt =	rupSurface.getColumnIterator(0);
			  while(locIt.hasNext()) {
				  if(region.contains((Location)locIt.next())) ++numLocsInside;
				  ++totPoints;
			  }
		  }
	  } else {
		  numLocsInside=1;
		  totPoints = numLocsInside;
	  }
	  if(isPoissonian)
		  return Math.log(1-tempRup.getProbability()*numLocsInside/(double)totPoints);
	  else
		  return tempRup.getProbability()*numLocsInside/(double)totPoints;
  }

  /**
   * This draws a random list of ruptures.  Non-poisson sources are not yet implemented
   * @return
   */
  public ArrayList<ProbEqkRupture> drawRandomEqkRuptures() {
	  ArrayList<ProbEqkRupture> rupList = new ArrayList();
//	  System.out.println("New Rupture")
	  if(isPoissonian) {
		  for(int r=0; r<getNumRuptures();r++) {
			  ProbEqkRupture rup = getRupture(r);
//			  if(rup.getProbability() > 0.99) System.out.println("Problem!");
			  double expected = -Math.log(1-rup.getProbability());
//			  double rand = 0.99;
			  double rand = Math.random();
			  double sum =0;
			  double factoral = 1;
			  int maxNum = (int) Math.round(10*expected)+2;
			  int num;
			  for(num=0; num <maxNum; num++) {
				  if(num != 0) factoral *= num;
				  double prob = Math.pow(expected, num)*Math.exp(-expected)/factoral;
				  sum += prob;
				  if(rand <= sum) break;
			  }
			  for(int i=0;i<num;i++) rupList.add((ProbEqkRupture)rup.clone());
/*			  if(num >0)
				  System.out.println("expected="+expected+"\t"+
					  "rand="+rand+"\t"+
					  "num="+num+"\t"+
					  "mag="+rup.getMag());
*/			  
		  }
	  }
	  else
		  throw new RuntimeException("drawRandomEqkRuptures(): Non poissonsources are not yet supported");
	  return rupList;
  }
  
  /**
   * This gets the TectonicRegionType for this source
   */
  public TectonicRegionType getTectonicRegionType() {
	  return tectonicRegionType;
  }
  
  
  /**
   * This allows one to change the default tectonic-region type.  The value must be one of those
   * defined by the TYPE_* fields of the class org.opensha.sha.imr.param.OtherParams.TectonicRegionTypeParam.
   * @param tectonicRegionType
   */
  public void setTectonicRegionType(TectonicRegionType tectonicRegionType) {
		  this.tectonicRegionType=tectonicRegionType;
  }


/*
  public IncrementalMagFreqDist computeMagProbDist() {

    ArbDiscrEmpiricalDistFunc distFunc = new ArbDiscrEmpiricalDistFunc();
    ArbitrarilyDiscretizedFunc tempFunc = new ArbitrarilyDiscretizedFunc();
    IncrementalMagFreqDist magFreqDist = null;

    ProbEqkRupture qkRup;
    for(int i=0; i<getNumRuptures(); i++) {
      qkRup = getRupture(i);
      distFunc.set(qkRup.getMag(),qkRup.getProbability());
    }
    // duplicate the distFunce
    for(int i = 0; i < distFunc.getNum(); i++) tempFunc.set(distFunc.get(i));

    // now get the cum dist
    for(int i=tempFunc.getNum()-2; i >=0; i--)
      tempFunc.set(tempFunc.getX(i),tempFunc.getY(i)+tempFunc.getY(i+1));

    // now make the evenly discretized

for(int i = 0; i < distFunc.getNum(); i++)
      System.out.println((float)distFunc.getX(i)+"  "+(float)tempFunc.getX(i)+"  "+(float)distFunc.getY(i)+"  "+(float)tempFunc.getY(i));

    return magFreqDist;
  }
*/
}
