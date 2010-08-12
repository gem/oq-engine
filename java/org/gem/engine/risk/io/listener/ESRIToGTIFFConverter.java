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

package org.gem.engine.risk.io.listener;

import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.event.EventSourceListener;
import org.gem.engine.risk.io.util.CommandRunner;

/**
 * Converts an ESRI ascii output to a GEOTiff output.
 * 
 * @author Andrea Cerisara
 * @version $Id: ESRIToGTIFFConverter.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class ESRIToGTIFFConverter extends EventSourceListener
{

    public static final String COMMAND = "gdal_translate";
    public static final String OPTIONS = "-a_srs EPSG:4326 -of GTiff";

    private final String path;
    private final String filename;
    private final CommandRunner runner;

    /**
     * @param runner the command runner used to run the command
     * @param path the path of the gdal_translate command tool
     * @param filename the name of the file to convert
     */
    public ESRIToGTIFFConverter(CommandRunner runner, String path, String filename)
    {
        this.path = path;
        this.runner = runner;
        this.filename = filename;
    }

    private String destination()
    {
        return filename.split("\\.")[0] + ".tif";
    }

    @Override
    public void process(String event, Cache buffer, Object... parameters)
    {
        runner.run(path + "/" + COMMAND + " " + OPTIONS + " " + filename + " " + destination());
    }

}
