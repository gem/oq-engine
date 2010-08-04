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

package org.gem.engine.data;

import java.util.Collection;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/**
 * A discrete function where values are pre calculated and fixed.
 * 
 * @author Andrea Cerisara
 * @version $Id: FixedDiscreteFunction.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class FixedDiscreteFunction implements DiscreteFunction
{

    private Map<Double, Double> values;

    public FixedDiscreteFunction()
    {
        this.values = new TreeMap<Double, Double>();
    }

    @Override
    public Set<Double> getDomain()
    {
        return values.keySet();
    }

    @Override
    public double getFor(double value)
    {
        return values.get(value);
    }

    /**
     * Adds a pair of values to this function.
     * 
     * @param x the value for the x axis (domain)
     * @param y the value for the y axis (codomain)
     */
    public void addPair(double x, double y)
    {
        values.put(x, y);
    }

    @Override
    public Collection<Double> getCodomain()
    {
        return values.values();
    }

}
