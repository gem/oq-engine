package scratch.vipin.relm;

import java.util.ArrayList;

import org.opensha.commons.geo.GriddedRegion;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.calc.ERF2GriddedSeisRatesCalc;
import org.opensha.sha.earthquake.griddedForecast.GriddedHypoMagFreqDistForecast;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * <p>Title: ERF_ToGriddedHypoMagFreqDistForecast.java </p>
 * <p>Description: this class accepts any ERF and converts into GriddedHypoMagFreDistForecast.
 * This class been validated using following procedure :
 * It was tested for Frankel02 ERF.
 * Following testing procedure was applied(Region used was RELM Gridded region and
 *  min mag=5, max Mag=9, Num mags=41):
 * 1. Choose an arbitrary location say 31.5, -117.2
 * 2. Make Frankel02 ERF with Background only sources
 * 3. Modify Frankel02 ERF for testing purposes to use ONLY CAmapC_OpenSHA input file
 * 4. Now print the Magnitude Frequency distribution in Frankel02 ERF for that location
 * 5. Using the same ERF settings, get the Magnitude Frequency distribution using
 * this function and it should be same as we printed out in ERF.
 * 6. In another test, we printed out cum dist above Mag 5.0 for All locations.
 * The cum dist from Frankel02 ERF and from MFD retured from this class should
 * be same.

 *
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class RELM_ERF_ToGriddedHypoMagFreqDistForecast  extends GriddedHypoMagFreqDistForecast {
  private EqkRupForecast eqkRupForecast;
  private HypoMagFreqDistAtLoc magFreqDistForLocations[];

  /**
   * Accepts a forecast and a region. It calculates Magnitude-Freq distribution for
   * each location within the region.
   *
   * @param forecast - the EqkRupForecast to be converted to GriddedHypoMagFreqDistForecast
   * @param griddedRegion - EvenlyGriddedRegion for calculating magnitude frequency distribution
   * @param minMag - Center of first magnitude bin to make IncrementalMagFreqDist.
   * @param maxMag - Center of last magnitude bin to make IncrementalMagFreqDist
   * @param numMags - Total number of  magnitude bins in IncrementalMagFreqDist
   *
   *
   */
  public RELM_ERF_ToGriddedHypoMagFreqDistForecast(EqkRupForecast eqkRupForecast,
                                              GriddedRegion griddedRegion,
                                              double minMag,
                                              double maxMag,
                                              int numMagBins,
                                              double duration) {
    this.eqkRupForecast = eqkRupForecast;
    setRegion(griddedRegion);
//    this.region = griddedRegion;

    ERF2GriddedSeisRatesCalc erfToGriddedSeisRatesCalc = new ERF2GriddedSeisRatesCalc();
    ArrayList incrementalMFD_List  = erfToGriddedSeisRatesCalc.calcMFD_ForGriddedRegion(minMag, maxMag, numMagBins,
        eqkRupForecast, getRegion(), duration);
    // make HypoMagFreqDist for each location in the region
    magFreqDistForLocations = new HypoMagFreqDistAtLoc[this.getNumHypoLocs()];
    for(int i=0; i<magFreqDistForLocations.length; ++i ) {
      IncrementalMagFreqDist[] magFreqDistArray = new IncrementalMagFreqDist[1];
      magFreqDistArray[0] = (IncrementalMagFreqDist)incrementalMFD_List.get(i);
      magFreqDistArray[0].set(0, magFreqDistArray[0].getIncrRate(1)*1.2); //Ned conveyed this in an email dated Nov 14, 2006 at 7:13 AM
      magFreqDistForLocations[i] = new HypoMagFreqDistAtLoc(magFreqDistArray,griddedRegion.locationForIndex(i));
    }
    
  }

  /**
   * gets the Hypocenter Mag.
   *
   * @param ithLocation int : Index of the location in the region
   * @return HypoMagFreqDistAtLoc Object using which user can retrieve the
   *   Magnitude Frequency Distribution.
   * @todo Implement this
   *   org.opensha.sha.earthquake.GriddedHypoMagFreqDistAtLocAPI method
   */
  public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc(int ithLocation) {
    return magFreqDistForLocations[ithLocation];
  }
  
  
}