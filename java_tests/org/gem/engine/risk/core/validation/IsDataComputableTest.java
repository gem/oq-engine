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

import org.gem.engine.risk.core.cache.Pipe;
import org.gem.engine.risk.core.validation.IsDataComputable;
import org.gem.engine.risk.data.Computable;
import org.junit.Before;
import org.junit.Test;

public class IsDataComputableTest
{

    private static final String TEST_KEY = "TESTKEY";

    private Pipe pipe;

    @Before
    public void setUp()
    {
        pipe = new Pipe();
    }

    @Test
    public void isSatisfiedWhenTheDataIdentifiedByTheGivenKeyIsComputable()
    {
        pipe.put(TEST_KEY, new Computable()
        {

            @Override
            public boolean isComputable()
            {
                return true;
            }
        });

        assertTrue(new IsDataComputable(TEST_KEY).isSatisfiedBy(pipe));
    }

    @Test
    public void notSatisfiedWhenTheDataIdentifiedByTheGivenKeyIsNotComputable()
    {
        pipe.put(TEST_KEY, new Computable()
        {

            @Override
            public boolean isComputable()
            {
                return false;
            }
        });

        assertFalse(new IsDataComputable(TEST_KEY).isSatisfiedBy(pipe));
    }

}
