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

package org.opensha.sha.earthquake.griddedForecast;

import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * <p>Title: HypoMagFreqDistAtLoc</p>
 *
 * <p>Description: This stores a list magFreqDists with associated a list of focal mechanisms 
 * (each must have the same number in the list unless the focal mech list is null).  </p>
 *
 * @author Ned Field
 * @version 1.0
 */
public class MagFreqDistsForFocalMechs implements java.io.Serializable{

  protected IncrementalMagFreqDist[] magFreqDist=null;
  protected FocalMechanism[] focalMechanism = null;

  /**
   * Class Constructor.
   * In this case the no focalMechanisms are specified.
   * @param magDist IncrementalMagFreqDist[] list of MagFreqDist.
   */
  public MagFreqDistsForFocalMechs(IncrementalMagFreqDist[] magDist) {
    magFreqDist = magDist;
    focalMechanism = null;
  }
  
  
  /**
   * Class Constructor.
   * This is for passing in a single magFreqDist (don't have to create an array) and no focal mechanism.
   * @param magDist IncrementalMagFreqDist MagFreqDist.
   */
  public MagFreqDistsForFocalMechs(IncrementalMagFreqDist magDist) {
    magFreqDist = new IncrementalMagFreqDist[1];
    magFreqDist[0] = magDist; 
    focalMechanism = null;
  }
  

  /**
   * Class constructor.
   * This constructor allows user to give a list of focalMechanisms and magDists.
   * @param magDist IncrementalMagFreqDist[] list of magFreqDist, same as number of focal mechanisms.
   * @param focalMechanism FocalMechanism[] list of focal mechanism for a given location.
   *
   */
  public MagFreqDistsForFocalMechs(IncrementalMagFreqDist[] magDist, FocalMechanism[] focalMechanism) {
    magFreqDist = magDist;
    this.focalMechanism = focalMechanism;
    if(magDist.length != focalMechanism.length)
    	throw new RuntimeException("Error - array lengths differ");
  }
  
  
  
  /**
   * Class constructor.
   * This constructor allows user to give a single magFreqDist and focalMechanism.
   * @param magDist IncrementalMagFreqDist
   * @param focalMechanism FocalMechanism
   *
   */
  public MagFreqDistsForFocalMechs(IncrementalMagFreqDist magDist, FocalMechanism focalMechanism) {
	  IncrementalMagFreqDist[] magDistArray = new IncrementalMagFreqDist[1];
	  magDistArray[0] = magDist;
	  FocalMechanism[] focalMechanismArray = new FocalMechanism[1];
	  focalMechanismArray[0]=focalMechanism;
	  this.magFreqDist = magDistArray;
	  this.focalMechanism = focalMechanismArray;
  }
 
  



  /**
   * This constructor allows a user to give a single magDist, a list of focalMechanisms, and a list of weights.
   * The list of focal mechanisms is made by assigning the associated weight to the the given magDist.
   * @param magDist an IncrementalMagFreqDist.
   * @param focalMechanism FocalMechanism[] list of focal mechanism for a given location.
   * @param wts - a list os weights that must be in the same order as FocalMechanism[].
   *
   */
  public MagFreqDistsForFocalMechs(IncrementalMagFreqDist magDist, FocalMechanism[] focalMechanism, double[] wt) {
    if(wt.length != focalMechanism.length)
    	throw new RuntimeException("Error - array lengths differ");
    this.focalMechanism = focalMechanism;
    magFreqDist = new IncrementalMagFreqDist[focalMechanism.length];
    double totRate = magDist.getTotalIncrRate();
    IncrementalMagFreqDist newMagDist;
    for(int i=0;i<focalMechanism.length; i++) {
    	newMagDist = magDist.deepClone();
    	newMagDist.scaleToCumRate(0, totRate*wt[i]);
    	magFreqDist[i]=newMagDist;
    }
  }

  /**
   * Returns the list of Focal Mechanism.
   * @return FocalMechanism[]
   */
  public FocalMechanism[] getFocalMechanismList() {
    return focalMechanism;
  }

  /**
   * Returns the list of MagFreqDists.
   * @return IncrementalMagFreqDist[]
   */
  public IncrementalMagFreqDist[] getMagFreqDistList() {
    return magFreqDist;
  }
  
  public int getNumMagFreqDists() {
	  return magFreqDist.length;
  }
  
  public int getNumFocalMechs() {
	  return focalMechanism.length;
  }
  
  public IncrementalMagFreqDist getMagFreqDist(int index){
	return magFreqDist[index];
  }
  
  public FocalMechanism getFocalMech(int index){
	return focalMechanism[index];
  }

  /**
   * Returns the first MagFreqDist from the list.
   * This function can be used when there are not multiple MagFreqDists and no Focal Mechanism, 
   * @return IncrementalMagFreqDist
   */
  public IncrementalMagFreqDist getFirstMagFreqDist(){
	return magFreqDist[0];
  }

  /**
   * Returns the first MagFreqDist from the list.
   * This function can be used when there are not multiple MagFreqDists and no Focal Mechanism, 
   * @return IncrementalMagFreqDist
   */
  public FocalMechanism getFirstFocalMech(){
	return focalMechanism[0];
  }
}
