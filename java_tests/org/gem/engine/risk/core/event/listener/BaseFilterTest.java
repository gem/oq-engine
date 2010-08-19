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

package org.gem.engine.risk.core.event.listener;

import static org.gem.engine.risk.core.cache.Pipe.CURRENT_SITE;
import static org.junit.Assert.assertTrue;

import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.cache.Pipe;
import org.gem.engine.risk.core.event.EventSourceListener;
import org.gem.engine.risk.core.event.Filter;

public class BaseFilterTest extends EventSourceListener
{

    private static final String AN_EVENT = null;

    protected static final Cache A_BUFFER = null;
    protected static final String A_KEY = "AKEY";
    protected static final String A_VALUE = "AVALUE";

    protected Pipe pipe;
    protected Filter filter;
    protected String eventRaised;
    protected Object[] parameters;

    public BaseFilterTest()
    {
        pipe = new Pipe();
    }

    protected void runOn(Site site)
    {
        pipe.put(CURRENT_SITE, site);
        filter.process(AN_EVENT, A_BUFFER, pipe);
    }

    @Override
    public void process(String event, Cache buffer, Object... parameters)
    {
        this.eventRaised = event;
        this.parameters = parameters;
    }

    protected void assertPipeForwarded()
    {
        assertTrue(parameters.length > 0);
        assertTrue(parameters[0] instanceof Pipe);
    }

    protected Site anySite()
    {
        return new Site(1.0, 1.0);
    }

    protected Object pipeValueAtKey(String key)
    {
        return pipe.get(key);
    }

    protected void addToPipe(String key, Object value)
    {
        pipe.put(key, value);
    }

}
