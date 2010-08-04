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
public class AftershockZone_Calc {

  public AftershockZone_Calc(STEP_AftershockForecast aftershockModel,
                             ObsEqkRupList previousAftershocks,
                             ObsEqkRupList newObsEvents) {
   // calc_AftershockZone(aftershockModel, previousAftershocks, newObsEvents);
  }

  /*public void calc_AftershockZone(STEP_AftershockHypoMagForecast aftershockModel,
                                  ObsEqkRupList previousAftershocks,
                                  ObsEqkRupList newObsEvents){
    ObsEqkRupList eventsInZoneList = new ObsEqkRupList();
    ObsEqkRupList allEventsList = new ObsEqkRupList();
    allEventsList.addAllObsEqkRupEvents(newObsEvents);
    allEventsList.addAllObsEqkRupEvents(previousAftershocks);

    if (aftershockModel.hasExternalFaultModel) {
      // This needs to be set up to read an external fault model.
    }
    else {
      Location mainshockLocation = mainshock.getHypocenterLocation();
      CircularGeographicRegion aftershockZone = new CircularGeographicRegion(
          mainshockLocation, zoneRadius);
      eventsInZoneList = allEventsList.getObsEqkRupsInside(aftershockZone);
      if (eventsInZoneList.size() > 100) {
        STEP_TypeIIAftershockZone_Calc typeIIcalc = new
            STEP_TypeIIAftershockZone_Calc(eventsInZoneList, this);
        EvenlyGriddedSausageGeographicRegion typeII_Zone = typeIIcalc.
            get_TypeIIAftershockZone();
        this.setAfterShockZone(typeII_Zone);
        eventsInZoneList.getObsEqkRupsInside(typeII_Zone);
      }
    }
    this.setAfterShocks(eventsInZoneList);
  }*/
}
