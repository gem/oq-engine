package org.gem.engine.hazard.parsers.ssAfrica;

public class SsAfricaSourceSeismicity {

    double lambda;
    double beta;
    double mmin;
    double mmax;
    int id;

    public SsAfricaSourceSeismicity(int id, double mmin, double mmax,
            double beta, double lambda) {
        this.id = id;
        this.mmin = mmin;
        this.mmax = mmax;
        this.beta = beta;
        this.lambda = lambda;
    }

    public double getLambda() {
        return this.lambda;
    }

    public double getBeta() {
        return this.beta;
    }

    public double getMMax() {
        return this.mmax;
    }

    public double getMMin() {
        return this.mmin;
    }
}
