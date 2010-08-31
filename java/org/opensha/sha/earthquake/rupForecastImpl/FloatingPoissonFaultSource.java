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

import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;

import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.MagLengthRelationship;
import org.opensha.commons.calc.magScalingRelations.MagScalingRelationship;
import org.opensha.commons.data.Site;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;


/**
 * <p>Title: FloatingPoissonFaultSource </p>
 * <p>Description: This implements a basic Poisson fault source for arbitrary: <p>
 * <UL>
 * <LI>magDist - any IncrementalMagFreqDist (rate per year)
 * <LI>faultSurface - any EvenlyDiscretizedSurface
 * <LI>magScalingRel- any magLenthRelationship or magAreaRelalationship
 * <LI>magScalingSigma - the standard deviation of log(Length) or log(Area)
 * <LI>rupAspectRatio - the ratio of rupture length to rupture width (down-dip)
 * <LI>rupOffset - the amount by which ruptures are offset on the fault.
 * <LI>rake - that rake (in degrees) assigned to all ruptures.
 * <LI>minMag - the minimum magnitude to be considered from magDist (lower mags are ignored)
 * <LI>floatTypeFlag - if = 0 full down-dip width ruptures; if = 1 float both along strike and down dip; 
 *                        if = 2 float only along strike and centered down dip.
 * <LI>fullFaultRupMagThresh - magnitudes greater than or equal to this value will be forced to rupture the entire fault
 * <LI>duration - the duration of the forecast in years.
 * </UL><p>
 * 
 * Note that few of these input objects are saved internally (after construction) in
 * order to conserve memory (this is why there are no associated get/set methods for each).<p>
 * The floatTypeFlag specifies the type of floaters as described above.  For floating,
 * ruptures are placed uniformly across the fault surface (at rupOffset spacing), which
 * means there is a tapering of implied slip amounts at the ends of the fault.<p>
 * All magnitudes below minMag in the magDist are ignored in building the ruptures. <p>
 * Note that magScalingSigma can be either a MagAreaRelationship or a
 * MagLengthRelationship.  If a MagAreaRelationship is being used, and the rupture
 * width implied for a given magnitude exceeds the down-dip width of the faultSurface,
 * then the rupture length is increased accordingly and the rupture width is set as
 * the down-dip width.  If a MagLengthRelationship is being used, and the rupture
 * width implied by the rupAspectRatio exceeds the down-dip width, everything below
 * the bottom edge of the fault is simply cut off (ignored).  Thus, with a
 * MagLengthRelationship you can force rupture of the entire down-dip width by giving
 * rupAspecRatio a very small value (using floatTypeFlag=1).  The fullFaultRupMagThresh
 * value allows you to force full-fault ruptures for large mags.</p>
 * magScalingSigma is set by hand (rather than getting it from the magScalingRel) to
 * allow maximum flexibility (e.g., some relationships do not even give a sigma value).<p>
 * If magScalingSigma is non zero, then 25 branches from -3 to +3 sigma are considered 
 * for the Area or Length values (this high number was implemented to match PEER test
 * cases); the option for other numbers of branches should be added to speed things up
 * if this feature will be widely used.<p>
 * 
 * To Do: 1) generalize makeFaultCornerLocs() to work better for large surfaces; 
 * 2) clarify documentation on magSigma branches
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Ned Field
 * @date Sept, 2003
 * @version 1.0
 */


public class FloatingPoissonFaultSource extends ProbEqkSource {

	//for Debug purposes
	private static String  C = new String("FloatingPoissonFaultSource");
	private boolean D = false;

	//name for this classs
	protected String  NAME = "Floating Poisson Fault Source";

	// private fields
	private ArrayList<ProbEqkRupture> ruptureList;
		
//	private ArrayList<Location> faultCornerLocations = new ArrayList<Location>();   // used for the getMinDistance(Site) method
	private double duration;
	private EvenlyGriddedSurface faultSurface;
	
	// used for the getMinDistance(Site) method
	private Region sourceRegion;
	private LocationList sourceTrace;
	
	private double lastDuration = Double.NaN;


	/**
	 * This creates the Simple Poisson Fault Source, where a variety floating options are given
	 * by the floatTypeFlag described below. All magnitudes below minMag are given a zero probability,
	 * and all those greater than or equal to fullFaultRupMagThresh are forced to rupture the entire fault.
	 * @param magDist - any incremental mag. freq. dist. object
	 * @param faultSurface - any EvenlyGriddedSurface representation of the fault
	 * @param magScalingRel - any magAreaRelationship or magLengthRelationthip
	 * @param magScalingSigma - uncertainty of the length(mag) or area(mag) relationship
	 * @param rupAspectRatio - ratio of rupture length to rupture width
	 * @param rupOffset - amount of offset for floating ruptures in km
	 * @param rake - average rake of the ruptures
	 * @param duration - the timeSpan of interest in years (this is a Poissonian source)
	 * @param minMag - the minimum magnitude to be considered from magDist (lower mags are ignored)
	 * @param floatTypeFlag - if = 0 full down-dip width ruptures; if = 1 float both along strike and down dip; 
	 *                        if = 2 float only along strike and centered down dip.
	 * @param fullFaultRupMagThresh - magnitudes greater than or equal to this value will be forced to rupture the entire fault
	 */
	public FloatingPoissonFaultSource(IncrementalMagFreqDist magDist,
			EvenlyGriddedSurface faultSurface,
			MagScalingRelationship magScalingRel,
			double magScalingSigma,
			double rupAspectRatio,
			double rupOffset,
			double rake,
			double duration,
			double minMag,
			int floatTypeFlag,
			double fullFaultRupMagThresh) {

		this.duration = duration;
		this.faultSurface = faultSurface;

		if (D) {
			System.out.println(magDist.getName());
			System.out.println("surface rows, cols: "+faultSurface.getNumCols()+", "+faultSurface.getNumRows());
			System.out.println("magScalingRelationship: "+magScalingRel.getName());
			System.out.println("magScalingSigma: "+magScalingSigma);
			System.out.println("rupAspectRatio: "+rupAspectRatio);
			System.out.println("rupOffset: "+rupOffset);
			System.out.println("rake: "+rake);
			System.out.println("timeSpan: "+duration);
			System.out.println("minMag: "+minMag);

		}
		// make a list of a subset of locations on the fault for use in the getMinDistance(site) method
		mkApproxSourceSurface(faultSurface);

		// make the rupture list
		ruptureList = new ArrayList<ProbEqkRupture>();
		if(magScalingSigma == 0.0)
			addRupturesToList(magDist, faultSurface, magScalingRel, magScalingSigma, rupAspectRatio, rupOffset, 
					rake, minMag, 0.0, 1.0, floatTypeFlag, fullFaultRupMagThresh);
		else {
			GaussianMagFreqDist gDist = new GaussianMagFreqDist(-3.0,3.0,25,0.0,1.0,1.0);
			gDist.scaleToCumRate(0, 1.0);  // normalize to make it a probability density
			if(D) System.out.println("gDist:\n"+gDist.toString());
			for(int m=0; m<gDist.getNum(); m++) {
				addRupturesToList(magDist, faultSurface, magScalingRel, magScalingSigma,
						rupAspectRatio, rupOffset, rake, minMag, gDist.getX(m), gDist.getY(m), 
						floatTypeFlag, fullFaultRupMagThresh);
				if(D) System.out.println(m+"\t"+gDist.getX(m)+"\t"+gDist.getY(m));
			}
		}

		lastDuration = duration;
	}


	/**
	 * This constructor sets floatTypeFlag=1 and fullFaultRupMagThresh = Double.MAX_VALUE.  Otherwise it's the same.
	 */
	public FloatingPoissonFaultSource(IncrementalMagFreqDist magDist,
			EvenlyGriddedSurface faultSurface,
			MagScalingRelationship magScalingRel,
			double magScalingSigma,
			double rupAspectRatio,
			double rupOffset,
			double rake,
			double duration,
			double minMag) {
		this( magDist, faultSurface, magScalingRel,magScalingSigma,rupAspectRatio,rupOffset,rake,duration,minMag, 1,Double.MAX_VALUE);
	}


	/**
	 * This constructor sets minMag=5, floatTypeFlag=1 and 
	 * fullFaultRupMagThresh = Double.MAX_VALUE.  Otherwise it's the same.
	 */
	public FloatingPoissonFaultSource(IncrementalMagFreqDist magDist,
			EvenlyGriddedSurface faultSurface,
			MagScalingRelationship magScalingRel,
			double magScalingSigma,
			double rupAspectRatio,
			double rupOffset,
			double rake,
			double duration) {
		this( magDist, faultSurface, magScalingRel,magScalingSigma,rupAspectRatio,rupOffset,rake,duration,5.0);
	}

	/**
	 * This allows you to change the duration of the forecast
	 * @param newDuration
	 */
	public void setDuration(double newDuration) {
		for(int r=0; r<ruptureList.size(); r++) {
			ProbEqkRupture rup = ruptureList.get(r);
			double rate = rup.getMeanAnnualRate(lastDuration);
			rup.setProbability(1.0 - Math.exp(-duration*rate));
		}
		lastDuration = newDuration;
	}


	/**
	 * This computes the rupture length from the information supplied
	 * @param magScalingRel - a MagLengthRelationship or a MagAreaRelationship
	 * @param magScalingSigma - the standard deviation of the Area or Length estimate
	 * @param numSigma - the number of sigmas from the mean for which the estimate is for
	 * @param rupAspectRatio
	 * @param mag
	 * @return
	 */
	private double getRupLength(MagScalingRelationship magScalingRel,
			double magScalingSigma,
			double numSigma,
			double rupAspectRatio,
			double mag) throws RuntimeException {

		// if it's a mag-area relationship
		if(magScalingRel instanceof MagAreaRelationship) {
			double area = magScalingRel.getMedianScale(mag) * Math.pow(10,numSigma*magScalingSigma);
			return Math.sqrt(area*rupAspectRatio);
		}
		else if (magScalingRel instanceof MagLengthRelationship) {
			return magScalingRel.getMedianScale(mag) * Math.pow(10,numSigma*magScalingSigma);
		}
		else throw new RuntimeException("bad type of MagScalingRelationship");
	}



	/**
	 * This method makes and adds ruptures to the list
	 */
	private void addRupturesToList(IncrementalMagFreqDist magDist,
			EvenlyGriddedSurface faultSurface,
			MagScalingRelationship magScalingRel,
			double magScalingSigma,
			double rupAspectRatio,
			double rupOffset,
			double rake,
			double minMag,
			double numSigma,
			double weight,
			int floatTypeFlag,
			double fullFaultRupMagThresh) {


		double rupLen;
		double rupWidth;
		int numRup;
		double mag;
		double rate;
		double prob=Double.NaN;



		if( D ) System.out.println(C+": magScalingSigma="+magScalingSigma);

		// loop over magnitudes
		int numMags = magDist.getNum();
		for(int i=0;i<numMags;++i){
			mag = magDist.getX(i);
			rate = magDist.getY(i);
			// make sure it has a non-zero rate & the mag is >= minMag
			if(rate > 10E-15 && mag >= minMag) {

				// if floater
				if(mag < fullFaultRupMagThresh) {
					// get down-dip width of fault
					double ddw=faultSurface.getSurfaceWidth();

					rupLen = getRupLength(magScalingRel,magScalingSigma,numSigma,rupAspectRatio,mag);
					rupWidth= rupLen/rupAspectRatio;

					// if magScalingRel is a MagAreaRelationship, then rescale rupLen if rupWidth
					// exceeds the down-dip width (don't do anything for MagLengthRelationship)
					if(magScalingRel instanceof MagAreaRelationship  && rupWidth > ddw) {
						rupLen *= rupWidth/ddw;
						rupWidth = ddw;
					}

					// check if full down-dip rupture chosen
					if(floatTypeFlag==0)
						rupWidth = 2*ddw;  // factor of 2 more than ensures full ddw ruptures

					//System.out.println((float)mag+"\t"+(float)rupLen+"\t"+(float)rupWidth+"\t"+(float)(rupLen*rupWidth));

					// get number of ruptures depending on whether we're floating down the middle
					if(floatTypeFlag != 2)
						numRup = faultSurface.getNumSubsetSurfaces(rupLen,rupWidth,rupOffset);
					else
						numRup = faultSurface.getNumSubsetSurfacesAlongLength(rupLen, rupOffset);

					for(int r=0; r < numRup; ++r) {
						probEqkRupture = new ProbEqkRupture();
						probEqkRupture.setAveRake(rake);
						if(floatTypeFlag != 2)
							probEqkRupture.setRuptureSurface(faultSurface.getNthSubsetSurface(rupLen,rupWidth,rupOffset,r));
						else
							probEqkRupture.setRuptureSurface(faultSurface.getNthSubsetSurfaceCenteredDownDip(rupLen,rupWidth,rupOffset,r));
						probEqkRupture.setMag(mag);
						prob = (1.0 - Math.exp(-duration*weight*rate/numRup));
						probEqkRupture.setProbability(prob);
						ruptureList.add(probEqkRupture);
					}
					/*    			if( D ) System.out.println(C+": ddw="+ddw+": mag="+mag+"; rupLen="+rupLen+"; rupWidth="+rupWidth+
    					"; rate="+rate+"; timeSpan="+duration+"; numRup="+numRup+
    					"; weight="+weight+"; prob="+prob+"; floatTypeFlag="+floatTypeFlag);
					 */

				}
				// Apply full fault rupture
				else {
					probEqkRupture = new ProbEqkRupture();
					probEqkRupture.setAveRake(rake);
					probEqkRupture.setRuptureSurface(faultSurface);
					probEqkRupture.setMag(mag);
					prob = (1.0 - Math.exp(-duration*weight*rate));
					probEqkRupture.setProbability(prob);
					ruptureList.add(probEqkRupture);
				}
			}
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
		return this.faultSurface.getLocationList();
	}

	public EvenlyGriddedSurfaceAPI getSourceSurface() { return this.faultSurface; }

	/**
	 * @return the total num of rutures for all magnitudes
	 */
	public int getNumRuptures() { return ruptureList.size(); }


	/**
	 * This method returns the nth Rupture in the list
	 */
	public ProbEqkRupture getRupture(int nthRupture){ return (ProbEqkRupture) ruptureList.get(nthRupture); }


	/**
	 * This returns the shortest dist to the fault surface approximated as a region according
	 * to the corners and mid-points along strike (both on top and bottom trace).
	 * @param site
	 * @return minimum distance in km
	 */
	public  double getMinDistance(Site site) {
		if (sourceRegion != null) {
			return sourceRegion.distanceToLocation(site.getLocation());
		} else {
			return sourceTrace.minDistToLocation(site.getLocation());
		}
	}


	/**
	 * This creates an approximation of the source surface, taking the end points and mid point along
	 * strike (both on top and bottom trace).  If region creation fails (e.g. due to vertical dip) 
	 * a sourceTrace is created instead.
	 * 
	 * @param faultSurface
	 */
	private void mkApproxSourceSurface(EvenlyGriddedSurface faultSurface) {

		if(faultSurface.getAveDip() != 90) {
			int nRows = faultSurface.getNumRows();
			int nCols = faultSurface.getNumCols();
			LocationList faultCornerLocations = new LocationList();
			faultCornerLocations.add(faultSurface.getLocation(0,0));
			faultCornerLocations.add(faultSurface.getLocation(0,(int)(nCols/2)));
			faultCornerLocations.add(faultSurface.getLocation(0,nCols-1));
			faultCornerLocations.add(faultSurface.getLocation(nRows-1,nCols-1));
			faultCornerLocations.add(faultSurface.getLocation(nRows-1,(int)(nCols/2)));
			faultCornerLocations.add(faultSurface.getLocation(nRows-1,0));
			try {
				sourceRegion = new Region(faultCornerLocations,BorderType.GREAT_CIRCLE);
			} catch (IllegalArgumentException iae) {
			}
		}
		else {
			Iterator it = faultSurface.getColumnIterator(0);
			sourceTrace = new LocationList();
			while (it.hasNext())
				sourceTrace.add((Location) it.next());
		}
	}
	

	/**
	 * set the name of this class
	 *
	 * @return
	 */
	public void setName(String name) {
		NAME=name;
	}

	/**
	 * get the name of this class
	 *
	 * @return
	 */
	public String getName() {
		return NAME;
	}
}
