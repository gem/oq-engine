package org.gem.engine.hazard.parsers.northernEurasia;

import java.util.ArrayList;
import org.opensha.commons.geo.Location;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;

public class NorthernEurasiaSourceData {

    private ArrayList<Location> loclis; // See OpenSHA Java-docs
    private String srcType;
    private ArbitrarilyDiscretizedFunc mfd; // See OpenSHA Java-docs
    private double[] dip;
    private double[] strike;

    public ArrayList<Location> getNodes() {
        return this.loclis;
    }

    public ArrayList<Location> addNode(double lat, double lon) {
        this.loclis.add(new Location(lat, lon));
        return this.loclis;
    }

    public String getType() {
        return this.srcType;
    }

    public String setType(String type) {
        this.srcType = type;
        return this.srcType;
    }

    public ArbitrarilyDiscretizedFunc getMfd() {
        return this.mfd;
    }

    public String setMfd(ArbitrarilyDiscretizedFunc mfdinp) {
        this.mfd = mfdinp;
        return this.srcType;
    }

    public double[] getStrike() {
        return this.strike;
    }

    public double[] setStrike() {
        return this.strike;
    }

    public double[] getDip() {
        return this.dip;
    }

    public double[] setDip() {
        return this.dip;
    }
}
