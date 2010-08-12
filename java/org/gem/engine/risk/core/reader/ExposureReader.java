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

package org.gem.engine.risk.core.reader;

import org.gem.engine.risk.core.Site;

/**
 * Specifies objects that are capable of reading values from external exposures.
 * 
 * @author Andrea Cerisara
 * @version $Id: ExposureReader.java 567 2010-07-20 10:10:52Z acerisara $
 */
public interface ExposureReader
{

    /**
     * Reads the value at the given site.
     * 
     * @param site the site used
     * @return the value at the given site
     */
    public double readAt(Site site);

}
