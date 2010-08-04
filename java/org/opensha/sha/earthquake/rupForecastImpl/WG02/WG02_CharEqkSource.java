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

import org.opensha.commons.data.Site;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.magdist.GaussianMagFreqDist;

/**
 * <p>Title: WG02_CharEqkSource</p>
 * <p>Description: Working Group 2002 characteristic earthquake source </p>
 * <p>Copyright: Copyright (c) 2003</p>
 * <p>Company: </p>
 * @author Edward Field
 * @date April, 2003
 * @version 1.0
 */

public class WG02_CharEqkSource extends ProbEqkSource {

  private double prob;
  private EvenlyGriddedSurface rupSurface;
  private String sourceName;
  private GaussianMagFreqDist gaussMagDist;
  private int numRupSurfaces, numMag;
  private double rupWidth, rupLength, rupOffset;

  /**
   * Name of this class
   */
  private String name = "WG02 Char Eqk Source";

  boolean D = false;
  private String C = "WG02_CharEqkSource";


  /**
   * Constructor for this class
   *
   * @param prob: probability of event
   * @param meanMag: Mean magnitude for the Gaussian Mag. Freq. Dist.
   * @param magSigma: Standared deviation for the Gaussian Mag. Freq. Dist.
   * @param nSigmaTrunc: Number of sigmas where trunction occurs on the Gaussian Dist.
   * @param deltaMag: The discretization interval for the Mag. Freq. Dist.
   * @param rupSurface: The rupture surface
   * @param rupArea: The rupture area (may be smaller than surface due to aseismic slip)
   * @param rupOffset: The offset length for sub-ruptures ("floating" ruptures)
   * @param rupName: The name to assign for this rupture
   * @param rake: The rake for the event
   */
  public WG02_CharEqkSource(double prob, double meanMag, double magSigma,
                            double nSigmaTrunc, double deltaMag, EvenlyGriddedSurface rupSurface,
                            double rupArea, double rupOffset, String sourceName,
                            double rake) {

      // set as a non-poissonian source
      isPoissonian = false;

      this.prob = prob;
      this.rupSurface = rupSurface;
      this.rupOffset = rupOffset;
      probEqkRupture = new ProbEqkRupture();
      probEqkRupture.setAveRake(rake);
      this.name = sourceName;

      if(D) System.out.println("prob="+prob+"; meanMag="+meanMag+"; =magSigma"+magSigma+
                               "; nSigmaTrunc="+nSigmaTrunc+"; rupArea="+rupArea+
                               "; rupOffset="+rupOffset+"; sourceName="+sourceName+
                               "; rake="+rake);

      // find the first mag increment below the cutoff
      double tempMag = ((meanMag+nSigmaTrunc*magSigma)-meanMag)/deltaMag;
      int tempNum = (int) Math.floor(tempMag);
      double maxMag = meanMag+tempNum*deltaMag;
      double minMag = meanMag-tempNum*deltaMag;
      numMag = 2*tempNum + 1;

      // make the gaussian mag freq dist & normalize to unit area
      gaussMagDist = new GaussianMagFreqDist(minMag,maxMag,numMag,meanMag,magSigma,1.0,nSigmaTrunc,2);
      gaussMagDist.scaleToCumRate(0,1.0);

      if(D) System.out.println(gaussMagDist.toString());
/*      if(D) {
        System.out.println(C+": mag  relative-prob:");
        for (int i=0;i<gaussMagDist.getNum();i++)
          System.out.println((float)gaussMagDist.getX(i)+"  "+(float)gaussMagDist.getY(i));
      }
*/
      // compute rupture width and length given the rupArea (rupArea is less than the
      // area of the fault surface (rupSurface) if the aseismic scaling factor (r) was
      // applied as a reduction of rupture area rather than slip rate)
      double faultLength = (rupSurface.getNumCols()-1)*rupSurface.getGridSpacingAlongStrike();
      double ddw = (rupSurface.getNumRows()-1)*rupSurface.getGridSpacingDownDip();
      rupWidth = Math.sqrt(rupArea);
      rupLength = rupWidth;
      // stretch it's length if the width exceeds the down dip width
      if(rupWidth > ddw) {
        rupWidth = ddw;
        rupLength = rupArea/ddw;
      }

      // get the number of rupture surfaces
      numRupSurfaces = rupSurface.getNumSubsetSurfaces(rupLength,rupWidth,rupOffset);

//      System.out.println("Name = "+sourceName+"; numMag = "+numMag+"; numRupSurfaces+"+numRupSurfaces+
//                   "; flt length = "+faultLength+"; ddw = "+ddw+"; rupArea = "+rupArea);

      if (D) System.out.println(C+ "  Name: "+sourceName);
      if (D) System.out.println(C+ " numMag, numRupSurfaces:"+numMag+"  "+numRupSurfaces);

      if(D) {
        ProbEqkRupture rup;
        double totProb=0;
//        System.out.println(C+" ruptures: 0-"+(getNumRuptures()-1));
        for (int i=0;i<getNumRuptures();i++) {
          rup = this.getRupture(i);
//          System.out.println(i+"  mag="+(float)rup.getMag()+"; prob="+(float)rup.getProbability());
          totProb += rup.getProbability();
        }
        System.out.println("  totProb="+(float)totProb);
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
    return this.rupSurface.getLocationList();
  }
  
  public EvenlyGriddedSurfaceAPI getSourceSurface() { return this.rupSurface; }




 /**
  * @return the total num of rutures for the mag which is 1 for the char type fault
  */
  public int getNumRuptures() {
   return numRupSurfaces*numMag;
 }

 /**
  * @param nRupture
  * @return the object for the ProbEqkRupture
  */
  public ProbEqkRupture getRupture(int nRupture){

    // set the mag and rupture surface indices
    int iMag = nRupture/numRupSurfaces;
    int iRupSurf = nRupture - iMag*numRupSurfaces;

    // set the magnitude
    probEqkRupture.setMag(gaussMagDist.getX(iMag));

    // set the probability (total prob * relative mag prob / num rupture subsurfaces)
    double p=prob*gaussMagDist.getIncrRate(iMag)/numRupSurfaces;
    probEqkRupture.setProbability(p);

    // now set the rupture surface as the the ith subset surface
    probEqkRupture.setRuptureSurface(rupSurface.getNthSubsetSurface(rupLength,rupWidth,rupOffset,iRupSurf));

    return probEqkRupture;
  }


  /**
   * This returns the shortest dist to either end of the fault trace, or to the
   * mid point of the fault trace.
   * @param site
   * @return minimum distance
   */
   public double getMinDistance(Site site) {

      double min;
      // get first location on fault trace
      LocationVector dir = LocationUtils.vector(site.getLocation(),(Location) rupSurface.get(0,0));
      min = dir.getHorzDistance();

      // get last location on fault trace
      dir = LocationUtils.vector(site.getLocation(), (Location) rupSurface.get(0,rupSurface.getNumCols()-1));
      if (min > dir.getHorzDistance())
          min = dir.getHorzDistance();

      // get mid location on fault trace
      dir = LocationUtils.vector(site.getLocation(), (Location) rupSurface.get(0,(int) rupSurface.getNumCols()/2));
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
