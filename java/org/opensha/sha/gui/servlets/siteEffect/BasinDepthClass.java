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

package org.opensha.sha.gui.servlets.siteEffect;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;
import java.util.StringTokenizer;

import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;



/**
 * <p>Title: BasinDepthClass</p>
 * <p>Description:This class creates a gridded region from the given lat, lons
 * and gridSpacing. Then for each site in the gridded region gets the  Basindepth
 * values for each site in the region</p>
 * @author : Nitin Gupta
 * @created Feb 4,2004
 * @version 1.0
 */

public final class BasinDepthClass {


  //ArrayList for computing the lat and lons for the given gridded region
  ArrayList<Location> locations ;
  String basinDepthFile;
  boolean loadFromJar = false;
  /**
   * Class constructor
   * @param minLon
   * @param maxLon
   * @param minLat
   * @param maxLat
   * @param gridSpacing
   * @param fileName : Name of the Basin Depth file
   */
  public BasinDepthClass(double minLon, double maxLon, double minLat,
                                      double maxLat, double gridSpacing,String fileName) throws
      RegionConstraintException {

    prepareSitesInput(minLon,maxLon,minLat,maxLat,gridSpacing);
    basinDepthFile = fileName;
  }


  /**
   *
   * @param locList
   * @param fileName
   */
  public BasinDepthClass(LocationList locList,String fileName){
    int numLocations = locList.size();
    basinDepthFile = fileName;
    locations = new ArrayList();
    for(int i=0;i<numLocations;++i)
      locations.add(locList.get(i));
  }

  /**
   * Prepare the input of the all the location in the gridded region and provide that input
   * to compute the Basin Depth values for each region.
   * @param minLon
   * @param maxLon
   * @param minLat
   * @param maxLat
   * @param gridSpacing
   * @return
   */
  private void prepareSitesInput(double minLon, double maxLon, double minLat,
                                      double maxLat, double gridSpacing) throws
      RegionConstraintException {

    locations = new ArrayList<Location>();
    //GriddedRegion region = new GriddedRegion(minLat,maxLat,minLon,maxLon,gridSpacing);
    GriddedRegion region = new GriddedRegion(
    		new Location(minLat, minLon),
    		new Location(maxLat, maxLon),
    		gridSpacing, new Location(0,0));

    Iterator<Location> it = region.getNodeList().iterator();
    while(it.hasNext())
      locations.add(it.next());
  }

  public void setLoadFromJar(boolean jar) {
	  loadFromJar = jar;
  }


  /**
   *
   * @returns the ArrayList of the Basin Depth values for each site in the
   * gridded region.
   */
  public ArrayList getBasinDepth() {

    //gridSpacing for the basin depth file and adding a small amount ot it
    double gridSpacingForBasinDepthInFile = .01001;
    try {

      //open the File Input Stream to read the file
    	InputStreamReader input;
      if (loadFromJar)
    	  input = new InputStreamReader(this.getClass().getResourceAsStream(basinDepthFile));
      else
    	  input = new FileReader(basinDepthFile);
      BufferedReader iBuf= new BufferedReader(input);
      String str;
      // parsing the file line by line
      //reading the first line from the file
      str=iBuf.readLine();

      int size= locations.size();

      ArrayList bd= new ArrayList();

      //initializing the bd vector with the Double.NaN values
      for(int i=0;i<size;++i)
        bd.add(new Double(Double.NaN));
      
      double prevLat=Double.NaN;
      for(int i=0;i<size;++i){
        double lat = ((Location)locations.get(i)).getLatitude();
        double lon = ((Location)locations.get(i)).getLongitude();
        boolean latFlag= false;

        while(str!=null) {
          StringTokenizer st = new StringTokenizer(str);

          // parse this line from the file
          //reading the Lons from the file
          double valLat = Double.parseDouble(st.nextToken());
          //reading the Lat from the file
          double valLon = Double.parseDouble(st.nextToken());

          if((valLat -lat) > gridSpacingForBasinDepthInFile/2)
            // if this lat does not exist in file. Lat is always increasing in the file and the location vector
            break;

          // add basinDepth for new location
          if(Math.abs(lat-valLat) <= (gridSpacingForBasinDepthInFile/2))
            //System.out.println("Lat:"+lat+";valLat:"+valLat+";valLatNext:"+valLatNext);
            latFlag=true;

          //iterating over lon's for each lat
          if(((Math.abs(lon-valLon)) <= gridSpacingForBasinDepthInFile/2) && latFlag){
            //if we found the desired lon in the file ,
            //we get the value of the basinDepth for the nearest point
            //returns the actual value for the basinDepth
            bd.set(i,new Double(st.nextToken()));
            break;

          }

           //this condition checks if the lat exists but lon does not exist
          if((valLon-lon) > (gridSpacingForBasinDepthInFile/2 ) && latFlag)
            // if this location does not exist in this file
            break;

          // read next line
          str=iBuf.readLine();
        }
      }
      
      //returns the ArrayList containg the Basin Depth values for each gridded site
      return bd;
    }catch (Exception e) {
      e.printStackTrace();
    }
    return null;
  }


}
