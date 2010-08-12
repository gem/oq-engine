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

import static org.hamcrest.Matchers.is;
import static org.hamcrest.Matchers.notNullValue;
import static org.junit.Assert.assertThat;

import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.cache.InMemoryCache;
import org.gem.engine.risk.core.event.MultiEventListener;
import org.junit.Test;

public class MultiEventListenerTest extends MultiEventListener
{

    private static final String AN_EVENT = "ANEVENT";
    private static final String ANOTHER_EVENT = "ANOTHEREVENT";
    private static final Cache A_BUFFER = new InMemoryCache();

    private boolean method1Called;
    private boolean method2Called;

    public void method1(Cache buffer, Object... parameters)
    {
        method1Called = true;
        assertThat(buffer, is(A_BUFFER));
        assertThat(parameters, is(notNullValue()));
    }

    public void method2(Cache buffer, Object... parameters)
    {
        method2Called = true;
        assertThat(buffer, is(A_BUFFER));
        assertThat(parameters, is(notNullValue()));
    }

    @Test
    public void canDispatchAnEventToASpecificMethod()
    {
        dispatchTo(AN_EVENT, "method1");
        process(AN_EVENT, A_BUFFER); // vararg with no values (empty array)

        assertThat(method1Called, is(true));
    }

    @Test
    public void canDispatchDifferentEventsToDifferentMethods()
    {
        dispatchTo(AN_EVENT, "method1");
        dispatchTo(ANOTHER_EVENT, "method2");

        process(AN_EVENT, A_BUFFER); // vararg with no values (empty array)
        process(ANOTHER_EVENT, A_BUFFER); // vararg with no values (empty array)

        assertThat(method1Called, is(true));
        assertThat(method2Called, is(true));
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrowAnExceptionWhenTheMethodIsUnknown()
    {
        dispatchTo(AN_EVENT, "method1");
        process(ANOTHER_EVENT, A_BUFFER, new Object()); // processing a different event
    }

}
