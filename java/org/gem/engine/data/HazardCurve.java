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

package org.gem.engine.data;

/**
 * Describes an hazard curve function.
 * <p>
 * For more information see Report11-GEM1_Global_Risk_Calculations document, chapter 5.2.
 *
 * @author Andrea Cerisara
 * @version $Id: HazardCurve.java 582 2010-07-21 08:51:15Z acerisara $
 */
public class HazardCurve extends FixedDiscreteFunction implements Computable
{

    private final String IMT;
    private final String ERF;
    private final String type;
    private final Integer timeSpan;
    private final String probabilisticType;

    /**
     * @param type the type of curve
     * @param IMT the intensity measure type used by the curve
     * @param timeSpan the time span to which the curve is valid
     * @param ERF the earthquake rupture forecast described by the curve
     * @param probabilisticType the probabilistic type used (PO, PE, AFE)
     */
    public HazardCurve(String probabilisticType, int timeSpan, String IMT, String type, String ERF)
    {
        this.IMT = IMT;
        this.ERF = ERF;
        this.type = type;
        this.timeSpan = timeSpan;
        this.probabilisticType = probabilisticType;
    }

    /**
     * Returns the time span to which this curve is valid.
     * 
     * @return the time span to which this curve is valid
     */
    public int getTimeSpan()
    {
        return timeSpan;
    }

    /**
     * Returns the intensity measure type used by this curve.
     * 
     * @return the intensity measure type used by this curve
     */
    public String getIMT()
    {
        return IMT;
    }

    /**
     * Returns the type of this curve.
     * 
     * @return the type of this curve
     */
    public String ofType()
    {
        return type;
    }

    /**
     * Returns the earthquake rupture forecast described by this curve.
     * 
     * @return the earthquake rupture forecast described by this curve
     */
    public String getERF()
    {
        return ERF;
    }

    public boolean isComputable()
    {
        return getDomain().size() > 0;
    }

    /**
     * Returns the probabilistic type (PO, PE, AFE) of this curve.
     * 
     * @return the probabilistic type of this curve
     */
    public String getProbabilisticType()
    {
        return probabilisticType;
    }

}
