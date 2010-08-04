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

import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.MagLengthRelationship;
import org.opensha.commons.calc.magScalingRelations.MagScalingRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagLengthRelationship;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.FrankelGriddedSurface;

/**
 * <p>Title: Point2MultVertSS_FaultSource </p>
 * <p>Description: This converts a point source (single magnitude and probability) into many
 * vertical strike-slip finite (rake=0) ruptures.  This is basically a spinning source, but one where
 * there are multiple rupture possibilities along stike as well (the hypocenter is not constrained to
 * be at the mid point).  This is a non-Poissonian source.  The fault discretization is
 * hard wired at 1 km.   <p>
 * The rupture length is computed from the supplied magScalingRelation.
 * Note that if this is a magAreaRelationship, the rupture length is computed as the area divivded
 * by the seismogenic thickness (rupLength = area/(lowerSeisDepth-upperSeisDepth).  Thus, ruptures will
 * have strange aspect ratios for: large mag and small seismogenic thickness (long line source), or small
 * mag and typical seismogenic thickness (narrow but deep rupture).  This class does not check for the
 * resonableness of the ruptures in terms of these issues. <p>
 * @author Edward Field
 * @date Sept 1, 2004
 * @version 1.0
 */
public class Point2MultVertSS_FaultSource extends ProbEqkSource implements java.io.Serializable{

  //for Debug purposes
  private static String  C = new String("Point2MultVertSS_FaultSource");
  private boolean D = false;

  double rupLength, upperSeisDepth, lowerSeisDepth;
  private Location loc;
  private ArrayList faultTraces = new ArrayList();
  private ProbEqkRupture probEqkRupture;
  private FrankelGriddedSurface frankelFaultSurface;

  /**
   * The Constructor
   * @param lat - the latitude of the point source
   * @param lon - the longitude of the point source
   * @param magnitude - the magnitude of the source
   * @param probability - the probability of the source
   * @param magScalingRel - the magScalingRelationship used to compute rupture length
   * @param upperSeisDepth - upper seismogenic depth
   * @param lowerSeisDepth - lower seismogenic depth
   * @param rupOffset - the amount by which possible rupture surfacess are affset along each strike
   * @param deltaStrike - the discretization of the strike
   */
  public Point2MultVertSS_FaultSource(double lat, double lon, double magnitude, double probability,
                                       MagScalingRelationship magScalingRel,
                                       double upperSeisDepth, double lowerSeisDepth,
                                       double maxRupOffset, double deltaStrike){

    // make the prob qk rupture
    probEqkRupture = new ProbEqkRupture();
    probEqkRupture.setAveRake(0.0);
    probEqkRupture.setMag(magnitude);

    this.isPoissonian = false;

    this.upperSeisDepth = upperSeisDepth;
    this.lowerSeisDepth = lowerSeisDepth;

    // Compute the rupture length
    if(magScalingRel instanceof MagAreaRelationship)
      rupLength = magScalingRel.getMedianScale(magnitude)/(lowerSeisDepth-upperSeisDepth);
    else if (magScalingRel instanceof MagLengthRelationship)
      rupLength = magScalingRel.getMedianScale(magnitude);
    else throw new RuntimeException("bad type of MagScalingRelationship");

    loc = new Location(lat,lon,0.0);

    // now make the list of rupture surfaces
    mkFaultTraces(loc, rupLength, maxRupOffset, deltaStrike);
    if(D) System.out.println("num ruptures="+faultTraces.size());

    // set the probability (normalized by the number of ruptures)
    probEqkRupture.setProbability(probability/faultTraces.size());
    if(D) System.out.println("prob="+probEqkRupture.getProbability());
  }


  private void mkFaultTraces(Location loc, double rupLength, double maxDeltaRupOffset, double deltaStrike) {

    int numRupAlong = (int)(rupLength/maxDeltaRupOffset) + 2;
    double deltaRupOffset = rupLength/(double)(numRupAlong-1);  // this should be just less than maxDeltaRupOffset
    int numStrikes = (int) (180.0/deltaStrike);
    Location loc1, loc2;
    LocationVector dir;
    FaultTrace fltTrace;

    if(D) {
      System.out.println("rupLength="+rupLength+"; maxDeltaRupOffset="+maxDeltaRupOffset+
                         ";  numRupAlong="+numRupAlong+";  deltaRupOffset="+deltaRupOffset);
    }

    if (D) System.out.println("lon1\tlat1\tlon2\tlat2\tstike\toffSet");
    for(double strike=0; strike <180; strike+=deltaStrike) {
      for(double offSet=0; offSet < rupLength+deltaRupOffset/2.0; offSet += deltaRupOffset){
//        dir = new LocationVector(0.0,offSet,strike,Double.NaN);
          dir = new LocationVector(strike, offSet, 0.0);
        loc1 = LocationUtils.location(loc,dir);
//        dir = new LocationVector(0.0,rupLength-offSet,strike+180,Double.NaN);
        dir = new LocationVector(strike+180, rupLength-offSet, 0.0);
        loc2 = LocationUtils.location(loc,dir);
        fltTrace = new FaultTrace(null);
        fltTrace.add(loc1);
        fltTrace.add(loc2);
        faultTraces.add(fltTrace);
/*        if (D) System.out.println((float)loc1.getLongitude()+"\t"+(float)loc1.getLatitude()+"\t" +
                                               (float)loc2.getLongitude()+"\t"+(float)loc2.getLatitude()+"\t" +
                                               "\t"+(float)strike+"\t"+(float)offSet);
*/
      }
    }
  }


  /**
   * @return the number of rutures (equals number of mags with non-zero rates)
   */
  public int getNumRuptures() {
    //return magsAndRates.getNum();
    return faultTraces.size();
  }


  /**
   * This makes and returns the nth probEqkRupture for this source.
   */
  public ProbEqkRupture getRupture(int nthRupture){
    // set the rupture surface in the eqkRupture
    probEqkRupture.setRuptureSurface(getRuptureSurface(nthRupture));
    return probEqkRupture;
  }

  /**
   * This makes the surface for nth rupture
   * @param nthRupture
   * @return
   */
  private EvenlyGriddedSurfaceAPI getRuptureSurface(int nthRupture) {
    // set the parameters for the fault factory
    frankelFaultSurface = new FrankelGriddedSurface((FaultTrace)faultTraces.get(nthRupture),90,upperSeisDepth,lowerSeisDepth,1.0);
    return frankelFaultSurface;
  }

  /**
  * It returns a list of all the locations which make up the surface for this
  * source.
  *
  * @return LocationList - List of all the locations which constitute the surface
  * of this source
  */
  public LocationList getAllSourceLocs() {
    int numRuptures= this.getNumRuptures();
    LocationList locList = new LocationList(); //master location list
    // get location list of all possible ruptures
    for(int i=0; i<numRuptures; ++i) {
      LocationList rupLocList = getRuptureSurface(i).getLocationList();
      // add all locations in a rupture to the master location list
      for(int j=0; j<rupLocList.size(); ++j)
        locList.add(rupLocList.get(j));
    }
    return locList;
  }
  
  public EvenlyGriddedSurfaceAPI getSourceSurface() { throw new RuntimeException("method not supported (not sure what to return)"); }




     /**
   * This returns the shortest horizontal dist to the point source.
   * @param site
   * @return minimum distance
   */
   public  double getMinDistance(Site site) {
     return LocationUtils.horzDistance(site.getLocation(),loc) - rupLength;
    }

 /**
  * get the name of this class
  *
  * @return
  */
 public String getName() {
   return C;
  }

  // this is temporary for testing purposes
  public static void main(String[] args) {
    WC1994_MagLengthRelationship magLengthRel = new WC1994_MagLengthRelationship();
    WC1994_MagAreaRelationship magAreaRel = new WC1994_MagAreaRelationship();
    double mag = 7.0;
    System.out.println("Length(mag)="+magLengthRel.getMedianScale(mag)+";  Area(mag)="+magAreaRel.getMedianScale(mag));
    Point2MultVertSS_FaultSource src = new Point2MultVertSS_FaultSource(34,-118,mag,1,magLengthRel,0,10,2,5);
    System.out.println("numRuptures="+src.getNumRuptures());
    for(int r=0; r<src.getNumRuptures(); r++) {
      int lastCol = src.getRupture(r).getRuptureSurface().getNumCols()-1;
/*      System.out.println((float)src.getRupture(r).getRuptureSurface().getLocation(0,0).getLongitude()+"\t"+
                         (float)src.getRupture(r).getRuptureSurface().getLocation(0,0).getLatitude()+"\t"+
                         (float)src.getRupture(r).getRuptureSurface().getLocation(0,lastCol).getLongitude()+"\t"+
                         (float)src.getRupture(r).getRuptureSurface().getLocation(0,lastCol).getLatitude());
*/
    }
  }
}
