package org.opensha.gem.GEM1.commons;

public class moment_rate {

    /**
     * Get the value of scalar pippo seismic moment rate given GR parameters
     * mmin and mmax
     * 
     * @param magLower
     * @param numMag
     * @param deltaMag
     * @param aVal
     * @param bVal
     * @return
     */
    public static double getMomentRateFromGR(double magLower, int numMag,
            double deltaMag, double aVal, double bVal) {
        double mo = 0;
        double mag;
        for (int i = 0; i < numMag; i++) {
            mag = magLower + i * deltaMag;
            mo += Math.pow(10, aVal - bVal * mag + 1.5 * mag + 9.05);
        }
        return mo;
    }

}
