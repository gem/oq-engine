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

package org.gem.engine.io.reader;

import org.gem.engine.core.Site;
import org.gem.engine.core.reader.CountryReader;
import org.gem.engine.core.reader.ExposureReader;
import org.gem.engine.data.country.Country;
import org.gem.engine.io.reader.definition.ESRIRasterFileDefinition;

/**
 * Reads countries using an ESRI raster binary file as source.
 * <p>
 * For more information about the format used, take a look <a href="http://en.wikipedia.org/wiki/ESRI_grid">here</a>.
 * <br/>This implementation is not thread safe.
 *
 * @author Andrea Cerisara
 * @version $Id: ESRIBinaryFileCountryReader.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class ESRIBinaryFileCountryReader implements CountryReader
{

    private final ExposureReader exposure;
    private final ESRIRasterFileDefinition definition;

    /**
     * @param exposure the exposure reader to use
     * @param definition the ESRI raster file definition to use
     */
    public ESRIBinaryFileCountryReader(ExposureReader exposure, ESRIRasterFileDefinition definition)
    {
        this.exposure = exposure;
        this.definition = definition;
    }

    @Override
    public Country readAt(Site site)
    {
        double adminCode = exposure.readAt(site);
        return definition.isNoData(adminCode) ? Country.emptyCountry() : Country.newCountry((int) adminCode);
    }

}
