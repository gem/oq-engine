package org.opensha.gem.GEM1.util;

import java.util.ArrayList;

import org.opensha.commons.data.TimeSpan;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

public class GEM1ERFCreator {

	private static GEM1ERF erf;
	
	public GEM1ERFCreator (ArrayList<GEMSourceData> sourceDataList,
			double timeSpan){
		TimeSpan tms = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS);
		tms.setDuration(timeSpan);
		erf = new GEM1ERF(sourceDataList);
		erf.setTimeSpan(tms);
		erf.updateForecast();
	}

	public static GEM1ERF getErf() {
		return erf;
	}
}
