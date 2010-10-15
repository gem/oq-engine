/**
 * 
 */
package org.opensha.sha.faultSurface;

import java.io.FileWriter;
import java.util.Iterator;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.util.FaultTraceUtils;

/**
 * This classe represents and approximately evenly gridded surface, where the
 * gridSpacing represents some average value.
 * 
 * We could add methods here like: getMinGridSpacing(), getMaxGridSpacing(),
 * etc.
 * 
 * @author field
 */
public class ApproxEvenlyGriddedSurface extends EvenlyGriddedSurface {

    // for debugging
    private final static boolean D = false;

    /**
	 * 
	 */
    private static final long serialVersionUID = 1L;

    /**
     * This constructor creates a blank surface enabling the user to populate
     * the surface any way they want
     * 
     * @param numRows
     * @param numCols
     * @param aveGridSpacing
     */
    public ApproxEvenlyGriddedSurface(int numRows, int numCols,
            double aveGridSpacing) {
        setNumRowsAndNumCols(numRows, numCols);
        gridSpacingAlong = aveGridSpacing;
        gridSpacingDown = aveGridSpacing;
        sameGridSpacing = true;
    }

    /**
     * This constructor takes an upper and lower fault trace, re-samples these
     * according the the given aveGridSpacing to represent the first and last
     * rows of the surface, and then fills in the intermediate rows by evenly
     * sampling a straight line between the top and bottom point of each column.
     * The number of columns is the average length the top and bottom trace
     * divided by the aveGridSpacing (plus 1), and the number of rows is the
     * average distance between the top and bottom points in each column divided
     * by the aveGridSpacing (plus 1). and then
     * 
     * @param numRows
     * @param numCols
     * @param aveGridSpacing
     */
    public ApproxEvenlyGriddedSurface(FaultTrace upperFaultTrace,
            FaultTrace lowerFaultTrace, double aveGridSpacing) {

        gridSpacingAlong = aveGridSpacing;
        gridSpacingDown = aveGridSpacing;
        sameGridSpacing = true;

        // check that the traces are both in the same order
        Location firstUpperLoc = upperFaultTrace.get(0);
        Location firstLowerLoc = lowerFaultTrace.get(0);
        Location lastLowerLoc = lowerFaultTrace.get(lowerFaultTrace.size() - 1);
        double firstFirstDist =
                LocationUtils.horzDistanceFast(firstUpperLoc, firstLowerLoc);
        double firstLastDist =
                LocationUtils.horzDistanceFast(firstUpperLoc, lastLowerLoc);
        if (firstLastDist < firstFirstDist) {
            lowerFaultTrace.reverse();
            if (D)
                System.out
                        .println("Needed to reversed lower trace to comply with upper trace");
        }

        // Now check that Aki-Richards convention is adhered to (fault dips to
        // right)
        double dipDir =
                LocationUtils.azimuth(upperFaultTrace.get(0),
                        lowerFaultTrace.get(0));
        double strikeDir = upperFaultTrace.getStrikeDirection();
        if ((strikeDir - dipDir) < 0 || (strikeDir - dipDir) > 180) {
            upperFaultTrace.reverse();
            lowerFaultTrace.reverse();
            if (D)
                System.out
                        .println("reversed trace order to adhere to Aki Richards");
        }

        // now compute num subsection of trace
        double aveTraceLength =
                (upperFaultTrace.getTraceLength() + lowerFaultTrace
                        .getTraceLength()) / 2;
        int num = (int) Math.round(aveTraceLength / aveGridSpacing);

        if (D)
            System.out.println("gridSpacing=" + gridSpacingAlong
                    + ", aveTraceLength=" + aveTraceLength + ", numCol=" + num);

        // get resampled traces (note that number of locs in trace will be
        // num+1)
        FaultTrace resampUpperTrace =
                FaultTraceUtils.resampleTrace(upperFaultTrace, num);
        FaultTrace resampLowerTrace =
                FaultTraceUtils.resampleTrace(lowerFaultTrace, num);

        if (D)
            System.out
                    .println("resample trace lengths: "
                            + resampUpperTrace.size() + " & "
                            + resampLowerTrace.size());
        // compute ave num columns
        double aveDist = 0;
        for (int i = 0; i < resampUpperTrace.size(); i++) {
            Location topLoc = resampUpperTrace.get(i);
            Location botLoc = resampLowerTrace.get(i);
            aveDist += LocationUtils.linearDistanceFast(topLoc, botLoc);
        }
        aveDist /= resampUpperTrace.size();
        int nRows = (int) Math.round(aveDist / aveGridSpacing) + 1;

        if (D)
            System.out.println("aveDist=" + aveDist + ", nRows=" + nRows);

        this.setNumRowsAndNumCols(nRows, num + 1); // note the plus 1!

        // now set the surface locations
        for (int c = 0; c < resampUpperTrace.size(); c++) {
            Location topLoc = resampUpperTrace.get(c);
            Location botLoc = resampLowerTrace.get(c);
            LocationVector dir = LocationUtils.vector(topLoc, botLoc);
            double horzIncr = dir.getHorzDistance() / (nRows - 1);
            double vertIncr = dir.getVertDistance() / (nRows - 1); // minus sign
                                                                   // because
                                                                   // vertDist
                                                                   // is pos up
                                                                   // and depth
                                                                   // is pos
                                                                   // down
            dir.setHorzDistance(horzIncr);
            dir.setVertDistance(vertIncr);
            this.setLocation(0, c, topLoc);
            Location prevLoc = topLoc;
            for (int r = 1; r < nRows; r++) {
                Location nextLoc = LocationUtils.location(prevLoc, dir);
                this.setLocation(r, c, nextLoc);
                prevLoc = nextLoc;
            }
            // double accuracyCheck = LocationUtils.linearDistanceFast(botLoc,
            // this.getLocation(nRows-1,c));
            // System.out.println("Distance between actual and computed bottom point = "+(float)accuracyCheck);

            // override last location
            // this.setLocation(nRows-1, c, botLoc);
        }

        Location loc1 = resampLowerTrace.get(resampLowerTrace.size() - 1);
        Location loc2 = this.getLocation(numRows - 1, numCols - 1);
        if (D)
            System.out
                    .println("DeltaLat = "
                            + (float) ((loc1.getLatitude() - loc2.getLatitude()) * 111));
        if (D)
            System.out
                    .println("DeltaLon = "
                            + (float) ((loc1.getLongitude() - loc2
                                    .getLongitude()) * 111));
        if (D)
            System.out.println("DeltaDepth = "
                    + (float) (loc1.getDepth() - loc2.getDepth()));

        if (D)
            System.out.println(resampLowerTrace
                    .get(resampLowerTrace.size() - 1).toString());
        if (D)
            System.out.println(resampUpperTrace
                    .get(resampLowerTrace.size() - 1).toString());

    }

    /**
     * This explores an accuracy issue (final depth is right be lats and lons
     * are more off)
     */
    public static void test1(Location l1, Location l2) {
        System.out.println("TEST-1");
        // Location topLoc = new Location(-34.36338,-71.32979,50.0);
        // Location botLoc = new Location(-33.94507,-72.7105,10.0);
        double numSubdivisions = 100;
        LocationVector dir = LocationUtils.vector(l1, l2);
        System.out.println("Azimuth p1 to p2: " + dir.getAzimuth());
        double horzIncr = dir.getHorzDistance() / numSubdivisions;
        double vertIncr = dir.getVertDistance() / numSubdivisions; // minus sign
                                                                   // because
                                                                   // vertDist
                                                                   // is pos up
                                                                   // and depth
                                                                   // is pos
                                                                   // down
        dir.setHorzDistance(horzIncr);
        dir.setVertDistance(vertIncr);
        Location prevLoc = l1;
        for (int r = 0; r < numSubdivisions; r++) {
            Location nextLoc = LocationUtils.location(prevLoc, dir);
            prevLoc = nextLoc;
        }
        double accuracyCheck = LocationUtils.linearDistanceFast(l2, prevLoc);
        System.out
                .println("Distance between actual and computed bottom point = "
                        + (float) accuracyCheck);
        System.out.println("DeltaLat = "
                + (float) ((l2.getLatitude() - prevLoc.getLatitude()) * 111));
        System.out.println("DeltaLon = "
                + (float) ((l2.getLongitude() - prevLoc.getLongitude()) * 111));
        System.out.println("DeltaDepth = "
                + (float) (l2.getDepth() - prevLoc.getDepth()));
        System.out.println("");
    }

    public static void test2(Location l1, Location l2) {
        System.out.println("TEST-2");
        double numSubdivisions = 100;
        LocationVector dir = LocationUtils.vector(l1, l2);
        double horzIncr = dir.getHorzDistance() / numSubdivisions;
        double vertIncr = dir.getVertDistance() / numSubdivisions; // minus sign
                                                                   // because
                                                                   // vertDist
                                                                   // is pos up
                                                                   // and depth
                                                                   // is pos
                                                                   // down
        dir.setHorzDistance(horzIncr);
        dir.setVertDistance(vertIncr);
        Location prevLoc = l1;
        for (int r = 0; r < numSubdivisions; r++) {
            Location nextLoc = LocationUtils.location(prevLoc, dir);
            prevLoc = nextLoc;
            dir.setAzimuth(LocationUtils.azimuth(prevLoc, l2));
        }
        double accuracyCheck = LocationUtils.linearDistanceFast(l2, prevLoc);
        System.out
                .println("Distance between actual and computed bottom point = "
                        + (float) accuracyCheck);
        System.out.println("DeltaLat = "
                + (float) ((l2.getLatitude() - prevLoc.getLatitude()) * 111));
        System.out.println("DeltaLon = "
                + (float) ((l2.getLongitude() - prevLoc.getLongitude()) * 111));
        System.out.println("DeltaDepth = "
                + (float) (l2.getDepth() - prevLoc.getDepth()));
        System.out.println("");
    }

    /**
     * Add a Location to the grid - does the same thing as set except that it
     * ensures the object is a Location object.
     * 
     * @param row
     *            The row to set this Location at.
     * @param column
     *            The column to set this Location at.
     * @param location
     *            The new location value.
     * @exception ArrayIndexOutOfBoundsException
     *                Thrown if the row or column lies beyond the grid space
     *                indexes.
     */
    public void setLocation(int row, int column, Location location) {
        super.setLocation(row, column, location);
    }

    public void writeXYZ_toFile(String fileName) {
        try {
            FileWriter fw = new FileWriter(fileName);
            fw.write("lat\tlon\tdepth\n");
            Iterator<Location> it = this.getLocationsIterator();
            while (it.hasNext()) {
                Location loc = (Location) it.next();
                fw.write(loc.getLatitude() + "\t" + loc.getLongitude() + "\t"
                        + loc.getDepth() + "\n");
            }
            fw.close();
        } catch (Exception e) {
            e.printStackTrace();
        }

    }

    /**
     * This computes the average grid spacing for adjacent locations along
     * strike (averaged over all rows as well)
     * 
     * @return
     */
    public double computeAveGridSpacingAlongStrike() {
        double aveDist = 0;
        int num = 0;
        for (int r = 0; r < numRows; r++)
            for (int c = 0; c < numCols - 1; c++) {
                aveDist +=
                        LocationUtils.linearDistanceFast(getLocation(r, c),
                                getLocation(r, c + 1));
                num += 1;
            }
        return aveDist / num;
    }

    /**
     * This computes the average grid spacing for adjacent locations down dip
     * (averaged over all cols as well)
     * 
     * @return
     */
    public double computeAveGridSpacingDownDip() {
        double aveDist = 0;
        int num = 0;
        for (int c = 0; c < numCols; c++)
            for (int r = 0; r < numRows - 1; r++) {
                aveDist +=
                        LocationUtils.linearDistanceFast(getLocation(r, c),
                                getLocation(r + 1, c));
                num += 1;
            }
        return aveDist / num;
    }

    /**
     * @param args
     */
    public static void main(String[] args) {

        // //these traces come from the file "sub-ch9-z4.in" from the NSHMP 2008
        // model (South America subduction zone)
        // FaultTrace topTrace = new FaultTrace(null);
        //
        // topTrace.addLocation(-33.9450824793, -72.710497654, 10.);
        // topTrace.addLocation(-33.7588818362, -72.6388800048, 10.);
        // topTrace.addLocation(-33.5399999996, -72.5818237309, 10.);
        // topTrace.addLocation(-32.9000000001, -72.4949902347, 10.);
        // topTrace.addLocation(-31.9400000003, -72.4908227539, 10.);
        // topTrace.addLocation(-30.2999999998, -72.3911303709, 10.);
        // topTrace.addLocation(-29.9600000004, -72.3579357913, 10.);
        // topTrace.addLocation(-29.2320361332, -72.2279632571, 10.);
        // topTrace.addLocation(-28.0045263675, -71.9045263674, 10.);
        // topTrace.addLocation(-26.8599999996, -71.6779882813, 10.);
        // topTrace.addLocation(-25.9555615232, -71.584437256, 10.);
        // topTrace.addLocation(-25.1200000003, -71.4298706053, 10.);
        // topTrace.addLocation(-24.7841723632, -71.3841735843, 10.);
        // topTrace.addLocation(-23.0199999996, -71.2632910159, 10.);
        // topTrace.addLocation(-22.22, -71.1589331058, 10.);
        // topTrace.addLocation(-21.8942095629, -71.1322380371, 10.);
        //
        // FaultTrace botTrace = new FaultTrace(null);
        //
        // botTrace.addLocation(-34.3633763178, -71.3297920084, 50.);
        // botTrace.addLocation(-34.02, -71.1744982909, 50.);
        // botTrace.addLocation(-33.7199999999, -71.0928930662, 50.);
        // botTrace.addLocation(-33.4399999999, -71.0548120114, 50.);
        // botTrace.addLocation(-32.6400000002, -70.993572998, 50.);
        // botTrace.addLocation(-32.2813330081, -70.9813330075, 50.);
        // botTrace.addLocation(-31.9799999997, -70.9924999998, 50.);
        // botTrace.addLocation(-31.3460058597, -71.1060070798, 50.);
        // botTrace.addLocation(-31.093046875, -71.1330468748, 50.);
        // botTrace.addLocation(-30.8200000004, -71.1281042477, 50.);
        // botTrace.addLocation(-30.5200000003, -71.0938342283, 50.);
        // botTrace.addLocation(-29.6231591798, -70.9168408208, 50.);
        // botTrace.addLocation(-28.1739575199, -70.5260412594, 50.);
        // botTrace.addLocation(-26.872775879, -70.2672241207, 50.);
        // botTrace.addLocation(-26.2200000001, -70.1064562992, 50.);
        // botTrace.addLocation(-25.9844946293, -70.0644934082, 50.);
        // botTrace.addLocation(-25.7599999999, -70.0563464355, 50.);
        // botTrace.addLocation(-25.1999999999, -70.0945446773, 50.);
        // botTrace.addLocation(-24.9400000001, -70.0942907718, 50.);
        // botTrace.addLocation(-22.5600000003, -69.8766857908, 50.);
        // botTrace.addLocation(-22.0599999998, -69.855518799, 50.);
        // botTrace.addLocation(-21.5010148695, -69.8649200561, 50.);
        //
        // ApproxEvenlyGriddedSurface surf = new
        // ApproxEvenlyGriddedSurface(topTrace,botTrace,5);
        // // surf.writeXYZ_toFile("dev/scratch/ned/hereItIs.txt");
        //
        // System.out.println
        // ("AveGridSpacingAlongStrike="+surf.computeAveGridSpacingAlongStrike());
        // System.out.println
        // ("AveGridSpacingDownDip="+surf.computeAveGridSpacingDownDip());
        //
        // surf.test();

        // lat aligned
        Location top1 = new Location(20.0, 0.0, 10.0);
        Location bot1 = new Location(40.0, 0.0, 50.0);

        // ln aligned
        Location top2 = new Location(40.0, 0.0, 10.0);
        Location bot2 = new Location(40.0, 20.0, 50.0);

        test1(top1, bot1);
        test1(top2, bot2);

        test2(top1, bot1);
        test2(top2, bot2);

    }

    /*
     * 16 Zone 4 top 4 -33.9450824793 -72.710497654 10. -33.7588818362
     * -72.6388800048 10. -33.5399999996 -72.5818237309 10. -32.9000000001
     * -72.4949902347 10. -31.9400000003 -72.4908227539 10. -30.2999999998
     * -72.3911303709 10. -29.9600000004 -72.3579357913 10. -29.2320361332
     * -72.2279632571 10. -28.0045263675 -71.9045263674 10. -26.8599999996
     * -71.6779882813 10. -25.9555615232 -71.584437256 10. -25.1200000003
     * -71.4298706053 10. -24.7841723632 -71.3841735843 10. -23.0199999996
     * -71.2632910159 10. -22.22 -71.1589331058 10. -21.8942095629
     * -71.1322380371 10. 22 bottom 4 -34.3633763178 -71.3297920084 50. -34.02
     * -71.1744982909 50. -33.7199999999 -71.0928930662 50. -33.4399999999
     * -71.0548120114 50. -32.6400000002 -70.993572998 50. -32.2813330081
     * -70.9813330075 50. -31.9799999997 -70.9924999998 50. -31.3460058597
     * -71.1060070798 50. -31.093046875 -71.1330468748 50. -30.8200000004
     * -71.1281042477 50. -30.5200000003 -71.0938342283 50. -29.6231591798
     * -70.9168408208 50. -28.1739575199 -70.5260412594 50. -26.872775879
     * -70.2672241207 50. -26.2200000001 -70.1064562992 50. -25.9844946293
     * -70.0644934082 50. -25.7599999999 -70.0563464355 50. -25.1999999999
     * -70.0945446773 50. -24.9400000001 -70.0942907718 50. -22.5600000003
     * -69.8766857908 50. -22.0599999998 -69.855518799 50. -21.5010148695
     * -69.8649200561 50.
     */

}
