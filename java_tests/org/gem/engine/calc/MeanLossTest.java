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

package org.gem.engine.calc;

import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.gem.engine.data.FixedDiscreteFunction;
import org.junit.Before;
import org.junit.Test;

public class MeanLossTest
{

    private MeanLoss meanLoss;
    private ProbabilityOfOccurrence calculator;

    @Before
    public void setUp()
    {
        calculator = mock(ProbabilityOfOccurrence.class);
        FixedDiscreteFunction lossCurve = new FixedDiscreteFunction();

        lossCurve.addPair(0.21, 0.131);
        lossCurve.addPair(0.24, 0.108);
        lossCurve.addPair(0.27, 0.089);
        lossCurve.addPair(0.30, 0.066);

        meanLoss = new MeanLoss(lossCurve, calculator);
    }

    @Test
    public void zeroWhenTheCurveHasNoValues()
    {
        assertThat(new MeanLoss(new FixedDiscreteFunction(), calculator).compute(), is(0.0));
    }

    @Test
    public void compute()
    {
        when(calculator.compute(0.21)).thenReturn(1.0);
        when(calculator.compute(0.24)).thenReturn(1.0);
        when(calculator.compute(0.27)).thenReturn(1.0);
        when(calculator.compute(0.30)).thenReturn(1.0);

        assertThat(meanLoss.compute(), is(0.21 + 0.24 + 0.27 + 0.30));
    }

}
