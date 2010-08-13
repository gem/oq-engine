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

package org.gem.engine.risk.core.validation;

import org.gem.engine.risk.core.cache.Pipe;
import org.gem.engine.risk.data.Computable;

/**
 * A specification that checks if a previously loaded data is {@link Computable}.
 * 
 * @author Andrea Cerisara
 * @version $Id: IsDataComputable.java 499 2010-05-18 12:51:39Z acerisara $
 */
public class IsDataComputable extends Specification
{

    private final String key;

    /**
     * @param key the key used to extract the data from the pipe
     */
    public IsDataComputable(String key)
    {
        this.key = key;
    }

    @Override
    public boolean isSatisfiedBy(Pipe pipe)
    {
        return ((Computable) pipe.get(key)).isComputable();
    }

}
