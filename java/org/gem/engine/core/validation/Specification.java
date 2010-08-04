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

package org.gem.engine.core.validation;

import org.gem.engine.core.cache.Pipe;

/**
 * A business rule specification, according to the <a href="http://en.wikipedia.org/wiki/Specification_pattern">pattern</a>.
 * 
 * @author Andrea Cerisara
 * @version $Id: Specification.java 499 2010-05-18 12:51:39Z acerisara $
 */
public abstract class Specification
{

    /**
     * Returns a specification that is valid when the data identified by the given key is computable.
     * 
     * @param key the key used to extract the data from the pipe
     * @return the newly created specification
     */
    public static Specification computable(String key)
    {
        return new IsDataComputable(key);
    }

    /**
     * Returns a specification that is valid when all the given specifications are valid.
     * 
     * @param specifications the specifications to use
     * @return the specification with the given specifications and-joined
     */
    public static Specification and(Specification... specifications)
    {
        return new AndSpecification(specifications);
    }

    /**
     * Checks if this business rule is satisfied by the given pipe.
     * 
     * @param pipe the pipe used
     * @return <code>true</code> if this business rule is satisfied, <code>false</code> otherwise
     */
    public abstract boolean isSatisfiedBy(Pipe pipe);

}
