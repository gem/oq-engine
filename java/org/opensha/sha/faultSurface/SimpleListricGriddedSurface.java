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

package org.opensha.sha.faultSurface;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.exceptions.FaultException;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.util.FaultUtils;





/**
 * <b>Title:</b> SimpleListricGriddedFaultFactory.   <br>
 * <b>Description: This creates an EvenlyGriddedSurface for a listric fault
 * (a fault where dip changes with depth).  As with the StirlingGriddedSurface,
 * grid points are projected down at an angle perpendicular to the end points of
 * the faultTrace.<br>NOTE: this assumes that all depths in the fault trace are
 * the same as the first depth in the ArrayList (this is check for).<br>  Accuracy Note:
 * the bending points can be off by up to the gridSpacing (this could be fixed).
</b> <br>
 * <b>Copyright:</b> Copyright (c) 2001<br>
 * <b>Company:</b> <br>
 * @author Ned Field.
 * @version 1.0
 */

public class SimpleListricGriddedSurface extends EvenlyGriddedSurface {

  /**
	 * 
	 */
	private static final long serialVersionUID = 1L;
protected final static String C = "SimpleListricGriddedFaultFactory";
    protected final static boolean D = false;

    protected final static double PI_RADIANS = Math.PI / 180;

    /**
     * The fault trace to use.
     */
    protected FaultTrace faultTrace;

    /**
     * A ArrayList of Double objects representing the dips (from top to
     * bottom) over the various depth intervals.  The number of elements here must be
     * one less that those in the depths ArrayList.
     */
    protected ArrayList<Double> dips;

    /**
     * A ArrayList of Double objects representing the depth intervals on the fault
     * surface (from top to bottom).  This must have one more element that the dips ArrayList.
     */
    protected ArrayList<Double> depths;


    public SimpleListricGriddedSurface( FaultTrace faultTrace,
                                        ArrayList<Double> dips,
                                        ArrayList<Double> depths,
                                        double gridSpacing )
                                        throws FaultException {

            this.faultTrace = faultTrace;
            this.dips = dips;
            this.depths = depths;
            this.gridSpacingAlong = gridSpacing;
            this.gridSpacingDown = gridSpacing;
            this.sameGridSpacing = true;
            if(D){
              System.out.println("FaultTrace: "+faultTrace.toString()+"\n"+
                                 "gridSpacing :"+gridSpacing);

              System.out.println("Depths :");
              for(int i=0;i<depths.size();++i)
                System.out.println(i+1+": "+depths.get(i) );
              System.out.println("\nDips :");
              for(int i=0;i<dips.size();++i)
                System.out.println(i+1+": "+dips.get(i) );
            }
            createEvenlyGriddedSurface();
    }


    /**
     * This method creates the EvenlyGriddedSurface for the Listric fault.
     * @return
     * @throws FaultException
     */
    private void createEvenlyGriddedSurface()throws FaultException {

        String S = C + ": createEvenlyGriddedSurface():";

        if( D ) System.out.println(S + "Starting");

        assertValidData();

        final int numSegments = faultTrace.getNumLocations() - 1;

        double[] segmentLenth = new double[numSegments];
        double[] segmentAzimuth = new double[numSegments];
        double[] segmentCumLenth = new double[numSegments];

        double cumDistance = 0;
        int i = 0;

       // Find aveDipDirection (defined by end locations):
        Location firstLoc = faultTrace.get(0);
        Location lastLoc = faultTrace.get(faultTrace.getNumLocations() - 1);;
        LocationVector aveDir = LocationUtils.vector(firstLoc, lastLoc);
        if(D) System.out.println("aveDir.getAzimuth(): = " + aveDir.getAzimuth());
        double aveDipDirection = ( aveDir.getAzimuth() + 90 );




        // Iterate over each Location in Fault Trace
        // Calculate distance, cumulativeDistance and azimuth for
        // each segment
        Iterator<Location> it = faultTrace.iterator();
        firstLoc = it.next();
        lastLoc = firstLoc;
        Location loc = null;
        LocationVector dir = null;
        while( it.hasNext() ){

            loc = it.next();
            dir = LocationUtils.vector(lastLoc, loc);

            double azimuth = dir.getAzimuth();
            double distance = dir.getHorzDistance();
            cumDistance += distance;

            segmentLenth[i] = distance;
            segmentAzimuth[i] = azimuth;
            segmentCumLenth[i] = cumDistance;

            i++;
            lastLoc = loc;

        }

        // Calculate down dip width & ave dip
        double downDipWidth = 0;
        double totVert=0, totHorz=0;
        double depth, dip;
        double depthLast = ( (Double) depths.get(0) ).doubleValue();
        for(i=1; i<depths.size(); i++) {
              depth = ( (Double) depths.get(i) ).doubleValue();
              dip = ( (Double) dips.get(i-1) ).doubleValue();
              downDipWidth += Math.abs(depth-depthLast) / Math.sin(dip*PI_RADIANS);
              totVert += depth-depthLast;
              totHorz += Math.abs(depth-depthLast) / Math.tan(dip*PI_RADIANS);
              depthLast = depth;
        }

        aveDip = Math.atan(totVert/totHorz) / PI_RADIANS;

        // Calculate the number of rows and columns
        int rows = 1 + Math.round((float) (downDipWidth/gridSpacingDown));
        int cols = 1 + Math.round((float) (segmentCumLenth[numSegments - 1] / gridSpacingAlong));


        if(D) System.out.println("numLocs: = " + faultTrace.getNumLocations());
        if(D) System.out.println("numSegments: = " + numSegments);
        if(D) System.out.println("firstLoc: = " + firstLoc);
        if(D) System.out.println("lastLoc(): = " + lastLoc);
        if(D) System.out.println("downDipWidth: = " + downDipWidth);
        if(D) System.out.println("totTraceLength: = " + segmentCumLenth[ numSegments - 1]);
        if(D) System.out.println("numRows: = " + rows);
        if(D) System.out.println("numCols: = " + cols);
        if(D) System.out.println("aveDip: = " + aveDip);


        // Create GriddedSurface
        int segmentNumber, ith_row, ith_col = 0;
        double distanceAlong, distance, hDistance, vDistance;
        Location location1;

        //initialize the num of Rows and Cols for the container2d object that holds
        setNumRowsAndNumCols(rows,cols);

        // Loop over each column - ith_col is ith grid step along the fault trace
        if( D ) System.out.println(S + "Iterating over columns up to " + cols );
        while( ith_col < cols ){

            if( D ) System.out.println(S + "ith_col = " + ith_col);

            // calculate distance from column number and grid spacing
            distanceAlong = ith_col * gridSpacingAlong;
            if( D ) System.out.println(S + "distanceAlongFault = " + distanceAlong);

            // Determine which segment distanceAlong is in
            segmentNumber = 1;
            while( segmentNumber <= numSegments && distanceAlong > segmentCumLenth[ segmentNumber - 1] ){
                segmentNumber++;
            }
            // put back in last segment if grid point has just barely stepped off the end
            if( segmentNumber == numSegments+1) segmentNumber--;

            if( D ) System.out.println(S + "segmentNumber " + segmentNumber );

            // Calculate the distance from the last segment point
            if ( segmentNumber > 1 ) distance = distanceAlong - segmentCumLenth[ segmentNumber - 2 ];
            else distance = distanceAlong;
            if( D ) System.out.println(S + "distanceFromLastSegPt " + distance );

            // Calculate the grid location along fault trace and put into grid
            location1 = faultTrace.get( segmentNumber - 1 );
//            dir = new LocationVector(0, distance, segmentAzimuth[ segmentNumber - 1 ], 0);
            dir = new LocationVector(segmentAzimuth[ segmentNumber - 1 ], distance, 0);

            // location on the trace
            Location topLocation = LocationUtils.location( location1, dir  );

            setLocation(0, ith_col, topLocation.clone());
            if( D ) System.out.println(S + "(x,y) topLocation = (0, " + ith_col + ") " + topLocation );

            // Loop over each row - calculating location at depth along the fault trace
            dip = ( (Double) dips.get(0) ).doubleValue();
            hDistance = gridSpacingDown * Math.cos( dip*PI_RADIANS );
            vDistance = gridSpacingDown * Math.sin( dip*PI_RADIANS );
            //vDistance = -gridSpacing * Math.sin( dip*PI_RADIANS );
//            dir = new LocationVector(vDistance, hDistance, aveDipDirection, 0);
            dir = new LocationVector(aveDipDirection, hDistance, vDistance);
            int depthNum = 1;
            Location lastLocation = topLocation;
            ith_row = 1;
            while(ith_row < rows){

                if( D ) System.out.println(S + "ith_row = " + ith_row);
                if( D ) System.out.println(S + "dip = " + dip + "; hDist = " + dir.getHorzDistance()
                                              + "; vDist = " + dir.getVertDistance() );

                Location nextLocation = LocationUtils.location( lastLocation, dir );
                setLocation(ith_row, ith_col, nextLocation.clone());

                if( D ) System.out.println(S + "(x,y) nextLocation = (" + ith_row + ", " + ith_col + ") " + nextLocation );

                // Change dir if dip has changed
                if( nextLocation.getDepth() > ((Double) depths.get(depthNum)).doubleValue() &&
                    ith_row != rows-1 ) {
                      dip = ( (Double) dips.get(depthNum) ).doubleValue();
                      hDistance = gridSpacingDown * Math.cos( dip*PI_RADIANS );
                      vDistance = gridSpacingDown * Math.sin( dip*PI_RADIANS );
                      //vDistance = -gridSpacing * Math.sin( dip*PI_RADIANS );
//                      dir = new LocationVector(vDistance, hDistance, aveDipDirection, 0);
                      dir = new LocationVector(aveDipDirection, hDistance, vDistance);
                      depthNum++;
                }
                lastLocation = nextLocation;
                ith_row++;
            }
            ith_col++;
        }

        if( D ) System.out.println(S + "Ending");
        setAveDip(aveDip);
    }




    /**
     * This method checks the input data.
     * @throws FaultException
     */
    protected void assertValidData() throws FaultException {

        // check the dips
        ListIterator<Double> it1 = dips.listIterator();
        while(it1.hasNext()) {
          FaultUtils.assertValidDip( ((Double)it1.next()).doubleValue() );
        }

        // check the depths
        ListIterator<Double> it2 = depths.listIterator();
        // store the first one
        double depth = ((Double)it2.next()).doubleValue();
        FaultUtils.assertValidDepth(depth);
        double lastDepth = depth;
        double nextDepth;
        while(it2.hasNext()) {
          nextDepth = ((Double)it2.next()).doubleValue();
          FaultUtils.assertValidDepth( nextDepth );
          if(nextDepth < lastDepth)
              throw new FaultException(C + "Fault depths must be monotonically increasing");
          lastDepth = nextDepth;
        }

        // makes sure numDepths = numDips+1
        if( depths.size() != dips.size() + 1 )
            throw new FaultException(C + "Number of Depths must equal Number of Dips + 1");

        // check the faultTrace data
        if( faultTrace == null ) throw new FaultException(C + "Fault Trace is null");

        Iterator<Location> it = faultTrace.iterator();
        while(it.hasNext()) {
          if(it.next().getDepth() != depth){
            throw new FaultException(C + "All depths of faultTrace locations must be same as the first depth in the depths ArrayList");
          }
        }

        if( !(gridSpacingAlong > 0.0) ) throw new FaultException(C + "invalid gridSpacing");

    }

    /**
     * Sets the AveDip.
     * @param aveDip double
     * @throws FaultException
     */
    private void setAveDip(double aveDip) throws FaultException {
      FaultUtils.assertValidDip(aveDip);
      this.aveDip = aveDip;
    }


    /**
     * This is to test this factory using PEER's Fault E in their test-case set #2.
     * @param args
     */
    public static void main(String[] args) {

//         FaultTrace faultTrace = new FaultTrace("test");
//         faultTrace.addLocation(new Location(38.22480, -122.0, 0.0));
//         faultTrace.addLocation(new Location(38.00000, -122.0, 0.0));
//         faultTrace.addLocation(new Location(37.80000, -122.2, 0.0));
//
//         ArrayList dips = new ArrayList();
//         dips.add(new Double(60.0));
//         dips.add(new Double(45.0));
//
//         ArrayList depths = new ArrayList();
//         depths.add(new Double(0.0));
//         depths.add(new Double(5.0));
//         depths.add(new Double(10.0));
//
//         SimpleListricGriddedSurface test = new SimpleListricGriddedSurface(
//                                        faultTrace,
//                                        dips,
//                                        depths,
//                                        1.0 );
//
//
//         Iterator it = test.getLocationsIterator();
//         Location loc;
//         while (it.hasNext()) {
//            loc = (Location) it.next();
//            System.out.println(loc.getLatitude() +"  "+loc.getLongitude()+"  "+loc.getDepth());
//         }

         FaultTrace faultTrace = new FaultTrace("test");
         faultTrace.add(new Location(20.0, -120.0, 0.0));
         faultTrace.add(new Location(20.2, -120.0, 0.0));

         ArrayList<Double> dips = new ArrayList<Double>();
         dips.add(new Double(60.0));
         dips.add(new Double(45.0));

         ArrayList<Double> depths = new ArrayList<Double>();
         depths.add(new Double(0.0));
         depths.add(new Double(5.0));
         depths.add(new Double(10.0));

         SimpleListricGriddedSurface test = new SimpleListricGriddedSurface(
                                        faultTrace,
                                        dips,
                                        depths,
                                        5.0 );


         Iterator<Location> it = test.getLocationsIterator();
         Location loc;
         while (it.hasNext()) {
            loc = it.next();
            System.out.println(loc.getLatitude() +"  "+loc.getLongitude()+"  "+loc.getDepth());
         }

    }
}
