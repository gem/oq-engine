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

package org.gem.engine.risk.core.validation;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.gem.engine.risk.core.validation.AlwaysFalseSpecification;
import org.gem.engine.risk.core.validation.AlwaysTrueSpecification;
import org.gem.engine.risk.core.validation.AndSpecification;
import org.gem.engine.risk.core.validation.Specification;
import org.junit.Test;

public class AndSpecificationTest
{

    @Test
    public void isSatisfiedWhenAllAreSatisfied1()
    {
        assertTrue(new AndSpecification().isSatisfiedBy(null));
    }

    @Test
    public void isSatisfiedWhenAllAreSatisfied2()
    {
        assertTrue(new AndSpecification(new AlwaysTrueSpecification()).isSatisfiedBy(null));
    }

    @Test
    public void isSatisfiedWhenAllAreSatisfied3()
    {
        assertFalse(new AndSpecification(new AlwaysFalseSpecification()).isSatisfiedBy(null));
    }

    @Test
    public void isSatisfiedWhenAllAreSatisfied4()
    {
        Specification alwaysTrue = new AlwaysTrueSpecification();
        Specification alwaysFalse = new AlwaysFalseSpecification();
        assertFalse(new AndSpecification(alwaysFalse, alwaysTrue).isSatisfiedBy(null));
    }

    @Test
    public void isSatisfiedWhenAllAreSatisfied5()
    {
        Specification alwaysTrue1 = new AlwaysTrueSpecification();
        Specification alwaysTrue2 = new AlwaysFalseSpecification();
        assertFalse(new AndSpecification(alwaysTrue1, alwaysTrue2).isSatisfiedBy(null));
    }

}
