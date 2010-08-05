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

import org.gem.engine.core.EngineTest;
import org.gem.engine.core.RegionTest;
import org.gem.engine.core.SiteTest;
import org.gem.engine.core.cache.InMemoryCacheTest;
import org.gem.engine.core.event.EventSourceTest;
import org.gem.engine.core.event.MultiEventFilterTest;
import org.gem.engine.core.event.MultiEventListenerTest;
import org.junit.runner.RunWith;
import org.junit.runners.Suite;
import org.junit.runners.Suite.SuiteClasses;

@RunWith(Suite.class)
@SuiteClasses( { EngineTest.class, RegionTest.class, SiteTest.class, EventSourceTest.class, InMemoryCacheTest.class,
        MultiEventFilterTest.class, MultiEventListenerTest.class })
public class RiskEngineCoreTests
{

}
