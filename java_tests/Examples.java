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

import static org.gem.engine.core.Engine.SITE_LOADED;
import static org.gem.engine.core.Engine.START;
import static org.gem.engine.core.Engine.STOP;
import static org.gem.engine.core.Region.singleCellRegion;
import static org.gem.engine.core.cache.Pipe.CURRENT_SITE;

import org.gem.engine.core.Engine;
import org.gem.engine.core.Region;
import org.gem.engine.core.Site;
import org.gem.engine.core.cache.Cache;
import org.gem.engine.core.cache.Pipe;
import org.gem.engine.core.event.EventListener;
import org.gem.engine.core.event.Filter;
import org.junit.Test;

public class Examples
{

    @Test
    // To run select the method name, right click, Run As, JUnit Test
    public void simpleConfigurationWithOneListenerForEachEvent()
    {
        Engine engine = new Engine();
        engine.on(START, new EventListener()
        {

            @Override
            public void process(String event, Cache buffer, Object... parameters)
            {
                System.out.println("Engine started!");
            }
        });

        engine.on(SITE_LOADED, new Filter()
        {

            @Override
            protected void filter(Cache buffer, Pipe pipe)
            {
                System.out.println("Processing site " + pipe.get(CURRENT_SITE));
            }
        });

        engine.on(STOP, new EventListener()
        {

            @Override
            public void process(String event, Cache buffer, Object... parameters)
            {
                System.out.println("Engine stopped!");
            }
        });

        engine.compute(singleCellRegion(new Site(1.0, 1.0)));
    }

    @Test
    public void onTheStartEventTheComputedRegionIsPassedAsParameter()
    {
        Engine engine = new Engine();
        engine.on(START, new EventListener()
        {

            @Override
            public void process(String event, Cache buffer, Object... parameters)
            {
                System.out.println("Region computed is " + parameters[0]);
            }
        });

        engine.compute(singleCellRegion(new Site(1.0, 1.0)));
    }

    @Test
    public void theSiteLoadedEventIsRaisedForEachSiteInTheRegion()
    {
        Engine engine = new Engine();
        engine.on(SITE_LOADED, new Filter()
        {

            @Override
            protected void filter(Cache buffer, Pipe pipe)
            {
                System.out.println("Processing site " + pipe.get(CURRENT_SITE));
            }
        });

        engine.compute(new Region(new Site(1.0, 2.0), new Site(2.0, 1.0), 0.3));
    }

    @Test
    public void youCanAttachMultipleListenersToTheSameEvent()
    {
        Engine engine = new Engine();
        engine.on(START, new EventListener()
        {

            @Override
            public void process(String event, Cache buffer, Object... parameters)
            {
                System.out.println("Listener 1...");
            }
        });

        engine.on(START, new EventListener()
        {

            @Override
            public void process(String event, Cache buffer, Object... parameters)
            {
                System.out.println("Listener 2...");
            }
        });

        engine.on(START, new EventListener()
        {

            @Override
            public void process(String event, Cache buffer, Object... parameters)
            {
                System.out.println("Listener 3...");
            }
        });

        engine.compute(singleCellRegion(new Site(1.0, 1.0)));
    }

    @Test
    public void onTheSiteLoadedEventYouCanShareDataBetweenListeners()
    {
        Engine engine = new Engine();
        engine.on(SITE_LOADED, new Filter()
        {

            @Override
            protected void filter(Cache buffer, Pipe pipe)
            {
                pipe.put("KEY", "VALUE");
                System.out.println("Filter 1, saving value...");
            }
        });

        engine.on(SITE_LOADED, new Filter()
        {

            @Override
            protected void filter(Cache buffer, Pipe pipe)
            {
                System.out.println("Filter 2, value is " + pipe.get("KEY"));
            }
        });

        engine.on(SITE_LOADED, new Filter()
        {

            @Override
            protected void filter(Cache buffer, Pipe pipe)
            {
                System.out.println("Filter 3, value is " + pipe.get("KEY"));
            }
        });

        engine.compute(singleCellRegion(new Site(1.0, 1.0)));
    }

    @Test
    public void thereIsAlsoABufferThatIsSharedBetweenAllListeners()
    {
        Engine engine = new Engine();
        engine.on(START, new EventListener()
        {

            @Override
            public void process(String event, Cache buffer, Object... parameters)
            {
                buffer.put("KEY", "GLOBAL VALUE");
                System.out.println("START event, saving a value...");
            }
        });

        engine.on(SITE_LOADED, new Filter()
        {

            @Override
            protected void filter(Cache buffer, Pipe pipe)
            {
                System.out.println("SITE_LOADED event, value is " + buffer.get("KEY"));
            }
        });

        engine.on(STOP, new EventListener()
        {

            @Override
            public void process(String event, Cache buffer, Object... parameters)
            {
                System.out.println("STOP event, value is " + buffer.get("KEY"));
            }
        });

        engine.compute(singleCellRegion(new Site(1.0, 1.0)));
    }

}
