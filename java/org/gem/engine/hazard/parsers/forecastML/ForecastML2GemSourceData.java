package org.gem.engine.hazard.parsers.forecastML;

import java.net.URL;
import java.util.ArrayList;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.commons.geo.Location;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.SingleMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

public class ForecastML2GemSourceData extends GemFileParser {

    // default focal mechanism
    private static double strike = 0.0;
    private static double dip = 90.0;
    private static double rake = 0.0;
    private FocalMechanism fm = new FocalMechanism(strike, dip, rake);

    // default tectonic region
    private static TectonicRegionType trt = TectonicRegionType.ACTIVE_SHALLOW;

    // default depth
    private static double defaultDepth = 0.0;

    public ForecastML2GemSourceData(String inputfile) {

        srcDataList = new ArrayList<GEMSourceData>();

        try {

            int is = 0;

            DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
            DocumentBuilder db = dbf.newDocumentBuilder();
            Document doc =
                    db.parse(this.getClass().getClassLoader()
                            .getResource(inputfile).getPath());
            doc.getDocumentElement().normalize();

            // ******* period of the forecast *******//

            // starting year
            NodeList forecastStart =
                    doc.getElementsByTagName("forecastStartDate");
            int startYear =
                    Integer.parseInt(forecastStart.item(0).getFirstChild()
                            .getNodeValue().substring(0, 4));
            System.out.println("Forecast Start Date: " + startYear);

            // ending year
            NodeList forecastEnd = doc.getElementsByTagName("forecastEndDate");
            int endYear =
                    Integer.parseInt(forecastEnd.item(0).getFirstChild()
                            .getNodeValue().substring(0, 4));
            System.out.println("Forecast End Date: " + endYear);

            // ******** magnitude bin dimension ********//
            NodeList magBin =
                    doc.getElementsByTagName("defaultMagBinDimension");
            double delta =
                    Double.parseDouble(magBin.item(0).getFirstChild()
                            .getNodeValue());
            System.out.println("Default magnitude bin dimension: " + delta);

            // ******** cell dimension *********//
            NodeList cellDim = doc.getElementsByTagName("defaultCellDimension");
            double cellDimLat =
                    Double.parseDouble(cellDim.item(0).getAttributes()
                            .getNamedItem("latRange").getNodeValue());
            double cellDimLon =
                    Double.parseDouble(cellDim.item(0).getAttributes()
                            .getNamedItem("lonRange").getNodeValue());
            System.out.println("Default cell dimension");
            System.out.println("Latitude range: " + cellDimLat);
            System.out.println("Longitude range: " + cellDimLon);

            // ******* source cells ***********//
            NodeList cellLst = doc.getElementsByTagName("cell");

            // loop over cells
            for (int i = 0; i < cellLst.getLength(); i++) {

                System.out.println("Cell: " + (i + 1) + " of "
                        + cellLst.getLength());

                Node cell = cellLst.item(i);
                // ******** cell coordinates ***********//
                // latitude
                double lat =
                        Double.parseDouble(cell.getAttributes()
                                .getNamedItem("lat").getNodeValue());
                // longitude
                double lon =
                        Double.parseDouble(cell.getAttributes()
                                .getNamedItem("lon").getNodeValue());
                System.out.println("Lat: " + lat);
                System.out.println("Lon: " + lon);

                // ************ magnitude-frequency distribution ***********//
                NodeList MFd = cell.getChildNodes();

                // minimum magnitude
                double mMin =
                        Double.parseDouble(MFd.item(1).getAttributes()
                                .getNamedItem("m").getNodeValue());
                // maximum magnitude
                double mMax =
                        Double.parseDouble(MFd.item(MFd.getLength() - 2)
                                .getAttributes().getNamedItem("m")
                                .getNodeValue());
                // number of values
                int nVal = (int) (MFd.getLength() - 1) / 2;

                // loop over magnitude bins
                SingleMagFreqDist mfd =
                        new SingleMagFreqDist(mMin, nVal, delta);
                int ii = 0;
                for (int im = 1; im <= MFd.getLength() - 2; im = im + 2) {
                    Node MFd0 = MFd.item(im);
                    // magnitude
                    mfd.set(ii,
                            Double.valueOf(MFd0.getChildNodes().item(0)
                                    .getNodeValue())
                                    / (endYear - startYear));
                    ii = ii + 1;
                }

                // average top of rupture-magnitude distribution
                ArbitrarilyDiscretizedFunc aveRupTopVsMag =
                        new ArbitrarilyDiscretizedFunc();
                for (int iv = 0; iv < mfd.getNum(); iv++) {
                    double mag = mfd.getX(iv);
                    aveRupTopVsMag.set(mag, defaultDepth);
                }

                // select only those sources for which rates are different than
                // zero
                if (mfd.getY(0) != 0.0) {

                    // define GEMGridSourceData
                    // id
                    String id = Integer.toString(i);

                    // name
                    String name = "";

                    // define HypoMagFreqDistAtLoc object for the is-th grid
                    // cell
                    HypoMagFreqDistAtLoc hmfd =
                            new HypoMagFreqDistAtLoc(mfd,
                                    new Location(lat, lon), fm);

                    srcDataList.add(new GEMPointSourceData(id, name, trt, hmfd,
                            aveRupTopVsMag, defaultDepth));

                }

            }

        } catch (Exception e) {
            e.printStackTrace();
        }

    }

    public static void main(String[] args) {

        String inputFile =
                "global_smooth_seismicity/zechar.triple_s.global.rate_forecast.xml";

        ForecastML2GemSourceData model =
                new ForecastML2GemSourceData(inputFile);

    }

}
