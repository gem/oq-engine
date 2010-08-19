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
import org.gem.engine.risk.core.reader.HazardReader;
import org.gem.engine.risk.data.HazardCurve;
import org.gem.engine.risk.io.reader.definition.ESRIRasterFileDefinition;
import org.gem.engine.risk.io.reader.definition.Point;

/**
 * Reads a set of {@link HazardCurve} from an external ascii file.
 * <p>
 * This is a buffered implementation, so it is safe to use files with big size. This implementation is not thread safe.
 * <br/>This is the file format used:
 * <p>
 * <i>PO 50.0  MMI mean    turkeyEmme<br/>
 * 26  46  +27.0000    +39.5000    0.1000<br/>
 * 1 6.0 5.4032e-03 7.0 3.0347e-02 8.0 9.9950e-02 9.0 2.1122e-01 10.0 0 1 6.0[...]<br/>
 * 1 6.0 1.9097e-03 7.0 1.2358e-02 8.0 4.6640e-02 9.0 1.1766e-01 10.0 0 1 6.0[...]<br/>
 * [...]
 * </i><p>
 * To know more about the format, take a look at the Report11-GEM1_Global_Risk_Calculations document, chapter 5.2.
 * 
 * @author Andrea Cerisara
 * @version $Id: AsciiFileHazardCurveReader.java 582 2010-07-21 08:51:15Z acerisara $
 */
public class AsciiFileHazardCurveReader implements HazardReader<HazardCurve>
{

    private static final int LINES_TO_CACHE = 15;
    private static final int HEADER_LINES_TO_SKIP = 2;

    private String[] specs;

    private final String filename;
    private final LineReader reader;
    private final ESRIRasterFileDefinition definition;

    /**
     * @param filename the name of the file used
     * @param definition the ESRI raster file definition used
     */
    public AsciiFileHazardCurveReader(String filename, ESRIRasterFileDefinition definition)
    {
        this.filename = filename;
        this.definition = definition;

        AsciiFileReader simpleReader = new AsciiFileReader(filename);
        this.reader = new BufferedLineReader(new HeaderLineReader(HEADER_LINES_TO_SKIP, simpleReader), LINES_TO_CACHE);
    }

    @Override
    public HazardCurve readAt(Site site)
    {
        if (specs == null)
        {
            loadCurveSpecification();
        }

        HazardCurve curve = newCurve();
        Point point = definition.fromSiteToGridPoint(site);
        addProbabilitiesTo(curve, reader.readAndSplit(point.getRow(), "\t")[point.getColumn() - 1]);

        return curve;
    }

    private HazardCurve newCurve()
    {
        // PO   50.0    MMI mean    turkeyEmme
        return new HazardCurve(specs[0], new Double(specs[1]).intValue(), specs[2], specs[3], specs[4]);
    }

    private void addProbabilitiesTo(HazardCurve curve, String unparsedValues)
    {
        String[] values = unparsedValues.split(" ");

        if (values.length > 1) // some values, curve valid
        {
            // 1 6.0 0.20747 7.0 0.18165 8.0 0.13784 9.0 0.06782
            for (int i = 1; i < values.length - 1; i += 2)
            {
                curve.addPair(Double.parseDouble(values[i]), Double.parseDouble(values[i + 1]));
            }
        }
    }

    private void loadCurveSpecification()
    {
        specs = new AsciiFileReader(filename).open().parseNextLineAndClose("\t");
    }

}
