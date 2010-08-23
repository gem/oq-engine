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

package org.gem.engine.risk.io.reader;

import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.core.reader.AssetReader;
import org.gem.engine.risk.core.reader.ExposureReader;
import org.gem.engine.risk.data.asset.Asset;
import org.gem.engine.risk.io.reader.definition.ESRIRasterFileDefinition;

/**
 * Reads assets using an ESRI raster binary file as source.
 * <p>
 * For more information about the format used, take a look <a href="http://en.wikipedia.org/wiki/ESRI_grid">here</a>.
 * <br/>This implementation is not thread safe.
 * 
 * @author Andrea Cerisara
 * @version $Id: ESRIBinaryFileAssetReader.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class ESRIBinaryFileAssetReader implements AssetReader
{

    private final ExposureReader exposure;
    private final ESRIRasterFileDefinition definition;

    /**
     * @param exposure the exposure reader to use
     * @param definition the ESRI raster file definition to use
     */
    public ESRIBinaryFileAssetReader(ExposureReader exposure, ESRIRasterFileDefinition definition)
    {
        this.exposure = exposure;
        this.definition = definition;
    }

    @Override
    public Asset readAt(Site site)
    {
        double amount = exposure.readAt(site);
        return definition.isNoData(amount) ? Asset.emptyAsset(site) : Asset.newAsset(amount, site);
    }

}
