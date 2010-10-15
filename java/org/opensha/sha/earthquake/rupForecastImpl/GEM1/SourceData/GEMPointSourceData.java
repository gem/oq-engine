package org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData;

import java.io.Serializable;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This holds data for a grid source (single location).
 */
public class GEMPointSourceData extends GEMSourceData implements Serializable {

    /**
	 * 
	 */
    private static final long serialVersionUID = 1L;

    // this holds the MagFreqDists, FocalMechs, and location.
    private HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc;
    // the following specifies the average depth to top of rupture as a function
    // of magnitude.
    private ArbitrarilyDiscretizedFunc aveRupTopVsMag;
    // the following is used to locate small sources (i.e., for all mags lower
    // than the minimum mag in aveRupTopVsMag)
    private double aveHypoDepth;

    /**
	 * 
	 */
    public GEMPointSourceData(String id, String name,
            TectonicRegionType tectReg,
            HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc,
            ArbitrarilyDiscretizedFunc aveRupTopVsMag, double aveHypoDepth) {
        this.id = id;
        this.name = name;
        this.tectReg = tectReg;
        this.hypoMagFreqDistAtLoc = hypoMagFreqDistAtLoc;
        this.aveRupTopVsMag = aveRupTopVsMag;
        this.aveHypoDepth = aveHypoDepth;
    }

    /**
     * 
     * @return
     */
    public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc() {
        return this.hypoMagFreqDistAtLoc;
    }

    /**
     * 
     * @return
     */
    public ArbitrarilyDiscretizedFunc getAveRupTopVsMag() {
        return this.aveRupTopVsMag;
    }

    /**
     * 
     * @return
     */
    public double getAveHypoDepth() {
        return this.aveHypoDepth;
    }
}
