package org.opensha.sha.earthquake.rupForecastImpl;

import java.util.ArrayList;

import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.MagLengthRelationship;
import org.opensha.commons.calc.magScalingRelations.MagScalingRelationship;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.PointEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * <p>Title: PoissonAreaSource </p>
 * <p>Description: This is basically a more sophisticated version of the class GriddedRegionPoissonEqkSource. 
 * The options to account for the finiteness of rupture surfaces are the same as provided in the <code>PointToLineSource</code>
 * class, plus the option to treat all sources as point sources is added included here. </p>
 * 
 * @author Marco Pagani and Edward Field
 * @version 1.0
 */

public class PoissonAreaSource extends PointToLineSource implements java.io.Serializable{

	private static final long serialVersionUID = 1L;
	// for Debug purposes
	private static String C = new String("PoissonAreaSource");
	private static String NAME = "Poisson Area Source";
	private boolean D = false;

	Region reg;
	double gridResolution;
	GriddedRegion gridReg;
	boolean pointSources = false;
	double[] nodeWeights;


	/**
	 * This constructor treats all ruptures as point sources.
	 * @param reg
	 * @param gridResolution
	 * @param magFreqDistsForFocalMechs
	 * @param aveRupTopVersusMag
	 * @param defaultHypoDepth
	 * @param duration
	 * @param minMag
	 */
	public PoissonAreaSource(Region reg, double gridResolution, MagFreqDistsForFocalMechs 
			magFreqDistsForFocalMechs, ArbitrarilyDiscretizedFunc aveRupTopVersusMag, 
			double defaultHypoDepth, double duration, double minMag) {
		
		this.magFreqDists = magFreqDistsForFocalMechs.getMagFreqDistList();
		this.focalMechanisms = magFreqDistsForFocalMechs.getFocalMechanismList();
		this.aveRupTopVersusMag = aveRupTopVersusMag;
		this.defaultHypoDepth = defaultHypoDepth;
		this.duration = duration;
		this.minMag = minMag;
		this.reg = reg;

		this.isPoissonian = true;
		
		pointSources=true;
		
		checkFocalMechs();  // need to do this before calling computeMaxLength()
		
		// Compute maxLength needed for the getMinDistance(Site) method, so this can be computed before ruptures are generated
		this.maxLength = 0.0;
		
		// Region discretization
		gridReg = new GriddedRegion(reg,gridResolution,null); 
		
		numRuptures = this.computeNumRuptures()*gridReg.getNodeCount();

	}
	
	
	/**
	 * This computes the weight for each node as one over the total number of nodes
	 * multiplied by the area of the node (which changes with lat), and then renormalized
	 */
	private void computeNodeWeights() {
		int numPts = gridReg.getNodeCount();
		nodeWeights = new double[numPts];
		double tot=0;
		for(int i=0;i<numPts;i++) {
			double latitude = gridReg.locationForIndex(i).getLatitude();
			nodeWeights[i] = Math.cos(latitude*Math.PI/180);
			tot += nodeWeights[i];
		}
		for(int i=0;i<numPts;i++) nodeWeights[i] /= (tot*numPts);
	}
	
	/*
	private void setScaledMFD() {
		
		IncrementalMagFreqDist[] magFreqDistsScld = new IncrementalMagFreqDist[totMagFreqDists.length];
		// Scale the MagFreqDist 
		for (int i=0; i<totMagFreqDists.length; i++) {
			IncrementalMagFreqDist tmpDst = totMagFreqDists[i].deepClone();
			for (int j=0; j < totMagFreqDists[i].getNum(); j++){
				double tmpX = totMagFreqDists[i].getX(j);
				double tmpY = totMagFreqDists[i].getY(j)/gridReg.getNodeCount();
				tmpDst.set(tmpX,tmpY);
			}
			magFreqDistsScld[i] = tmpDst;
			
			if (D){
				for (int j=0; j < magFreqDistsScld[i].getNum(); j++){
					System.out.printf(" %5.2f %6.3f\n",magFreqDistsScld[i].getX(j),
							magFreqDistsScld[i].getY(j));
				}
			}
		}
		this.magFreqDists=magFreqDistsScld;
	}
	*/
	
	
	/**
	 * Sets default focal mechanisms if that passed in was null
	 */
	private void checkFocalMechs() {
		
		// Define the focal mechanism array if it's null
		if (focalMechanisms == null){
			focalMechanisms = new FocalMechanism[magFreqDists.length];	
			// TODO fix the default	properties of the focal mechanism	
			for (int i=0; i<magFreqDists.length; i++) {
				focalMechanisms[i] = new FocalMechanism(Double.NaN,90.0,0);
			}
		}

	}
	
	private void mkAllRuptures() {

		probEqkRuptureList = new ArrayList<ProbEqkRupture>();
		rates = new ArrayList<Double>();

		// computes the node wts (including fact that area changes with latitude)
		computeNodeWeights();

		// If they are point sources
		if(pointSources) {
			for (int j=0; j<gridReg.getNodeCount(); j++){	
				Location loc = gridReg.getNodeList().get(j);
				for (int k=0; k < magFreqDists.length; k++){
					IncrementalMagFreqDist mfd = magFreqDists[k];
					for (int w=0; w < mfd.getNum(); w++){
						double mag = mfd.getX(w);
						double rate = mfd.getY(w)*nodeWeights[j];
						double prob = 1.0 - Math.exp(-duration*(rate));
						if(mag >= minMag && prob > 0) {
							ProbEqkRupture rup = new ProbEqkRupture();
							rup.setMag(mag);
							rup.setProbability(prob);
							rup.setAveRake(focalMechanisms[k].getRake());
							double depth;
							if(mag < aveRupTopVersusMag.getMinX())
								depth = defaultHypoDepth;
							else
								depth = aveRupTopVersusMag.getClosestY(mag);
							Location finalLoc = new Location(
									loc.getLatitude(), loc.getLongitude(), depth);
							rup.setPointSurface(finalLoc,focalMechanisms[k].getDip());

							// Adding the rupture 
							probEqkRuptureList.add(rup);
							rates.add(rate);
						}
					}
				}	
			}
		}
		else {	// non-point source

			for (int j=0; j<gridReg.getNodeCount(); j++){
				location = gridReg.getNodeList().get(j);
				if(numStrikes == -1) { // random or applied strike
					for (int i=0; i<magFreqDists.length; i++) {
						mkAndAddRuptures(location, magFreqDists[i], focalMechanisms[i], aveRupTopVersusMag, defaultHypoDepth, 
								magScalingRel, lowerSeisDepth, duration, minMag, nodeWeights[j]);
					}			
				}
				else {	// spoked source
					// set the strikes
					double deltaStrike = 180/numStrikes;
					double[] strike = new double[numStrikes];
					for(int n=0;n<numStrikes;n++)
						strike[n]=firstStrike+n*deltaStrike;
					double weight = nodeWeights[j]/numStrikes;
					for (int i=0; i<magFreqDists.length; i++) {
						FocalMechanism focalMech = focalMechanisms[i].copy(); // COPY THIS
						for(int s=0;s<numStrikes;s++) {
							focalMech.setStrike(strike[s]);
							mkAndAddRuptures(location, magFreqDists[i], focalMech, aveRupTopVersusMag, defaultHypoDepth, 
									magScalingRel, lowerSeisDepth, duration, minMag,weight);			  
						}
					}			
				}
			}

		}

		// check num ruptures
		if(numRuptures != probEqkRuptureList.size())
			throw new RuntimeException("Error in computing number of ruptures");

	}
	
	/**
	 * This makes and returns the nth probEqkRupture for this source.
	 */
	public ProbEqkRupture getRupture(int nthRupture){
		if(probEqkRuptureList == null) mkAllRuptures();
		return probEqkRuptureList.get(nthRupture);
	}

		
	/**
	 * This constructor takes a Region, grid resolution (grid spacing), MagFreqDistsForFocalMechs, 
	 * depth as a function of mag (aveRupTopVersusMag), and a default depth (defaultHypoDepth).  
	 * The depth of each source is set according to the mag using the aveRupTopVersusMag function; 
	 * if mag is below the minimum x value of this function, then defaultHypoDepth is applied.  
	 * The FocalMechanism of MagFreqDistsForFocalMechs is applied, and a random strike is applied 
	 * if the associated strike is NaN (a different random value for each and every rupture).  
	 * This sets the source as Poissonian. 
	 */
	public PoissonAreaSource(Region reg, double gridResolution, MagFreqDistsForFocalMechs 
			magFreqDistsForFocalMechs, ArbitrarilyDiscretizedFunc aveRupTopVersusMag, 
			double defaultHypoDepth, MagScalingRelationship magScalingRel, double lowerSeisDepth, 
			double duration, double minMag) {
		
		// call the other constructor setting numStrikes to -1.
		this(reg, gridResolution, magFreqDistsForFocalMechs, aveRupTopVersusMag, defaultHypoDepth, 
				magScalingRel, lowerSeisDepth, duration, minMag, -1, Double.NaN);
		
	}
	

	/**
	 * This constructor is the same as the previous one, but rather than using the given or a 
	 * random strike, this applies a spoked source where several strikes are applied with even  
	 * spacing in azimuth. numStrikes defines the number of strikes applied (e.g., numStrikes=2 
	 * would be a cross hair) and firstStrike defines the azimuth of the first one (e.g., 
	 * firstStrike=0 with numStrikes=2 would be a cross-hair source that is perfectly aligned NS 
	 * and EW).
	 */
	public PoissonAreaSource(Region reg, double gridResolution, MagFreqDistsForFocalMechs 
			magFreqDistsForFocalMechs, ArbitrarilyDiscretizedFunc aveRupTopVersusMag, 
			double defaultHypoDepth, MagScalingRelationship magScalingRel, double lowerSeisDepth, 
			double duration, double minMag, int numStrikes, double firstStrike){
		
		this.reg = reg;
		this.magFreqDists = magFreqDistsForFocalMechs.getMagFreqDistList();
		this.focalMechanisms = magFreqDistsForFocalMechs.getFocalMechanismList();
		this.aveRupTopVersusMag = aveRupTopVersusMag;
		this.defaultHypoDepth = defaultHypoDepth;
		this.magScalingRel = magScalingRel;
		this.lowerSeisDepth = lowerSeisDepth;
		this.duration = duration;
		this.minMag = minMag;
		this.numStrikes = numStrikes;
		this.firstStrike = firstStrike;


		this.isPoissonian = true;
		
		checkFocalMechs();  // need to do this before calling computeMaxLength()
		
		// Compute stuff needed for the getMinDistance(Site) method, so this can be computed before ruptures are generated
		this.maxLength = computeMaxLength();
		
		// Create Discretized Region
		gridReg = new GriddedRegion(reg,gridResolution,null); 
		
		numRuptures = this.computeNumRuptures()*gridReg.getNodeCount();
	}
	
	
	/**
	 * 
	 * @return
	 */
	public Region getRegion() { return reg;}



	/**
	 * This returns the shortest horizontal dist to the point source (minus half the length of the 
	 * longest rupture).
	 * 
	 * @param site
	 * @return minimum distance
	 */
	public double getMinDistance(Site site) {
		double dist = reg.distanceToLocation(site.getLocation()) - maxLength/2.0;
		if(dist < 0) dist=0;
		return dist;
	}

}

