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

package org.gem.engine.risk.data.asset;

import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.data.Computable;

/**
 * Describes an asset.
 * 
 * @author Andrea Cerisara
 * @version $Id: Asset.java 537 2010-06-16 18:29:36Z acerisara $
 */
public abstract class Asset implements Computable
{

    private final double value;
    private final Site definedAt;

    /**
     * Creates a new asset with the given value.
     * 
     * @param value the value to use
     * @param definedAt the site where the asset is defined
     * @return the newly created asset
     */
    public static Asset newAsset(double value, Site definedAt)
    {
        return new AssetWithValue(value, definedAt);
    }

    /**
     * Creates a new empty asset.
     * 
     * @param definedAt the site where the asset is defined
     * @return the newly created asset
     */
    public static Asset emptyAsset(Site definedAt)
    {
        return new EmptyAsset(definedAt);
    }

    /**
     * @param value the value of the asset
     * @param definedAt the site where the asset is defined
     */
    public Asset(double value, Site definedAt)
    {
        this.value = value;
        this.definedAt = definedAt;
    }

    /**
     * Returns the value of this asset.
     * 
     * @return the values of this asset
     */
    public double getValue()
    {
        return value;
    }

    /**
     * Returns the site where this asset is defined.
     * 
     * @return the site where this asset is defined
     */
    public Site definedAt()
    {
        return definedAt;
    }

}
