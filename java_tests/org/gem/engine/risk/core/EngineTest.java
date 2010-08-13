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

package org.gem.engine.risk.core;

import static org.gem.engine.risk.core.Engine.SITE_LOADED;
import static org.gem.engine.risk.core.Engine.START;
import static org.gem.engine.risk.core.Engine.STOP;
import static org.gem.engine.risk.core.cache.Pipe.CURRENT_SITE;
import static org.gem.engine.risk.core.cache.Pipe.REGION;
import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertThat;
import static org.junit.Assert.assertTrue;

import java.util.ArrayList;
import java.util.List;

import org.gem.engine.risk.core.Engine;
import org.gem.engine.risk.core.Region;
import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.cache.InMemoryCache;
import org.gem.engine.risk.core.cache.Pipe;
import org.gem.engine.risk.core.event.EventListener;
import org.gem.engine.risk.core.event.Filter;
import org.junit.Before;
import org.junit.Test;

public class EngineTest implements EventListener
{

    private Region region;
    private Engine engine;

    private boolean processed;
    private Object[] parameters;

    @Before
    public void setUp()
    {
        engine = new Engine();
        region = Region.singleCellRegion(new Site(1.0, 1.0));
    }

    @Test
    public void theStartEventIsRaisedWhenComputationStarts()
    {
        engine.on(START, this);
        engine.compute(region);
        assertThat(parameterAt(0, Region.class), is(region));
    }

    @Test
    public void theSiteLoadedEventIsRaisedWhenASiteIsLoaded()
    {
        engine.on(SITE_LOADED, this);
        engine.compute(region);

        assertThat(pipeValueIdentifiedBy(REGION, Region.class), is(region));
        assertThat(pipeValueIdentifiedBy(CURRENT_SITE, Site.class), is(new Site(1.0, 1.0)));
    }

    @Test
    public void theSiteLoadedEventIsRaisedWhenEachSiteIsLoaded()
    {
        final List<Site> sites = new ArrayList<Site>();
        engine.on(SITE_LOADED, new Filter()
        {

            @Override
            protected void filter(Cache buffer, Pipe pipe)
            {
                sites.add((Site) pipe.get(CURRENT_SITE));
            }
        });

        // four sites region
        engine.compute(new Region(new Site(1.0, 2.0), new Site(2.0, 1.0), 1.0));

        assertThat(sites.size(), is(4));
        assertThat(sites.get(0), is(new Site(1.0, 2.0)));
        assertThat(sites.get(1), is(new Site(2.0, 2.0)));
        assertThat(sites.get(2), is(new Site(1.0, 1.0)));
        assertThat(sites.get(3), is(new Site(2.0, 1.0)));
    }

    @Test
    public void theStopEventIsRaisedWhenComputationStops()
    {
        engine.on(STOP, this);
        engine.compute(region);
        assertTrue(processed);
    }

    @Test
    public void aBufferIsSharedBetweenListenersAttachedToDifferentEvents()
    {
        engine = new Engine(new InMemoryCache());

        engine.on(START, new EventListener()
        {

            @Override
            public void process(String event, Cache buffer, Object... parameters)
            {
                buffer.put("KEY", "VALUE");
            }
        });

        engine.on(STOP, new EventListener()
        {

            @Override
            public void process(String event, Cache buffer, Object... parameters)
            {
                assertThat((String) buffer.get("KEY"), is("VALUE"));
            }
        });

        engine.compute(region);
    }

    @Test
    public void aBufferIsSharedBetweenListenersAndFiltersAttachedToDifferentEvents()
    {
        engine = new Engine(new InMemoryCache());

        engine.on(START, new EventListener()
        {

            @Override
            public void process(String event, Cache buffer, Object... parameters)
            {
                buffer.put("KEY", "VALUE");
            }
        });

        engine.on(SITE_LOADED, new Filter()
        {

            @Override
            protected void filter(Cache buffer, Pipe pipe)
            {
                assertThat((String) buffer.get("KEY"), is("VALUE"));
            }
        });

        engine.compute(region);
    }

    @SuppressWarnings("unchecked")
    private <T> T pipeValueIdentifiedBy(String key, Class<T> type)
    {
        return (T) ((Pipe) parameters[0]).get(key);
    }

    @SuppressWarnings("unchecked")
    private <T> T parameterAt(int index, Class<T> type)
    {
        return (T) parameters[index];
    }

    @Override
    public void process(String event, Cache buffer, Object... parameters)
    {
        this.processed = true;
        this.parameters = parameters;
    }

}
