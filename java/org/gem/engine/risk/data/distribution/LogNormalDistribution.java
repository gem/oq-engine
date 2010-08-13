/*
 * [COPYRIGHT]
 *
 * [NAME] is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation; either version 2.1 of
 * the License, or (at your option) any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this software; if not, write to the Free
 * Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
 * 02110-1301 USA, or see the FSF site: http://www.fsf.org.
 */

package org.gem.engine.risk.data.distribution;

import org.apache.commons.math.MathException;

/**
 * Describes a log normal distribution.
 * 
 * @author Andrea Cerisara
 * @version $Id: LogNormalDistribution.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class LogNormalDistribution implements Distribution
{

    private final double cov;
    private final double mean;

    /**
     * @param mean the mean to use for the distribution
     * @param cov the cov to use for the distribution
     */
    public LogNormalDistribution(double mean, double cov)
    {
        this.cov = cov;
        this.mean = mean;
    }

    @Override
    public double getStdDev()
    {
        return mean * cov;
    }

    private org.openshra.common.distribution.LogNormalDistribution distribution()
    {
        return new org.openshra.common.distribution.LogNormalDistribution();
    }

    private double comulativeProbabilityFor(double from, double to)
    {
        org.openshra.common.distribution.LogNormalDistribution distribution = distribution();

        distribution.setMean(lambda());
        distribution.setStandardDeviation(zeta());

        try
        {
            return distribution.cumulativeProbability(from, to);
        }
        catch (MathException e)
        {
            throw new RuntimeException(e);
        }
    }

    private double comulativeProbabilityFor(double to)
    {
        org.openshra.common.distribution.LogNormalDistribution distribution = distribution();

        distribution.setMean(lambda());
        distribution.setStandardDeviation(zeta());

        try
        {
            return distribution.cumulativeProbability(to);
        }
        catch (MathException e)
        {
            throw new RuntimeException(e);
        }
    }

    protected double zeta()
    {
        double lnArgument = 1 + Math.pow(cov, 2);

        return Math.sqrt(Math.log(lnArgument));
    }

    protected double lambda()
    {
        return Math.log(mean) - (0.5 * Math.pow(zeta(), 2));
    }

    public double getMean()
    {
        return mean;
    }

    public double getCov()
    {
        return cov;
    }

    @Override
    public double cumulativeProbability(double from, double to)
    {
        return comulativeProbabilityFor(from, to);
    }

    @Override
    public double cumulativeProbability(double to)
    {
        return comulativeProbabilityFor(to);
    }

}
