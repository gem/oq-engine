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

package org.gem.engine.risk.data.country;

import org.gem.engine.risk.data.Computable;

/**
 * Describes a country.
 * <p>
 * For more information about the country codes see Report11-GEM1_Global_Risk_Calculations document, chapter 4.3.
 *
 * @author Andrea Cerisara
 * @version $Id: Country.java 537 2010-06-16 18:29:36Z acerisara $
 */
public abstract class Country implements Computable
{

    private final int code;

    /**
     * Creates a new country with the given code.
     * 
     * @param code the code to use
     * @return the newly created country
     */
    public static Country newCountry(int code)
    {
        return new CountryWithValue(code);
    }

    /**
     * Creates a new empty country.
     * 
     * @return the newly created country
     */
    public static Country emptyCountry()
    {
        return new EmptyCountry();
    }

    /**
     * @param code the code of the country
     */
    public Country(int code)
    {
        this.code = code;
    }

    /**
     * Returns the code of this country.
     * 
     * @return the code of this country
     */
    public int getCode()
    {
        return code;
    }

}
