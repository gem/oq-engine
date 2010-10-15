package org.opensha.gem.GEM1.commons;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;

public class IMLLis {

    private ArbitrarilyDiscretizedFunc adf;
    private boolean isLogX;
    private boolean isLogY;

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
    public IMLLis(double minIML, int nIML, double deltaIML) {
        this.adf = new ArbitrarilyDiscretizedFunc();
        for (int in = 0; in < nIML; in++) {
            this.adf.set(Math.log(minIML + deltaIML * in), 1.0);
        }
        this.isLogX = true;
        this.isLogY = true;
    }

    /**
     * Main constructor
     * 
     * @param minIML
     *            Minimum intensity level
     * @param nIML
     *            Maximum intensity level
     * @param deltaIML
     *            Number of values
     */
    public IMLLis(double minIML, double maxIML, int numV, String lab) {
        this.adf = new ArbitrarilyDiscretizedFunc();
        if (lab.matches("l")) {
            double delta = (Math.log(maxIML) - Math.log(minIML)) / (numV - 1);
            double tmp = Math.log(minIML);
            while (tmp <= Math.log(maxIML) + delta * 0.1) {
                this.adf.set(tmp, 1.0);
                tmp = tmp + delta;
            }
        } else if (lab.matches("n")) {
            double delta = (maxIML - minIML) / (numV - 1);
            double tmp = minIML;
            while (tmp <= maxIML + delta * 0.1) {
                this.adf.set(Math.log(tmp), 1.0);
                tmp = tmp + delta;
            }
        } else
            this.isLogX = true;
        this.isLogY = true;
    }

    /**
     * Returns the arbitrarily discretized function
     * 
     */
    public ArbitrarilyDiscretizedFunc getArbDisFun() {
        return this.adf;
    }

    /**
     * Sets the arbitrarily discretized function
     */
    public void setArbDisFun(ArbitrarilyDiscretizedFunc adfIn) {
        this.adf = adfIn;
    }

    /**
	 * 
	 */
    public void expX_Values() {
        ArbitrarilyDiscretizedFunc tmpAdf = new ArbitrarilyDiscretizedFunc();
        for (int i = 0; i < this.adf.getXVals().length; i++) {
            double tmp = Math.exp(this.adf.getX(i));
            tmpAdf.set(tmp, this.adf.getY(i));
        }
        this.isLogX = false;
        this.adf = tmpAdf;
    }

    /**
     * 
     * @return
     */
    public void isLogX_Values() {
        ArbitrarilyDiscretizedFunc tmpAdf = new ArbitrarilyDiscretizedFunc();
        for (int i = 0; i < this.adf.getXVals().length; i++) {
            double tmp = Math.log(this.adf.getX(i));
            tmpAdf.set(tmp, this.adf.getY(i));
        }
        this.isLogX = true;
        this.adf = tmpAdf;
    }

    /**
	 * 
	 */
    public void expY_Values() {
        ArbitrarilyDiscretizedFunc tmpAdf = new ArbitrarilyDiscretizedFunc();
        for (int i = 0; i < this.adf.getYVals().length; i++) {
            double tmp = Math.exp(this.adf.getY(i));
            tmpAdf.set(this.adf.getX(i), tmp);
        }
        this.isLogY = false;
        this.adf = tmpAdf;
    }

    /**
	 * 
	 */
    public void isLogY_Values() {
        ArbitrarilyDiscretizedFunc tmpAdf = new ArbitrarilyDiscretizedFunc();
        for (int i = 0; i < this.adf.getYVals().length; i++) {
            double tmp = Math.log(this.adf.getY(i));
            tmpAdf.set(this.adf.getX(i), tmp);
        }
        this.isLogY = true;
        this.adf = tmpAdf;
    }
}
