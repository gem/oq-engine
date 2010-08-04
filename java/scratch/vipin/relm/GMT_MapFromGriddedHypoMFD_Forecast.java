package scratch.vipin.relm;

import java.util.ArrayList;

import org.opensha.commons.data.ArbDiscretizedXYZ_DataSet;
import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.exceptions.DataPoint2DException;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.mapping.gmt.GMT_MapGenerator;
import org.opensha.sha.earthquake.griddedForecast.GriddedHypoMagFreqDistForecast;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.gui.infoTools.ImageViewerWindow;
import org.opensha.sha.magdist.IncrementalMagFreqDist;


/**
 * <p>Title: GMT_MapFromGriddedHypoMFD_Forecast.java </p>
 * <p>Description: This class accepts Gridded Hypo Mag Freq Dist forecast and makes
 * a map or generates a file in RELM format</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class GMT_MapFromGriddedHypoMFD_Forecast {
  private GriddedHypoMagFreqDistForecast griddedHypoMFD;


  /**
   * constructor accepts GriddedHypoMagFreqDistForecast
   * @param griddedHypoMagFreqDistForecast
   */
  public GMT_MapFromGriddedHypoMFD_Forecast(
      GriddedHypoMagFreqDistForecast griddedHypoMagFreqDistForecast) {
    setGriddedHypoMagFreqDistForecast( griddedHypoMagFreqDistForecast);
  }

  /**
   * Set the GriddedHypoMagFreqDistForecast
   * @param griddedHypoMagFreqDistForecast
   */
  public void setGriddedHypoMagFreqDistForecast(
      GriddedHypoMagFreqDistForecast griddedHypoMagFreqDistForecast) {
    this.griddedHypoMFD = griddedHypoMagFreqDistForecast;
  }


  /**
   * Calculate the rates above the specified magnitude for each location
   * and display in a map
   *
   * @param mag
   */
  public void makeMap(double mag, String dirName, boolean isAdjustLatLon, double adjustmentVal) {
    XYZ_DataSetAPI xyzData = getRELM_XYZ_DataAboveMag(mag, isAdjustLatLon, adjustmentVal);
    GriddedRegion region  = griddedHypoMFD.getRegion();
    // make GMT_MapGenerator to make the map
    GMT_MapGenerator mapGenerator = new GMT_MapGenerator();

    // TODO :   SET VARIOUS  GMT PARAMETERS TO MAKE MAP
    if(isAdjustLatLon) {
    	mapGenerator.setParameter(GMT_MapGenerator.MIN_LAT_PARAM_NAME, new Double(region.getMinGridLat()));
    	mapGenerator.setParameter(GMT_MapGenerator.MAX_LAT_PARAM_NAME, new Double(region.getMaxGridLat()));
    	mapGenerator.setParameter(GMT_MapGenerator.MIN_LON_PARAM_NAME, new Double(region.getMinGridLon()));
    	mapGenerator.setParameter(GMT_MapGenerator.MAX_LON_PARAM_NAME, new Double(region.getMaxGridLon()));
    } else {
    	mapGenerator.setParameter(GMT_MapGenerator.MIN_LAT_PARAM_NAME, new Double(region.getMinGridLat())-adjustmentVal);
    	mapGenerator.setParameter(GMT_MapGenerator.MAX_LAT_PARAM_NAME, new Double(region.getMaxGridLat())-adjustmentVal);
    	mapGenerator.setParameter(GMT_MapGenerator.MIN_LON_PARAM_NAME, new Double(region.getMinGridLon())-adjustmentVal);
    	mapGenerator.setParameter(GMT_MapGenerator.MAX_LON_PARAM_NAME, new Double(region.getMaxGridLon())-adjustmentVal);
    }
    mapGenerator.setParameter(GMT_MapGenerator.GRID_SPACING_PARAM_NAME, new Double(region.getSpacing()));
    mapGenerator.setParameter(GMT_MapGenerator.LOG_PLOT_NAME, new Boolean(true));
    mapGenerator.setParameter(GMT_MapGenerator.COAST_PARAM_NAME, GMT_MapGenerator.COAST_DRAW);
    mapGenerator.setParameter(GMT_MapGenerator.TOPO_RESOLUTION_PARAM_NAME, GMT_MapGenerator.TOPO_RESOLUTION_NONE);
    mapGenerator.setParameter(GMT_MapGenerator.CPT_FILE_PARAM_NAME, GMT_MapGenerator.CPT_FILE_MAX_SPECTRUM);

    //manual color scale
    mapGenerator.setParameter(GMT_MapGenerator.COLOR_SCALE_MODE_NAME, GMT_MapGenerator.COLOR_SCALE_MODE_MANUALLY);
    /* For Mag=5, Min=-5 and Max=-1
       For Mag=6.5, Min=-6 and Max=-2
       For Mag=8, Min=-8 and Max=-4
    */
    mapGenerator.setParameter(GMT_MapGenerator.COLOR_SCALE_MIN_PARAM_NAME, new Double(-5));
    mapGenerator.setParameter(GMT_MapGenerator.COLOR_SCALE_MAX_PARAM_NAME, new Double(-1));

    try {
      String metadata = "Rate Above magnitude " + mag;
      String imageFileName = mapGenerator.makeMapUsingServlet(xyzData, "Rates",
                                         metadata, dirName);
      new ImageViewerWindow(imageFileName, metadata, true);

    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * For each location, return the rate above the specified magnitude
   *
   * It returns the XYZ data above a specific magnitude
   * It returns a list of XYZ values where each X,Y,Z are lat,lon and rate respectively.
   * The rate is the rate above the given magnitude
   *
   * @return
   */
  public  XYZ_DataSetAPI getRELM_XYZ_DataAboveMag(double mag, boolean isAdjustLatLon, double adjustment) {
    ArbDiscretizedXYZ_DataSet xyzDataSet = new ArbDiscretizedXYZ_DataSet();
    ArrayList xVals = new ArrayList();
    ArrayList yVals = new ArrayList();
    ArrayList zVals = new ArrayList();
    // iterate over all locations.
    double rateAboveMag=0.0, totalIncrRate=0;
    int numLocs = griddedHypoMFD.getNumHypoLocs();
   
    for(int i=0; i<numLocs; ++i) {
      HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc = griddedHypoMFD.getHypoMagFreqDistAtLoc(i);
      Location loc = hypoMagFreqDistAtLoc.getLocation();
      if(isAdjustLatLon) {
    	  xVals.add(new Double(loc.getLatitude()-adjustment)); 
    	  yVals.add(new Double(loc.getLongitude()-adjustment));
      } else {
    	  xVals.add(new Double(loc.getLatitude())); 
    	  yVals.add(new Double(loc.getLongitude()));
      }
      IncrementalMagFreqDist magFreqDist = hypoMagFreqDistAtLoc.getMagFreqDistList()[0];
      
      // rate above magnitude
      try {
        rateAboveMag = magFreqDist.getCumRate(mag); 
        
      }catch(DataPoint2DException dataPointException) {
        // if magnitude is less than least magnitude in this Mag-Freq dist
        if(mag<magFreqDist.getMinX()) rateAboveMag = magFreqDist.getTotalIncrRate();
        // if this mag is above highest mag in this MagFreqDist
        else if(mag>magFreqDist.getMaxX()) rateAboveMag = 0.0;
        else dataPointException.printStackTrace();
      }
      totalIncrRate+=rateAboveMag;
      zVals.add(new Double(rateAboveMag));
    }
    xyzDataSet.setXYZ_DataSet(xVals, yVals, zVals);
    //System.out.println("Total  Rate above mag " + mag+"="+totalIncrRate);
    return xyzDataSet;
  }

  /**
   *
   * @param args
   */
  public static void main(String[] args) {
   
   try {
     // region to view the rates
	   CaliforniaRegions.RELM_TESTING_GRIDDED evenlyGriddedRegion  = new CaliforniaRegions.RELM_TESTING_GRIDDED();
     // min mag, maxMag, These are Centers of first and last bin
     double minMag=5.0, maxMag=9.00;
     int numMag = 41; // number of Mag bins

     /* Following names can be used for RELM files:
      * ward.geodetic81.forecast
      * helmstetter_et_al.hkj.forecast
      * helmstetter_et_al.hkj.aftershock.forecast
      * ward.simulation.forecast
      * ward.combo81.forecast
      * ward.geologic81.forecast
      * ward.geodetic85.forecast
      * ward.seismic81.forecast
      * wiemer_schorlemmer.alm.forecast
      * bird_liu.neokiname.forecast
      * ebel.mainshock.forecast
      * ebel.aftershock.forecast
      * holliday.pi.forecast
      * UCERF1.0_AnnualRates.txt
      * NSHMP2002_AnnualRates.txt
      * shen_et_al.geodetic.forecast
      * shen_et_al.geodetic.aftershock
      */
     ArrayList<String> relmFileNames = new ArrayList<String>();
     ArrayList<Boolean> useMaskList = new ArrayList<Boolean>(); // whether to use mask bit
     ArrayList<Boolean> adjustLatLons = new ArrayList<Boolean>(); // whwther to add-subtract gridSpacing/2
     relmFileNames.add("ward.geodetic81.forecast");
     useMaskList.add(true);
     adjustLatLons.add(true);
     relmFileNames.add("helmstetter_et_al.hkj.forecast");
     useMaskList.add(true);
     adjustLatLons.add(true);
     relmFileNames.add("helmstetter_et_al.hkj.aftershock.forecast");
     useMaskList.add(true);
     adjustLatLons.add(true);
     relmFileNames.add("ward.simulation.forecast");
     useMaskList.add(true);
     adjustLatLons.add(true);
     relmFileNames.add("ward.combo81.forecast");
     useMaskList.add(true);
     adjustLatLons.add(true);
     relmFileNames.add("ward.geologic81.forecast");
     useMaskList.add(true);
     adjustLatLons.add(true);
     relmFileNames.add("ward.seismic81.forecast");
     useMaskList.add(true);
     adjustLatLons.add(true);
     relmFileNames.add("wiemer_schorlemmer.alm.forecast");
     useMaskList.add(true);
     adjustLatLons.add(true);
     relmFileNames.add("bird_liu.neokiname.forecast");
     useMaskList.add(true);
     adjustLatLons.add(true);
     relmFileNames.add("ebel.mainshock.forecast");
     useMaskList.add(false);
     adjustLatLons.add(true);
     relmFileNames.add("ebel.aftershock.forecast");
     useMaskList.add(false);
     adjustLatLons.add(true);
     relmFileNames.add("holliday.pi.forecast");
     useMaskList.add(false);
     adjustLatLons.add(true);
     relmFileNames.add("UCERF1.forecast");
     useMaskList.add(true);
     adjustLatLons.add(false);
     relmFileNames.add("NSHMP2002.forecast");
     adjustLatLons.add(false);
     useMaskList.add(true);
     relmFileNames.add("shen_et_al.geodetic.forecast");
     useMaskList.add(true);
     adjustLatLons.add(true);
     relmFileNames.add("shen_et_al.geodetic.aftershock");
     useMaskList.add(true);
     adjustLatLons.add(true);
     relmFileNames.add("kagan_et_al.mainshock.forecast");
     useMaskList.add(true);
     adjustLatLons.add(true);
     relmFileNames.add("kagan_et_al.aftershock.forecast");
     useMaskList.add(true);
     adjustLatLons.add(true);
   
    /*for(int i=0; i<relmFileNames.size(); ++i) {
    	System.out.println("Processing "+relmFileNames.get(i));
    	 GriddedHypoMagFreqDistForecast griddedHypoMagFeqDistForecast =
    		 new ReadRELM_FileIntoGriddedHypoMFD_Forecast(relmFileNames.get(i), evenlyGriddedRegion,
    				 minMag, maxMag, numMag, useMaskList.get(i), adjustLatLons.get(i));
      
    	 // Make GMT map of rates
    	GMT_MapFromGriddedHypoMFD_Forecast viewRates = new GMT_MapFromGriddedHypoMFD_Forecast(griddedHypoMagFeqDistForecast);
    	viewRates.makeMap(5.0,relmFileNames.get(i), adjustLatLons.get(i), 0.05);
     } */

    GriddedHypoMagFreqDistForecast griddedHypoMagFeqDistForecast =
		 new ReadRELM_FileIntoGriddedHypoMFD_Forecast("NSHMP2002Rates.txt", evenlyGriddedRegion,
				 minMag, maxMag, numMag, true, true);
 
	 // Make GMT map of rates
	GMT_MapFromGriddedHypoMFD_Forecast viewRates = new GMT_MapFromGriddedHypoMFD_Forecast(griddedHypoMagFeqDistForecast);
	viewRates.makeMap(5.0, "NSHMP_For_RELM", true, 0.05);
    
     //	 make GriddedHypoMFD Forecast from the EqkRupForecast
     /*EqkRupForecast eqkRupForecast = new Frankel02_AdjustableEqkRupForecast();
     // include background sources as point sources
     eqkRupForecast.setParameter(Frankel02_AdjustableEqkRupForecast.RUP_OFFSET_PARAM_NAME,
    		 new Double(10.0));
     eqkRupForecast.setParameter(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_NAME,
    		 Frankel02_AdjustableEqkRupForecast.BACK_SEIS_INCLUDE);
     eqkRupForecast.setParameter(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_RUP_NAME,
    		 Frankel02_AdjustableEqkRupForecast.BACK_SEIS_RUP_POINT);
     eqkRupForecast.getTimeSpan().setDuration(5.0);
     eqkRupForecast.updateForecast();
     GriddedHypoMagFreqDistForecast griddedHypoMagFeqDistForecast =
		   new RELM_ERF_ToGriddedHypoMagFreqDistForecast(eqkRupForecast, evenlyGriddedRegion,
				   minMag, maxMag, numMag,5.0); // 5 year rates
	 // Make GMT map of rates
     GMT_MapFromGriddedHypoMFD_Forecast viewRates = new GMT_MapFromGriddedHypoMFD_Forecast(griddedHypoMagFeqDistForecast);
     viewRates.makeMap(5.0, "NSHMP2002_Original", false, 0.05);*/
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

}