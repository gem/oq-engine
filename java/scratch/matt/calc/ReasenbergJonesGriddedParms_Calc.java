package scratch.matt.calc;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupList;

/**
 * <p>Title: </p>
 *
 * <p>Description: </p>
 *
 * <p>Copyright: Copyright (c) 2002</p>
 *
 * <p>Company: </p>
 *
 * @author not attributable
 * @version 1.0
 */
public class ReasenbergJonesGriddedParms_Calc {

  private static boolean useFixed_cValue = true;
  private double[] grid_pVal,grid_cVal,grid_kVal,grid_aVal,grid_bVal, grid_Mc;
  private double constantAddToMc = .2;
  private double searchRadius;


// the first constructor must be used if a non-fixed c value is to be used and then useFixed_cValue must be set to false
  public ReasenbergJonesGriddedParms_Calc(GriddedRegion
                                          gridNodes, ObsEqkRupList eventList,
                                          boolean useFixed_cValue) {
    setGriddedMags(gridNodes, eventList);
    setUseFixed_cVal(useFixed_cValue);
  }

  public ReasenbergJonesGriddedParms_Calc(GriddedRegion
                                          gridNodes, ObsEqkRupList eventList) {
    setGriddedMags(gridNodes, eventList);
  }


  /**
   * setUseFixed_cVal
   * if true c will be fixed for the Omori calculations
   * default is fixed
   */
  public void setUseFixed_cVal(boolean fix_cVal) {
    useFixed_cValue = fix_cVal;
  }

  /**
   * set_constantAddToCompleteness
   */
  public void set_constantAddToCompleteness(double mcConst) {
    constantAddToMc = mcConst;
  }

  /**
   * get_Gridded_pVals
   */
  public double[] get_Gridded_pVals() {
    return grid_pVal;
  }

  /**
   * get_Gridded_cVals
   */
  public double[] get_Gridded_cVals() {
    return grid_cVal;
  }

  /**
   * get_Gridded_kVals
   */
  public double[] get_Gridded_kVals() {
    return grid_kVal;
  }

  /**
   * get_Gridded_aVals
   */
  public double[] get_Gridded_aVals() {
    return grid_aVal;
  }

  /**
   * get_Gridded_bVals
   */
  public double[] get_Gridded_bVals() {
    return grid_bVal;
  }

  /**
     * getAllGriddedVals
     * Returns an arraylist of all RJ Parms
     * 1 - a value
     * 2 - b value
     * 3 - p value
     * 4 - k value
     * 5 - c value
     */
    public ArrayList getAllGriddedVals() {
      ArrayList RJParms = new ArrayList(5);
      RJParms.add(0,grid_aVal);
      RJParms.add(1,grid_bVal);
      RJParms.add(2,grid_pVal);
      RJParms.add(3,grid_kVal);
      RJParms.add(4,grid_cVal);
      RJParms.add(5,grid_Mc);
      return RJParms;
  }


  /**
   * setGriddedMags
   * calculate the Reasenberg & Jones parms (a,b,p,c,k) on the evenly gridded region grid.
   *
   */
  public void setGriddedMags(GriddedRegion gridNodes,
                             ObsEqkRupList eventList) {
    calc_RJParmsOnGrid(gridNodes, eventList);
  }

  /**
   * calc_RJParmsOnGrid
   */
  private void calc_RJParmsOnGrid(GriddedRegion gridNodes,
                                  ObsEqkRupList eventList){
    Iterator<Location> gridIt = gridNodes.getNodeList().iterator();
    int numNodes = gridNodes.getNodeCount();
    grid_aVal = new double[numNodes];
    grid_bVal = new double[numNodes];
    grid_pVal = new double[numNodes];
    grid_kVal = new double[numNodes];
    grid_cVal = new double[numNodes];
    grid_Mc = new double[numNodes];

    //ListIterator eventIt = eventList.listIterator();
    int numEvents = eventList.size();
    double[] eventDist = new double[numEvents];
    //double searchRadius;
    double completenessMag, allEventsMc;
    int ind = 0;
    
    // first find the overall min completeness mag
    CompletenessMagCalc.setMcBest(eventList);
    allEventsMc = CompletenessMagCalc.getMcBest() + constantAddToMc;
    // # of events in total sequence > Mc
    int totalCompleteEvents = eventList.getObsEqkRupsAboveMag(allEventsMc).size();
    // set the appropriate radius to use for collecting events for the node
    if (totalCompleteEvents < 1000) this.searchRadius = 15;
    else if (totalCompleteEvents < 1500) this.searchRadius = 12;
    else if (totalCompleteEvents < 2000) this.searchRadius = 10;
    else this.searchRadius = 75;


    while (gridIt.hasNext()) {
      Region gridRegion =
          new Region(gridIt.next(),this.searchRadius);
      ObsEqkRupList regionList = eventList.getObsEqkRupsInside(gridRegion);

      // Calculate the completeness of the events selected for the node and remove
      // events below this mag.
      CompletenessMagCalc.setMcBest(regionList);
      completenessMag = CompletenessMagCalc.getMcBest();
      grid_Mc[ind] = completenessMag + constantAddToMc;
      ObsEqkRupList completeRegionList =
          regionList.getObsEqkRupsAboveMag(completenessMag + constantAddToMc);

      // Calculate the Gutenberg-Richter parms
      MaxLikeGR_Calc.setMags(completeRegionList);
      grid_aVal[ind] = MaxLikeGR_Calc.get_aValueMaxLike();
      grid_bVal[ind] = MaxLikeGR_Calc.get_bValueMaxLike();

      // If there are 100 events of more, calculate the Omori parms.
      if (completeRegionList.size() >= 100){
        MaxLikeOmori_Calc omoriCalc = new MaxLikeOmori_Calc();
        if (useFixed_cValue)
          omoriCalc.set_AfterShockListFixed_c(completeRegionList);
        else
          omoriCalc.set_AfterShockList(completeRegionList);

        grid_cVal[ind] = omoriCalc.get_c_value();
        grid_pVal[ind] = omoriCalc.get_p_value();
        grid_kVal[ind++] = omoriCalc.get_k_value();
      }
      // if less than 100 events, fill the parms with dummy vals.
      else {
        grid_cVal[ind] = Double.NaN;
        grid_pVal[ind] = Double.NaN;
        grid_kVal[ind++] = Double.NaN;
      }
    }
  }
  
  /**
   * getGridSearchRadius
   * @return double
   * get the radius used when calculating the Reasenberg & Jones Params.
   */
  public double getGridSearchRadius(){
	  return this.searchRadius;
  }
}
