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

package org.gem.engine.data.builder;

import org.gem.engine.data.HazardCurve;

public class HazardCurveBuilder
{

    private HazardCurve curve;

    public static HazardCurveBuilder aCurve()
    {
        return new HazardCurveBuilder();
    }

    private HazardCurveBuilder()
    {
        curve = new HazardCurve(null, 0, null, null, null);
    }

    public HazardCurve build()
    {
        return curve;
    }

    public HazardCurveBuilder withPair(double IML, double value)
    {
        curve.addPair(IML, value);

        return this;
    }

}
