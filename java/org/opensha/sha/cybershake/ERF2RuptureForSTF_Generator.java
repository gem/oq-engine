/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.cybershake;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.ListIterator;

import org.apache.commons.lang.SystemUtils;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast;
import org.opensha.sha.faultSurface.EvenlyGridCenteredSurface;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.PointSurface;

/**
 * <p>Title: ERF2RuptureForSTF_Generator</p>
 *
 * <p>Description: This class provides with the capability of dumping the String
 * represenation of a ProbEqkRupture in a file. It creates a directory as specified
 * by the user and puts all the ruptures file in it. It also creates a Site file
 * that specifies which source and rupture were in its radius of cuttoff-distance.
 * </p>
 * <p>
 * This class also provides the user with the functionality of computing region bounds
 * around a given site which will let user which sources and rupture can affect a
 * given Site.
 * </p>
 * <p>
 * </p>
 * @author Nitin Gupta and Ned Field
 * @version 1.0
 */


public class ERF2RuptureForSTF_Generator {

  private EqkRupForecastAPI eqkRupForecast;

  private Site site;
  private double distance;

  //max Depth of any location rupture in the volume
  private double maxDepth;

  //to see if the rupture is within the circular distance of the given Site.
  private Region region;
  private final static double DEFAULT_GRID_SPACING_FOR_POINT_SURFACE = 1.0;



  public ERF2RuptureForSTF_Generator(EqkRupForecast eqkRupForecast, Site site,
                      double cuttOffDistance) {
    this.eqkRupForecast = eqkRupForecast;
    this.site = site;
    this.distance = cuttOffDistance;
    region = new
        Region(site.getLocation(), distance);
  }

  /**
   * Returns the list of the EqkRupture for a Site. Only those ruptures are
   * included which are with in the cut-off distance.
   * @return ArrayList List of ProbEqkRupRuptures
   */
  public ArrayList getEqkRupturesNearSite() {

    //initializing the list for containing the EqkRuptures
    ArrayList probEqkList = new ArrayList();
    int numSources = eqkRupForecast.getNumSources();

    //Going over each and every source in the forecast
    for (int sourceIndex = 0; sourceIndex < numSources; ++sourceIndex) {
      // get the ith source
      ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);
      int numRuptures = source.getNumRuptures();

      //going over all the ruptures in the source
      for (int rupIndex = 0; rupIndex < numRuptures; ++rupIndex) {
        ProbEqkRupture rupture = source.getRupture(rupIndex);

        EvenlyGriddedSurfaceAPI rupSurface = new EvenlyGridCenteredSurface(rupture.getRuptureSurface());


        //getting the iterator for all points on the rupture
        ListIterator it = rupSurface.getAllByRowsIterator();
        //looping over all the rupture pt locations and if any of those lies
        //within the provided distance range then include the rupture in the list.
        while (it.hasNext()) {
          Location ptLoc = (Location) it.next();
          if (region.contains(ptLoc)) {
            probEqkList.add(rupture.clone());
            break;
          }
        }
      }
    }
    return probEqkList;
  }

  /**
   * This function creates ruptures files in the specified directory, if it already
   * does not exists. It creates a single rupture file for a given rupture.
   * If the directory in which files are to be created already exists then it assumes
   * that will contain the "EqkRupForecast_Params.txt" metadata file.
   * This function allows the user with the flexibility of creating rupture files
   * for multiple sites keeping the ERf parameters same for all sites.
   * Also it will also generate a file for for each site which will tell the source
   * and rupture index which were within the cutt-off distance of the site.
   * It generates rupture file with following naming convention:
   * sourceIndex+"_"+ruptureIndex+".txt". It generates a new rupture file only
   * if it does not exists.
   * @param directoryName String Name of the directory in which rupture files are
   * to be  created
   */
  public void getEqkRupturesAsStringNearSite(String directoryName) {

    //Location of the Site
    Location siteLoc = site.getLocation();


    FileWriter fw = null;
    try {
      //creating the file with the directory name provided by the user. It will
      // then it sees if directory already exists and if it does then don't create
      //else create a new directory.
      File f = new File(directoryName);

      String directoryPath = f.getAbsolutePath();

      if(!directoryPath.endsWith(SystemUtils.FILE_SEPARATOR))
      directoryPath += SystemUtils.FILE_SEPARATOR;
      if(!f.exists() || !f.isDirectory()){
        f.mkdir();

        //creating the ERF params file in the directory.
        fw = new FileWriter(directoryPath + "EqkRupForecast_Params.txt");

        String erfString = "EqkRupForecast_Class = " +
            eqkRupForecast.getClass().getName() + "\n";
        //filling the metadata for ERF params.
        ListIterator it = eqkRupForecast.getAdjustableParamsIterator();
        while (it.hasNext()) {
          ParameterAPI param = (ParameterAPI) it.next();
          erfString += param.getName() + "=" + param.getValue() + "\n";
        }
        fw.write(erfString);
        fw.close();
      }
      f = null;
      //creating the Site file
      FileWriter siteFw = new FileWriter(directoryPath+(float)siteLoc.getLatitude()+"_"+(float)siteLoc.getLongitude()+".txt");
      String siteString ="";
      siteString += "Site-Latitude = "+(float)siteLoc.getLatitude() +"\n";
      siteString += "Site-Longitude = "+(float)siteLoc.getLongitude() +"\n";

      siteString += "Site-Depth = " + (float)siteLoc.getDepth() + "\n";
      siteString += "Cut-Off-Distance = " + distance +"\n";
      siteFw.write(siteString+"\n\n");
      siteFw.write("# Below are the Source and Ruptures that within the cutt-off "+
          "distance from the Site for the ERF\n\n");
      siteFw.write("#SourceIndex   RuptureIndex    Probability    Magnitude\n");

      int numSources = eqkRupForecast.getNumSources();
      //Going over each and every source in the forecast
      for (int sourceIndex = 0; sourceIndex < numSources; ++sourceIndex) {

        // get the ith source
        ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);
        int numRuptures = source.getNumRuptures();
        //going over all the ruptures in the source
        for (int rupIndex = 0; rupIndex < numRuptures; ++rupIndex) {

          //getting the rupture on the source and its gridCentered Surface
          ProbEqkRupture rupture = source.getRupture(rupIndex);
          EvenlyGriddedSurfaceAPI rupSurface = new EvenlyGridCenteredSurface(rupture.getRuptureSurface());

          //getting the iterator for all points on the rupture
          ListIterator lit = rupSurface.getAllByRowsIterator();
          //looping over all the rupture pt locations and if any of those lies
          //within the provided distance range then include the rupture in the list.
          while (lit.hasNext()) {
            Location ptLoc = (Location) lit.next();
            //if any location of the rupture is within the cutt-off distance of
            //the site then include that rupture.
            if(region.contains(ptLoc)) {
              //writing the source rupture index for the Site in the Site file
              siteFw.write(sourceIndex+"    "+rupIndex+"    "+ (float)rupture.getProbability()+
                           "    "+(float)rupture.getMag()+"\n");
              //creating the rupture file if it already does not exists else go to the next rupture.
             /* String ruptureFileName = directoryPath+sourceIndex+"_"+rupIndex+".txt";
              f = new File(ruptureFileName);
              if(!f.exists() || !f.isFile()){
                fw = new FileWriter(ruptureFileName);
                String ruptureString = ruptureString(rupture);
                fw.write(ruptureString);
                fw.close();
              }*/
              break;
            }
          }
        }
      }
      siteFw.close();
    }
    catch (IOException ex) {
      ex.printStackTrace();
    }
  }

  /**
   * Returns the Hashmap for the EqkRuptures with key being the SourceIndex
   * and values being the ArrayList of the rupture indicies.
   * @param eqkRupForecast EqkRupForecastAPI
   * @param site Site
   * @param distance double
   * @return HashMap
   */
  public HashMap getProbEqkRuptureIdentifiersNearSite() {
    //initializing the list for containing the EqkRuptures
    HashMap probRupIdentifierList = new HashMap();

    int numSources = eqkRupForecast.getNumSources();
    //creating a ArrayList to hold the rupture indices for a given site and eqkrupforecast.
    for (int sourceIndex = 0; sourceIndex < numSources; ++sourceIndex)
      probRupIdentifierList.put(new Integer(sourceIndex), new ArrayList());


    //Going over each and every source in the forecast
    for (int sourceIndex = 0; sourceIndex < numSources; ++sourceIndex) {
      // get the ith source
      ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);
      int numRuptures = source.getNumRuptures();

      //going over all the ruptures in the source
      for (int rupIndex = 0; rupIndex < numRuptures; ++rupIndex) {
        ProbEqkRupture rupture = source.getRupture(rupIndex);

        EvenlyGriddedSurfaceAPI rupSurface = new EvenlyGridCenteredSurface(rupture.getRuptureSurface());

        //getting the iterator for all points on the rupture
        ListIterator it = rupSurface.getAllByRowsIterator();
        //looping over all the rupture pt locations and if any of those lies
        //within the provided distance range then include the rupture in the list.
        while (it.hasNext()) {
          Location ptLoc = (Location) it.next();
          if (region.contains(ptLoc)) {
            ArrayList rupIndicesList = (ArrayList) probRupIdentifierList.get(new
                Integer(sourceIndex));
            rupIndicesList.add(new Integer(rupIndex));
            break;
          }
        }
      }
    }
    return probRupIdentifierList;
  }



  /**
   * Returns the regional bounds of the largest rectangular region around the
   * site that include all the ruptures surface locations within the range of
   * provided distance.
   * @return RectangularGeographicRegion
   */
  public Region getSiteRegionBounds() throws
      RegionConstraintException {
    int numSources = eqkRupForecast.getNumSources();

    double minLat = Double.POSITIVE_INFINITY;
    double maxLat = Double.NEGATIVE_INFINITY;
    double minLon = Double.POSITIVE_INFINITY;
    double maxLon = Double.NEGATIVE_INFINITY;


    //Going over each and every source in the forecast
    for (int sourceIndex = 0; sourceIndex < numSources; ++sourceIndex) {
      // get the ith source
      ProbEqkSource source = eqkRupForecast.getSource(sourceIndex);
      int numRuptures = source.getNumRuptures();

      //going over all the ruptures in the source
      for (int rupIndex = 0; rupIndex < numRuptures; ++rupIndex) {
        ProbEqkRupture rupture = source.getRupture(rupIndex);

        EvenlyGriddedSurfaceAPI rupSurface = rupture.getRuptureSurface();

        //getting the iterator for all points on the rupture
        ListIterator it = rupSurface.getAllByRowsIterator();
        boolean rupInside = false;
        //looping over all the rupture pt locations and if any of those lies
        //within the provided distance range then include the rupture in the list.
        while (it.hasNext()) {
          Location ptLoc = (Location) it.next();
          if (region.contains(ptLoc)) {
            rupInside = true;
            break;
          }
        }
        it = rupSurface.getAllByRowsIterator();
        while (it.hasNext() && rupInside) {
          Location ptLoc = (Location) it.next();
          double lat = ptLoc.getLatitude();
          double lon = ptLoc.getLongitude();
          double depth = ptLoc.getDepth();
          if (lat < minLat)
            minLat = lat;
          if (lat > maxLat)
            maxLat = lat;
          if (lon < minLon)
            minLon = lon;
          if (lon > maxLon)
            maxLon = lon;
          if (depth > maxDepth)
            maxDepth = depth;
        }
      }
    }
    return new Region(
    		new Location(minLat, minLon),
    		new Location(maxLat, maxLon));
  }

  /**
   * Returns the maximum depth for which any given rupture in a given geographic
   * region extends.
   * @return double
   */
  public double getMaxDepthForRuptureInRegionBounds() throws
      RegionConstraintException {
    if(maxDepth == 0)
      getSiteRegionBounds();
    return maxDepth;
  }

  /**
   *
   * @param args String[]
   */
  public static void main(String[] args) {

    Frankel02_AdjustableEqkRupForecast frankelForecast = null;

    frankelForecast = new
        Frankel02_AdjustableEqkRupForecast();

    frankelForecast.getAdjustableParameterList().getParameter(
        Frankel02_AdjustableEqkRupForecast.
        BACK_SEIS_NAME).setValue(Frankel02_AdjustableEqkRupForecast.
                                 BACK_SEIS_EXCLUDE);

    frankelForecast.getAdjustableParameterList().getParameter(
      Frankel02_AdjustableEqkRupForecast.FAULT_MODEL_NAME).setValue(
        frankelForecast.FAULT_MODEL_STIRLING);
    frankelForecast.getAdjustableParameterList().getParameter(
      Frankel02_AdjustableEqkRupForecast.RUP_OFFSET_PARAM_NAME).setValue(
        new Double(5.0));

    frankelForecast.getTimeSpan().setDuration(1.0);
    frankelForecast.updateForecast();
    LocationList locList = new LocationList();

    /**
     * Site List for Cybershake
     */

    locList.add(new Location(34.019200, -118.28600)); //USC
    locList.add(new Location(34.148427 , -118.17119)); //PAS
    locList.add(new Location(34.052041, -118.25713)); //LADT
    locList.add(new Location(33.754944 , -118.22300)); //LBP
    locList.add(new Location(34.041823 , -118.06530)); //WNGC
    locList.add(new Location(33.754111 , -117.86778)); //SABD
    locList.add(new Location(34.064986 , -117.29201)); //SBSM
    locList.add(new Location(34.336030 , -118.50862));//FFI
    locList.add(new Location(34.054884 , -118.41302));//CCP
    locList.add(new Location(34.009092 , -118.48939));//SMCA 

    //2nd set of sites for Cybershake
    //locList.addLocation(new Location(34.1977, -118.3566)); //Burbank Airport
    //locList.addLocation(new Location(34.2356, -118.5275)); //Northridge CSUN Campus
    /*locList.addLocation(new Location(34.00742,-118.239326 )); //Vernon
    locList.addLocation(new Location(33.957493,-118.22975)); //SouthGate
    locList.addLocation(new Location(33.92221,-118.223104 )); //North Compton
    locList.addLocation(new Location(33.866282,-118.211689 )); //Dominquez Hills
    locList.addLocation(new Location(33.98750,-117.46211));//Pedley-1
    locList.addLocation(new Location(34.39545,-118.0801));//Gleason Road
    locList.addLocation(new Location(34.4202,-118.0967 ));//Aliso Canyon
    locList.addLocation(new Location(34.5895,-117.8481 ));//Lovejoy Buttes*/


    FileWriter fw = null;
    try {
      fw = new FileWriter("Sites_1_DistanceBounds_Cybershake.txt");
    }
    catch (IOException ex1) {
      ex1.printStackTrace();
    }
    double regionMinLat=Double.POSITIVE_INFINITY,regionMaxLat=Double.NEGATIVE_INFINITY,
    regionMinLon=Double.POSITIVE_INFINITY,regionMaxLon=Double.NEGATIVE_INFINITY;
    
    Iterator<Location> it = locList.iterator();
    while (it.hasNext()) {
      Location loc = it.next();

      //creating the Site object
      Site site = new Site(loc);
      //Creating the STF Generator object
      ERF2RuptureForSTF_Generator calc = new ERF2RuptureForSTF_Generator(frankelForecast, site, 200.0);

      //calling the function to generate the rupture files with directory name.
      //calc.getEqkRupturesAsStringNearSite("Temp");
      Region region = null;
      try {
        region = calc.getSiteRegionBounds();
        double maxDepth = calc.getMaxDepthForRuptureInRegionBounds();
        double minLat = region.getMinLat();
        double maxLat = region.getMaxLat();
        double minLon = region.getMinLon();
        double maxLon = region.getMaxLon();
        double distanceSWSE = LocationUtils.horzDistanceFast(
        		new Location(minLat,minLon),
        		new Location(minLat, maxLon));
        double distanceNWSW = LocationUtils.horzDistanceFast(
        		new Location(minLat,minLon),
        		new Location(maxLat, minLon));
        if(regionMinLat > minLat)
        	regionMinLat = minLat;
        if(regionMaxLat < maxLat)
        	regionMaxLat = maxLat;
        if(regionMinLon > minLon)
        	regionMinLon = minLon;
        if(regionMaxLon < maxLon)
        	regionMaxLon = maxLon;
        try {
          fw.write("Site : Lat =" + loc.getLatitude() + "   Lon =" +
                   loc.getLongitude() + "\n");
          fw.write("Site Region Bounds :\n");
          fw.write("MinLat = " + minLat + "  MaxLat = " + maxLat + "  MinLon = " +
                   minLon + "  MaxLon = " + maxLon +
                   "  MaxDepth = " + maxDepth + "\n");
          fw.write("Length of the box along longitude = "+distanceSWSE+"\n");
          fw.write("Length of the box along latitude = "+distanceNWSW+"\n");
        }
        catch (IOException ex2) {
          ex2.printStackTrace();
        }

      }
      catch (RegionConstraintException ex) {
        ex.printStackTrace();
      }
      try {
        fw.write("\n\n\n");
      }
      catch (IOException ex4) {
        ex4.printStackTrace() ;
      }
    }
    try {
      fw.write("Region MinLat = " + regionMinLat +  "  Region MaxLat = " + regionMaxLat + " Region MinLon = " +
                regionMinLon + " Region MaxLon = " + regionMaxLon+"\n\n\n");
      fw.close();
    }
    catch (IOException ex3) {
      ex3.printStackTrace();
    }
  }

  /**
   * Creates the String represenation for the Prob Eqk Rupture, SRF file format
   * @return String
   */
  private String ruptureString(ProbEqkRupture rupture) {

    String rupInfo = "";
    rupInfo += "Probability = " + (float)rupture.getProbability() +"\n";
    rupInfo += "Magnitude = " + (float)rupture.getMag() +"\n";

    EvenlyGriddedSurfaceAPI surface = rupture.getRuptureSurface();
    double gridSpacing = (float)this.getGridSpacing(surface);
    rupInfo += "GridSpacing = " + gridSpacing +"\n";
    ListIterator it = rupture.getAddedParametersIterator();
    if (it != null) {
      while (it.hasNext()) {
        ParameterAPI param = (ParameterAPI) it.next();
        rupInfo += param.getName() + "=" + param.getValue() + "\n";
      }
    }

    double rake = rupture.getAveRake();
    double dip = surface.getAveDip();

    //Local Strike for each grid centered location on the rupture
    double[] localStrikeList = this.getLocalStrikeList(surface);

    EvenlyGriddedSurfaceAPI rupSurface = new EvenlyGridCenteredSurface(surface);
    int numRows = rupSurface.getNumRows();
    int numCols = rupSurface.getNumCols();
    rupInfo += "NumRows = "+numRows+"\n";
    rupInfo += "NumCols = "+numCols+"\n";
    rupInfo +="# Lat  Lon  Depth  Rake  Dip  Strike\n";
    for(int i=0;i<numRows;++i){
      for (int j = 0; j < numCols; ++j) {
        Location loc = rupSurface.getLocation(i,j);
        rupInfo += (float)loc.getLatitude() + "    " + (float)loc.getLongitude() + "    " +
            (float)loc.getDepth() +"   "+(float)rake+"    "+(float)dip+"   "+(float)localStrikeList[j]+"\n";
      }
    }
    return rupInfo;
  }

  /**
   * Returns the local strike list for a given rupture
   * @param surface GriddedSurfaceAPI
   * @return double[]
   */
  private double[] getLocalStrikeList(EvenlyGriddedSurfaceAPI surface){
    int numCols = surface.getNumCols();
    double[] localStrike = null;
    //if it not a point surface, then get the Azimuth(strike) for 2 neighbouring
    //horizontal locations on the rupture surface.
    //if it is a point surface then it will be just having one location so
    //in that we take the Ave. Strike for the Surface.
    if(! (surface instanceof PointSurface)){
      localStrike = new double[numCols - 1];
      for (int i = 0; i < numCols - 1; ++i) {
        Location loc1 = surface.getLocation(0, i);
        Location loc2 = surface.getLocation(0, i + 1);
        double strike = LocationUtils.azimuth(loc1, loc2);
        localStrike[i] = strike;
      }
    }
    else if(surface instanceof PointSurface) {
      localStrike = new double[1];
      localStrike[0]= surface.getAveStrike();
    }

    return localStrike;
  }



  /**
   * Returns the gridspacing between the 2 locations on the surface
   * @return double
   */
  private double getGridSpacing(EvenlyGriddedSurfaceAPI surface) {

    double gridSpacing = surface.getGridSpacingAlongStrike();
    // Ned added the following in case different grid spacings are implemented at some time (existing class breaks?)
    if(!surface.isGridSpacingSame()) throw new RuntimeException("may not work now that spacind down dip can differ from along strike");
    if(Double.isNaN(gridSpacing))
      return this.DEFAULT_GRID_SPACING_FOR_POINT_SURFACE;

    return gridSpacing;

  }


}
