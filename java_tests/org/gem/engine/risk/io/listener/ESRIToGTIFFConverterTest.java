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

import static org.gem.engine.risk.io.listener.ESRIToGTIFFConverter.COMMAND;
import static org.gem.engine.risk.io.listener.ESRIToGTIFFConverter.OPTIONS;
import static org.hamcrest.Matchers.containsString;
import static org.junit.Assert.assertThat;

import org.gem.engine.risk.core.event.EventListener;
import org.gem.engine.risk.io.listener.ESRIToGTIFFConverter;
import org.gem.engine.risk.io.util.CommandRunner;
import org.junit.Before;
import org.junit.Test;

public class ESRIToGTIFFConverterTest implements CommandRunner
{

    private static final String PATH = "/path";
    private static final String SOURCE = "SOURCE.txt";

    private String command;
    private EventListener converter;

    @Before
    public void setUp()
    {
        converter = new ESRIToGTIFFConverter(this, PATH, SOURCE);
    }

    @Test
    public void shouldPassTheCommandName()
    {
        process();
        assertThat(command, containsString(PATH + "/" + COMMAND));
    }

    @Test
    public void shouldPassTheCommandOptions()
    {
        process();
        assertThat(command, containsString(COMMAND + " " + OPTIONS));
    }

    @Test
    public void shouldPassTheSourceFilename()
    {
        process();
        assertThat(command, containsString(OPTIONS + " " + SOURCE));
    }

    @Test
    public void shouldPassTheDestinationFilename()
    {
        process();
        assertThat(command, containsString(SOURCE + " " + "SOURCE.tif"));
    }

    private void process()
    {
        converter.process(null, null);
    }

    @Override
    public void run(String command)
    {
        this.command = command;
    }

}
