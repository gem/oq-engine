package org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

/**
 * Add another constructor that takes the info taken in the GEMAreaSourceData constructor and treat those
 * area sources here (and remove GEMAreaSourceData).
 */
public class GEMGriddedAreaSourceData extends GEMSourceData {
 
	// this holds a MagFreqDistsForFocalMechs for each location.
	private HypoMagFreqDistAtLoc[] hypoMagFreqDistAtLocList;
	// the following specifies the average depth to top of rupture as a function of
	// magnitude, which will be obtained using the getInterpolatedY(mag) method.
	private ArbitrarilyDiscretizedFunc aveRupTopVsMag;
	// the following will be used to locate point sources (i.e., for all mags lower than the minimum mag in aveRupTopVsMag)
	private double aveHypoDepth;

	/**
	 * 
	 */
	public GEMGriddedAreaSourceData(String id, String name, TectonicRegionType tectReg, 
			HypoMagFreqDistAtLoc[] hypoMagFreqDistAtLocList,
			ArbitrarilyDiscretizedFunc aveRupTopVsMag, double aveHypoDepth) {
		this.id = id;
		this.name = name;
		this.tectReg = tectReg;
		this.hypoMagFreqDistAtLocList = hypoMagFreqDistAtLocList;
		this.aveRupTopVsMag = aveRupTopVsMag;
		this.aveHypoDepth = aveHypoDepth;
		
	} 
	
	/**
	 * 
	 * @return
	 */
	public HypoMagFreqDistAtLoc[] getHypoMagFreqDistAtLocList(){
		return this.hypoMagFreqDistAtLocList;
	}
	
	/**
	 * 
	 * @return
	 */
	public ArbitrarilyDiscretizedFunc getAveRupTopVsMag(){
		return this.aveRupTopVsMag;
	}

	
	
	/**
	 * 
	 * @return
	 */
	public double getAveHypoDepth(){
		return this.aveHypoDepth;
	}
}
