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
import java.util.Set;

/**
 * Describes a discrete function, ie. a function that can be represented using a finite number of values.
 * 
 * @author Andrea Cerisara
 * @version $Id: DiscreteFunction.java 537 2010-06-16 18:29:36Z acerisara $
 */
public interface DiscreteFunction extends Function
{

    /**
     * Returns the domain values of this function, in ascending order.
     * 
     * @return the domain values of this function
     */
    public Set<Double> getDomain();

    /**
     * Returns the codomain values of this function.
     * <p>
     * The values are returned in ascending order of the corresponding domain values.
     * 
     * @return the codomain values of this function
     */
    public Collection<Double> getCodomain();

}
