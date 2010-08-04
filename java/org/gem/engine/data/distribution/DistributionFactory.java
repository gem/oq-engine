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

package org.gem.engine.data.distribution;

/**
 * A simple factory that is capable of creating distributions.
 * 
 * @author Andrea Cerisara
 * @version $Id: DistributionFactory.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class DistributionFactory
{

    /**
     * Log normal distribution code.
     */
    public static final String LOG_NORMAL = "LN";

    /**
     * Creates a distribution of type specified by the given code.
     * 
     * @param code the type of the distribution
     * @param mean the mean of the distribution
     * @param cov the cov of the distribution
     * @return the distribution instance
     */
    public Distribution create(String code, double mean, double cov)
    {
        if (LOG_NORMAL.equalsIgnoreCase(code))
        {
            return new LogNormalDistribution(mean, cov);
        }

        throw new RuntimeException("Distribution with code " + code + " unknown!");
    }

}
