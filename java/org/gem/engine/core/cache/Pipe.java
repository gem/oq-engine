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

package org.gem.engine.core.cache;

import org.gem.engine.core.Region;
import org.gem.engine.core.Site;

/**
 * Represents a pipe in the Pipe&Filter architecture.
 * 
 * @author Andrea Cerisara
 * @version $Id: Pipe.java 556 2010-07-16 08:29:56Z acerisara $
 */
public class Pipe extends InMemoryCache
{

    /**
     * The key used to store the {@link Region} the engine is computing.
     */
    public static final String REGION = "REGION";

    /**
     * The key used to store the {@link Site} the engine is currently processing.
     */
    public static final String CURRENT_SITE = "CURRENTSITE";

}
