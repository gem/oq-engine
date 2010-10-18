package org.gem.engine.hazard.parsers.japan;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class RectangularFaultData {

    private static boolean INFO = true;

    private int id;
    private String name;
    private String occurrenceModelLabel;
    private double averageActivity;
    private double newActivity;
    private double alpha;
    private double magnitude;
    private String source;
    private String sourceTypology;
    private double slip;
    private int idSecondary;
    private double lon;
    private double lat;
    private double depth;
    private double rectangleLenght;
    private double rectangleWidth;
    private double strike;
    private double dip;

    public RectangularFaultData(String line) {

        String[] aa = line.split(",");
        this.id = Integer.valueOf(aa[0]).intValue();
        this.name = aa[1];
        this.occurrenceModelLabel = aa[2];
        this.averageActivity = 1.0 / Double.valueOf(aa[3]).doubleValue(); // rate
        this.newActivity = 1.0 / Double.valueOf(aa[4]).doubleValue(); // rate
        this.alpha = Double.valueOf(aa[5]).doubleValue();
        this.magnitude = Double.valueOf(aa[6]).doubleValue();
        this.source = aa[7];
        this.sourceTypology = aa[8];
        if (aa[9].matches("\\d"))
            this.slip = Double.valueOf(aa[9]).doubleValue();
        this.idSecondary = 0;
        this.idSecondary = Integer.valueOf(aa[11]).intValue();
        this.lon = Double.valueOf(aa[12]).doubleValue();
        this.lat = Double.valueOf(aa[13]).doubleValue();
        this.depth = Double.valueOf(aa[16]).doubleValue();
        this.rectangleLenght = Double.valueOf(aa[22]).doubleValue();
        this.rectangleWidth = Double.valueOf(aa[23]).doubleValue();
        this.strike = Double.valueOf(aa[24]).doubleValue();
        this.dip = Double.valueOf(aa[25]).doubleValue();

        if (INFO) {
            System.out.printf("\nFault id ..............: %d-%d\n", this.id,
                    this.idSecondary);
            System.out.printf("Fault name ............: %s\n", this.name);
            System.out
                    .printf("Fault magnitude .......: %.2f\n", this.magnitude);
            System.out.printf("Fault lenght ..........: %6.2e\n",
                    this.rectangleLenght);
            System.out.printf("Fault width ...........: %6.2e\n",
                    this.rectangleWidth);
            System.out.printf("Fault strike ..........: %+6.2f\n", this.strike);
            System.out.printf("Fault dip .............: %+6.2f\n", this.dip);
            System.out.printf("Fault activity rate ...: %+10.8f\n",
                    this.averageActivity);
        }
    }

    public GEMFaultSourceData getFaultSourceData() {

        // Create the fault trace
        Location loc1 = new Location(this.lat, this.lon, this.depth);
        if (this.strike > 180)
            this.strike -= 360;
        // Location loctmp =
        // RelativeLocation.location(loc1,strike/180.0*Math.PI,this.rectangleLenght);
        Location loctmp =
                LocationUtils.location(loc1, strike / 180.0 * Math.PI,
                        this.rectangleLenght);
        if (INFO) {
            System.out.printf("  Fault origin   : %6.2f %6.2f\n", this.lon,
                    this.lat);
            System.out.printf("  Fault end point: %6.2f %6.2f\n",
                    loctmp.getLongitude(), loctmp.getLatitude());
        }

        System.out.printf("New fault strike .......: %+6.2f\n", this.strike);
        FaultTrace trace = new FaultTrace(String.format("%d", this.id));
        Location loc2 =
                new Location(loctmp.getLatitude(), loctmp.getLongitude(),
                        this.depth);
        if (this.dip > 90.0) {
            trace.add(loc2);
            trace.add(loc1);
            this.dip = 180.0 - this.dip;
            System.out.println("reverting");
        } else {
            trace.add(loc1);
            trace.add(loc2);
        }

        // Magnitude-frequency distribution - mmin, mmax, numInt
        IncrementalMagFreqDist mfd =
                new IncrementalMagFreqDist(this.magnitude, this.magnitude, 1);
        mfd.add(0, this.averageActivity);

        // Lower seismogenic depth
        double seismDepthLow =
                this.depth + this.rectangleWidth
                        * Math.sin(this.dip / 180.0 * Math.PI);

        if (INFO)
            System.out.println(this.id);

        // Checking dip value
        if (dip > 90.0 || this.dip < 0.0) {
            System.out.println("ID" + id + " dip:" + dip);
            throw new RuntimeException("dip out of range");
        }

        // Checking depth value
        if (depth < 0.0) {
            System.out.println("ID" + id + " depth:" + depth);
            throw new RuntimeException("depth out of range");
        }

        // Checking Seismogenic layer
        if (seismDepthLow < this.depth) {
            System.out.println("ID" + id + " Depth upp:" + depth + " Depth low"
                    + seismDepthLow);
            throw new RuntimeException("inconsistent depths");
        }

        // Create the GEM fault source data
        GEMFaultSourceData srcData =
                new GEMFaultSourceData(String.format("%d", this.id), this.name,
                        TectonicRegionType.ACTIVE_SHALLOW, mfd, trace,
                        this.dip, -90.0, seismDepthLow, this.depth, true);

        return srcData;
    }
}
