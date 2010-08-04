package org.opensha.gem.GEM1.commons;

import java.io.IOException; 
import java.util.ArrayList;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.siteData.SiteDataValueList;
import org.opensha.commons.data.siteData.impl.WaldAllenGlobalVs30;
import org.opensha.commons.geo.LocationList;

public class Vs30Accessor {
	
	private WaldAllenGlobalVs30 topoSlopeVs30;
	
	public Vs30Accessor() throws IOException {
		topoSlopeVs30 = new WaldAllenGlobalVs30();
	}
	
	public SiteDataValueList<Double> getVs30(ArrayList<Site> sites) throws IOException {
		LocationList locs = new LocationList();
		for (Site site : sites) {
			locs.add(site.getLocation());
		}
		return topoSlopeVs30.getAnnotatedValues(locs);
	}
	
	public void setActiveTectonic() {
		topoSlopeVs30.getAdjustableParameterList().getParameter(WaldAllenGlobalVs30.COEFF_SELECT_PARAM_NAME)
			.setValue(WaldAllenGlobalVs30.COEFF_ACTIVE_NAME);
	}
	
	public void setStableContinent() {
		topoSlopeVs30.getAdjustableParameterList().getParameter(WaldAllenGlobalVs30.COEFF_SELECT_PARAM_NAME)
			.setValue(WaldAllenGlobalVs30.COEFF_STABLE_NAME);
	}

}
