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

import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.cache.Pipe;
import org.gem.engine.risk.core.event.Filter;
import org.gem.engine.risk.core.validation.Specification;

/**
 * Checks if some business rules are satisfied by the current {@link Pipe}.
 * <p>
 * This filter raises:<br/>
 * <ul>
 * <li><code>Event.VALIDATION_SUCCEEDED</code> when the business rules are satisfied
 * <li><code>Event.VALIDATION_FAILED</code> when the business rules are not satisfied
 * </ul>
 * 
 * @author Andrea Cerisara
 * @version $Id: Validator.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class Validator extends Filter
{

    private final Specification specification;

    /**
     * @param specification the specification of the business rules
     */
    public Validator(Specification specification)
    {
        this.specification = specification;
        canRaise(VALIDATION_FAILED, VALIDATION_SUCCEEDED);
    }

    @Override
    protected void filter(Cache buffer, Pipe pipe)
    {
        if (specification.isSatisfiedBy(pipe))
        {
            raise(VALIDATION_SUCCEEDED, buffer, pipe);
        }
        else
        {
            raise(VALIDATION_FAILED, buffer, pipe);
        }
    }

}
