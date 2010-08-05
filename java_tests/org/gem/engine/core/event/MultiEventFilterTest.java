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

import org.gem.engine.core.cache.Cache;
import org.gem.engine.core.cache.InMemoryCache;
import org.gem.engine.core.cache.Pipe;
import org.junit.Before;
import org.junit.Test;

public class MultiEventFilterTest extends MultiEventFilter
{

    private static final String AN_EVENT = "ANEVENT";
    private static final String ANOTHER_EVENT = "ANOTHEREVENT";
    private static final Cache A_BUFFER = new InMemoryCache();

    private Pipe pipe;

    private boolean method1Called;
    private boolean method2Called;

    public void method1(Cache buffer, Pipe pipe)
    {
        method1Called = true;
        assertThat(this.pipe, is(pipe));
        assertThat(buffer, is(A_BUFFER));
    }

    public void method2(Cache buffer, Pipe pipe)
    {
        method2Called = true;
        assertThat(this.pipe, is(pipe));
        assertThat(buffer, is(A_BUFFER));
    }

    @Before
    public void setUp()
    {
        pipe = new Pipe();
    }

    @Test
    public void canDispatchAnEventToASpecificMethod()
    {
        dispatchTo(AN_EVENT, "method1");
        process(AN_EVENT, A_BUFFER, pipe);

        assertThat(method1Called, is(true));
    }

    @Test
    public void canDispatchDifferentEventsToDifferentMethods()
    {
        dispatchTo(AN_EVENT, "method1");
        dispatchTo(ANOTHER_EVENT, "method2");

        process(AN_EVENT, A_BUFFER, pipe);
        process(ANOTHER_EVENT, A_BUFFER, pipe);

        assertThat(method1Called, is(true));
        assertThat(method2Called, is(true));
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrowAnExceptionWhenTheMethodIsUnknown()
    {
        dispatchTo(AN_EVENT, "method1");
        process(ANOTHER_EVENT, A_BUFFER, pipe); // processing a different event
    }

}
