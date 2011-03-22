package org.gem.engine.hazard.parsers;

import java.io.File;
import java.util.HashMap;
import java.util.Map;
import java.util.StringTokenizer;

import org.dom4j.Document;
import org.dom4j.XPath;
import org.dom4j.io.SAXReader;
import org.dom4j.xpath.DefaultXPath;
import org.jaxen.SimpleNamespaceContext;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.PointSurface;
import org.opensha.sha.util.TectonicRegionType;

/**
 * Reads NRML definitions of rupture elements.
 * <p>
 * It currently supports point ruptures.
 */
public class RuptureReader
{

    private final File file;
    private Document document;

    private static final Map<String, String> namespaces = new HashMap<String, String>();

    {
        namespaces.put("gml", "http://www.opengis.net/gml");
        namespaces.put("qml", "http://quakeml.org/xmlns/quakeml/1.1");
        namespaces.put("nrml", "http://openquake.org/xmlns/nrml/0.2");
    }

    public RuptureReader(File file)
    {
        if (!file.isFile())
        {
            throw new IllegalArgumentException("unknown file!");
        }

        this.file = file;
    }

    public EqkRupture read()
    {
        SAXReader reader = new SAXReader();

        try
        {
            document = reader.read(this.file);
        }
        catch (Exception e)
        {
            throw new RuntimeException(e);
        }

        EqkRupture rupture = new EqkRupture();

        rupture.setMag(magnitude());
        rupture.setTectRegType(tectonicRegionType());
        rupture.setHypocenterLocation(location());
        rupture.setAveRake(averageRake());

        PointSurface surface = new PointSurface(location());
        surface.setAveStrike(strike());
        surface.setAveDip(dip());

        rupture.setRuptureSurface(surface);

        return rupture;
    }

    private double dip()
    {
        return Double.parseDouble(xpath("//qml:dip/qml:value[1]").selectSingleNode(document).getText());
    }

    private double strike()
    {
        return Double.parseDouble(xpath("//qml:strike/qml:value[1]").selectSingleNode(document).getText());
    }

    private double averageRake()
    {
        return Double.parseDouble(xpath("//qml:rake/qml:value[1]").selectSingleNode(document).getText());
    }

    private Location location()
    {
        String pos = xpath("//gml:pos").selectSingleNode(document).getText();
        StringTokenizer splitter = new StringTokenizer(pos);

        double lon = Double.parseDouble(splitter.nextToken());
        double lat = Double.parseDouble(splitter.nextToken());
        double depth = Double.parseDouble(splitter.nextToken());

        return new Location(lat, lon, depth);
    }

    private XPath xpath(String pattern)
    {
        XPath xpath = new DefaultXPath(pattern);
        xpath.setNamespaceContext(new SimpleNamespaceContext(namespaces));

        return xpath;
    }

    private TectonicRegionType tectonicRegionType()
    {
        String name = xpath("//nrml:tectonicRegion").selectSingleNode(document).getText();
        return TectonicRegionType.getTypeForName(name);
    }

    private double magnitude()
    {
        return Double.parseDouble(xpath("//nrml:magnitude").selectSingleNode(document).getText());
    }

}
