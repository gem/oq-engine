/*
    Copyright (c) 2010-2012, GEM Foundation.

    OpenQuake is free software: you can redistribute it and/or modify it
    under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenQuake is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
*/

package org.gem.calc;

import java.util.ArrayList;

import org.junit.Ignore;

import org.opensha.commons.data.Site;
import org.opensha.commons.geo.LocationList;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

@Ignore
public class NonPoissonianERF extends EqkRupForecast
{
	public static class NonPoissonianEqkSource extends ProbEqkSource
	{
		public boolean isPoissonianSource()
		{
			return false;
		}
		public LocationList getAllSourceLocs()
		{
			return null;
		}

		public EvenlyGriddedSurfaceAPI getSourceSurface()
		{
			return null;
		}

		public double getMinDistance(Site site)
		{
			return 0;
		}

		public int getNumRuptures()
		{
			return 0;
		}

		public ProbEqkRupture getRupture(int nRupture)
		{
			return null;
		}
	}

	private NonPoissonianEqkSource nonPossSource = new NonPoissonianEqkSource();

	@Override
	public void updateForecast() {}

	@Override
	public String getName()
	{
		return null;
	}

	@Override
	public int getNumSources()
	{
		return 1;
	}

	@Override
	public ProbEqkSource getSource(int iSource)
	{
		if (iSource == 0)
		{
			return nonPossSource;
		}
		return null;
	}

	@Override
	public ArrayList getSourceList()
	{
		ArrayList list = new ArrayList();
		list.add(nonPossSource);
		return list;
	}
}
