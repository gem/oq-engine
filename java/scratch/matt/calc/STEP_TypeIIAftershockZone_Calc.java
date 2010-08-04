package scratch.matt.calc;

import java.util.ListIterator;

import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.sha.earthquake.griddedForecast.STEP_CombineForecastModels;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupList;
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
public class STEP_TypeIIAftershockZone_Calc {
  //private ObsEqkRupList newObsEventsList;
  private GriddedRegion typeIIAftershockZone;
  private LocationList faultSegments;
  private double zoneRadius, gridSpacing;

  public STEP_TypeIIAftershockZone_Calc(ObsEqkRupList newObsEventsList, STEP_CombineForecastModels aftershockModel) {
    ObsEqkRupture mainshock = aftershockModel.getMainShock();
    Location mainshockLoc = mainshock.getHypocenterLocation();
    double gridSpacing = aftershockModel.get_GridSpacing();
    double zoneRadius = aftershockModel.get_AftershockZoneRadius();
    double faultRadius = aftershockModel.get_AftershockZoneRadius();
    calc_SyntheticFault(newObsEventsList, mainshockLoc);
  }

  /**
   * calc_SyntheticFault
   * This method is not yet finished.  A sort method is needed in LocationList
   * to sort on lats and longs.
   */
  public static void calc_SyntheticFault(ObsEqkRupList newObsEventsList, Location mainshockLoc) {
    ListIterator eventIt = newObsEventsList.listIterator();
    int numEvents = newObsEventsList.size();
    double[] eLat = new double[numEvents];
    double[] eLong = new double[numEvents];
    ObsEqkRupture event = new ObsEqkRupture();
    Location eLoc = new Location(0,0,0);
    LocationList latLongList = new LocationList();

    int ind = 0;
    while (eventIt.hasNext()){
      event = (ObsEqkRupture)eventIt.next();
      eLoc = event.getHypocenterLocation();
      latLongList.add(eLoc);
    }

    /**
     * sort the lat long pairs and ignore the extreme values (.01 and .99)
     */
    int minInd = (int)Math.round(0.01*numEvents);
    int maxInd = (int)Math.round(0.99*numEvents);
    int numIn = (int)Math.round(.8*numEvents);
    double maxLat_LatSort = eLat[maxInd];
    double minLat_LatSort = eLat[minInd];
    double maxLong_LongSort = eLong[maxInd];
    double minLong_LongSort = eLong[minInd];

    /**
     * THESE WILL NEED TO BE SET ONCE THE SORT METHOD IS
     * implemented in LocationList
     */
    double maxLong_LatSort = 0;
    double minLong_LatSort = 0;
    double maxLat_LongSort = 0;
    double minLat_LongSort = 0;
    double latDiff = maxLat_LatSort-minLat_LatSort;
    double longDiff = maxLong_LongSort-minLong_LongSort;

    /** find the largest dimension - either in Lat or in Long
     *  this needs to be improved
     */

    LocationList faultSegments = new LocationList();
    double topEventLat, topEventLong, bottomEventLat, bottomEventLong;
    Location topEndPoint;
    Location bottomEndPoint;
    if (latDiff > longDiff){
    	topEndPoint = new Location(maxLat_LatSort, maxLong_LatSort);
    	bottomEndPoint = new Location(minLat_LatSort, minLong_LatSort);
//      topEndPoint.setLatitude(maxLat_LatSort);
//      topEndPoint.setLongitude(maxLong_LatSort);
//      bottomEndPoint.setLatitude(minLat_LatSort);
//      bottomEndPoint.setLongitude(minLong_LatSort);
    }
    else {
    	topEndPoint = new Location(maxLat_LongSort, maxLong_LongSort);
    	bottomEndPoint = new Location(minLat_LongSort, minLong_LongSort);
//      topEndPoint.setLatitude(maxLat_LongSort);
//      topEndPoint.setLongitude(maxLong_LongSort);
//      bottomEndPoint.setLatitude(minLat_LongSort);
//      bottomEndPoint.setLongitude(minLong_LongSort);
    }

    /**
     * Create a two segment fault that passes thru the mainshock
     * using the extreme widths defined above
     */
    faultSegments.add(topEndPoint);
    faultSegments.add(mainshockLoc);
    faultSegments.add(mainshockLoc);
    faultSegments.add(bottomEndPoint);
  }

  /**
   * CreateAftershockZoneDef
   */
  public void CreateAftershockZoneDef() {
	  GriddedRegion typeIIAftershockZone =
        new GriddedRegion(faultSegments,zoneRadius,gridSpacing, new Location(0,0));
    /**
     * The rest will have to be filled in for a "Sausage" Geographic
     * Region on a SausageGeographicRegion is defined.
     */
  }

  /**
   * get_TypeIIAftershockZone
   * This needs to be changed to return a sausage region once
   * this type of region is defined.
   */
  public GriddedRegion get_TypeIIAftershockZone() {
    return typeIIAftershockZone;
  }

  /**
   * getTypeIIFaultModel
   */
  public LocationList getTypeIIFaultModel() {
    return faultSegments;
  }

}
