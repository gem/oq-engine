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

import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertThat;
import static org.junit.Assert.assertTrue;
import static org.mockito.Matchers.anyObject;
import static org.mockito.Matchers.anyString;
import static org.mockito.Matchers.anyVararg;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import java.util.List;

import org.gem.engine.core.cache.Cache;
import org.gem.engine.core.cache.InMemoryCache;
import org.junit.Before;
import org.junit.Test;

public class EventSourceTest implements EventListener
{

    private static final String AN_EVENT = "ANEVENT";
    private static final String A_PARAMETER = "APARAMETER";
    private static final String ANOTHER_EVENT = "ANOTHEREVENT";
    private static final String ANOTHER_PARAMETER = "ANOTHERPARAMETER";
    private static final String UNREGISTERED_EVENT = "UNREGISTEREDEVENT";

    private EventSource source;

    @Before
    public void setUp()
    {
        source = new EventSource();
        source.canRaise(AN_EVENT, ANOTHER_EVENT);
    }

    @Test
    public void containsNoListenersWhenCreated1()
    {
        assertThat(sizeOf(listenersFor(AN_EVENT)), is(0));
    }

    @Test
    public void containsNoListenersWhenCreated2()
    {
        assertThat(sizeOf(listenersFor(ANOTHER_EVENT)), is(0));
    }

    @Test
    public void canAddAListenerToAnEvent()
    {
        source.on(AN_EVENT, this);
        assertThat(sizeOf(listenersFor(AN_EVENT)), is(1));
    }

    @Test
    public void canAddMultipleListenersToAnEvent()
    {
        source.on(AN_EVENT, this);
        source.on(AN_EVENT, this);
        assertThat(sizeOf(listenersFor(AN_EVENT)), is(2));
    }

    @Test
    public void canAddMultipleListenersToDifferentEvents()
    {
        source.on(AN_EVENT, this);
        source.on(ANOTHER_EVENT, this);
        source.on(ANOTHER_EVENT, this);

        assertThat(sizeOf(listenersFor(AN_EVENT)), is(1));
        assertThat(sizeOf(listenersFor(ANOTHER_EVENT)), is(2));
    }

    @Test
    public void shouldForwardTheParametersWhenThereAreRegisteredListeners()
    {
        Cache buffer = new InMemoryCache();
        EventListener listener1 = mock(EventListener.class);
        EventListener listener2 = mock(EventListener.class);

        source.on(AN_EVENT, listener1);
        source.on(AN_EVENT, listener2);
        source.raise(AN_EVENT, buffer, A_PARAMETER);

        // TODO Refactoring!
        assertListenerInvokedWith(listener1, AN_EVENT, buffer, A_PARAMETER);
        assertListenerInvokedWith(listener2, AN_EVENT, buffer, A_PARAMETER);
    }

    @Test
    public void shouldNotCallListenersRegisteredToOtherEvents()
    {
        EventListener listener = mock(EventListener.class);
        source.on(AN_EVENT, listener);

        // not interested in this event
        source.raise(ANOTHER_EVENT, null, A_PARAMETER, ANOTHER_PARAMETER);

        assertListenerNotInvoked(listener);
    }

    @Test(expected = UnknownListenerException.class)
    public void shouldThrowAnExceptionWhenLookupAnUnknowListener()
    {
        source.get(this);
    }

    @Test
    public void canLookupAListener()
    {
        source.on(AN_EVENT, this);
        assertTrue(this == source.get(this));
    }

    @Test(expected = UnknownEventException.class)
    public void shouldThrownAnExceptionOnUnknownEvents()
    {
        source.on(UNREGISTERED_EVENT, null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrownAnExceptionWhenGettingListenersForANullEvent()
    {
        source.listenersFor(null);
    }

    @Test(expected = UnknownEventException.class)
    public void shouldThrownAnExceptionWhenGettingListenersForAnUnknownEvent()
    {
        source.listenersFor(UNREGISTERED_EVENT);
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrownAnExceptionOnNullEvents()
    {
        source.on(null, null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrownAnExceptionWhenAttachingANullListener()
    {
        source.on(AN_EVENT, null);
    }

    @Test(expected = UnknownEventException.class)
    public void shouldThrownAnExceptionWhenRaisingAnUnknownEvent()
    {
        source.raise(UNREGISTERED_EVENT, null, (Object[]) null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrownAnExceptionWhenRaisingANullEvent()
    {
        source.raise(null, null, (Object[]) null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrownAnExceptionWhenRegisteringNullEvents1()
    {
        source.canRaise((String[]) null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrownAnExceptionWhenRegisteringNullEvents2()
    {
        source.canRaise(null, null);
    }

    private void assertListenerNotInvoked(EventListener listener)
    {
        verify(listener, times(0)).process(anyString(), (Cache) anyObject(), anyVararg());
    }

    private void assertListenerInvokedWith(EventListener listener, String event, Cache buffer, Object... parameters)
    {
        verify(listener).process(event, buffer, parameters);
    }

    private int sizeOf(List<EventListener> listeners)
    {
        return listeners.size();
    }

    private List<EventListener> listenersFor(String event)
    {
        return source.listenersFor(event);
    }

    @Override
    public void process(String event, Cache buffer, Object... parameters)
    {
        // TODO Auto-generated method stub
    }

}
