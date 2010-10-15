package org.gem.engine.hazard.parsers.europe;

public class EuropeSourceSeismicity {

    double bVal;
    double occRate;
    double depth;
    double mmax;
    double mmin;
    String id;

    public EuropeSourceSeismicity(String id, double bVal, double occRate,
            double depth, double mmax) {
        this.id = id;
        this.bVal = bVal;
        this.occRate = occRate;
        this.depth = depth;
        this.mmax = mmax;
    }

    public double getOccRate() {
        return this.occRate;
    }

    public double getBVal() {
        return this.bVal;
    }

    public double getDepth() {
        return this.depth;
    }

    public double getMMax() {
        return this.mmax;
    }
    // public double getMMin() {
    // return this.mmin;
    // }

}
