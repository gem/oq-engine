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

import java.util.HashMap;
import java.util.Map;

import org.gem.engine.risk.core.cache.Cache;

abstract class MultiEventComponent extends EventSourceListener
{

    private Map<String, String> listeners;

    MultiEventComponent()
    {
        listeners = new HashMap<String, String>();
    }

    /**
     * Binds a method to the given event.
     * <p>
     * The method will be called via reflection.
     * 
     * @param event the event name
     * @param methodName the name of the method to call when the event is raised
     */
    public void dispatchTo(String event, String methodName)
    {
        listeners.put(event, methodName);
    }

    @Override
    public void process(String event, Cache buffer, Object... parameters)
    {
        String methodToInvoke = listeners.get(event);

        if (methodToInvoke == null)
        {
            throw new IllegalArgumentException("No method defined for event " + event + ".");
        }

        invoke(methodToInvoke, buffer, parameters);
    }

    protected abstract void invoke(String methodToInvoke, Cache buffer, Object... parameters);

}
