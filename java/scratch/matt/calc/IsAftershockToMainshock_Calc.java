package scratch.matt.calc;

import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.griddedForecast.STEP_CombineForecastModels;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupture;

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
public class IsAftershockToMainshock_Calc {
  private ObsEqkRupture newEvent;
  private STEP_CombineForecastModels mainshockModel;
  private boolean isInZone;
  private boolean sameEvent;

  public IsAftershockToMainshock_Calc(ObsEqkRupture newEvent,
                                      STEP_CombineForecastModels
                                      mainshockModel) {
	this.mainshockModel = mainshockModel;
	this.newEvent = newEvent;
    Calc_IsAftershockToMainshock();
  }

  /**
   * get_isAftershock
   */
  public boolean get_isAftershock() {
    return isInZone;
  }
  
  

  public boolean isSameEvent() {
	return sameEvent;
}

/**
   * Calc_IsAftershockToPrev
   */
  private boolean Calc_IsAftershockToMainshock() {
	  sameEvent = false;
	  if(mainshockModel.getMainShock().equalsObsEqkRupEvent(newEvent)){
		  sameEvent = true;
	  }
	  
    boolean isInZone;
    GriddedRegion aftershockZone;
    aftershockZone = mainshockModel.getAfterShockZone();
    ObsEqkRupture mainshock = mainshockModel.getMainShock();
    Location newEventLoc = newEvent.getHypocenterLocation();
    boolean isStatic = mainshockModel.get_isStatic();

    // if this event is not accepting aftershocks any more stop
    // here and return a false
    if (isStatic)
      this.isInZone = false;

    // if it is accepting look and see if this event fits
    else {
      this.isInZone = aftershockZone.contains(newEventLoc);

      if (this.isInZone) {
        //if ( (double) mainshock.getMag() > (double) newEvent.getMag()) {
        //mainshockModel.addToAftershockList(newEvent);
      }
      else {
        mainshockModel.set_isStatic(true);
      }
    }

    return this.isInZone;
  }
}

