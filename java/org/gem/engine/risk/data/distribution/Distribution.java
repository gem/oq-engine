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

/**
 * Describes a probability distribution.
 * 
 * @author Andrea Cerisara
 * @version $Id: Distribution.java 537 2010-06-16 18:29:36Z acerisara $
 */
public interface Distribution
{

    /**
     * Returns the mean of this distribution.
     * 
     * @return the mean of this distribution
     */
    public double getMean();

    /**
     * Returns the cumulative probability for the given interval.
     * 
     * @param from the value to start from
     * @param to the value to end to
     * @return the cumulative probability for the given interval
     */
    public double cumulativeProbability(double from, double to);

    /**
     * Returns the cumulative probability for the given value.
     * 
     * @param to the value to end to
     * @return the cumulative probability for the given value
     */
    public double cumulativeProbability(double to);

    /**
     * Returns the standard deviation of this distribution.
     * 
     * @return the standard deviation of this distribution
     */
    public double getStdDev();

}
