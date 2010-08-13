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

package org.gem.engine.risk.core.event.listener;

import static org.gem.engine.risk.core.AdditionalPipeKeys.ASSET;
import static org.junit.Assert.assertEquals;

import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.core.event.listener.AssetLoader;
import org.gem.engine.risk.core.reader.AssetReader;
import org.gem.engine.risk.data.asset.Asset;
import org.junit.Before;
import org.junit.Test;

public class AssetLoaderTest extends BaseFilterTest implements AssetReader
{

    private Asset asset;

    @Before
    public void setUp()
    {
        filter = new AssetLoader(this);
        asset = Asset.newAsset(1.0, anySite());
    }

    @Test
    public void shouldLoadAnAssetIntoThePipe()
    {
        runOn(anySite());
        assertEquals(asset, pipeValueAtKey(ASSET));
    }

    @Test
    public void shouldLinkTheCurrentSiteToTheAssetLoaded()
    {
        runOn(anySite());
        assertEquals(anySite(), ((Asset) pipeValueAtKey(ASSET)).definedAt());
    }

    @Override
    public Asset readAt(Site site)
    {
        return asset;
    }

}
