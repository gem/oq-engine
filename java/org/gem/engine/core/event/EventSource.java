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

package org.gem.engine.core.event;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.gem.engine.core.cache.Cache;

/**
 * An object that is capable to raise events.
 * 
 * @author Andrea Cerisara
 * @version $Id: EventSource.java 562 2010-07-16 12:58:03Z acerisara $
 */
public class EventSource
{

    private Set<String> events;
    private Map<String, List<EventListener>> listeners;

    public EventSource()
    {
        this.events = new HashSet<String>();
        this.listeners = new HashMap<String, List<EventListener>>();
    }

    /**
     * Adds a listener to this source for the given event.
     * 
     * @param event the event name
     * @param listener the listener to attach
     * @throws UnknownEventException if the event is not registered
     * @throws IllegalArgumentException if the event is <code>null</code>
     * @throws IllegalArgumentException if the listener is <code>null</code>
     */
    public void on(String event, EventListener listener)
    {
        checkEventNotNull(event);
        checkEventRegistered(event);
        checkListenerNotNull(listener);

        listeners.get(event).add(listener);
    }

    private void checkListenerNotNull(EventListener listener)
    {
        if (listener == null)
        {
            throw new IllegalArgumentException("null is not accepted as a valid listener.");
        }
    }

    private void checkEventRegistered(String event)
    {
        if (!events.contains(event))
        {
            throw new UnknownEventException(event);
        }
    }

    private void checkEventNotNull(String event)
    {
        if (event == null)
        {
            throw new IllegalArgumentException("null is not accepted as a valid event.");
        }
    }

    /**
     * Raises the specified event forwarding the given parameters.
     * 
     * @param event the event to raise
     * @param buffer the buffer shared between all the listeners attached to the engine
     * @param parameters the parameters to forward to the attached listeners
     * @throws UnknownEventException if the event is not registered
     * @throws IllegalArgumentException if the event is <code>null</code>
     */
    public void raise(String event, Cache buffer, Object... parameters)
    {
        checkEventNotNull(event);
        checkEventRegistered(event);

        List<EventListener> listenersFor = listeners.get(event);

        for (EventListener listener : listenersFor)
        {
            listener.process(event, buffer, parameters);
        }
    }

    /**
     * Returns the listeners registered for the given event.
     * 
     * @param event the event used for retrieving listeners
     * @return the listeners registered for the given event
     * @throws UnknownEventException if the event is not registered
     * @throws IllegalArgumentException if the event is <code>null</code>
     */
    public List<EventListener> listenersFor(String event)
    {
        checkEventNotNull(event);
        checkEventRegistered(event);

        return listeners.get(event);
    }

    private void checkEventsNotNull(String[] events)
    {
        if (events == null)
        {
            throw new IllegalArgumentException("null is not accepted as a valid event.");
        }

        for (String event : events)
        {
            checkEventNotNull(event);
        }
    }

    /**
     * Returns the listener that is equal to the given listener.
     * <p>
     * The lookup works using <code>equals(Object)</code>.
     * 
     * @param listener the listener used for the lookup
     * @return the listener that is equal to the given listener
     * @throws UnknownListenerException if the listener is not found for any registered event
     */
    public EventListener get(EventListener listener)
    {
        for (String event : events)
        {
            List<EventListener> listeners = this.listeners.get(event);

            if (listeners.contains(listener))
            {
                return listeners.get(listeners.indexOf(listener));
            }
        }

        throw new UnknownListenerException(listener);
    }

    /**
     * Registers the events that this source can raise.
     * 
     * @param events the events that this source can raise
     * @throws IllegalArgumentException if one or more events are <code>null</code>
     */
    public void canRaise(String... events)
    {
        checkEventsNotNull(events);

        this.events.addAll(Arrays.asList(events));

        for (String event : events)
        {
            listeners.put(event, new ArrayList<EventListener>());
        }
    }

}
