package org.opensha.gem.GEM1.commons;

import java.util.ArrayList;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;

public class IMLList {

    private double minIML;
    private int nIML;
    private double deltaIML;

    /**
     * Main constructor
     * 
     * @param minIML
     *            Minimum intensity level
     * @param nIML
     *            Maximum intensity level
     * @param deltaIML
     *            Interval width
     */
    public IMLList(double minIML, int nIML, double deltaIML) {
        this.minIML = minIML;
        this.nIML = nIML;
        this.deltaIML = deltaIML;
    }

    /**
     * Provides an ArbitrarilyDiscretizedFunc object. The X values are equally
     * spaced in a logarithmic space and they're comprised between log(minIML)
     * and log(maxIML).
     * 
     * @return hc
     */
    public ArbitrarilyDiscretizedFunc getLnIML() {
        ArbitrarilyDiscretizedFunc hc = new ArbitrarilyDiscretizedFunc();
        for (int in = 0; in < nIML; in++) {
            hc.set(Math.log(minIML + deltaIML * in), 1.0);
        }
        return hc;
    }

    /**
     * Provides an ArrayList object. The values are equally spaced in a
     * logarithmic space.
     * 
     * @return
     */
    public ArrayList<Double> getArrayLnIML() {
        ArrayList<Double> iml = new ArrayList<Double>();
        for (int in = 0; in < nIML; in++) {
            iml.add(Math.log(minIML + deltaIML * in));
        }
        return iml;
    }

    /**
     * Provides an ArbitrarilyDiscretizedFunc object whose X values are equal to
     * exp(X_o) where X_o are the X values of the input
     * ArbitrarilyDiscretizedFunc.
     * 
     * @param iml
     *            An arbitrarily discretized function
     * @return
     */
    public ArbitrarilyDiscretizedFunc expX_Values(
            ArbitrarilyDiscretizedFunc func) {
        ArbitrarilyDiscretizedFunc oul = func.deepClone();
        for (int i = 0; i < oul.getXVals().length; i++) {
            double tmp = Math.exp(func.getX(i));
            oul.set(tmp, func.getY(i));
        }
        return oul;
    }

}
