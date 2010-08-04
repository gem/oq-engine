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

package org.gem.engine.core;

import static org.gem.engine.core.cache.Pipe.CURRENT_SITE;
import static org.gem.engine.core.cache.Pipe.REGION;

import org.gem.engine.core.cache.Cache;
import org.gem.engine.core.cache.InMemoryCache;
import org.gem.engine.core.cache.Pipe;
import org.gem.engine.core.event.EventSource;

/**
 * The entry point to trigger computations.
 * <p>
 * An {@link EventSource} that is capable of triggering events for each {@link Site} in the {@link Region}.
 * <p>
 * This source raises:<br>
 * <ul>
 * <li><code>STOP</code> when the computation stops
 * <li><code>START</code> when the computation starts
 * <li><code>SITE_LOADED</code> for each {@link Site} in the {@link Region}
 * </ul>
 * <p>
 * These are the optional parameters passed:<br>
 * <ul>
 * <li>for <code>STOP</code> no parameters
 * <li>for <code>START</code> the {@link Region} to compute
 * <li>for <code>SITE_LOADED</code> a new {@link Pipe} containing the {@link Region} to compute and the current {@link Site}
 * </ul>
 * 
 * @author Andrea Cerisara
 * @version $Id: Engine.java 562 2010-07-16 12:58:03Z acerisara $
 */
public class Engine extends EventSource
{

    /**
     * Identifies the event raised when the computation stops.
     */
    public static final String STOP = "STOP";

    /**
     * Identifies the event raised when the computation starts.
     */
    public static final String START = "START";

    /**
     * Identifies the event raised when a {@link Site} has been loaded inside the engine.
     */
    public static final String SITE_LOADED = "SITELOADED";

    private final Cache buffer;

    /**
     * Default constructor.
     * <p>
     * <code>org.gem.engine.core.cache.InMemoryCache</code> is the implementation used as buffer shared between all the listeners attached to this engine.
     */
    public Engine()
    {
        this(new InMemoryCache());
    }

    /**
     * @param buffer the buffer shared between all the listeners attached to the engine
     */
    public Engine(Cache buffer)
    {
        this.buffer = buffer;
        canRaise(START, STOP, SITE_LOADED);
    }

    /**
     * Computes the given region.
     * 
     * @param region the region to compute
     */
    public void compute(Region region)
    {
        raise(START, buffer, region);

        for (Site site : region)
        {
            raise(SITE_LOADED, buffer, pipe(region, site));
        }

        raise(STOP, buffer);
    }

    private Pipe pipe(Region region, Site currentSite)
    {
        Pipe pipe = new Pipe();

        pipe.put(REGION, region);
        pipe.put(CURRENT_SITE, currentSite);

        return pipe;
    }

}
