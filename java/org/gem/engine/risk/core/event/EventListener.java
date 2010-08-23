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

package org.gem.engine.risk.core.event;

import org.gem.engine.risk.core.cache.Cache;

/**
 * A piece of logic that can be executed when an event is raised.
 * 
 * @author Andrea Cerisara
 * @version $Id: EventListener.java 562 2010-07-16 12:58:03Z acerisara $
 */
public interface EventListener
{

    /**
     * Executes the logic of this listener.
     * 
     * @param event the event raised
     * @param buffer the buffer shared between all the listeners attached to the engine
     * @param parameters the parameters forwarded by the component that raised the event
     */
    public void process(String event, Cache buffer, Object... parameters);

}
