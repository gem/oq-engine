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

import static org.gem.engine.risk.core.AdditionalEvents.VALIDATION_FAILED;
import static org.gem.engine.risk.core.AdditionalEvents.VALIDATION_SUCCEEDED;
import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertThat;

import org.gem.engine.risk.core.event.listener.Validator;
import org.gem.engine.risk.core.validation.AlwaysFalseSpecification;
import org.gem.engine.risk.core.validation.AlwaysTrueSpecification;
import org.junit.Test;

public class ValidatorTest extends BaseFilterTest
{

    @Test
    public void shouldRaiseAnEventWhenTheValidationFails()
    {
        filter = new Validator(new AlwaysFalseSpecification());
        filter.on(VALIDATION_FAILED, this);

        runOn(anySite());
        assertPipeForwarded();
        assertThat(eventRaised, is(VALIDATION_FAILED));
    }

    @Test
    public void shouldRaiseAnEventWhenTheValidationSucceeds()
    {
        filter = new Validator(new AlwaysTrueSpecification());
        filter.on(VALIDATION_SUCCEEDED, this);

        runOn(anySite());
        assertPipeForwarded();
        assertThat(eventRaised, is(VALIDATION_SUCCEEDED));
    }

}
