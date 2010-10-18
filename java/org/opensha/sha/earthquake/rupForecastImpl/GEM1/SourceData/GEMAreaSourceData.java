package org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData;

import java.io.BufferedWriter;
import java.io.IOException;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;

import org.opensha.sha.util.TectonicRegionType;

public class GEMAreaSourceData extends GEMSourceData {

    // this defines the geometry (border) of the region
    private Region reg;
    // this holds the MagFreqDists, FocalMechs, and location.
    private MagFreqDistsForFocalMechs magfreqDistFocMech;
    // the following specifies the average depth to top of rupture as a function
    // of magnitude.
    private ArbitrarilyDiscretizedFunc aveRupTopVsMag;
    // the following is used to locate small sources (i.e., for all mags lower
    // than the minimum mag in aveRupTopVsMag)
    private double aveHypoDepth;

    /**
     * This is the constructor for the GEMAreaSourceData class. It takes as
     * input parameters the ID of the source, its name and
     * <code>TectonicRegion</code> definition, the <code>Region</code> bordering
     * the area, a <code>MagFreqDistsForFocalMechs</code> object containing the
     * MFD and the focal mechanism of the fault families within the source,
     * 
     * @param id
     * @param name
     * @param tectReg
     * @param reg
     * @param magfreqDistFocMech
     * @param aveRupTopVsMag
     * @param aveHypoDepth
     */
    public GEMAreaSourceData(String id, String name,
            TectonicRegionType tectReg, Region reg,
            MagFreqDistsForFocalMechs magfreqDistFocMech,
            ArbitrarilyDiscretizedFunc aveRupTopVsMag, double aveHypoDepth) {
        this.id = id;
        this.name = name;
        this.tectReg = tectReg;
        this.reg = reg;
        this.magfreqDistFocMech = magfreqDistFocMech;
        this.aveRupTopVsMag = aveRupTopVsMag;
        this.aveHypoDepth = aveHypoDepth;
    }

    public Region getRegion() {
        return this.reg;
    }

    public double getMagfreqDistFocMech(int i) {
        return this.getMagfreqDistFocMech(i);
    }

    public MagFreqDistsForFocalMechs getMagfreqDistFocMech() {
        return this.magfreqDistFocMech;
    }

    public ArbitrarilyDiscretizedFunc getAveRupTopVsMag() {
        return this.aveRupTopVsMag;
    }

    public double getAveHypoDepth() {
        return this.aveHypoDepth;
    }

    /**
     * D.M. This computes an approximate extension of an area source meant as a
     * polygon on a sphere. The algorithm is taken from
     * "Some algorithms for Polygons on a Sphere", R.G.Chamberlain,
     * W.H.Duquette, Jet Propulsion Laboratory, presented at the Association of
     * American Geographers Annual Meeting, San Francisco California, 17-21
     * April 2007. JPL publication 07-3 I commented the algorithm from Marco for
     * the moment, because I found it slower and in case of the Autralia model
     * it was giving some strange values. Maybe somo more investigation is
     * needed? I checked the results of this algorithm with the areas provide in
     * the Australia model and the numbers are consistent (not identical
     * however).
     * 
     * @return area
     */
    public double getArea() {

        double earthRadiusEquator = 6378.1370;
        double earthRadiusPole = 6356.7523;
        double meanRadius = (2 * earthRadiusEquator + earthRadiusPole) / 3;

        LocationList border = this.reg.getBorder();

        // loop over border coordinates
        double a = 0.0;
        for (int i = 0; i < border.size(); i++) {

            double lon_i_plus_1 = Double.NaN;
            double lon_i_minus_1 = Double.NaN;
            double lat_i = Double.NaN;
            if (i == 0) {
                lon_i_plus_1 =
                        border.get(i + 1).getLongitude() * (Math.PI / 180);
                lon_i_minus_1 =
                        border.get(border.size() - 1).getLongitude()
                                * (Math.PI / 180);
                lat_i = border.get(i).getLatitude() * (Math.PI / 180);
            } else if (i == border.size() - 1) {
                lon_i_plus_1 = border.get(0).getLongitude() * (Math.PI / 180);
                lon_i_minus_1 =
                        border.get(i - 1).getLongitude() * (Math.PI / 180);
                lat_i = border.get(i).getLatitude() * (Math.PI / 180);
            } else {
                lon_i_plus_1 =
                        border.get(i + 1).getLongitude() * (Math.PI / 180);
                lon_i_minus_1 =
                        border.get(i - 1).getLongitude() * (Math.PI / 180);
                lat_i = border.get(i).getLatitude() * (Math.PI / 180);
            }

            a = a + (lon_i_plus_1 - lon_i_minus_1) * Math.sin(lat_i);

        }
        a = a * (-Math.pow(meanRadius, 2) / 2);

        // the absolute value is taken because the sign depends on the fact
        // that the polygon is specified in a clock or counter-clock wise order.
        a = Math.abs(a);

        // subtract interiors
        if (this.reg.getInteriors() != null) {
            // loop over interiors
            for (int i = 0; i < this.reg.getInteriors().size(); i++) {

                LocationList innerBorder = this.reg.getInteriors().get(i);

                // loop over border coordinates
                double innerA = 0.0;
                for (int j = 0; j < innerBorder.size(); j++) {

                    double lon_i_plus_1 = Double.NaN;
                    double lon_i_minus_1 = Double.NaN;
                    double lat_i = Double.NaN;
                    if (j == 0) {
                        lon_i_plus_1 =
                                innerBorder.get(j + 1).getLongitude()
                                        * (Math.PI / 180);
                        lon_i_minus_1 =
                                innerBorder.get(innerBorder.size() - 1)
                                        .getLongitude() * (Math.PI / 180);
                        lat_i =
                                innerBorder.get(j).getLatitude()
                                        * (Math.PI / 180);
                    } else if (j == innerBorder.size() - 1) {
                        lon_i_plus_1 =
                                innerBorder.get(0).getLongitude()
                                        * (Math.PI / 180);
                        lon_i_minus_1 =
                                innerBorder.get(j - 1).getLongitude()
                                        * (Math.PI / 180);
                        lat_i =
                                innerBorder.get(j).getLatitude()
                                        * (Math.PI / 180);
                    } else {
                        lon_i_plus_1 =
                                innerBorder.get(j + 1).getLongitude()
                                        * (Math.PI / 180);
                        lon_i_minus_1 =
                                innerBorder.get(j - 1).getLongitude()
                                        * (Math.PI / 180);
                        lat_i =
                                innerBorder.get(j).getLatitude()
                                        * (Math.PI / 180);
                    }

                    innerA =
                            innerA + (lon_i_plus_1 - lon_i_minus_1)
                                    * Math.sin(lat_i);

                }
                innerA = innerA * (-Math.pow(meanRadius, 2) / 2);

                innerA = Math.abs(innerA);

                a = a - innerA;
            }
        }

        return a;

        // double area = 0.0;
        // double grdSpacing = 0.005;
        //
        // double oldLat = 0.0;
        // double tmpArea = 0.0;
        // double tmpRadius = 0.0;
        //
        // // Gridding the region
        // GriddedRegion grd = new GriddedRegion(this.reg,grdSpacing,null);
        //
        // // Mean radius
        // double meanRadius = (2*earthRadiusEquator + earthRadiusPole) / 3.0;
        //
        // // Computing the area
        // for (Location loc: grd.getNodeList()){
        // double tmpLat = loc.getLatitude();
        // if ( Math.abs(tmpLat-oldLat) > grdSpacing/10) {
        // double tmpLatRad = tmpLat / 180 * Math.PI;
        // double tmpNum =
        // Math.pow(earthRadiusEquator*earthRadiusEquator*Math.cos(tmpLatRad),2)
        // +
        // Math.pow(earthRadiusPole*earthRadiusPole*Math.sin(tmpLatRad),2);
        // double tmpDen = Math.pow(earthRadiusEquator*Math.cos(tmpLatRad),2) +
        // Math.pow(earthRadiusPole*Math.sin(tmpLatRad),2);
        // tmpRadius = Math.sqrt(tmpNum/tmpDen);
        //
        // tmpArea = Math.pow(grdSpacing/360*2.0*Math.PI,2) * tmpRadius *
        // Math.sin(Math.PI-tmpLatRad) * meanRadius;
        // area += tmpArea;
        // oldLat = tmpLat;
        // } else {
        // area += tmpArea;
        // }
        // }
        // // System.out.println("Area:"+area);
        // return area;

    }

    /**
     * 
     * @param buf
     * @throws IOException
     */
    public void writeXML(BufferedWriter buf) throws IOException {
        String prefix = "ns4:";
        String prefix1 = "ns3:";

        // Write the geometry
        buf.write(String.format("<%sSource>\n", prefix));
        buf.write(String.format("<%sArea>\n", prefix));
        buf.write(String.format("\t<%sPolygon>\n", prefix));
        buf.write(String.format("\t\t<%sexterior>\n", prefix1));
        buf.write(String.format("\t\t\t<%sLinearRing>\n", prefix1));
        buf.write(String.format(
                "\t\t\t\t<%sposList srsDimension=\"2\" count=\"%d\">", prefix1,
                this.reg.getBorder().size()));
        LocationList border = this.reg.getBorder();
        for (int i = 0; i < border.size(); i++) {
            buf.write(String.format("%.4f %.4f ", border.get(i).getLongitude(),
                    border.get(i).getLatitude()));
        }
        buf.write(String.format("</%sposList>\n", prefix1));
        buf.write(String.format("\t\t\t</%sLinearRing>\n", prefix1));
        buf.write(String.format("\t\t</%sexterior>\n", prefix1));
        buf.write(String.format("\t</%sPolygon>\n", prefix));

        // Write the MFD
        buf.write(String.format("\t<%sHypoRateModelList>\n", prefix));
        buf.write(String.format("\t\t<%sModel mMax=\"%.2f\">\n", prefix,
                this.magfreqDistFocMech.getMagFreqDist(0).getMaxX()
                        + this.magfreqDistFocMech.getMagFreqDist(0).getDelta()
                        / 2));
        buf.write(String.format("\t\t\t<%sParameters>\n", prefix));
        buf.write(String.format("\t\t\t\t<%sMagFreqDist>\n", prefix));
        buf.write(String
                .format("\t\t\t\t\t<%sEvenlyDiscretized binSize=\"%.2f\" minVal=\"5.0\" binCount=\"%d\"> \n",
                        prefix, this.magfreqDistFocMech.getMagFreqDist(0)
                                .getDelta(), this.magfreqDistFocMech
                                .getMagFreqDist(0).getNum()));
        buf.write(String.format("\t\t\t\t\t\t<DistributionValues xmlns=\"\">"));
        for (int j = 0; j < this.magfreqDistFocMech.getMagFreqDist(0).getNum(); j++) {
            buf.write(String.format("%.3f %.5e ", this.magfreqDistFocMech
                    .getMagFreqDist(0).get(j).getX(), this.magfreqDistFocMech
                    .getMagFreqDist(0).get(j).getY()));
        }
        buf.write(String.format("\n\t\t\t\t\t\t</DistributionValues>\n"));
        buf.write(String.format("\t\t\t\t\t</%sEvenlyDiscretized>\n", prefix));
        buf.write(String.format("\t\t\t\t</%sMagFreqDist>\n", prefix));
        if (this.getMagfreqDistFocMech().getFocalMechanismList().length > 0) {
            buf.write(String
                    .format("\t\t\t\t<%sFocalMech dip=\"90.0\" rake=\"90.0\" strike=\"0.0\"/>\n",
                            prefix));
            buf.write(String.format("\t\t\t\t\t<%sRupTopDist>\n", prefix));
            buf.write(String
                    .format("\t\t\t\t\t\t<DistributionValues xmlns=\"\">"));
            for (int j = 0; j < this.getAveRupTopVsMag().getNum(); j++) {
                buf.write(String.format("%.3f %.5e ", this.getAveRupTopVsMag()
                        .getX(j), this.getAveRupTopVsMag().getY(j)));
            }
            buf.write(String.format("\n\t\t\t\t\t\t</DistributionValues>"));
            buf.write(String.format("\n\t\t\t\t\t</%sRupTopDist>\n", prefix));
        }
        buf.write(String.format("\t\t\t</%sParameters>\n", prefix));
        buf.write(String.format("\t\t</%sModel>\n", prefix));
        buf.write(String.format("\t</%sHypoRateModelList>\n", prefix));

        buf.write(String.format("</%sArea>\n", prefix));
        buf.write(String.format("</%sSource>\n", prefix));
    }
}
