package org.gem.engine.hazard.parsers;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.faultSurface.ApproxEvenlyGriddedSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class GemFileParser {

    protected ArrayList<GEMSourceData> srcDataList;
    private static boolean INFO = false;

    /**
     * This gives the list of GEMSourceData parsed from the input ascii file
     * 
     * @return srcDataList
     */
    public ArrayList<GEMSourceData> getList() {
        return this.srcDataList;
    }

    /**
     * This is just for testing purposed and will be removed
     */
    public ArrayList<GEMSourceData> getList(ArrayList<GEMSourceData> lst) {
        return this.srcDataList;
    }

    /**
     * This is just for testing purposed and will be removed
     */
    public void setList(ArrayList<GEMSourceData> lst) {
        this.srcDataList = lst;
    }

    // /**
    // * This is just for testing purposed and will be removed
    // */
    // public ArrayList<GEMSourceData> getList(){
    // return this.srcDataList;
    // }

    /**
     * 
     * @return number of source data objects
     */
    public int getNumSources() {
        return this.srcDataList.size();
    }

    /**
     * This writes to a file the coordinates of the polygon. The format of the
     * outfile is compatible with the GMT psxy multiple segment file. The
     * separator adopted here is the default separator suggested in GMT (i.e.
     * '>')
     * 
     * @param file
     * @throws IOException
     */
    public void writeAreaGMTfile(FileWriter file) throws IOException {
        BufferedWriter out = new BufferedWriter(file);

        // Search for area sources
        int idx = 0;
        for (GEMSourceData dat : srcDataList) {
            if (dat instanceof GEMAreaSourceData) {

                if (INFO)
                    System.out.println("===" + dat.getID() + " "
                            + dat.getName());

                // Get the polygon vertexes
                GEMAreaSourceData src = (GEMAreaSourceData) dat;

                // Get polygon area
                double area = src.getArea();
                if (INFO)
                    System.out.printf("Area: %6.2e", area);

                // Total scalar seismic moment above m
                double totMom = 0.0;
                double momRate = 0.0;
                double magThreshold = 5.0;

                for (IncrementalMagFreqDist mfdffm : src
                        .getMagfreqDistFocMech().getMagFreqDistList()) {
                    EvenlyDiscretizedFunc momRateDist =
                            mfdffm.getMomentRateDist();

                    if (INFO)
                        System.out.println("MinX " + momRateDist.getMinX()
                                + " MaxX" + momRateDist.getMaxX());
                    if (INFO)
                        System.out.println("Mo(idx5):"
                                + src.getMagfreqDistFocMech().getMagFreqDist(0)
                                        .getMomentRate(5));

                    for (int i = 0; i < momRateDist.getNum(); i++) {
                        if (momRateDist.get(i).getX() >= magThreshold) {
                            totMom += momRateDist.get(i).getY();
                            if (INFO)
                                System.out.println(i + " "
                                        + momRateDist.get(i).getY());
                        }
                    }

                }
                momRate = totMom / area;

                // Info
                if (INFO)
                    System.out.println(src.getID() + " " + totMom);

                // Write separator +
                // Scalar seismic moment rate per units of time and area above
                // 'magThreshold'
                out.write(String.format("> -Z %6.2e idx %d \n",
                        Math.log10(momRate), idx));

                // Write trace coordinates
                for (Location loc : src.getRegion().getBorder()) {
                    out.write(String.format("%+7.3f %+6.3f %+6.2f \n",
                            loc.getLongitude(), loc.getLatitude(),
                            loc.getDepth()));
                    if (INFO) {
                        System.out.printf("%+7.3f %+6.3f %+6.2f \n",
                                loc.getLongitude(), loc.getLatitude(),
                                loc.getDepth());
                    }
                }
            }
        }
        // Write separator
        out.write('>');
        out.close();
    }

    /**
     * This writes all sources into KML file
     */
    public void writeSources2KMLfile(FileWriter file) throws IOException {

        // loop over all sources and find maximum depth
        double maxDepth = 0.0;
        // loop over sources
        for (GEMSourceData dat : srcDataList) {

            if (dat instanceof GEMFaultSourceData) {

                // create area source object
                GEMFaultSourceData src = (GEMFaultSourceData) dat;

                // create fault surface using Stirling method
                StirlingGriddedSurface faultSurface =
                        new StirlingGriddedSurface(src.getTrace(),
                                src.getDip(), src.getSeismDepthUpp(),
                                src.getSeismDepthLow(), 1.0);

                for (int ic =
                        faultSurface.getSurfacePerimeterLocsList().size() - 1; ic >= 0; ic--) {
                    double currentDepth =
                            faultSurface.getSurfacePerimeterLocsList().get(ic)
                                    .getDepth();
                    if (currentDepth > maxDepth)
                        maxDepth = currentDepth;
                }

            }

            if (dat instanceof GEMSubductionFaultSourceData) {

                // create area source object
                GEMSubductionFaultSourceData src =
                        (GEMSubductionFaultSourceData) dat;

                ApproxEvenlyGriddedSurface faultSurface =
                        new ApproxEvenlyGriddedSurface(src.getTopTrace(),
                                src.getBottomTrace(), 10.0);

                for (int ic =
                        faultSurface.getSurfacePerimeterLocsList().size() - 1; ic >= 0; ic--) {
                    double currentDepth =
                            faultSurface.getSurfacePerimeterLocsList().get(ic)
                                    .getDepth();
                    if (currentDepth > maxDepth)
                        maxDepth = currentDepth;
                }
            }

        }

        // output KML file
        BufferedWriter out = new BufferedWriter(file);

        // XML header
        out.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        // KML namespace declaration
        out.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n");

        out.write("<Document>\n");

        out.write("<Style id=\"transRedPoly\">");
        out.write("<LineStyle>");
        out.write("<width>1.5</width>");
        out.write("</LineStyle>");
        out.write("<PolyStyle>");
        out.write("<color>7d0000ff</color>");
        out.write("</PolyStyle>");
        out.write("</Style>");

        out.write("<Style id=\"transGreenPoly\">");
        out.write("<LineStyle>");
        out.write("<width>1.5</width>");
        out.write("</LineStyle>");
        out.write("<PolyStyle>");
        out.write("<color>7d00ff00</color>");
        out.write("</PolyStyle>");
        out.write("</Style>");

        out.write("<Style id=\"transYellowPoly\">");
        out.write("<LineStyle>");
        out.write("<width>1.5</width>");
        out.write("</LineStyle>");
        out.write("<PolyStyle>");
        out.write("<color>7d00ffff</color>");
        out.write("</PolyStyle>");
        out.write("</Style>");

        // loop over sources
        for (GEMSourceData dat : srcDataList) {

            if (dat instanceof GEMAreaSourceData) {

                // create area source object
                GEMAreaSourceData src = (GEMAreaSourceData) dat;

                // create Placemarck object
                out.write("<Placemark>\n");

                // define name
                out.write("<name>" + src.getName() + "</name>\n");

                out.write("<styleUrl>#transRedPoly</styleUrl>");

                // description
                String descr = "";
                // loop over focal mechanisms
                for (int ifm = 0; ifm < src.getMagfreqDistFocMech()
                        .getNumFocalMechs(); ifm++) {

                    descr =
                            descr
                                    + "Mmin = "
                                    + src.getMagfreqDistFocMech()
                                            .getMagFreqDist(ifm).getMinX()
                                    + ", "
                                    + "Mmax = "
                                    + src.getMagfreqDistFocMech()
                                            .getMagFreqDist(ifm).getMaxX()
                                    + ", "
                                    + "TotalCumulativeRate (ev/yr) = "
                                    + src.getMagfreqDistFocMech()
                                            .getMagFreqDist(ifm)
                                            .getTotalIncrRate()
                                    + ", "
                                    + "Strike: "
                                    + src.getMagfreqDistFocMech()
                                            .getFocalMech(ifm).getStrike()
                                    + ", "
                                    + "Dip: "
                                    + src.getMagfreqDistFocMech()
                                            .getFocalMech(ifm).getDip()
                                    + ", "
                                    + "Rake: "
                                    + src.getMagfreqDistFocMech()
                                            .getFocalMech(ifm).getRake() + ", "
                                    + "Average Hypo Depth (km): "
                                    + src.getAveHypoDepth();

                }
                out.write("<description>\n");
                out.write(descr + "\n");
                out.write("</description>\n");

                // write outer polygon
                out.write("<Polygon>\n");
                // outer boundary
                out.write("<outerBoundaryIs>\n");
                out.write("<LinearRing>\n");
                out.write("<coordinates>\n");
                // loop over coordinates
                for (int ic = 0; ic < src.getRegion().getBorder().size(); ic++) {
                    double lon =
                            src.getRegion().getBorder().get(ic).getLongitude();
                    double lat =
                            src.getRegion().getBorder().get(ic).getLatitude();
                    out.write(lon + "," + lat + "\n");
                }
                out.write("</coordinates>\n");
                out.write("</LinearRing>\n");
                out.write("</outerBoundaryIs>\n");

                // write inner polygons
                // loop over interiors
                if (src.getRegion().getInteriors() != null) {
                    for (int ireg = 0; ireg < src.getRegion().getInteriors()
                            .size(); ireg++) {
                        out.write("<innerBoundaryIs>\n");
                        out.write("<LinearRing>\n");
                        out.write("<coordinates>\n");
                        // loop over coordinates
                        for (int ic = 0; ic < src.getRegion().getInteriors()
                                .get(ireg).size(); ic++) {
                            double lon =
                                    src.getRegion().getInteriors().get(ireg)
                                            .get(ic).getLongitude();
                            double lat =
                                    src.getRegion().getInteriors().get(ireg)
                                            .get(ic).getLatitude();
                            out.write(lon + "," + lat + "\n");
                        }
                        out.write("</coordinates>\n");
                        out.write("</LinearRing>\n");
                        out.write("</innerBoundaryIs>\n");
                    }
                }

                out.write("</Polygon>\n");
                out.write("</Placemark>\n");

            }

            if (dat instanceof GEMPointSourceData) {

                // create area source object
                GEMPointSourceData src = (GEMPointSourceData) dat;

                // create Placemarck object
                out.write("<Placemark>\n");

                // define name
                out.write("<name>" + src.getName() + "</name>\n");

                out.write("<styleUrl>#transRedPoly</styleUrl>");

                // description
                String descr = "";
                // loop over focal mechanisms
                for (int ifm = 0; ifm < src.getHypoMagFreqDistAtLoc()
                        .getNumFocalMechs(); ifm++) {

                    descr =
                            descr
                                    + "Mmin = "
                                    + src.getHypoMagFreqDistAtLoc()
                                            .getMagFreqDist(ifm).getMinX()
                                    + ", "
                                    + "Mmax = "
                                    + src.getHypoMagFreqDistAtLoc()
                                            .getMagFreqDist(ifm).getMaxX()
                                    + ", "
                                    + "TotalCumulativeRate (ev/yr) = "
                                    + src.getHypoMagFreqDistAtLoc()
                                            .getMagFreqDist(ifm)
                                            .getTotalIncrRate()
                                    + ", "
                                    + "Strike: "
                                    + src.getHypoMagFreqDistAtLoc()
                                            .getFocalMech(ifm).getStrike()
                                    + ", "
                                    + "Dip: "
                                    + src.getHypoMagFreqDistAtLoc()
                                            .getFocalMech(ifm).getDip()
                                    + ", "
                                    + "Rake: "
                                    + src.getHypoMagFreqDistAtLoc()
                                            .getFocalMech(ifm).getRake() + ", "
                                    + "Average Hypo Depth (km): "
                                    + src.getAveHypoDepth();

                }
                out.write("<description>\n");
                out.write(descr + "\n");
                out.write("</description>\n");

                // write outer polygon
                out.write("<Polygon>\n");
                // outer boundary
                out.write("<outerBoundaryIs>\n");
                out.write("<LinearRing>\n");
                out.write("<coordinates>\n");

                // write coordinates
                double lon =
                        src.getHypoMagFreqDistAtLoc().getLocation()
                                .getLongitude() - 0.05;
                double lat =
                        src.getHypoMagFreqDistAtLoc().getLocation()
                                .getLatitude() + 0.05;
                out.write(lon + "," + lat + "\n");
                lon =
                        src.getHypoMagFreqDistAtLoc().getLocation()
                                .getLongitude() - 0.05;
                lat =
                        src.getHypoMagFreqDistAtLoc().getLocation()
                                .getLatitude() - 0.05;
                out.write(lon + "," + lat + "\n");
                lon =
                        src.getHypoMagFreqDistAtLoc().getLocation()
                                .getLongitude() + 0.05;
                lat =
                        src.getHypoMagFreqDistAtLoc().getLocation()
                                .getLatitude() - 0.05;
                out.write(lon + "," + lat + "\n");
                lon =
                        src.getHypoMagFreqDistAtLoc().getLocation()
                                .getLongitude() + 0.05;
                lat =
                        src.getHypoMagFreqDistAtLoc().getLocation()
                                .getLatitude() + 0.05;
                out.write(lon + "," + lat + "\n");
                out.write("</coordinates>\n");
                out.write("</LinearRing>\n");
                out.write("</outerBoundaryIs>\n");

                out.write("</Polygon>\n");
                out.write("</Placemark>\n");

            }

            if (dat instanceof GEMFaultSourceData) {

                // create area source object
                GEMFaultSourceData src = (GEMFaultSourceData) dat;

                // create fault surface using Stirling method
                StirlingGriddedSurface faultSurface =
                        new StirlingGriddedSurface(src.getTrace(),
                                src.getDip(), src.getSeismDepthUpp(),
                                src.getSeismDepthLow(), 1.0);

                // create Placemarck object
                out.write("<Placemark>\n");

                // define name
                out.write("<name>" + src.getName() + "</name>\n");

                out.write("<styleUrl>#transGreenPoly</styleUrl>");

                // description
                String descr =
                        "Mmin = " + src.getMfd().getMinX() + ", " + "Mmax = "
                                + src.getMfd().getMaxX() + ", "
                                + "TotalCumulativeRate (ev/yr) = "
                                + src.getMfd().getTotalIncrRate() + ", "
                                + "Dip: " + src.getDip() + ", " + "Rake: "
                                + src.getRake() + ".";

                out.write("<description>\n");
                out.write(descr + "\n");
                out.write("</description>\n");

                // write outer polygon
                out.write("<Polygon>\n");
                out.write("<altitudeMode>absolute</altitudeMode>");

                // outer boundary
                out.write("<outerBoundaryIs>\n");
                out.write("<LinearRing>\n");
                out.write("<tessellate>1</tessellate>");
                out.write("<coordinates>\n");

                // loop over coordinates
                // coordinates given in counterclockwise order
                for (int ic =
                        faultSurface.getSurfacePerimeterLocsList().size() - 1; ic >= 0; ic--) {
                    double lon =
                            faultSurface.getSurfacePerimeterLocsList().get(ic)
                                    .getLongitude();
                    double lat =
                            faultSurface.getSurfacePerimeterLocsList().get(ic)
                                    .getLatitude();
                    double depth =
                            faultSurface.getSurfacePerimeterLocsList().get(ic)
                                    .getDepth();
                    out.write(lon + "," + lat + "," + (maxDepth - depth) * 10e3
                            + "\n");
                }
                out.write("</coordinates>\n");
                out.write("</LinearRing>\n");
                out.write("</outerBoundaryIs>\n");

                out.write("</Polygon>\n");
                out.write("</Placemark>\n");

            }

            if (dat instanceof GEMSubductionFaultSourceData) {

                // create area source object
                GEMSubductionFaultSourceData src =
                        (GEMSubductionFaultSourceData) dat;

                ApproxEvenlyGriddedSurface faultSurface =
                        new ApproxEvenlyGriddedSurface(src.getTopTrace(),
                                src.getBottomTrace(), 10.0);

                // create Placemarck object
                out.write("<Placemark>\n");

                // define name
                out.write("<name>" + src.getName() + "</name>\n");

                out.write("<styleUrl>#transYellowPoly</styleUrl>");

                // description
                String descr =
                        "Mmin = " + src.getMfd().getMinX() + ", " + "Mmax = "
                                + src.getMfd().getMaxX() + ", "
                                + "TotalCumulativeRate (ev/yr) = "
                                + src.getMfd().getTotalIncrRate() + ", "
                                + "Rake: " + src.getRake() + ".";

                out.write("<description>\n");
                out.write(descr + "\n");
                out.write("</description>\n");

                // write outer polygon
                out.write("<Polygon>\n");
                out.write("<altitudeMode>absolute</altitudeMode>");

                // outer boundary
                out.write("<outerBoundaryIs>\n");
                out.write("<LinearRing>\n");
                out.write("<coordinates>\n");

                // loop over coordinates
                // coordinates given in counterclockwise order
                for (int ic =
                        faultSurface.getSurfacePerimeterLocsList().size() - 1; ic >= 0; ic--) {
                    double lon =
                            faultSurface.getSurfacePerimeterLocsList().get(ic)
                                    .getLongitude();
                    double lat =
                            faultSurface.getSurfacePerimeterLocsList().get(ic)
                                    .getLatitude();
                    double depth =
                            faultSurface.getSurfacePerimeterLocsList().get(ic)
                                    .getDepth();
                    out.write(lon + "," + lat + "," + (maxDepth - depth) * 10e3
                            + "\n");
                }
                out.write("</coordinates>\n");
                out.write("</LinearRing>\n");
                out.write("</outerBoundaryIs>\n");

                out.write("</Polygon>\n");
                out.write("</Placemark>\n");

            }

        }
        out.write("</Document>\n");
        out.write("</kml>");
        out.close();
    }

    /**
     * This writes all sources into KML file
     */
    public void writeAreaSources2KMLfile(FileWriter file) throws IOException {

        // colors for colorbar (in HTML format)
        ArrayList<String> colorName = new ArrayList<String>();
        colorName.add("990000");
        colorName.add("CC0000");
        colorName.add("FF0000");
        colorName.add("FF3200");
        colorName.add("FF6500");
        colorName.add("FF9800");
        colorName.add("FFCB00");
        colorName.add("FFFE00");
        colorName.add("CEFF31");
        colorName.add("9BFF64");
        colorName.add("68FF97");
        colorName.add("35FFCA");
        colorName.add("02FFFD");
        colorName.add("00CFFF");
        colorName.add("009CFF");
        colorName.add("0069FF");
        colorName.add("0036FF");
        colorName.add("0003FF");
        colorName.add("0000D0");
        colorName.add("00009D");

        // maximum total moment rate
        double maxTmr = -Double.MAX_VALUE;
        // minimum total moment rate
        double minTmr = Double.MAX_VALUE;

        // minimum latitude and maximum longitude
        // for placing the colorbar
        double minLat = Double.MAX_VALUE;
        double maxLon = -Double.MAX_VALUE;

        // array list containing total moment rate for each source
        ArrayList<Double> sourceTMR = new ArrayList<Double>();

        // loop over sources
        for (GEMSourceData dat : srcDataList) {

            if (dat instanceof GEMAreaSourceData) {

                // create area source object
                GEMAreaSourceData src = (GEMAreaSourceData) dat;

                // total moment rate
                double tmr =
                        src.getMagfreqDistFocMech().getFirstMagFreqDist()
                                .getTotalMomentRate();
                // normalize by the area source
                double area = src.getArea();

                System.out.println("Source name: " + src.getName()
                        + ", total moment rate: " + tmr + ", area: " + area
                        + ", total moment rate normalized by area: " + tmr
                        / area);

                tmr = tmr / area;

                sourceTMR.add(tmr);

                if (tmr > maxTmr)
                    maxTmr = tmr;
                if (tmr < minTmr)
                    minTmr = tmr;

                // minimum latitude
                double latMin = src.getRegion().getMinLat();
                // maximum longitude
                double lonMax = src.getRegion().getMaxLon();

                if (latMin < minLat)
                    minLat = latMin;
                if (lonMax > maxLon)
                    maxLon = lonMax;

            }
        }

        // compute delta bin for colorbar (in log scale)
        double deltaColorBar =
                (Math.log10(maxTmr) - Math.log10(minTmr)) / colorName.size();

        // output KML file
        BufferedWriter out = new BufferedWriter(file);

        // XML header
        out.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        // KML namespace declaration
        out.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n");
        out.write("<Document>\n");

        out.write("<name>\n");
        out.write("area sources\n");
        out.write("</name>\n");

        out.write("<Placemark id=\"colorbar\">\n");
        out.write("<name>\n");
        out.write("colorbar\n");
        out.write("</name>\n");

        out.write("<visibility>\n");
        out.write("1\n");
        out.write("</visibility>\n");

        out.write("<description>\n");
        out.write("Total Moment Rate (J/year/km2) ");
        out.write("<![CDATA[<TABLE border=1 bgcolor=#FFFFFF>\n");
        // define colorbar
        for (int i = 0; i < colorName.size(); i++) {
            out.write("<TR><TD bgcolor=#" + colorName.get(i)
                    + ">&nbsp;</TD><TD bgcolor=#FFFFFF>");
            out.write(String.format("%2.2e", Math.pow(10,
                    (Math.log10(maxTmr) - (i + 1) * deltaColorBar))));
            out.write(" to ");
            out.write(String.format("%2.2e",
                    Math.pow(10, (Math.log10(maxTmr) - i * deltaColorBar))));
            out.write("</TR>\n");
        }
        out.write("</TABLE>]]>\n");
        out.write("</description>\n");

        out.write("<Style><IconStyle><scale>1</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/donut.png</href></Icon></IconStyle><ListStyle></ListStyle></Style>\n");
        out.write("<Point id=\"colorbar\">\n");
        out.write("<altitudeMode>\n");
        out.write("clampToGround\n");
        out.write("</altitudeMode>\n");
        out.write("<extrude>\n");
        out.write("1\n");
        out.write("</extrude>\n");
        out.write("<tessellate>\n");
        out.write("1\n");
        out.write("</tessellate>\n");
        out.write("<coordinates>\n");
        out.write((maxLon) + "," + minLat + "\n");
        out.write("</coordinates>\n");
        out.write("</Point>\n");
        out.write("</Placemark>");

        // loop over area sources
        // index of the source
        int sourceIndex = 0;
        for (GEMSourceData dat : srcDataList) {

            if (dat instanceof GEMAreaSourceData) {

                // create area source object
                GEMAreaSourceData src = (GEMAreaSourceData) dat;

                String color = null;

                // find to which color is associated
                for (int i = 0; i < colorName.size(); i++) {

                    if (i != (colorName.size() - 1)
                            && Math.log10(sourceTMR.get(sourceIndex)) > Math
                                    .log10(maxTmr) - (i + 1) * deltaColorBar
                            && Math.log10(sourceTMR.get(sourceIndex)) <= Math
                                    .log10(maxTmr) - i * deltaColorBar) {
                        color = colorName.get(i);
                        break;
                    } else if (i == colorName.size() - 1) {
                        color = colorName.get(i);
                        break;
                    }

                }

                // convert color from HTML to KML format
                String newColor = "90"; // alpha factor for transparency
                for (int ic = color.length() - 1; ic >= 0; ic--)
                    newColor = newColor + color.charAt(ic);

                // create Placemarck object
                out.write("<Placemark>\n");

                // define name
                out.write("<name>" + src.getName() + "</name>\n");

                out.write("<Style id=\"transGreenPoly\">");
                out.write("<LineStyle>");
                out.write("<width>1.5</width>");
                out.write("</LineStyle>");
                out.write("<PolyStyle>");
                out.write("<color>" + newColor + "</color>");
                out.write("</PolyStyle>");
                out.write("</Style>");

                // description
                String descr = "";
                // loop over focal mechanisms
                for (int ifm = 0; ifm < src.getMagfreqDistFocMech()
                        .getNumFocalMechs(); ifm++) {

                    descr =
                            descr
                                    + "Mmin = "
                                    + src.getMagfreqDistFocMech()
                                            .getMagFreqDist(ifm).getMinX()
                                    + ", "
                                    + "Mmax = "
                                    + src.getMagfreqDistFocMech()
                                            .getMagFreqDist(ifm).getMaxX()
                                    + ", "
                                    + "TotalCumulativeRate (ev/yr) = "
                                    + src.getMagfreqDistFocMech()
                                            .getMagFreqDist(ifm)
                                            .getTotalIncrRate()
                                    + ", "
                                    + "Strike: "
                                    + src.getMagfreqDistFocMech()
                                            .getFocalMech(ifm).getStrike()
                                    + ", "
                                    + "Dip: "
                                    + src.getMagfreqDistFocMech()
                                            .getFocalMech(ifm).getDip()
                                    + ", "
                                    + "Rake: "
                                    + src.getMagfreqDistFocMech()
                                            .getFocalMech(ifm).getRake() + ", "
                                    + "Average Hypo Depth (km): "
                                    + src.getAveHypoDepth();

                    // a and b value if GR
                    if (src.getMagfreqDistFocMech().getMagFreqDist(ifm) instanceof GutenbergRichterMagFreqDist) {
                        GutenbergRichterMagFreqDist mfd =
                                (GutenbergRichterMagFreqDist) src
                                        .getMagfreqDistFocMech()
                                        .getMagFreqDist(ifm);

                        double bVal = mfd.get_bValue();

                        double aVal =
                                bVal * mfd.getMagLower()
                                        + Math.log10(mfd.getTotCumRate());

                        descr =
                                descr + ", a value: " + aVal + ", b value: "
                                        + bVal;
                    }

                }

                out.write("<description>\n");
                out.write(descr + "\n");
                out.write("</description>\n");

                // write outer polygon
                out.write("<Polygon>\n");
                // outer boundary
                out.write("<outerBoundaryIs>\n");
                out.write("<LinearRing>\n");
                out.write("<coordinates>\n");
                // loop over coordinates
                for (int ic = 0; ic < src.getRegion().getBorder().size(); ic++) {
                    double lon =
                            src.getRegion().getBorder().get(ic).getLongitude();
                    double lat =
                            src.getRegion().getBorder().get(ic).getLatitude();
                    out.write(lon + "," + lat + "\n");
                }
                // write first point to have closed path
                out.write(src.getRegion().getBorder().get(0).getLongitude()
                        + ","
                        + src.getRegion().getBorder().get(0).getLatitude()
                        + "\n");
                out.write("</coordinates>\n");
                out.write("</LinearRing>\n");
                out.write("</outerBoundaryIs>\n");

                // write inner polygons
                // loop over interiors
                if (src.getRegion().getInteriors() != null) {
                    for (int ireg = 0; ireg < src.getRegion().getInteriors()
                            .size(); ireg++) {
                        out.write("<innerBoundaryIs>\n");
                        out.write("<LinearRing>\n");
                        out.write("<coordinates>\n");
                        // loop over coordinates
                        for (int ic = 0; ic < src.getRegion().getInteriors()
                                .get(ireg).size(); ic++) {
                            double lon =
                                    src.getRegion().getInteriors().get(ireg)
                                            .get(ic).getLongitude();
                            double lat =
                                    src.getRegion().getInteriors().get(ireg)
                                            .get(ic).getLatitude();
                            out.write(lon + "," + lat + "\n");
                        }
                        out.write("</coordinates>\n");
                        out.write("</LinearRing>\n");
                        out.write("</innerBoundaryIs>\n");
                    }
                }

                out.write("</Polygon>\n");
                out.write("</Placemark>\n");

                sourceIndex = sourceIndex + 1;

            }
        }

        out.write("</Document>\n");
        out.write("</kml>\n");
        out.close();

    }

    /**
     * This writes all sources into KML file
     */
    public void writeGridSources2KMLfile(FileWriter file, double gridSpacing)
            throws IOException {

        // colors for colorbar (in HTML format)
        ArrayList<String> colorName = new ArrayList<String>();
        colorName.add("990000");
        colorName.add("CC0000");
        colorName.add("FF0000");
        colorName.add("FF3200");
        colorName.add("FF6500");
        colorName.add("FF9800");
        colorName.add("FFCB00");
        colorName.add("FFFE00");
        colorName.add("CEFF31");
        colorName.add("9BFF64");
        colorName.add("68FF97");
        colorName.add("35FFCA");
        colorName.add("02FFFD");
        colorName.add("00CFFF");
        colorName.add("009CFF");
        colorName.add("0069FF");
        colorName.add("0036FF");
        colorName.add("0003FF");
        colorName.add("0000D0");
        colorName.add("00009D");

        // maximum total moment rate
        double maxTmr = -Double.MAX_VALUE;
        // minimum total moment rate
        double minTmr = Double.MAX_VALUE;

        // minimum latitude and maximum longitude
        // for placing the colorbar
        double minLat = Double.MAX_VALUE;
        double maxLon = -Double.MAX_VALUE;

        // array list containing total moment rate for each source
        ArrayList<Double> sourceTMR = new ArrayList<Double>();

        // loop over sources
        for (GEMSourceData dat : srcDataList) {

            if (dat instanceof GEMPointSourceData) {

                // create area source object
                GEMPointSourceData src = (GEMPointSourceData) dat;

                // source coordinates
                double srcLat =
                        src.getHypoMagFreqDistAtLoc().getLocation()
                                .getLatitude();
                double srcLon =
                        src.getHypoMagFreqDistAtLoc().getLocation()
                                .getLongitude();

                // region associated to the point
                LocationList locList = new LocationList();
                locList.add(new Location(srcLat + gridSpacing / 2, srcLon
                        - gridSpacing / 2));
                locList.add(new Location(srcLat - gridSpacing / 2, srcLon
                        - gridSpacing / 2));
                locList.add(new Location(srcLat - gridSpacing / 2, srcLon
                        + gridSpacing / 2));
                locList.add(new Location(srcLat + gridSpacing / 2, srcLon
                        + gridSpacing / 2));
                Region srcReg = new Region(locList, null);

                // mag frequency distribution for focal mechanism
                MagFreqDistsForFocalMechs magfreqDistFocMech =
                        new MagFreqDistsForFocalMechs(src
                                .getHypoMagFreqDistAtLoc()
                                .getFirstMagFreqDist(), src
                                .getHypoMagFreqDistAtLoc().getFirstFocalMech());

                // create corresponding GEMAreaSourceData
                GEMAreaSourceData srcArea =
                        new GEMAreaSourceData(src.getID(), src.getName(),
                                src.getTectReg(), srcReg, magfreqDistFocMech,
                                src.getAveRupTopVsMag(), src.getAveHypoDepth());

                // total moment rate
                double tmr =
                        src.getHypoMagFreqDistAtLoc().getFirstMagFreqDist()
                                .getTotalMomentRate();
                // normalize by the area source
                double area = srcArea.getArea();

                tmr = tmr / area;

                sourceTMR.add(tmr);

                if (tmr > maxTmr)
                    maxTmr = tmr;
                if (tmr < minTmr)
                    minTmr = tmr;

                // minimum latitude
                double latMin = srcArea.getRegion().getMinLat();
                // maximum longitude
                double lonMax = srcArea.getRegion().getMaxLon();

                if (latMin < minLat)
                    minLat = latMin;
                if (lonMax > maxLon)
                    maxLon = lonMax;

            }
        }

        // compute delta bin for colorbar (in log scale)
        double deltaColorBar =
                (Math.log10(maxTmr) - Math.log10(minTmr)) / colorName.size();

        // output KML file
        BufferedWriter out = new BufferedWriter(file);

        // XML header
        out.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        // KML namespace declaration
        out.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n");
        out.write("<Document>\n");

        out.write("<name>\n");
        out.write("area sources\n");
        out.write("</name>\n");

        out.write("<Placemark id=\"colorbar\">\n");
        out.write("<name>\n");
        out.write("colorbar\n");
        out.write("</name>\n");

        out.write("<visibility>\n");
        out.write("1\n");
        out.write("</visibility>\n");

        out.write("<description>\n");
        out.write("Total Moment Rate (J/year/km2) ");
        out.write("<![CDATA[<TABLE border=1 bgcolor=#FFFFFF>\n");
        // define colorbar
        for (int i = 0; i < colorName.size(); i++) {
            out.write("<TR><TD bgcolor=#" + colorName.get(i)
                    + ">&nbsp;</TD><TD bgcolor=#FFFFFF>");
            out.write(String.format("%2.2e", Math.pow(10,
                    (Math.log10(maxTmr) - (i + 1) * deltaColorBar))));
            out.write(" to ");
            out.write(String.format("%2.2e",
                    Math.pow(10, (Math.log10(maxTmr) - i * deltaColorBar))));
            out.write("</TR>\n");
        }
        out.write("</TABLE>]]>\n");
        out.write("</description>\n");

        out.write("<Style><IconStyle><scale>1</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/donut.png</href></Icon></IconStyle><ListStyle></ListStyle></Style>\n");
        out.write("<Point id=\"colorbar\">\n");
        out.write("<altitudeMode>\n");
        out.write("clampToGround\n");
        out.write("</altitudeMode>\n");
        out.write("<extrude>\n");
        out.write("1\n");
        out.write("</extrude>\n");
        out.write("<tessellate>\n");
        out.write("1\n");
        out.write("</tessellate>\n");
        out.write("<coordinates>\n");
        out.write((maxLon) + "," + minLat + "\n");
        out.write("</coordinates>\n");
        out.write("</Point>\n");
        out.write("</Placemark>");

        // loop over area sources
        // index of the source
        int sourceIndex = 0;
        for (GEMSourceData dat : srcDataList) {

            if (dat instanceof GEMPointSourceData) {

                // create area source object
                GEMPointSourceData src = (GEMPointSourceData) dat;

                // source coordinates
                double srcLat =
                        src.getHypoMagFreqDistAtLoc().getLocation()
                                .getLatitude();
                double srcLon =
                        src.getHypoMagFreqDistAtLoc().getLocation()
                                .getLongitude();

                // region associated to the point
                LocationList locList = new LocationList();
                locList.add(new Location(srcLat + gridSpacing / 2, srcLon
                        - gridSpacing / 2));
                locList.add(new Location(srcLat - gridSpacing / 2, srcLon
                        - gridSpacing / 2));
                locList.add(new Location(srcLat - gridSpacing / 2, srcLon
                        + gridSpacing / 2));
                locList.add(new Location(srcLat + gridSpacing / 2, srcLon
                        + gridSpacing / 2));
                Region srcReg = new Region(locList, null);

                // mag frequency distribution for focal mechanism
                MagFreqDistsForFocalMechs magfreqDistFocMech =
                        new MagFreqDistsForFocalMechs(src
                                .getHypoMagFreqDistAtLoc()
                                .getFirstMagFreqDist(), src
                                .getHypoMagFreqDistAtLoc().getFirstFocalMech());

                // create corresponding GEMAreaSourceData
                GEMAreaSourceData srcArea =
                        new GEMAreaSourceData(src.getID(), src.getName(),
                                src.getTectReg(), srcReg, magfreqDistFocMech,
                                src.getAveRupTopVsMag(), src.getAveHypoDepth());

                String color = null;

                // find to which color is associated
                for (int i = 0; i < colorName.size(); i++) {

                    if (i != (colorName.size() - 1)
                            && Math.log10(sourceTMR.get(sourceIndex)) > Math
                                    .log10(maxTmr) - (i + 1) * deltaColorBar
                            && Math.log10(sourceTMR.get(sourceIndex)) <= Math
                                    .log10(maxTmr) - i * deltaColorBar) {
                        color = colorName.get(i);
                        break;
                    } else if (i == colorName.size() - 1) {
                        color = colorName.get(i);
                        break;
                    }

                }

                // convert color from HTML to KML format
                String newColor = "90"; // alpha factor for transparency
                for (int ic = color.length() - 1; ic >= 0; ic--)
                    newColor = newColor + color.charAt(ic);

                // create Placemarck object
                out.write("<Placemark>\n");

                // define name
                out.write("<name>" + src.getName() + "</name>\n");

                out.write("<Style id=\"transGreenPoly\">");
                out.write("<LineStyle>");
                out.write("<width>0.01</width>");
                out.write("<color>" + newColor + "</color>");
                out.write("</LineStyle>");
                out.write("<PolyStyle>");
                out.write("<color>" + newColor + "</color>");
                out.write("</PolyStyle>");
                out.write("</Style>");

                // description
                String descr = "";
                // loop over focal mechanisms
                for (int ifm = 0; ifm < srcArea.getMagfreqDistFocMech()
                        .getNumFocalMechs(); ifm++) {

                    descr =
                            descr
                                    + "Mmin = "
                                    + srcArea.getMagfreqDistFocMech()
                                            .getMagFreqDist(ifm).getMinX()
                                    + ", "
                                    + "Mmax = "
                                    + srcArea.getMagfreqDistFocMech()
                                            .getMagFreqDist(ifm).getMaxX()
                                    + ", "
                                    + "TotalCumulativeRate (ev/yr) = "
                                    + srcArea.getMagfreqDistFocMech()
                                            .getMagFreqDist(ifm)
                                            .getTotalIncrRate()
                                    + ", "
                                    + "Strike: "
                                    + srcArea.getMagfreqDistFocMech()
                                            .getFocalMech(ifm).getStrike()
                                    + ", "
                                    + "Dip: "
                                    + srcArea.getMagfreqDistFocMech()
                                            .getFocalMech(ifm).getDip()
                                    + ", "
                                    + "Rake: "
                                    + srcArea.getMagfreqDistFocMech()
                                            .getFocalMech(ifm).getRake() + ", "
                                    + "Average Hypo Depth (km): "
                                    + src.getAveHypoDepth();

                }

                out.write("<description>\n");
                out.write(descr + "\n");
                out.write("</description>\n");

                // write outer polygon
                out.write("<Polygon>\n");
                // outer boundary
                out.write("<outerBoundaryIs>\n");
                out.write("<LinearRing>\n");
                out.write("<coordinates>\n");
                // loop over coordinates
                for (int ic = 0; ic < srcArea.getRegion().getBorder().size(); ic++) {
                    double lon =
                            srcArea.getRegion().getBorder().get(ic)
                                    .getLongitude();
                    double lat =
                            srcArea.getRegion().getBorder().get(ic)
                                    .getLatitude();
                    out.write(lon + "," + lat + "\n");
                }
                out.write("</coordinates>\n");
                out.write("</LinearRing>\n");
                out.write("</outerBoundaryIs>\n");

                out.write("</Polygon>\n");
                out.write("</Placemark>\n");

                sourceIndex = sourceIndex + 1;

            }
        }

        out.write("</Document>\n");
        out.write("</kml>\n");
        out.close();

    }

    public void writeFaultSources2KMLfile(FileWriter file) throws IOException {

        // colors for colorbar (in HTML format)
        ArrayList<String> colorName = new ArrayList<String>();
        colorName.add("990000");
        colorName.add("CC0000");
        colorName.add("FF0000");
        colorName.add("FF3200");
        colorName.add("FF6500");
        colorName.add("FF9800");
        colorName.add("FFCB00");
        colorName.add("FFFE00");
        colorName.add("CEFF31");
        colorName.add("9BFF64");
        colorName.add("68FF97");
        colorName.add("35FFCA");
        colorName.add("02FFFD");
        colorName.add("00CFFF");
        colorName.add("009CFF");
        colorName.add("0069FF");
        colorName.add("0036FF");
        colorName.add("0003FF");
        colorName.add("0000D0");
        colorName.add("00009D");

        // maximum total moment rate
        double maxTmr = -Double.MAX_VALUE;
        // minimum total moment rate
        double minTmr = Double.MAX_VALUE;

        // minimum latitude and maximum longitude
        // for placing the colorbar
        double minLat = Double.MAX_VALUE;
        double maxLon = -Double.MAX_VALUE;

        // maximum fault depth
        double maxDepth = -Double.MAX_VALUE;

        // array list containing total moment rate for each source
        ArrayList<Double> sourceTMR = new ArrayList<Double>();

        // loop over sources
        for (GEMSourceData dat : srcDataList) {

            if (dat instanceof GEMFaultSourceData) {

                // create area source object
                GEMFaultSourceData src = (GEMFaultSourceData) dat;

                // create fault surface using Stirling method
                StirlingGriddedSurface faultSurface =
                        new StirlingGriddedSurface(src.getTrace(),
                                src.getDip(), src.getSeismDepthUpp(),
                                src.getSeismDepthLow(), 10.0);

                // total moment rate
                double tmr = src.getMfd().getTotalMomentRate();

                sourceTMR.add(tmr);

                // minimum and maximum total moment rate
                if (tmr > maxTmr)
                    maxTmr = tmr;
                if (tmr < minTmr)
                    minTmr = tmr;

                // minimum latitude and maximum longitude
                for (int ic = 0; ic < src.getTrace().size(); ic++) {
                    double lat = src.getTrace().get(ic).getLatitude();
                    double lon = src.getTrace().get(ic).getLongitude();
                    if (lat < minLat)
                        minLat = lat;
                    if (lon > maxLon)
                        maxLon = lon;
                }

                // maximum fault depth
                for (int ic =
                        faultSurface.getSurfacePerimeterLocsList().size() - 1; ic >= 0; ic--) {
                    double currentDepth =
                            faultSurface.getSurfacePerimeterLocsList().get(ic)
                                    .getDepth();
                    if (currentDepth > maxDepth)
                        maxDepth = currentDepth;
                }

            }
        }

        // compute delta bin for colorbar (in log scale)
        double deltaColorBar =
                (Math.log10(maxTmr) - Math.log10(minTmr)) / colorName.size();

        // output KML file
        BufferedWriter out = new BufferedWriter(file);

        // XML header
        out.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        // KML namespace declaration
        out.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n");
        out.write("<Document>\n");

        out.write("<name>\n");
        out.write("fault sources\n");
        out.write("</name>\n");

        out.write("<Placemark id=\"colorbar\">\n");
        out.write("<name>\n");
        out.write("colorbar\n");
        out.write("</name>\n");

        out.write("<visibility>\n");
        out.write("1\n");
        out.write("</visibility>\n");

        out.write("<description>\n");
        out.write("Total Moment Rate (J/year) \n");
        out.write("<![CDATA[<TABLE border=1 bgcolor=#FFFFFF>\n");
        // define colorbar
        for (int i = 0; i < colorName.size(); i++) {
            out.write("<TR><TD bgcolor=#" + colorName.get(i)
                    + ">&nbsp;</TD><TD bgcolor=#FFFFFF>");
            out.write(String.format("%2.2e", Math.pow(10,
                    (Math.log10(maxTmr) - (i + 1) * deltaColorBar))));
            out.write(" to ");
            out.write(String.format("%2.2e",
                    Math.pow(10, (Math.log10(maxTmr) - i * deltaColorBar))));
            out.write("</TR>\n");
        }
        out.write("</TABLE>]]>\n");
        out.write("</description>\n");

        out.write("<Style><IconStyle><scale>1</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/donut.png</href></Icon></IconStyle><ListStyle></ListStyle></Style>\n");
        out.write("<Point id=\"colorbar\">\n");
        out.write("<altitudeMode>\n");
        out.write("clampToGround\n");
        out.write("</altitudeMode>\n");
        out.write("<extrude>\n");
        out.write("1\n");
        out.write("</extrude>\n");
        out.write("<tessellate>\n");
        out.write("1\n");
        out.write("</tessellate>\n");
        out.write("<coordinates>\n");
        out.write((maxLon + 10) + "," + minLat + "\n");
        out.write("</coordinates>\n");
        out.write("</Point>\n");
        out.write("</Placemark>");

        // loop over area sources
        // index of the source
        int sourceIndex = 0;
        for (GEMSourceData dat : srcDataList) {

            if (dat instanceof GEMFaultSourceData) {

                // create area source object
                GEMFaultSourceData src = (GEMFaultSourceData) dat;

                // create fault surface using Stirling method
                StirlingGriddedSurface faultSurface =
                        new StirlingGriddedSurface(src.getTrace(),
                                src.getDip(), src.getSeismDepthUpp(),
                                src.getSeismDepthLow(), 10.0);

                String color = null;

                // find to which color is associated
                for (int i = 0; i < colorName.size(); i++) {

                    if (i != (colorName.size() - 1)
                            && Math.log10(sourceTMR.get(sourceIndex)) > Math
                                    .log10(maxTmr) - (i + 1) * deltaColorBar
                            && Math.log10(sourceTMR.get(sourceIndex)) <= Math
                                    .log10(maxTmr) - i * deltaColorBar) {
                        color = colorName.get(i);
                        break;
                    } else if (i == colorName.size() - 1) {
                        color = colorName.get(i);
                        break;
                    }

                }

                // convert color from HTML to KML format
                String newColor = "95"; // alpha factor for transparency
                for (int ic = color.length() - 1; ic >= 0; ic--)
                    newColor = newColor + color.charAt(ic);

                // description
                String descr =
                        "Mmin = " + src.getMfd().getMinX() + ", " + "Mmax = "
                                + src.getMfd().getMaxX() + ", "
                                + "TotalCumulativeRate (ev/yr) = "
                                + src.getMfd().getTotalIncrRate() + ", "
                                + "Dip: " + src.getDip() + ", " + "Rake: "
                                + src.getRake() + ".";

                // number of rows
                int nrows = faultSurface.getNumRows();
                // number of columns
                int ncol = faultSurface.getNumCols();

                // create Placemarck object
                out.write("<Placemark id=\"" + src.getName() + "\">\n");
                out.write("<name>\n");
                // out.write("row="+i+";col="+j);
                out.write(src.getName());
                out.write("</name>\n");
                out.write("<visibility>\n");
                out.write("1\n");
                out.write("</visibility>\n");
                out.write("<description>\n");
                out.write(descr);
                out.write("<![CDATA[]]>\n");
                out.write("</description>\n");

                out.write("<Style>\n");
                out.write("<LineStyle>\n");
                out.write("<color>\n");
                out.write(newColor + "\n");
                out.write("</color>\n");
                out.write("<width>\n");
                out.write("0.01 \n");
                out.write("</width>\n");
                out.write("</LineStyle>\n");
                out.write("<PolyStyle>\n");
                out.write("<color>\n");
                out.write(newColor + "\n");
                out.write("</color>\n");
                out.write("</PolyStyle>\n");
                out.write("</Style>\n");

                // create multigeometry
                out.write("<MultiGeometry>\n");
                // loop over rows
                for (int i = 0; i < nrows - 1; i++) {
                    // loop over columns
                    for (int j = 0; j < ncol - 1; j++) {

                        double lon1 = faultSurface.get(i, j).getLongitude();
                        double lat1 = faultSurface.get(i, j).getLatitude();
                        double depth1 = faultSurface.get(i, j).getDepth();

                        double lon2 = faultSurface.get(i + 1, j).getLongitude();
                        double lat2 = faultSurface.get(i + 1, j).getLatitude();
                        double depth2 = faultSurface.get(i + 1, j).getDepth();

                        double lon3 =
                                faultSurface.get(i + 1, j + 1).getLongitude();
                        double lat3 =
                                faultSurface.get(i + 1, j + 1).getLatitude();
                        double depth3 =
                                faultSurface.get(i + 1, j + 1).getDepth();

                        double lon4 = faultSurface.get(i, j + 1).getLongitude();
                        double lat4 = faultSurface.get(i, j + 1).getLatitude();
                        double depth4 = faultSurface.get(i, j + 1).getDepth();

                        // create Placemarck object
                        // out.write("<Placemark id=\""+src.getName()+"\">\n");
                        // out.write("<name>");
                        // //out.write("row="+i+";col="+j);
                        // out.write(src.getName());
                        // out.write("</name>");
                        // out.write("<visibility>");
                        // out.write("1");
                        // out.write("</visibility>");
                        // out.write("<description>");
                        // out.write(descr);
                        // out.write("<![CDATA[]]>");
                        // out.write("</description>");
                        // out.write("<Style>");
                        // out.write("<LineStyle>");
                        // out.write("<color>");
                        // out.write(newColor);
                        // out.write("</color>");
                        // out.write("<width>");
                        // out.write("0.1");
                        // out.write("</width>");
                        // out.write("</LineStyle>");
                        // out.write("<PolyStyle>");
                        // out.write("<color>");
                        // out.write(newColor);
                        // out.write("</color>");
                        // out.write("</PolyStyle>");
                        // out.write("</Style>");

                        // out.write("<Polygon id=\""+src.getName()+"\">\n");
                        out.write("<Polygon>\n");
                        out.write("<altitudeMode>\n");
                        out.write("absolute\n");
                        out.write("</altitudeMode>\n");
                        out.write("<outerBoundaryIs>\n");
                        out.write("<extrude>1</extrude>\n");
                        out.write("<LinearRing>");
                        // out.write("<extrude>1</extrude>");
                        out.write("<tessellate>1</tessellate>");
                        out.write("<altitudeMode>");
                        out.write("absolute");
                        out.write("</altitudeMode>");
                        out.write("<coordinates>");
                        out.write(lon1 + "," + lat1 + "," + (maxDepth - depth1)
                                * 10e3 + "\n");
                        out.write(lon2 + "," + lat2 + "," + (maxDepth - depth2)
                                * 10e3 + "\n");
                        out.write(lon3 + "," + lat3 + "," + (maxDepth - depth3)
                                * 10e3 + "\n");
                        out.write(lon4 + "," + lat4 + "," + (maxDepth - depth4)
                                * 10e3 + "\n");
                        out.write("</coordinates>\n");
                        out.write("</LinearRing>\n");
                        out.write("</outerBoundaryIs>\n");
                        out.write("</Polygon>\n");
                        // out.write("</Placemark>");

                    }
                }

                out.write("</MultiGeometry>\n");
                out.write("</Placemark>");

                sourceIndex = sourceIndex + 1;

            }
        }

        out.write("</Document>\n");
        out.write("</kml>\n");
        out.close();

    }

    public void writeSubductionFaultSources2KMLfile(FileWriter file)
            throws IOException {

        // colors for colorbar (in HTML format)
        ArrayList<String> colorName = new ArrayList<String>();
        colorName.add("990000");
        colorName.add("CC0000");
        colorName.add("FF0000");
        colorName.add("FF3200");
        colorName.add("FF6500");
        colorName.add("FF9800");
        colorName.add("FFCB00");
        colorName.add("FFFE00");
        colorName.add("CEFF31");
        colorName.add("9BFF64");
        colorName.add("68FF97");
        colorName.add("35FFCA");
        colorName.add("02FFFD");
        colorName.add("00CFFF");
        colorName.add("009CFF");
        colorName.add("0069FF");
        colorName.add("0036FF");
        colorName.add("0003FF");
        colorName.add("0000D0");
        colorName.add("00009D");

        // maximum total moment rate
        double maxTmr = -Double.MAX_VALUE;
        // minimum total moment rate
        double minTmr = Double.MAX_VALUE;

        // minimum latitude and maximum longitude
        // for placing the colorbar
        double minLat = Double.MAX_VALUE;
        double maxLon = -Double.MAX_VALUE;

        // maximum fault depth
        double maxDepth = -Double.MAX_VALUE;

        // array list containing total moment rate for each source
        ArrayList<Double> sourceTMR = new ArrayList<Double>();

        // loop over sources
        for (GEMSourceData dat : srcDataList) {

            if (dat instanceof GEMSubductionFaultSourceData) {

                // create area source object
                GEMSubductionFaultSourceData src =
                        (GEMSubductionFaultSourceData) dat;

                ApproxEvenlyGriddedSurface faultSurface =
                        new ApproxEvenlyGriddedSurface(src.getTopTrace(),
                                src.getBottomTrace(), 10.0);

                // total moment rate
                double tmr = src.getMfd().getTotalMomentRate();

                sourceTMR.add(tmr);

                // minimum and maximum total moment rate
                if (tmr > maxTmr)
                    maxTmr = tmr;
                if (tmr < minTmr)
                    minTmr = tmr;

                // minimum latitude and maximum longitude
                for (int ic = 0; ic < src.getTopTrace().size(); ic++) {
                    double lat = src.getTopTrace().get(ic).getLatitude();
                    double lon = src.getTopTrace().get(ic).getLongitude();
                    if (lat < minLat)
                        minLat = lat;
                    if (lon > maxLon)
                        maxLon = lon;
                }

                // maximum fault depth
                for (int ic =
                        faultSurface.getSurfacePerimeterLocsList().size() - 1; ic >= 0; ic--) {
                    double currentDepth =
                            faultSurface.getSurfacePerimeterLocsList().get(ic)
                                    .getDepth();
                    if (currentDepth > maxDepth)
                        maxDepth = currentDepth;
                }

            }
        }

        // compute delta bin for colorbar (in log scale)
        double deltaColorBar =
                (Math.log10(maxTmr) - Math.log10(minTmr)) / colorName.size();

        // output KML file
        BufferedWriter out = new BufferedWriter(file);

        // XML header
        out.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        // KML namespace declaration
        out.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n");
        out.write("<Document>\n");

        out.write("<name>\n");
        out.write("fault sources\n");
        out.write("</name>\n");

        out.write("<Placemark id=\"colorbar\">\n");
        out.write("<name>\n");
        out.write("colorbar\n");
        out.write("</name>\n");

        out.write("<visibility>\n");
        out.write("1\n");
        out.write("</visibility>\n");

        out.write("<description>\n");
        out.write("Total Moment Rate (J/year) ");
        out.write("<![CDATA[<TABLE border=1 bgcolor=#FFFFFF>\n");
        // define colorbar
        for (int i = 0; i < colorName.size(); i++) {
            out.write("<TR><TD bgcolor=#" + colorName.get(i)
                    + ">&nbsp;</TD><TD bgcolor=#FFFFFF>");
            out.write(String.format("%2.2e", Math.pow(10,
                    (Math.log10(maxTmr) - (i + 1) * deltaColorBar))));
            out.write(" to ");
            out.write(String.format("%2.2e",
                    Math.pow(10, (Math.log10(maxTmr) - i * deltaColorBar))));
            out.write("</TR>\n");
        }
        out.write("</TABLE>]]>\n");
        out.write("</description>\n");

        out.write("<Style><IconStyle><scale>1</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/donut.png</href></Icon></IconStyle><ListStyle></ListStyle></Style>\n");
        out.write("<Point id=\"colorbar\">\n");
        out.write("<altitudeMode>\n");
        out.write("clampToGround\n");
        out.write("</altitudeMode>\n");
        out.write("<extrude>\n");
        out.write("1\n");
        out.write("</extrude>\n");
        out.write("<tessellate>\n");
        out.write("1\n");
        out.write("</tessellate>\n");
        out.write("<coordinates>\n");
        out.write((maxLon + 10) + "," + minLat + "\n");
        out.write("</coordinates>\n");
        out.write("</Point>\n");
        out.write("</Placemark>");

        // loop over area sources
        // index of the source
        int sourceIndex = 0;
        for (GEMSourceData dat : srcDataList) {

            if (dat instanceof GEMSubductionFaultSourceData) {

                // create area source object
                GEMSubductionFaultSourceData src =
                        (GEMSubductionFaultSourceData) dat;

                ApproxEvenlyGriddedSurface faultSurface =
                        new ApproxEvenlyGriddedSurface(src.getTopTrace(),
                                src.getBottomTrace(), 10.0);

                String color = null;

                // find to which color is associated
                for (int i = 0; i < colorName.size(); i++) {

                    if (i != (colorName.size() - 1)
                            && Math.log10(sourceTMR.get(sourceIndex)) > Math
                                    .log10(maxTmr) - (i + 1) * deltaColorBar
                            && Math.log10(sourceTMR.get(sourceIndex)) <= Math
                                    .log10(maxTmr) - i * deltaColorBar) {
                        color = colorName.get(i);
                        break;
                    } else if (i == colorName.size() - 1) {
                        color = colorName.get(i);
                        break;
                    }

                }

                // convert color from HTML to KML format
                String newColor = "90"; // alpha factor for transparency
                for (int ic = color.length() - 1; ic >= 0; ic--)
                    newColor = newColor + color.charAt(ic);

                // description
                String descr =
                        "Mmin = " + src.getMfd().getMinX() + ", " + "Mmax = "
                                + src.getMfd().getMaxX() + ", "
                                + "TotalCumulativeRate (ev/yr) = "
                                + src.getMfd().getTotalIncrRate() + ", "
                                + "Rake: " + src.getRake() + ".";

                // number of rows
                int nrows = faultSurface.getNumRows();
                // number of columns
                int ncol = faultSurface.getNumCols();

                // loop over rows
                for (int i = 0; i < nrows - 1; i++) {
                    // loop over columns
                    for (int j = 0; j < ncol - 1; j++) {

                        double lon1 = faultSurface.get(i, j).getLongitude();
                        double lat1 = faultSurface.get(i, j).getLatitude();
                        double depth1 = faultSurface.get(i, j).getDepth();

                        double lon2 = faultSurface.get(i + 1, j).getLongitude();
                        double lat2 = faultSurface.get(i + 1, j).getLatitude();
                        double depth2 = faultSurface.get(i + 1, j).getDepth();

                        double lon3 =
                                faultSurface.get(i + 1, j + 1).getLongitude();
                        double lat3 =
                                faultSurface.get(i + 1, j + 1).getLatitude();
                        double depth3 =
                                faultSurface.get(i + 1, j + 1).getDepth();

                        double lon4 = faultSurface.get(i, j + 1).getLongitude();
                        double lat4 = faultSurface.get(i, j + 1).getLatitude();
                        double depth4 = faultSurface.get(i, j + 1).getDepth();

                        // create Placemarck object
                        out.write("<Placemark id=\"" + src.getName() + "\">\n");
                        out.write("<name>");
                        // out.write("row="+i+";col="+j);
                        out.write(src.getName());
                        out.write("</name>");
                        out.write("<visibility>");
                        out.write("1");
                        out.write("</visibility>");
                        out.write("<description>");
                        out.write(descr);
                        out.write("<![CDATA[]]>");
                        out.write("</description>");
                        out.write("<Style>");
                        out.write("<LineStyle>");
                        out.write("<color>");
                        out.write(newColor);
                        out.write("</color>");
                        out.write("<width>");
                        out.write("0.1");
                        out.write("</width>");
                        out.write("</LineStyle>");
                        out.write("<PolyStyle>");
                        out.write("<color>");
                        out.write(newColor);
                        out.write("</color>");
                        out.write("</PolyStyle>");
                        out.write("</Style>");

                        out.write("<Polygon id=\"" + src.getName() + "\">\n");
                        out.write("<altitudeMode>");
                        out.write("absolute");
                        out.write("</altitudeMode>");
                        out.write("<outerBoundaryIs>");
                        out.write("<extrude>1</extrude>");
                        out.write("<LinearRing>");
                        // out.write("<extrude>1</extrude>");
                        out.write("<tessellate>1</tessellate>");
                        out.write("<altitudeMode>");
                        out.write("absolute");
                        out.write("</altitudeMode>");
                        out.write("<coordinates>");
                        out.write(lon1 + "," + lat1 + "," + (maxDepth - depth1)
                                * 10e3 + "\n");
                        out.write(lon2 + "," + lat2 + "," + (maxDepth - depth2)
                                * 10e3 + "\n");
                        out.write(lon3 + "," + lat3 + "," + (maxDepth - depth3)
                                * 10e3 + "\n");
                        out.write(lon4 + "," + lat4 + "," + (maxDepth - depth4)
                                * 10e3 + "\n");
                        out.write("</coordinates>");
                        out.write("</LinearRing>");
                        out.write("</outerBoundaryIs>");
                        out.write("</Polygon>");
                        out.write("</Placemark>");

                    }
                }

                sourceIndex = sourceIndex + 1;

            }
        }

        out.write("</Document>\n");
        out.write("</kml>\n");
        out.close();

    }

    /**
     * This writes the coordinates of the fault traces to a file. The format of
     * the outfile is compatible with the GMT psxy multiple segment file format.
     * The separator adopted here is the default separator suggested in GMT
     * (i.e. '>')
     * 
     * @param file
     * @throws IOException
     */
    public void writeFaultGMTfile(FileWriter file) throws IOException {
        BufferedWriter out = new BufferedWriter(file);

        // Search for fault sources
        for (GEMSourceData dat : srcDataList) {
            if (dat instanceof GEMFaultSourceData) {
                // Write the trace coordinate to a file
                GEMFaultSourceData src = (GEMFaultSourceData) dat;
                // Trace length
                Double len = src.getTrace().getTraceLength();
                // Total scalar seismic moment above m
                EvenlyDiscretizedFunc momRateDist =
                        src.getMfd().getMomentRateDist();

                if (INFO)
                    System.out.println("MinX " + momRateDist.getMinX()
                            + " MaxX" + momRateDist.getMaxX());
                if (INFO)
                    System.out.println("Length:" + len);

                double totMom = 0.0;
                double momRate = 0.0;
                double magThreshold = 5.0;
                for (int i = 0; i < momRateDist.getNum(); i++) {
                    if (momRateDist.get(i).getX() >= magThreshold) {
                        totMom += momRateDist.get(i).getY();
                    }
                }
                momRate = totMom / len;
                // Write separator
                out.write(String.format("> -Z %6.2e \n", Math.log10(momRate)));
                // Write trace coordinates
                for (Location loc : src.getTrace()) {
                    out.write(String.format("%+7.3f %+6.3f %+6.2f\n",
                            loc.getLongitude(), loc.getLatitude(),
                            loc.getDepth()));
                }

            }

        }
        out.write('>');
        out.close();
    }

    /**
     * This writes the coordinates of the fault traces to a file. The format of
     * the outfile is compatible with the GMT psxy multiple segment file format.
     * The separator adopted here is the default separator suggested in GMT
     * (i.e. '>')
     * 
     * @param file
     * @throws IOException
     */
    public void writeSubductionGMTfile(FileWriter file) throws IOException {
        BufferedWriter out = new BufferedWriter(file);

        // Search for fault sources
        for (GEMSourceData dat : srcDataList) {
            if (dat instanceof GEMSubductionFaultSourceData) {

                System.out.println("pippo");

                // Write the trace coordinate to a file
                GEMSubductionFaultSourceData src =
                        (GEMSubductionFaultSourceData) dat;
                // Trace length
                Double len = src.getTopTrace().getTraceLength();
                // Total scalar seismic moment above m
                EvenlyDiscretizedFunc momRateDist =
                        src.getMfd().getMomentRateDist();

                if (INFO)
                    System.out.println("MinX " + momRateDist.getMinX()
                            + " MaxX" + momRateDist.getMaxX());
                if (INFO)
                    System.out.println("Length:" + len);

                double totMom = 0.0;
                double momRate = 0.0;
                double magThreshold = 5.0;
                for (int i = 0; i < momRateDist.getNum(); i++) {
                    if (momRateDist.get(i).getX() >= magThreshold) {
                        totMom += momRateDist.get(i).getY();
                    }
                }
                momRate = totMom / len;
                // Write separator
                out.write(String.format("> -Z %6.2e \n", Math.log10(momRate)));
                // Write top trace coordinates
                for (Location loc : src.getTopTrace()) {
                    out.write(String.format("%+7.3f %+6.3f %+6.2f\n",
                            loc.getLongitude(), loc.getLatitude(),
                            loc.getDepth()));
                }
                out.write(String.format("> \n", Math.log10(momRate)));
                // Write bottom trace coordinates
                for (Location loc : src.getBottomTrace()) {
                    out.write(String.format("%+7.3f %+6.3f %+6.2f\n",
                            loc.getLongitude(), loc.getLatitude(),
                            loc.getDepth()));
                }

            }
        }
        out.write('>');
        out.close();
    }

    public void writeSource2CLformat(FileWriter file) throws IOException {

        BufferedWriter out = new BufferedWriter(file);

        // loop over sources
        for (GEMSourceData src : srcDataList) {

            // if area source
            if (src instanceof GEMAreaSourceData) {

                out.write("newsource\n");

                GEMAreaSourceData areaSrc = (GEMAreaSourceData) src;

                // source id
                out.write(areaSrc.getID() + "\n");

                // source name
                out.write(areaSrc.getName() + "\n");

                // tectonic region type
                out.write(areaSrc.getTectReg().toString() + "\n\n");

                out.write("area\n");

                // polygon coordinates
                out.write(areaSrc.getRegion().getBorder().size() + "\n");
                for (Location loc : areaSrc.getRegion().getBorder()) {
                    out.write(String.format("%+7.3f %+6.3f\n",
                            loc.getLatitude(), loc.getLongitude()));
                }

                // focal mechanims and mfd
                out.write(areaSrc.getMagfreqDistFocMech().getNumFocalMechs()
                        + "\n");
                for (int i = 0; i < areaSrc.getMagfreqDistFocMech()
                        .getNumFocalMechs(); i++) {

                    if (areaSrc.getMagfreqDistFocMech().getMagFreqDist(i) instanceof GutenbergRichterMagFreqDist) {

                        GutenbergRichterMagFreqDist mfd =
                                (GutenbergRichterMagFreqDist) areaSrc
                                        .getMagfreqDistFocMech()
                                        .getMagFreqDist(i);

                        // minimum magnitude
                        double mMin = mfd.getMagLower() - mfd.getDelta() / 2;

                        // maximum magnitude
                        double mMax = mfd.getMagUpper() + mfd.getDelta() / 2;

                        // a value
                        double aVal =
                                mfd.get_bValue() * mMin
                                        + Math.log10(mfd.getTotCumRate());

                        // write mfd parameters
                        out.write("gr " + aVal + " " + mfd.get_bValue() + " "
                                + mMax + "\n");

                        // write focal mechanism
                        FocalMechanism fm =
                                areaSrc.getMagfreqDistFocMech().getFocalMech(i);
                        out.write(fm.getStrike() + " " + fm.getDip() + " "
                                + fm.getRake() + "\n");

                    } // end if area source

                } // end number of focal mechanism

                // write rupture top vs. magnitude distribution
                for (int i = 0; i < areaSrc.getAveRupTopVsMag().getNum(); i++) {
                    out.write(areaSrc.getAveRupTopVsMag().getX(i) + " "
                            + areaSrc.getAveRupTopVsMag().getY(i) + " ");
                }
                out.write("\n");

                // write average hypocentral depth
                out.write(Double.toString(areaSrc.getAveHypoDepth()) + "\n\n");
            }

        }

    }

}
