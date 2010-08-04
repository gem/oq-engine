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

package org.gem.engine;

import org.gem.engine.core.reader.ExposureReader;
import org.gem.engine.core.reader.HazardReader;
import org.gem.engine.io.reader.AsciiFileHazardIMLReader;
import org.gem.engine.io.reader.ESRIBinaryFileExposureReader;
import org.gem.engine.io.reader.definition.ESRIRasterFileDefinition;
import org.gem.engine.io.reader.definition.reader.HazardIMLESRIRasterFileDefinitionReader;
import org.gem.engine.io.reader.definition.reader.StandardESRIRasterFileDefinitionReader;

public class BaseTestCase
{

    protected String pathFor(String filename)
    {
        return this.getClass().getClassLoader().getResource(filename).getPath();
    }

    protected String resultPathFor(String filename)
    {
        return this.getClass().getClassLoader().getResource("result_" + filename).getPath();
    }

    protected ExposureReader allValuesFilledExposure()
    {
        return new ESRIBinaryFileExposureReader(pathFor("all_values_filled.flt"),
                exposureDefinition("all_values_filled.hdr"));
    }

    protected ExposureReader noDataExposure()
    {
        return new ESRIBinaryFileExposureReader(pathFor("no_data.flt"), exposureDefinition("no_data.hdr"));
    }

    protected ExposureReader chilePopulationExposure()
    {
        return new ESRIBinaryFileExposureReader(pathFor("chile_population.flt"),
                exposureDefinition("chile_population.hdr"));
    }

    protected HazardReader<Double> hazardMMI()
    {
        return new AsciiFileHazardIMLReader(pathFor("Hazard_MMI.txt"), hazardDefinition("Hazard_MMI.txt"));
    }

    protected HazardReader<Double> hazardMMI1Km()
    {
        return new AsciiFileHazardIMLReader(pathFor("Hazard_MMI_1km.txt"), hazardDefinition("Hazard_MMI_1km.txt"));
    }

    protected HazardReader<Double> hazardMMI6Km()
    {
        return new AsciiFileHazardIMLReader(pathFor("Hazard_MMI_6km.txt"), hazardDefinition("Hazard_MMI_6km.txt"));
    }

    protected ESRIRasterFileDefinition exposureDefinition(String filename)
    {
        return new StandardESRIRasterFileDefinitionReader(pathFor(filename)).read();
    }

    protected ESRIRasterFileDefinition hazardDefinition(String filename)
    {
        return new HazardIMLESRIRasterFileDefinitionReader(pathFor(filename)).read();
    }

}
