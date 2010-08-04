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

package org.gem.engine.core.reader;

import org.gem.engine.core.Site;
import org.gem.engine.data.HazardCurve;

/**
 * Specifies objects that are capable of reading shakemap values from external sources.
 * 
 * @author Andrea Cerisara
 * @version $Id: HazardReader.java 567 2010-07-20 10:10:52Z acerisara $
 * @param <TYPE_OF_VALUE> the type of value readed ({@link Double} for IMLs or {@link HazardCurve} for curves)
 */
public interface HazardReader<TYPE_OF_VALUE>
{

    /**
     * Reads the shakemap value at the given site.
     * 
     * @param site the site used
     * @return the shakemap value at the given site
     */
    public TYPE_OF_VALUE readAt(Site site);

}
