package scratch.matt.calc;

import org.opensha.sha.earthquake.griddedForecast.STEP_AftershockForecast;
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
public class SortAftershocks_Calc {
  private STEP_AftershockForecast aftershockModel;  // this is the new event
  //private AftershockModelList previousMainshockModels,newEventModels;

  /*public SortAftershocks_Calc(AfterShockModelList newEventModels,
                              AfterShockModelList previousMainshockModels) {
  }*/

  /**
   * selectAftershocksToPrevMainshock_Calc
   */
 /* public void selectAftershocksToPrevMainshock_Calc() {
    int numNewEvents = newEventModels.getNumModels();
    int numPrevMainshocks = previousMainshockModels.getNumModels();
    STEP_AftershockHypoMagForecast msModel;
    EvenlyGriddedGeographicRegionAPI msZone;
    STEP_AftershockHypoMagForecast newEventModel;
    EvenlyGriddedGeographicRegionAPI newEventZone;
    ObsEqkRupList  prelimAftershockList;
    ObsEqkRupture newMs;
    ListIterator newIt = newEventModels.ListIterator;
    ListIterator prevIt = previousMainshockModels.ListIterator;
    Location newMsLoc;
    boolean isInZone;
    int msRefNum;

    // Loop through all newly recorded events and see if they are an aftershock
    // to an previoulsy recorded mainshocks.
    while (newIt.hasNext()) {
      newEventModel = newIt.next();
      newEventZone = newEventModel.getAfterShockZone();
      newMs = newEventModel.getMainShock();
      newMsLoc = newMs.getHypocenterLocation();
      while (prevIt.hasNext()){
        msModel = prevIt.next();
        msZone = msModel.getAfterShockZone();
        isInZone = msZone.isLocationInside(newMsLoc);
        if (isInZone){
          newEventModel.setIsAftershock(true);
          msRefNum = msModel.getMainshockRefNum();
        }
      }
    }

  }*/

  /**
   * Now find all aftershocks to each new event.
   *
   */


  /**
   * selectAfterShocksToNewMainshock_Calc
 * @return 
   */
	  

  public ObsEqkRupList selectAfterShocksToNewMainshock_Calc() {
	  return (new ObsEqkRupList());
  }






}
