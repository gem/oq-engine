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

package org.gem.engine.risk.calc;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;

/**
 * An utility class to handle intervals of values.
 * 
 * @author Andrea Cerisara
 * @version $Id: Interval.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class Interval implements Iterable<Double>
{

    private List<Double> values;

    /**
     * Constructs a new interval using the given list of values.
     * 
     * @param values the list of values to be used in this interval
     */
    public Interval(List<Double> values)
    {
        this.values = values;
    }

    /**
     * Constructs a new interval using the given set of values.
     * <p>
     * The order of this interval is the one provided by the iterator of the given set, so it really depends on the implementation.
     * 
     * @param values the set of values to be used in this interval
     */
    public Interval(Set<Double> values)
    {
        this.values = new ArrayList<Double>(values);
    }

    /**
     * Constructs a new interval using the given array of values.
     * 
     * @param values the array of values to be used in this interval
     */
    public Interval(Double... values)
    {
        this.values = Arrays.asList(values);
    }

    /**
     * Returns the lower bound for the given value.
     * <p>
     * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.2.1.
     * 
     * @param value the value used to compute the lower bound
     * @return the lower bound for the given value
     */
    public double lowerBoundFor(double value)
    {
        if (values.contains(value))
        {
            int index = isFirstElement(value) ? 1 : values.indexOf(value);
            double offSet = (values.get(index) - values.get(index - 1)) / 2;

            return value - offSet;
        }

        throw new RuntimeException("Value " + value + " not in the interval!");
    }

    private boolean isFirstElement(double value)
    {
        return values.indexOf(value) == 0;
    }

    private boolean isLastElement(double value)
    {
        return values.indexOf(value) == values.size() - 1;
    }

    /**
     * Returns the upper bound for the given value.
     * <p>
     * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 7.2.1.
     * 
     * @param value the value used to compute the upper bound
     * @return the upper bound for the given value
     */
    public double upperBoundFor(double value)
    {
        if (values.contains(value))
        {
            int index = isLastElement(value) ? values.size() - 2 : values.indexOf(value);
            double offSet = (values.get(index + 1) - values.get(index)) / 2;

            return value + offSet;
        }

        throw new RuntimeException("Value " + value + " not in the interval!");
    }

    /**
     * Returns the size of this interval.
     * 
     * @return the size of this interval
     */
    public int size()
    {
        return values.size();
    }

    /**
     * Splits each interval between two consecutive values in a new interval with the number of values specified.
     * <p>
     * For example [1.0, 2.0] splitted by 2 returns [1.0, 1.5, 2.0].
     * 
     * @param numberOfValuesBetween the number of values between two consecutive values
     * @return a new interval splitted with the number of values specified
     */
    public Interval split(int numberOfValuesBetween)
    {
        if (values.size() < 2)
        {
            throw new RuntimeException("You need at least two values to split this interval!");
        }

        Set<Double> result = new TreeSet<Double>();

        for (int i = 0; i < values.size() - 1; i++)
        {
            double lowerBound = values.get(i);
            double upperBound = values.get(i + 1);

            result.add(lowerBound);
            result.addAll(intervalFor(lowerBound, upperBound, numberOfValuesBetween));
            result.add(upperBound);
        }

        return new Interval(new ArrayList<Double>(result));
    }

    private Set<Double> intervalFor(double lowerBound, double upperBound, int numberOfValuesBetween)
    {
        Set<Double> result = new HashSet<Double>();
        BigDecimal step = new BigDecimal(upperBound - lowerBound).divide(new BigDecimal(numberOfValuesBetween));

        for (int i = 1; i < numberOfValuesBetween; i++)
        {
            result.add(lowerBound + (step.multiply(new BigDecimal(i))).doubleValue());
        }

        return result;
    }

    /**
     * Two interval are equal when have the same size and same values in the same order.
     */
    @Override
    public boolean equals(Object obj)
    {
        if (!(obj instanceof Interval))
        {
            return false;
        }

        Interval other = (Interval) obj;

        if (size() != other.size())
        {
            return false;
        }

        for (int i = 0; i < values.size(); i++)
        {
            if (!get(i).equals(other.get(i)))
            {
                return false;
            }
        }

        return true;
    }

    /**
     * Returns the element at the given index.
     * 
     * @param index the index to use
     * @return the element at the given index
     */
    public Double get(int index)
    {
        return values.get(index);
    }

    @Override
    public Iterator<Double> iterator()
    {
        return values.iterator();
    }

}
