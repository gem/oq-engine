package org.gem.calc;

import java.util.ArrayList;

import org.opensha.commons.data.Site;
import org.opensha.commons.geo.LocationList;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

public class NonPoissonianERF extends EqkRupForecast
{
	public class NonPoissonianEqkSource extends ProbEqkSource
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
