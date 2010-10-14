/*
 * [COPYRIGHT]
 * 
 * [NAME] is free software; you can redistribute it and/or modify it under the
 * terms of the GNU Lesser General Public License as published by the Free
 * Software Foundation; either version 2.1 of the License, or (at your option)
 * any later version.
 * 
 * This software is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
 * details.
 * 
 * You should have received a copy of the GNU Lesser General Public License
 * along with this software; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA, or see the FSF
 * site: http://www.fsf.org.
 */

package org.openshra.common.distribution;

import org.apache.commons.math.MathException;
import org.apache.commons.math.distribution.AbstractContinuousDistribution;
import org.apache.commons.math.distribution.NormalDistribution;
import org.apache.commons.math.special.Erf;

public class LogNormalDistribution extends AbstractContinuousDistribution
        implements NormalDistribution {

    private static final long serialVersionUID = 2333436780378218297L;

    private double mean = 0;
    private double standardDeviation = 1;

    public LogNormalDistribution(double mean, double sd) {
        super();

        setMean(mean);
        setStandardDeviation(sd);
    }

    public LogNormalDistribution() {
        this(0.0, 1.0);
    }

    public double getMean() {
        return mean;
    }

    public void setMean(double mean) {
        this.mean = mean;
    }

    public double getStandardDeviation() {
        return standardDeviation;
    }

    public void setStandardDeviation(double sd) {
        if (sd <= 0.0) {
            throw new IllegalArgumentException(
                    "Standard deviation must be positive.");
        }

        standardDeviation = sd;
    }

    @Override
    public double cumulativeProbability(double x) throws MathException {
        x = Math.log(x); // the only line changed

        try {
            return 0.5 * (1.0 + Erf.erf((x - mean)
                    / (standardDeviation * Math.sqrt(2.0))));
        } catch (MathException e) {
            if (x < (mean - 20 * standardDeviation)) {
                return 0.0;
            } else if (x > (mean + 20 * standardDeviation)) {
                return 1.0;
            } else {
                throw e;
            }
        }
    }

    @Override
    public double inverseCumulativeProbability(final double p)
            throws MathException {
        if (p == 0) {
            return Double.NEGATIVE_INFINITY;
        }
        if (p == 1) {
            return Double.POSITIVE_INFINITY;
        }

        return super.inverseCumulativeProbability(p);
    }

    @Override
    protected double getDomainLowerBound(double p) {
        double ret;

        if (p < .5) {
            ret = -Double.MAX_VALUE;
        } else {
            ret = getMean();
        }

        return ret;
    }

    @Override
    protected double getDomainUpperBound(double p) {
        double ret;

        if (p < .5) {
            ret = getMean();
        } else {
            ret = Double.MAX_VALUE;
        }

        return ret;
    }

    @Override
    protected double getInitialDomain(double p) {
        double ret;

        if (p < .5) {
            ret = getMean() - getStandardDeviation();
        } else if (p > .5) {
            ret = getMean() + getStandardDeviation();
        } else {
            ret = getMean();
        }

        return ret;
    }

    @Override
    public double density(Double arg0) {
        return 0;
    }

}
