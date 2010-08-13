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

import static org.junit.Assert.assertEquals;

import org.gem.engine.risk.BaseTestCase;
import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.core.reader.ExposureReader;
import org.gem.engine.risk.core.reader.HazardReader;
import org.gem.engine.risk.io.reader.AsciiFileReader;
import org.gem.engine.risk.io.reader.AsciiFileReader.LineBlock;
import org.junit.Test;

public class OtherIntegrationTests extends BaseTestCase
{

    private ExposureReader exposure;

    private Double expectedValue(String line, String separator)
    {
        return new Double(line.split(separator)[0]);
    }

    private Site site(String line, String separator)
    {
        return new Site(new Double(line.split(separator)[1]), new Double(line.split(separator)[2]));
    }

    @Test
    public void exposure1()
    {
        exposure = allValuesFilledExposure();
        AsciiFileReader reader = new AsciiFileReader(resultPathFor("all_values_filled.txt"));

        reader.open().forEachLineDo(new LineBlock()
        {

            @Override
            public void execute(String line)
            {
                assertEquals(expectedValue(line, " "), exposure.readAt(site(line, " ")), 0.00009);
            }
        }).close();
    }

    @Test
    public void exposure2()
    {
        exposure = noDataExposure();
        AsciiFileReader reader = new AsciiFileReader(resultPathFor("no_data.txt"));

        reader.open().forEachLineDo(new LineBlock()
        {

            @Override
            public void execute(String line)
            {
                assertEquals(expectedValue(line, " "), exposure.readAt(site(line, " ")), 0.00009);
            }
        }).close();
    }

    @Test
    public void exposure3()
    {
        exposure = chilePopulationExposure();
        AsciiFileReader reader = new AsciiFileReader(resultPathFor("chile_population.txt"));

        reader.open().forEachLineDo(new LineBlock()
        {

            @Override
            public void execute(String line)
            {
                assertEquals(expectedValue(line, "\t"), exposure.readAt(site(line, "\t")), 0.00009);
            }
        }).close();
    }

    @Test
    public void IMLs()
    {
        final HazardReader<Double> IMLs = hazardMMI();
        AsciiFileReader reader = new AsciiFileReader(resultPathFor("Hazard_MMI.txt"));

        reader.open().forEachLineDo(new LineBlock()
        {

            @Override
            public void execute(String line)
            {
                assertEquals(expectedValue(line, "\t"), IMLs.readAt(site(line, "\t")), 0.00009);
            }
        }).close();
    }

    @Test
    public void IMLs1Km()
    {
        final HazardReader<Double> IMLs = hazardMMI1Km();
        AsciiFileReader reader = new AsciiFileReader(resultPathFor("Hazard_MMI_1km.txt"));

        reader.open().forEachLineDo(new LineBlock()
        {

            @Override
            public void execute(String line)
            {
                assertEquals(expectedValue(line, "\t"), IMLs.readAt(site(line, "\t")), 0.00009);
            }
        }).close();
    }

    @Test
    public void IMLs6Km()
    {
        final HazardReader<Double> IMLs = hazardMMI6Km();
        AsciiFileReader reader = new AsciiFileReader(resultPathFor("Hazard_MMI_1km.txt"));

        reader.open().forEachLineDo(new LineBlock()
        {

            @Override
            public void execute(String line)
            {
                assertEquals(expectedValue(line, "\t"), IMLs.readAt(site(line, "\t")), 0.00009);
            }
        }).close();
    }

}
